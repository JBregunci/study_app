from urllib.parse import urlencode

from fastapi.responses import RedirectResponse

from .models import FeedbackMode


def redirect(url: str, msg: str | None = None, erro: str | None = None) -> RedirectResponse:
    params = {}
    if msg:
        params["msg"] = msg
    if erro:
        params["erro"] = erro
    if params:
        url = f"{url}?{urlencode(params)}"
    return RedirectResponse(url=url, status_code=303)


def parse_feedback_mode(
    value: str | None, default: FeedbackMode = FeedbackMode.immediate
) -> FeedbackMode:
    try:
        return FeedbackMode(value)
    except (TypeError, ValueError):
        return default


def parse_limit_seconds(value: str | None) -> int | None:
    if value is None:
        return None
    text = str(value).strip().replace(",", ".")
    if not text:
        return None
    try:
        minutes = float(text)
    except ValueError:
        return None
    if minutes <= 0:
        return None
    return int(round(minutes * 60))


def parse_int(value: str | None, default: int | None = None) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default
