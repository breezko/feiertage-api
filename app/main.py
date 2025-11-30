from datetime import datetime
from typing import Any, Dict, Optional

import httpx
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import PlainTextResponse

FEIERTAGE_BASE_URL = "https://feiertage-api.de/api/"

VALID_STATES = {
    "NATIONAL",
    "BW",
    "BY",
    "BE",
    "BB",
    "HB",
    "HH",
    "HE",
    "MV",
    "NI",
    "NW",
    "RP",
    "SL",
    "SN",
    "ST",
    "SH",
    "TH",
}

app = FastAPI(
    title="Feiertage API Wrapper",
    version="1.0.0",
    description=(
        "Eigener Wrapper um https://feiertage-api.de – JSON passthrough und iCal-Export."
    ),
)


async def fetch_feiertage(
    jahr: int,
    nur_land: Optional[str],
    nur_daten: Optional[int],
) -> Dict[str, Any]:
    """Call the original feiertage-api.de endpoint and return the JSON data."""
    params: Dict[str, Any] = {"jahr": jahr}
    if nur_land:
        params["nur_land"] = nur_land
    if nur_daten is not None:
        params["nur_daten"] = nur_daten

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(FEIERTAGE_BASE_URL, params=params)
    except httpx.HTTPError as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Fehler beim Aufruf von feiertage-api.de: {exc}",
        ) from exc

    if resp.status_code != 200:
        raise HTTPException(
            status_code=resp.status_code,
            detail="Upstream-API hat einen Fehler zurückgegeben.",
        )

    try:
        data = resp.json()
    except ValueError as exc:
        raise HTTPException(
            status_code=502,
            detail="Ungültiges JSON von feiertage-api.de.",
        ) from exc

    if not isinstance(data, dict):
        raise HTTPException(
            status_code=502,
            detail="Unerwartetes Datenformat von feiertage-api.de.",
        )

    return data


def holidays_to_ical(holidays: Dict[str, Any], scope: str) -> str:
    """
    Convert feiertage-api.de JSON result to a simple iCalendar (.ics) string.

    Supports both formats:
    - {"Name": {"datum": "YYYY-MM-DD", "hinweis": "..."}}
    - {"Name": "YYYY-MM-DD"}  (nur_daten=1)
    """
    now = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//feiertage-wrapper//DE",
    ]

    def extract_date(value: Any) -> Optional[datetime]:
        if isinstance(value, dict):
            date_str = value.get("datum")
        else:
            date_str = str(value)

        if not date_str:
            return None

        try:
            # "YYYY-MM-DD"
            return datetime.fromisoformat(date_str)
        except ValueError:
            return None

    items = []
    for name, value in holidays.items():
        dt = extract_date(value)
        if dt is None:
            continue
        items.append((name, dt))

    # Sort events by date
    items.sort(key=lambda item: item[1])

    for name, dt in items:
        date_compact = dt.strftime("%Y%m%d")
        uid = f"{date_compact}-{scope}@feiertage-wrapper"
        lines.extend(
            [
                "BEGIN:VEVENT",
                f"UID:{uid}",
                f"DTSTAMP:{now}",
                f"DTSTART;VALUE=DATE:{date_compact}",
                f"SUMMARY:{name}",
                "END:VEVENT",
            ]
        )

    lines.append("END:VCALENDAR")
    return "\r\n".join(lines) + "\r\n"


@app.get("/")
async def get_feiertage(
    jahr: int = Query(..., ge=1970, le=2100, description="Welches Jahr?"),
    nur_land: Optional[str] = Query(
        None, description="Welches Bundesland? (z.B. BW, BY, … oder NATIONAL)"
    ),
    nur_daten: Optional[int] = Query(
        None, description="Nur Daten (1) oder auch Hinweise (0 / leer)?"
    ),
    format: str = Query(
        "json",
        pattern="^(json|ical)$",
        description="Antwortformat (json oder ical)",
    ),
):
    """
    Wrapper-Endpunkt:
    - format=json (Standard): JSON passthrough
    - format=ical: text/calendar (.ics) mit allen Feiertagen
    """
    if nur_land is not None and nur_land not in VALID_STATES:
        raise HTTPException(status_code=422, detail="Ungültiges Bundesland-Kürzel.")

    holidays = await fetch_feiertage(jahr=jahr, nur_land=nur_land, nur_daten=nur_daten)

    if format == "ical":
        scope = nur_land or "NATIONAL"
        ical = holidays_to_ical(holidays, scope=scope)
        return PlainTextResponse(content=ical, media_type="text/calendar")

    # Default: JSON passthrough
    return holidays


@app.get(
    "/ical",
    response_class=PlainTextResponse,
    summary="Direkter iCal-Endpunkt",
    description="Wie '/', aber gibt immer iCalendar zurück.",
)
async def get_feiertage_ical(
    jahr: int = Query(..., ge=1970, le=2100, description="Welches Jahr?"),
    nur_land: Optional[str] = Query(
        None, description="Welches Bundesland? (z.B. BW, BY, … oder NATIONAL)"
    ),
    nur_daten: Optional[int] = Query(
        None, description="Nur Daten (1) oder auch Hinweise (0 / leer)?"
    ),
):
    holidays = await fetch_feiertage(jahr=jahr, nur_land=nur_land, nur_daten=nur_daten)
    scope = nur_land or "NATIONAL"
    ical = holidays_to_ical(holidays, scope=scope)
    return PlainTextResponse(content=ical, media_type="text/calendar")
