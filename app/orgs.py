from __future__ import annotations

from .utils import slugify

AGENCY_LOGOS = {
    "bacen": "/static/img/orgs/bacen.svg",
    "demo": "/static/img/orgs/demo.svg",
}
DEFAULT_ORG_LOGO = "/static/img/orgs/generic.svg"
ALL_ORGS_LOGO = "/static/img/orgs/all.svg"


def logo_for_agency(agency: str | None) -> str:
    if not agency:
        return DEFAULT_ORG_LOGO
    return AGENCY_LOGOS.get(slugify(agency), DEFAULT_ORG_LOGO)
