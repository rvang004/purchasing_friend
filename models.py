"""Validated domain models for Purchase Bot.

These are intentionally stdlib-only. Pydantic is lovely, but adding a new
runtime dependency before the project truly needs it would be peak yak-shaving.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, time
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
from decimal import Decimal, InvalidOperation
from typing import Any

VALID_SCHEDULE_TYPES = {
    "once",
    "daily",
    "weekly",
    "once_window",
    "daily_window",
    "weekly_window",
}
VALID_WEEKDAYS = {"Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"}
WINDOW_SCHEDULE_TYPES = {"once_window", "daily_window", "weekly_window"}
TIMEZONE_ALIASES = {
    "CT": "America/Chicago",
    "CST": "America/Chicago",
    "CDT": "America/Chicago",
    "ET": "America/New_York",
    "EST": "America/New_York",
    "EDT": "America/New_York",
    "MT": "America/Denver",
    "MST": "America/Denver",
    "MDT": "America/Denver",
    "PT": "America/Los_Angeles",
    "PST": "America/Los_Angeles",
    "PDT": "America/Los_Angeles",
}


def is_window_schedule(schedule_type: str) -> bool:
    """Return True when a schedule type uses a start/end time window."""
    return schedule_type in WINDOW_SCHEDULE_TYPES


def parse_time_string(value: Any, *, field_name: str = "time") -> time:
    """Parse human-friendly time strings into a time value.

    Supported examples: 20:00, 20:00:00, 8:00 PM, 8:00:00 PM.
    Seconds are accepted for input friendliness, but scheduler checks are still
    minute-oriented by default. Precision cosplay is how bugs get tiny hats.
    """
    if isinstance(value, time):
        return value.replace(second=0, microsecond=0)
    raw = str(value or "").strip().upper()
    for fmt in ("%H:%M", "%H:%M:%S", "%I:%M %p", "%I:%M:%S %p"):
        try:
            parsed = datetime.strptime(raw, fmt).time()
            return parsed.replace(second=0, microsecond=0)
        except ValueError:
            continue
    raise ValueError(f"{field_name} must be a time like HH:MM or 8:00 PM")


def normalize_time_string(value: Any, *, field_name: str = "time") -> str:
    """Normalize supported time strings to HH:MM."""
    return parse_time_string(value, field_name=field_name).strftime("%H:%M")


def normalize_timezone(value: Any) -> str | None:
    """Normalize optional timezone names and common US aliases.

    `CST` maps to America/Chicago because people usually mean Central Time,
    not fixed UTC-6 all year. Time zones are hard because humans invented lunch.
    """
    raw = str(value or "").strip()
    if not raw:
        return None
    normalized = TIMEZONE_ALIASES.get(raw.upper(), raw)
    try:
        ZoneInfo(normalized)
    except ZoneInfoNotFoundError as exc:
        raise ValueError(f"invalid timezone: {raw!r}") from exc
    return normalized


def parse_money(value: Any, *, default: Decimal | None = None) -> Decimal:
    """Parse money values safely as Decimal."""
    if value is None:
        if default is not None:
            return default
        raise ValueError("money value is required")

    try:
        amount = Decimal(str(value))
    except (InvalidOperation, ValueError) as exc:
        raise ValueError(f"invalid money value: {value!r}") from exc

    if amount < Decimal("0"):
        raise ValueError("money value cannot be negative")
    return amount.quantize(Decimal("0.01"))


def money_to_json(value: Decimal | None) -> float | None:
    """Convert Decimal money to JSON-friendly float."""
    return None if value is None else float(value)


def parse_optional_datetime(value: Any) -> datetime | None:
    """Parse ISO datetime/date-ish strings into datetime when possible."""
    if not value:
        return None
    if isinstance(value, datetime):
        return value
    if not isinstance(value, str):
        raise ValueError("datetime value must be an ISO string")

    normalized = value.replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(normalized)
    except ValueError:
        # Backward compatibility for old configs storing YYYY-MM-DD only.
        try:
            return datetime.fromisoformat(f"{value}T00:00:00")
        except ValueError as exc:
            raise ValueError(f"invalid ISO datetime: {value!r}") from exc


@dataclass(frozen=True)
class ShippingAddress:
    """Optional checkout address."""

    full_name: str = ""
    line1: str = ""
    line2: str = ""
    city: str = ""
    state: str = ""
    zip_code: str = ""
    country: str = "US"

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> "ShippingAddress | None":
        if not data:
            return None
        return cls(
            full_name=str(data.get("full_name", "")).strip(),
            line1=str(data.get("line1", "")).strip(),
            line2=str(data.get("line2", "")).strip(),
            city=str(data.get("city", "")).strip(),
            state=str(data.get("state", "")).strip(),
            zip_code=str(data.get("zip_code", "")).strip(),
            country=str(data.get("country", "US")).strip() or "US",
        )

    def to_dict(self) -> dict[str, str]:
        return {
            "full_name": self.full_name,
            "line1": self.line1,
            "line2": self.line2,
            "city": self.city,
            "state": self.state,
            "zip_code": self.zip_code,
            "country": self.country,
        }


@dataclass(frozen=True)
class Account:
    """Validated account settings without exposing behavior."""

    id: str
    site: str
    email: str
    password: str
    payment_method: str
    monthly_limit: Decimal
    price_limit_per_item: Decimal | None = None
    price_limit_enabled: bool = True
    quantity_limit_per_item: int | None = None
    shipping_address: ShippingAddress | None = None
    spent_this_month: Decimal = Decimal("0.00")

    @classmethod
    def from_dict(cls, account_id: str, data: dict[str, Any]) -> "Account":
        if not account_id:
            raise ValueError("account id is required")
        if not data.get("site"):
            raise ValueError(f"account {account_id}: site is required")
        if not data.get("email"):
            raise ValueError(f"account {account_id}: email is required")

        qty_limit = data.get("quantity_limit_per_item")
        if qty_limit in ("", None):
            qty_limit = None
        else:
            qty_limit = int(qty_limit)
            if qty_limit < 1:
                raise ValueError("quantity limit must be at least 1")

        price_limit = data.get("price_limit_per_item")
        parsed_price_limit = None if price_limit in ("", None) else parse_money(price_limit)

        return cls(
            id=account_id,
            site=str(data["site"]).strip(),
            email=str(data["email"]).strip(),
            password=str(data.get("password", "")),
            payment_method=str(data.get("payment_method", "credit_card")),
            monthly_limit=parse_money(data.get("monthly_limit", "0")),
            price_limit_per_item=parsed_price_limit,
            price_limit_enabled=bool(data.get("price_limit_enabled", True)),
            quantity_limit_per_item=qty_limit,
            shipping_address=ShippingAddress.from_dict(data.get("shipping_address")),
            spent_this_month=parse_money(data.get("spent_this_month", "0")),
        )


@dataclass
class PurchaseTask:
    """Validated purchase task."""

    id: str
    account_id: str
    product_url: str
    schedule_type: str
    run_time: str = ""
    quantity: int = 1
    enabled: bool = True
    created: str | None = None
    last_run: str | None = None
    days: list[str] = field(default_factory=list)
    start_time: str | None = None
    end_time: str | None = None
    timezone: str | None = None
    last_run_window: str | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "PurchaseTask":
        task_id = str(data.get("id", "")).strip()
        if not task_id:
            raise ValueError("task id is required")

        schedule_type = str(data.get("schedule_type", "once")).strip()
        if schedule_type not in VALID_SCHEDULE_TYPES:
            raise ValueError(f"task {task_id}: invalid schedule_type {schedule_type!r}")

        if is_window_schedule(schedule_type):
            run_time = ""
            start_time = normalize_time_string(
                data.get("start_time"),
                field_name=f"task {task_id}: start_time",
            )
            end_time = normalize_time_string(
                data.get("end_time"),
                field_name=f"task {task_id}: end_time",
            )
        else:
            run_time = normalize_time_string(
                data.get("run_time"),
                field_name=f"task {task_id}: run_time",
            )
            start_time = None
            end_time = None

        timezone = normalize_timezone(data.get("timezone"))

        quantity = int(data.get("quantity", 1))
        if quantity < 1:
            raise ValueError(f"task {task_id}: quantity must be at least 1")

        account_id = str(data.get("account_id", "")).strip()
        product_url = str(data.get("product_url", "")).strip()
        if not account_id:
            raise ValueError(f"task {task_id}: account_id is required")
        if not product_url:
            raise ValueError(f"task {task_id}: product_url is required")

        days = [str(day).strip() for day in data.get("days", []) if str(day).strip()]
        if schedule_type in {"weekly", "weekly_window"}:
            invalid_days = [day for day in days if day not in VALID_WEEKDAYS]
            if not days:
                raise ValueError(f"task {task_id}: weekly tasks require days")
            if invalid_days:
                raise ValueError(f"task {task_id}: invalid weekly days {invalid_days}")

        last_run = data.get("last_run")
        parse_optional_datetime(last_run)
        last_run_window = data.get("last_run_window")
        if last_run_window:
            try:
                datetime.strptime(str(last_run_window), "%Y-%m-%d")
            except ValueError as exc:
                raise ValueError(f"task {task_id}: last_run_window must be YYYY-MM-DD") from exc

        return cls(
            id=task_id,
            account_id=account_id,
            product_url=product_url,
            schedule_type=schedule_type,
            run_time=run_time,
            quantity=quantity,
            enabled=bool(data.get("enabled", True)),
            created=data.get("created"),
            last_run=last_run,
            days=days,
            start_time=start_time,
            end_time=end_time,
            timezone=timezone,
            last_run_window=last_run_window,
        )

    def to_dict(self) -> dict[str, Any]:
        data = {
            "id": self.id,
            "account_id": self.account_id,
            "product_url": self.product_url,
            "schedule_type": self.schedule_type,
            "run_time": self.run_time,
            "quantity": self.quantity,
            "enabled": self.enabled,
            "created": self.created,
            "last_run": self.last_run,
        }
        if self.days:
            data["days"] = self.days
        if self.start_time:
            data["start_time"] = self.start_time
        if self.end_time:
            data["end_time"] = self.end_time
        if self.timezone:
            data["timezone"] = self.timezone
        if self.last_run_window:
            data["last_run_window"] = self.last_run_window
        return data

    @property
    def last_run_date(self):
        parsed = parse_optional_datetime(self.last_run)
        return parsed.date() if parsed else None


@dataclass(frozen=True)
class PurchaseResult:
    """Normalized result for audit/history."""

    task_id: str
    account_id: str
    success: bool
    product_url: str
    timestamp: str
    error: str | None = None
    item_price: Decimal | None = None
    quantity: int = 1
    order_total: Decimal | None = None
    dry_run: bool = False
    mode: str | None = None
    review_required: bool = False
    artifact_dir: str | None = None
    screenshots: list[str] = field(default_factory=list)
    trace_path: str | None = None
    adapter: str | None = None
    final_url: str | None = None

    @classmethod
    def from_engine_result(
        cls,
        task: PurchaseTask,
        account_id: str,
        result: dict[str, Any],
        *,
        dry_run: bool,
    ) -> "PurchaseResult":
        quantity = int(result.get("quantity") or task.quantity)
        item_price = result.get("item_price")
        parsed_price = None if item_price in (None, "") else parse_money(item_price)
        order_total = result.get("order_total")
        parsed_total = None if order_total in (None, "") else parse_money(order_total)
        if parsed_total is None and parsed_price is not None:
            parsed_total = (parsed_price * Decimal(quantity)).quantize(Decimal("0.01"))

        return cls(
            task_id=task.id,
            account_id=account_id,
            success=bool(result.get("success", False)),
            product_url=str(result.get("product_url") or task.product_url),
            timestamp=str(result.get("timestamp") or datetime.now().isoformat()),
            error=result.get("error"),
            item_price=parsed_price,
            quantity=quantity,
            order_total=parsed_total,
            dry_run=dry_run,
            mode=result.get("mode"),
            review_required=bool(result.get("review_required", False)),
            artifact_dir=result.get("artifact_dir"),
            screenshots=list(result.get("screenshots", [])),
            trace_path=result.get("trace_path"),
            adapter=result.get("adapter"),
            final_url=result.get("final_url"),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "task_id": self.task_id,
            "account_id": self.account_id,
            "success": self.success,
            "product_url": self.product_url,
            "timestamp": self.timestamp,
            "error": self.error,
            "item_price": money_to_json(self.item_price),
            "quantity": self.quantity,
            "order_total": money_to_json(self.order_total),
            "dry_run": self.dry_run,
            "mode": self.mode,
            "review_required": self.review_required,
            "artifact_dir": self.artifact_dir,
            "screenshots": self.screenshots,
            "trace_path": self.trace_path,
            "adapter": self.adapter,
            "final_url": self.final_url,
        }
