#!/usr/bin/env python3
"""
Merges multiple ICS calendar feeds into one, tagging each event
with its source calendar's name (e.g. "[Mark] Dentist appointment").

Only keeps events from PAST_DAYS days ago to FUTURE_DAYS days ahead,
and converts all timed events to plain UTC (so no VTIMEZONE block is
needed) since the source feeds' VTIMEZONE definitions get dropped
once merged this way. This keeps the output small and in a form
widely-compatible calendar parsers (Google/Outlook/Apple/SwitchBot
etc.) expect.

Designed to run inside Home Assistant via shell_command + an
automation on a time_pattern trigger. Writes into /config/www so
the result is served at https://<your-ha-domain>/local/<OUTPUT_NAME>
without needing Home Assistant login (files in www/ are public if
the URL is known).
"""

import re
import os
import urllib.request
from datetime import datetime, timezone, timedelta
from zoneinfo import ZoneInfo

# ---- CONFIGURE THIS ----
CALENDARS = [
    {"name": "YOURNAME", "url": "CALENDARURL"},
    {"name": "SECONDNAME", "url": "CALENDARURL"}
]

# Use a non-obvious filename since /local/ files have no auth in front of them.
OUTPUT_NAME = "family-calendar.ics"
OUTPUT_DIR = "/config/www"
OUTPUT_FILE = os.path.join(OUTPUT_DIR, OUTPUT_NAME)

# How far back/forward to keep events. Keeps the feed small and avoids
# shipping years of historical events some CalDAV exports include.
PAST_DAYS = 365
FUTURE_DAYS = 365
# -------------------------

EVENT_RE = re.compile(r"BEGIN:VEVENT.*?END:VEVENT", re.DOTALL)
SUMMARY_RE = re.compile(r"^SUMMARY:(.*)$", re.MULTILINE)
SUMMARY_PARAM_RE = re.compile(r"^(SUMMARY;[^:]*):(.*)$", re.MULTILINE)
DT_LINE_RE = re.compile(r"^(DTSTART|DTEND)(;[^:]*)?:(.*)$", re.MULTILINE)
VALARM_RE = re.compile(r"BEGIN:VALARM.*?END:VALARM\n?", re.DOTALL)
DROP_PREFIXES = ("ATTENDEE", "ORGANIZER", "X-APPLE-", "CREATED", "LAST-MODIFIED")


def unfold(ics_text: str) -> str:
    # ICS folds long lines with a leading space/tab on the continuation line.
    text = re.sub(r"\r?\n[ \t]", "", ics_text)
    return text.replace("\r\n", "\n")


def fetch(url: str) -> str:
    with urllib.request.urlopen(url, timeout=20) as resp:
        return resp.read().decode("utf-8", errors="replace")


def get_params(params_str):
    if not params_str:
        return {}
    return dict(p.split("=", 1) for p in params_str.lstrip(";").split(";") if "=" in p)


def resolve_tzinfo(tzid: str):
    """Resolves a TZID to a tzinfo. Falls back to parsing fixed-offset
    style TZIDs like 'GMT+0100' or 'UTC-0400' that aren't valid IANA
    zone names but show up in some calendar exports (e.g. Eventbrite)."""
    try:
        return ZoneInfo(tzid)
    except Exception:
        pass
    m = re.match(r"^(?:GMT|UTC)?([+-])(\d{2}):?(\d{2})$", tzid)
    if m:
        sign, hh, mm = m.groups()
        offset = timedelta(hours=int(hh), minutes=int(mm))
        if sign == "-":
            offset = -offset
        return timezone(offset)
    return None


def parse_start(event_block):
    """Returns the event's start as a UTC datetime, or None if it can't be determined."""
    m = re.search(r"^DTSTART(;[^:]*)?:(.*)$", event_block, re.MULTILINE)
    if not m:
        return None
    params = get_params(m.group(1))
    value = m.group(2).strip()
    try:
        if params.get("VALUE") == "DATE":
            return datetime.strptime(value[:8], "%Y%m%d").replace(tzinfo=timezone.utc)
        if value.endswith("Z"):
            return datetime.strptime(value[:-1], "%Y%m%dT%H%M%S").replace(tzinfo=timezone.utc)
        tzid = params.get("TZID")
        dt = datetime.strptime(value, "%Y%m%dT%H%M%S")
        if tzid:
            tzinfo = resolve_tzinfo(tzid)
            if tzinfo is not None:
                dt = dt.replace(tzinfo=tzinfo)
                return dt.astimezone(timezone.utc)
            return None  # unknown tzid — can't safely place in the window, keep it
        return dt.replace(tzinfo=timezone.utc)  # floating time, treat as UTC for filtering
    except Exception:
        return None


def normalize_dt(match):
    """Converts DTSTART/DTEND lines with a TZID into plain UTC (Z) so no
    VTIMEZONE block is required in the merged output."""
    prop, params_str, value = match.group(1), match.group(2), match.group(3).strip()
    params = get_params(params_str)
    if params.get("VALUE") == "DATE":
        return f"{prop};VALUE=DATE:{value}"
    tzid = params.get("TZID")
    if tzid:
        tzinfo = resolve_tzinfo(tzid)
        if tzinfo is not None:
            try:
                dt = datetime.strptime(value, "%Y%m%dT%H%M%S").replace(tzinfo=tzinfo)
                dt_utc = dt.astimezone(timezone.utc)
                return f"{prop}:{dt_utc.strftime('%Y%m%dT%H%M%SZ')}"
            except Exception:
                pass
    return match.group(0)  # already UTC (Z) or floating — leave as-is


def clean_event(event_block: str) -> str:
    event_block = VALARM_RE.sub("", event_block)
    lines = event_block.split("\n")
    lines = [l for l in lines if not any(l.startswith(p) for p in DROP_PREFIXES)]
    cleaned = "\n".join(lines)
    return DT_LINE_RE.sub(normalize_dt, cleaned)


def tag_event(event_block: str, name: str) -> str:
    tagged = SUMMARY_RE.sub(lambda m: f"SUMMARY:[{name}] {m.group(1)}", event_block)
    tagged = SUMMARY_PARAM_RE.sub(lambda m: f"{m.group(1)}:[{name}] {m.group(2)}", tagged)
    return tagged


def main():
    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//Merged Calendar//EN",
        "CALSCALE:GREGORIAN",
    ]

    now = datetime.now(timezone.utc)
    window_start = now - timedelta(days=PAST_DAYS)
    window_end = now + timedelta(days=FUTURE_DAYS)

    for cal in CALENDARS:
        try:
            text = unfold(fetch(cal["url"]))
            events = EVENT_RE.findall(text)
            kept = 0
            for ev in events:
                start = parse_start(ev)
                if start is not None and not (window_start <= start <= window_end):
                    continue
                cleaned = clean_event(ev)
                lines.append(tag_event(cleaned, cal["name"]))
                kept += 1
            print(f"{cal['name']}: kept {kept} of {len(events)} events")
        except Exception as e:
            print(f"Warning: failed to fetch {cal['name']} ({cal['url']}): {e}")

    lines.append("END:VCALENDAR")

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    with open(OUTPUT_FILE, "w") as f:
        f.write("\r\n".join(lines) + "\r\n")

    print(f"Wrote {OUTPUT_FILE}")


if __name__ == "__main__":
    main()