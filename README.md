# Deutschland Feiertage 
[![Maven Central](https://img.shields.io/badge/feiertage--api.onrender.com%20-8A2BE2)](https://feiertage-api.onrender.com/)

*a.k.a "BundesAPI on steroids"*

---
Eigener kleiner Service, der die öffentliche API von  
[`https://feiertage-api.de`](https://feiertage-api.de/) kapselt und zusätzlich einen **iCal-Export** anbietet.

- JSON passthrough zu `feiertage-api.de`
- iCalendar (`.ics`) Feed für Kalender-Abos (Google Calendar, Apple Kalender, Outlook, …)
- Modernes Python-Setup mit [`uv`](https://docs.astral.sh/uv/) und FastAPI


Produktion:
- Base URL: [feiertage-api.onrender.com](https://feiertage-api.onrender.com/)
- Swagger: [feiertage-api.onrender.com/docs](https://feiertage-api.onrender.com/docs)


---

## Inhalt

- [Architektur](#architektur)
- [Voraussetzungen](#voraussetzungen)
- [Installation mit uv](#installation-mit-uv)
- [Lokale Entwicklung](#lokale-entwicklung)
- [API-Endpunkte](#api-endpunkte)
  - [`GET /`](#get-)
  - [`GET /ical`](#get-ical)
- [Beispiele](#beispiele)
  - [JSON](#json)
  - [iCal](#ical)
- [Lizenz](#lizenz)

---

## Architektur

Die Anwendung ist ein kleiner **FastAPI**-Service, der:

1. Anfragen entgegennimmt (`jahr`, `nur_land`, `nur_daten` …)
2. Diese an `https://feiertage-api.de/api/` weiterleitet
3. Die Antwort entweder
   - unverändert als JSON zurückgibt (**Passthrough**), oder
   - in ein **iCalendar (`text/calendar`)**-Dokument umwandelt und als `.ics` ausliefert.

Der Code sitzt in:

- `app/main.py` – FastAPI-Applikation inkl. iCal-Generierung
- `pyproject.toml` – Projekt- und Dependency-Definition für `uv`
- `uv.lock` – Lockfile (wird von `uv` erzeugt, nicht manuell anfassen)

---

## Voraussetzungen

- **Python**: empfohlen wird Python 3.12+
- **uv**: modernes Tool für Python-Management (virtuelle Envs, Dependencies, Scripts)

Installation von `uv` (einmalig, global), z. B. unter Windows PowerShell:

```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

---

## Installation mit uv

Im Projektverzeichnis:

```bash
# Abhängigkeiten installieren + venv/Lockfile verwalten
uv sync
```

Das liest die Abhängigkeiten aus `pyproject.toml` und erstellt/aktualisiert:

* ein lokales virtuelles Environment (`.venv`)
* das Lockfile `uv.lock`

---

## Lokale Entwicklung

### Development-Server (Auto-Reload)

```bash
uv run fastapi dev app/main.py
```

Standardmäßig läuft der Server dann unter:

* [http://127.0.0.1:8000](http://127.0.0.1:8000)

Developer-Dokumentation:

* Swagger UI: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
* ReDoc: [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)
* OpenAPI JSON: [http://127.0.0.1:8000/openapi.json](http://127.0.0.1:8000/openapi.json)


## API-Endpunkte

### `GET /`

**Beschreibung:**
Liefert Feiertage eines Jahres entweder als **JSON** (Standard) oder als **iCal**, je nach `format`-Parameter.

**Query-Parameter:**

* `jahr` (**required**, `int`)
  – Zieljahr (z. B. `2024`)

* `nur_land` (*optional*, `string`)
  – Bundesland-Kürzel, wie bei `feiertage-api.de`, z. B.:

  * `NATIONAL`, `BW`, `BY`, `BE`, `BB`, `HB`, `HH`, `HE`, `MV`,
    `NI`, `NW`, `RP`, `SL`, `SN`, `ST`, `SH`, `TH`

* `nur_daten` (*optional*, `int`)
  – Entspricht dem Upstream-Parameter (z. B. `1` für “nur Daten”)

* `format` (*optional*, `string`)
  – Antwortformat:

  * `json` (Standard)
  * `ical` (liefert `text/calendar`)

---

### `GET /ical`

**Beschreibung:**
Wie `/`, aber **immer** iCal-Ausgabe (`text/calendar`), ohne dass `format` gesetzt werden muss.

**Query-Parameter:**

* `jahr` (**required**, `int`)
* `nur_land` (*optional*, `string`)
* `nur_daten` (*optional*, `int`)

---

## Beispiele

### JSON

Alle Feiertage für 2025, bundesweit:

```http
GET /?jahr=2025
Accept: application/json
```

Feiertage 2025 nur in Baden-Württemberg:

```http
GET /?jahr=2025&nur_land=BW
Accept: application/json
```

### iCal

1. Über `format=ical` auf `/`:

```http
GET /?jahr=2025&nur_land=BY&format=ical
Accept: text/calendar
```

2. Direkt über `/ical`:

```http
GET /ical?jahr=2025&nur_land=BY
Accept: text/calendar
```

In beiden Fällen bekommst du ein `.ics`-Dokument, das du in Kalender-Apps abonnieren kannst.

---

## License

MIT
