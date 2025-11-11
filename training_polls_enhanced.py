#!/usr/bin/env python3
"""Configurable training poll manager driven entirely by Google Sheets."""

import asyncio
import datetime
import json
import os
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

import gspread
from dotenv import load_dotenv
from google.oauth2.service_account import Credentials
from telegram import Bot

from datetime_utils import get_moscow_time, log_current_time
from enhanced_duplicate_protection import duplicate_protection

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
ANNOUNCEMENTS_TOPIC_ID = os.getenv("ANNOUNCEMENTS_TOPIC_ID")
GOOGLE_SHEETS_CREDENTIALS = os.getenv("GOOGLE_SHEETS_CREDENTIALS")
SPREADSHEET_ID = os.getenv("SPREADSHEET_ID")

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

TRAINING_SHEET_HEADER = [
    "Дата создания",
    "ID опроса",
    "Название",
    "Дата тренировки",
    "Время",
    "Локация",
    "Варианты ответа",
]

WEEKDAY_NAMES = [
    "понедельник",
    "вторник",
    "среда",
    "четверг",
    "пятница",
    "суббота",
    "воскресенье",
]

DEFAULT_POLL_OPTIONS = [
    "✅ Приду",
    "❌ Не смогу",
    "🤔 Уточню позже",
]


@dataclass
class TrainingPollConfig:
    """Represents one poll definition taken from the service sheet."""

    title: str
    weekday: int
    time: Optional[datetime.time]
    location: str
    options: List[str] = field(default_factory=list)
    topic_id: Optional[int] = None
    allows_multiple_answers: bool = True
    is_anonymous: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)
    raw: Dict[str, Any] = field(default_factory=dict)

    def unique_base(self) -> str:
        """Returns a stable base string for duplicate detection."""
        candidates: List[Any] = [
            self.metadata.get("unique_key"),
            self.metadata.get("key"),
            self.metadata.get("id"),
            self.raw.get("title"),
            self.title,
        ]
        for candidate in candidates:
            if candidate:
                return str(candidate).strip()
        return f"weekday_{self.weekday}"


class TrainingPollsManager:
    """Manages training polls using configuration stored in Google Sheets."""

    def __init__(self) -> None:
        self.bot: Optional[Bot] = None
        self.gc: Optional[gspread.Client] = None
        self.spreadsheet: Optional[gspread.Spreadsheet] = None
        self.chat_id: Optional[Any] = self._resolve_chat_id(CHAT_ID)
        self.default_topic_id: Optional[int] = self._parse_topic_id(ANNOUNCEMENTS_TOPIC_ID)
        self._training_sheet_cache: Optional[gspread.Worksheet] = None

        self._init_bot()
        self._init_google_sheets()
    
    def _init_bot(self) -> None:
        if BOT_TOKEN:
            self.bot = Bot(token=BOT_TOKEN)
            print("✅ Telegram bot initialised")
        else:
            print("⚠️ BOT_TOKEN is not configured; poll creation is disabled")

    def _init_google_sheets(self) -> None:
        if not GOOGLE_SHEETS_CREDENTIALS and not os.path.exists("google_credentials.json"):
            print("⚠️ GOOGLE_SHEETS_CREDENTIALS is not configured; Google Sheets logging disabled")
            return

        try:
            if os.path.exists("google_credentials.json"):
                with open("google_credentials.json", "r", encoding="utf-8") as fp:
                    creds_payload = json.load(fp)
                print("✅ Loaded Google credentials from google_credentials.json")
            else:
                creds_payload = json.loads(GOOGLE_SHEETS_CREDENTIALS)
                print("✅ Loaded Google credentials from environment variable")
            
            creds = Credentials.from_service_account_info(creds_payload, scopes=SCOPES)
            self.gc = gspread.authorize(creds)
            
            if SPREADSHEET_ID:
                self.spreadsheet = self.gc.open_by_key(SPREADSHEET_ID)
                print("✅ Connected to Google Sheets spreadsheet")
            else:
                print("⚠️ SPREADSHEET_ID is not provided; sheet logging disabled")
        except Exception as error:
            print(f"❌ Failed to initialise Google Sheets: {error}")

    async def create_configured_polls(self) -> bool:
        """Creates polls for all configs found in the service sheet."""
        if not self.bot or self.chat_id is None:
            print("❌ Bot or CHAT_ID is not configured; skip poll creation")
            return False

        configs = self._load_configs()
        if not configs:
            print("ℹ️ No training poll configurations found in the service sheet")
            return False
        
        created_any = False
        for config in configs:
            try:
                created = await self._create_poll(config)
                created_any = created_any or created
            except Exception as error:
                print(f"❌ Failed to create poll '{config.title}': {error}")
        return created_any

    def _load_configs(self) -> List[TrainingPollConfig]:
        snapshot = duplicate_protection.get_config_ids()
        raw_configs = snapshot.get("training_polls", []) or []

        configs: List[TrainingPollConfig] = []
        for raw in raw_configs:
            metadata = raw.get("metadata") if isinstance(raw.get("metadata"), dict) else {}

            weekday = self._parse_weekday(raw.get("weekday") or metadata.get("weekday"))
            if weekday is None:
                print(f"⚠️ Skipping training poll config with invalid weekday: {raw}")
                continue

            title = (raw.get("title") or metadata.get("title") or "Тренировка").strip()
            location = (raw.get("location") or metadata.get("location") or "").strip()
            time_obj = self._parse_time(raw.get("time") or metadata.get("time"))
            topic_id = self._parse_topic_id(raw.get("topic_id") or metadata.get("topic_id"))

            options_source = raw.get("options") or metadata.get("options") or []
            options = self._normalize_options(options_source)

            allows_multiple = metadata.get("allows_multiple_answers")
            if allows_multiple is None:
                allows_multiple = True

            is_anonymous = bool(metadata.get("is_anonymous", False))

            config = TrainingPollConfig(
                title=title,
                weekday=weekday,
                time=time_obj,
                location=location,
                options=options,
                topic_id=topic_id,
                allows_multiple_answers=bool(allows_multiple),
                is_anonymous=is_anonymous,
                metadata=metadata,
                raw=raw,
            )
            configs.append(config)

        return configs

    async def _create_poll(self, config: TrainingPollConfig) -> bool:
        scheduled_dt = self._get_next_occurrence(config.weekday, config.time)
        unique_key = self._build_unique_key(config, scheduled_dt)

        duplicate = duplicate_protection.check_duplicate("ОПРОС_ТРЕНИРОВКА", unique_key)
        if duplicate.get("exists"):
            print(f"ℹ️ Poll '{config.title}' for {scheduled_dt.date()} already exists; skip")
            return False
    
        question = self._build_question(config, scheduled_dt)
        thread_id = config.topic_id if config.topic_id is not None else self.default_topic_id

        poll_message = await self.bot.send_poll(
            chat_id=self.chat_id,
            question=question,
            options=config.options,
            is_anonymous=config.is_anonymous,
            allows_multiple_answers=config.allows_multiple_answers,
            message_thread_id=thread_id,
        )

        now = self.get_moscow_time()
        poll_info = {
            "unique_key": unique_key,
            "title": config.title,
            "question": question,
            "options": config.options,
            "poll_id": poll_message.poll.id,
            "message_id": poll_message.message_id,
            "chat_id": self.chat_id,
            "topic_id": thread_id,
            "scheduled_datetime": scheduled_dt.isoformat(),
            "created_at": now.isoformat(),
            "location": config.location,
        }

        self._persist_poll_info(poll_info)
        self._log_poll_to_sheet(config, scheduled_dt, poll_info)

        duplicate_protection.add_record(
            data_type="ОПРОС_ТРЕНИРОВКА",
            identifier=unique_key,
            status="АКТИВЕН",
            additional_data=question,
            settings=json.dumps(
                self._build_settings_payload(config, scheduled_dt),
                ensure_ascii=False,
            ),
        )

        print(f"✅ Created training poll '{config.title}' for {scheduled_dt.date()}")
        return True
        
    def _persist_poll_info(self, poll_info: Dict[str, Any]) -> None:
        path = "current_poll_info.json"
        existing: Dict[str, Any] = {}

        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as fp:
                    existing = json.load(fp)
            except (json.JSONDecodeError, OSError):
                existing = {}

        records = existing.get("polls", []) if isinstance(existing.get("polls"), list) else []
        records = [entry for entry in records if entry.get("unique_key") != poll_info["unique_key"]]
        records.append(poll_info)

        payload = {
            "updated_at": self.get_moscow_time().isoformat(),
            "polls": records,
        }

        with open(path, "w", encoding="utf-8") as fp:
            json.dump(payload, fp, ensure_ascii=False, indent=2)

    def _log_poll_to_sheet(
        self,
        config: TrainingPollConfig,
        scheduled_dt: datetime.datetime,
        poll_info: Dict[str, Any],
    ) -> None:
        worksheet = self._ensure_training_sheet()
        if not worksheet:
            return

        row = [
            self._format_datetime_for_sheet(self.get_moscow_time()),
            poll_info["poll_id"],
            config.title,
            scheduled_dt.strftime("%d.%m.%Y"),
            config.time.strftime("%H:%M") if config.time else "",
            config.location,
            ", ".join(config.options),
        ]

        try:
            worksheet.insert_row(row, index=2)
        except Exception as error:
            print(f"⚠️ Failed to log poll to training sheet: {error}")

    def _ensure_training_sheet(self) -> Optional[gspread.Worksheet]:
        if not self.spreadsheet:
            return None
            
        if self._training_sheet_cache:
            return self._training_sheet_cache
            
        try:
            worksheet = self.spreadsheet.worksheet("Тренировки")
        except gspread.WorksheetNotFound:
            worksheet = self.spreadsheet.add_worksheet(title="Тренировки", rows=500, cols=10)

        header = worksheet.row_values(1)
        normalized = [value.strip() for value in header] if header else []

        if normalized != TRAINING_SHEET_HEADER:
            end_col = chr(ord("A") + len(TRAINING_SHEET_HEADER) - 1)
            worksheet.update(
                f"A1:{end_col}1",
                [TRAINING_SHEET_HEADER],
            )

        self._training_sheet_cache = worksheet
        return worksheet

    def _build_settings_payload(
        self,
        config: TrainingPollConfig,
        scheduled_dt: datetime.datetime,
    ) -> Dict[str, Any]:
        payload = {
            "title": config.title,
            "weekday": config.weekday,
            "weekday_name": WEEKDAY_NAMES[config.weekday],
            "time": config.time.strftime("%H:%M") if config.time else None,
            "location": config.location,
            "scheduled_iso": scheduled_dt.isoformat(),
            "options": config.options,
            "topic_id": config.topic_id,
            "allows_multiple_answers": config.allows_multiple_answers,
            "is_anonymous": config.is_anonymous,
        }
        if config.metadata:
            payload["metadata"] = config.metadata
        return payload

    def _build_question(self, config: TrainingPollConfig, scheduled_dt: datetime.datetime) -> str:
        weekday_name = WEEKDAY_NAMES[config.weekday].capitalize()
        date_str = scheduled_dt.strftime("%d.%m")
        time_str = config.time.strftime("%H:%M") if config.time else ""

        primary_line = f"🗓️ {config.title} · {weekday_name} {date_str}"
        if time_str:
            primary_line = f"{primary_line}, {time_str}"

        lines = [primary_line]
        if config.location:
            lines.append(f"📍 {config.location}")

        note = config.metadata.get("note") or config.metadata.get("description")
        if note:
            lines.append(str(note))

        return "\n".join(lines)

    def _build_unique_key(self, config: TrainingPollConfig, scheduled_dt: datetime.datetime) -> str:
        base = self._slugify(config.unique_base())
        date_part = scheduled_dt.strftime("%Y%m%d")
        time_part = config.time.strftime("%H%M") if config.time else "0000"
        return f"{base}_{date_part}_{time_part}"

    def _slugify(self, value: str) -> str:
        slug = value.strip().lower()
        replacements = [" ", ".", ",", ":", ";", "/", "\\", "|", "@", "#", "!", "?", "&"]
        for symbol in replacements:
            slug = slug.replace(symbol, "_")
        slug = "_".join(part for part in slug.split("_") if part)
        return slug or "poll"

    def _parse_weekday(self, value: Any) -> Optional[int]:
        if value is None:
            return None
        if isinstance(value, int) and 0 <= value <= 6:
            return value
        if isinstance(value, str):
            normalized = value.strip().lower()
            mapping = {
                "0": 0,
                "1": 1,
                "2": 2,
                "3": 3,
                "4": 4,
                "5": 5,
                "6": 6,
                "mon": 0,
                "tue": 1,
                "wed": 2,
                "thu": 3,
                "fri": 4,
                "sat": 5,
                "sun": 6,
            }
            mapping.update({name: idx for idx, name in enumerate(WEEKDAY_NAMES)})
            return mapping.get(normalized)
        return None

    def _parse_time(self, value: Any) -> Optional[datetime.time]:
        if not value:
            return None
        if isinstance(value, datetime.time):
            return value
        if isinstance(value, (int, float)):
            total_minutes = int(value)
            hours, minutes = divmod(total_minutes, 60)
            try:
                return datetime.time(hour=hours % 24, minute=minutes % 60)
            except ValueError:
                return None
        if isinstance(value, str):
            sanitized = value.strip().replace(".", ":")
            for fmt in ("%H:%M", "%H:%M:%S"):
                try:
                    parsed = datetime.datetime.strptime(sanitized, fmt)
                    return parsed.time()
                except ValueError:
                    continue
        return None

    def _parse_topic_id(self, value: Any) -> Optional[int]:
        if value in (None, "", 0):
            return None
        try:
            return int(str(value).strip())
        except (TypeError, ValueError):
            return None

    def _normalize_options(self, options: Any) -> List[str]:
        if not options:
            return DEFAULT_POLL_OPTIONS.copy()

        if isinstance(options, str):
            options = [options]

        normalized: List[str] = []
        for option in options:
            if not isinstance(option, str):
                continue
            text = option.strip()
            if text and text not in normalized:
                normalized.append(text)

        if len(normalized) < 2:
            for fallback in DEFAULT_POLL_OPTIONS:
                if fallback not in normalized:
                    normalized.append(fallback)
            normalized = normalized[: max(2, len(normalized))]

        return normalized

    def _get_next_occurrence(self, weekday: int, time_obj: Optional[datetime.time]) -> datetime.datetime:
        now = self.get_moscow_time()
        current_weekday = now.weekday()
        days_ahead = (weekday - current_weekday) % 7
        if days_ahead == 0 and time_obj and now.time() >= time_obj:
            days_ahead = 7
        target_date = now.date() + datetime.timedelta(days=days_ahead)
        time_component = time_obj or datetime.time(hour=10, minute=0)
        target_dt = datetime.datetime.combine(target_date, time_component)
        return target_dt.replace(tzinfo=now.tzinfo)

    def _resolve_chat_id(self, value: Optional[str]) -> Optional[Any]:
        if not value:
            return None
        candidate = value.strip()
        if candidate.startswith("@"):
            return candidate
        try:
            return int(candidate)
        except ValueError:
            return candidate

    def _format_datetime_for_sheet(self, dt: datetime.datetime) -> str:
        return dt.strftime("%d.%m.%Y %H:%M")

    def get_moscow_time(self) -> datetime.datetime:
        return get_moscow_time()


async def main() -> None:
    print("🏀 TRAINING POLL MANAGER")
    print("=" * 40)
    time_info = log_current_time()
    print(f"🕒 Current Moscow time: {time_info['formatted_datetime']}")

    manager = TrainingPollsManager()
    created = await manager.create_configured_polls()

    if created:
        print("✅ At least one poll has been created")
    else:
        print("ℹ️ No polls were created during this run")


if __name__ == "__main__":
    asyncio.run(main())

