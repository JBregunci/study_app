from pathlib import Path

from fastapi.templating import Jinja2Templates

from .config import APP_NAME
from .utils import to_local

TEMPLATES_DIR = Path(__file__).resolve().parent / "templates"
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


def fmt_duration(seconds) -> str:
    if seconds is None:
        return "—"
    total = max(0, int(seconds))
    if total < 60:
        return f"{total}s"
    minutes, secs = divmod(total, 60)
    if minutes < 60:
        return f"{minutes}m {secs:02d}s"
    hours, minutes = divmod(minutes, 60)
    return f"{hours}h {minutes:02d}m"


def fmt_clock(seconds) -> str:
    total = max(0, int(seconds or 0))
    hours, remainder = divmod(total, 3600)
    minutes, secs = divmod(remainder, 60)
    if hours:
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    return f"{minutes:02d}:{secs:02d}"


def fmt_datetime(value) -> str:
    local = to_local(value)
    if local is None:
        return "—"
    return local.strftime("%d/%m/%Y às %H:%M")


def fmt_date(value) -> str:
    if value is None:
        return "—"
    if hasattr(value, "hour"):
        value = to_local(value).date()
    return value.strftime("%d/%m/%Y")


def fmt_minutes(seconds) -> str:
    if not seconds:
        return "Sem limite"
    minutes = round(seconds / 60, 1)
    if minutes == int(minutes):
        return f"{int(minutes)} min"
    return f"{minutes:.1f} min"


def pct(correct, total) -> int:
    if not total:
        return 0
    return round(correct * 100 / total)


templates.env.filters["duration"] = fmt_duration
templates.env.filters["clock"] = fmt_clock
templates.env.filters["datetime"] = fmt_datetime
templates.env.filters["date"] = fmt_date
templates.env.filters["minutes"] = fmt_minutes
templates.env.globals["app_name"] = APP_NAME
templates.env.globals["pct"] = pct
