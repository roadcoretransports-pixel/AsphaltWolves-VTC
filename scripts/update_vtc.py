#!/usr/bin/env python3

"""
AsphaltWolves - TruckersMP VTC updater

VTC ID:
    92769

Output:
    data/vtc.json

Endpoints:
    /vtc/{id}
    /vtc/{id}/members
    /vtc/{id}/news
    /vtc/{id}/events
"""

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


# ============================================================
# CONFIGURATION
# ============================================================

VTC_ID = os.getenv("VTC_ID", "92769")

API_BASE = "https://api.truckersmp.com/v2"

VTC_URL = f"https://truckersmp.com/vtc/{VTC_ID}"

OUTPUT_FILE = Path("data/vtc.json")

TIMEOUT = 30


# ============================================================
# HELPERS
# ============================================================

def utc_now():
    """Return current UTC timestamp in ISO 8601 format."""
    return datetime.now(timezone.utc).isoformat()


def request_json(endpoint):
    """
    Request JSON from TruckersMP.

    Returns:
        {
            "ok": bool,
            "status": int,
            "data": dict/list/None,
            "error": str/None
        }
    """

    url = f"{API_BASE}{endpoint}"

    request = Request(
        url,
        headers={
            "Accept": "application/json",
            "User-Agent": "AsphaltWolves-VTC-Bot/1.0"
        },
        method="GET"
    )

    try:

        with urlopen(request, timeout=TIMEOUT) as response:

            status = response.status

            raw = response.read().decode("utf-8")

            if not raw:
                return {
                    "ok": False,
                    "status": status,
                    "data": None,
                    "error": "Empty response"
                }

            try:
                data = json.loads(raw)

            except json.JSONDecodeError:
                return {
                    "ok": False,
                    "status": status,
                    "data": None,
                    "error": "Response was not valid JSON"
                }

            return {
                "ok": True,
                "status": status,
                "data": data,
                "error": None
            }

    except HTTPError as error:

        return {
            "ok": False,
            "status": error.code,
            "data": None,
            "error": f"HTTP {error.code}"
        }

    except URLError as error:

        return {
            "ok": False,
            "status": 0,
            "data": None,
            "error": f"Network error: {error.reason}"
        }

    except TimeoutError:

        return {
            "ok": False,
            "status": 0,
            "data": None,
            "error": "Request timeout"
        }

    except Exception as error:

        return {
            "ok": False,
            "status": 0,
            "data": None,
            "error": str(error)
        }


def extract_list(data, possible_keys):
    """
    Extract an array from different possible API response structures.
    """

    if isinstance(data, list):
        return data

    if not isinstance(data, dict):
        return []

    for key in possible_keys:

        value = data.get(key)

        if isinstance(value, list):
            return value

    response = data.get("response")

    if isinstance(response, list):
        return response

    if isinstance(response, dict):

        for key in possible_keys:

            value = response.get(key)

            if isinstance(value, list):
                return value

    return []


# ============================================================
# VTC
# ============================================================

def parse_vtc(result):
    """
    Parse VTC information.
    """

    if not result["ok"]:
        return {
            "success": False,
            "data": None
        }

    data = result["data"]

    if not isinstance(data, dict):
        return {
            "success": False,
            "data": None
        }

    vtc = data.get("response", data)

    if not isinstance(vtc, dict):
        return {
            "success": False,
            "data": None
        }

    return {
        "success": True,
        "data": {
            "id": vtc.get("id", int(VTC_ID)),
            "name": vtc.get("name", "AsphaltWolves"),
            "url": VTC_URL,

            "tag": vtc.get("tag"),
            "owner": vtc.get("owner"),
            "language": vtc.get("language"),
            "verified": vtc.get("verified"),

            "createdAt":
                vtc.get("created_at")
                or vtc.get("createdAt")
        }
    }


# ============================================================
# MEMBERS
# ============================================================

def parse_members(result):
    """
    Parse VTC members and calculate driver count.
    """

    if not result["ok"]:

        return {
            "success": False,
            "driverCount": 0,
            "members": []
        }

    members = extract_list(
        result["data"],
        [
            "members",
            "users",
            "drivers"
        ]
    )

    normalized = []

    for member in members:

        if not isinstance(member, dict):
            continue

        normalized.append({

            "id":
                member.get("id"),

            "username":
                member.get("username")
                or member.get("name"),

            "role":
                member.get("role"),

            "joinDate":
                member.get("joinDate")
                or member.get("join_date")
                or member.get("joined_at"),

            "steamId":
                member.get("steam_id")
                or member.get("steamId"),

            "truckersmpId":
                member.get("truckersmp_id")
                or member.get("truckersmpId")
                or member.get("id")

        })

    return {
        "success": True,
        "driverCount": len(normalized),
        "members": normalized
    }


# ============================================================
# NEWS
# ============================================================

def parse_news(result):
    """
    Parse VTC news.
    """

    if not result["ok"]:
        return {
            "success": False,
            "news": []
        }

    news_items = extract_list(
        result["data"],
        [
            "news",
            "items"
        ]
    )

    normalized = []

    for item in news_items[:20]:

        if not isinstance(item, dict):
            continue

        normalized.append({

            "id":
                item.get("id"),

            "title":
                item.get("title")
                or item.get("name")
                or "TruckersMP News",

            "description":
                item.get("description")
                or item.get("content")
                or "",

            "date":
                item.get("date")
                or item.get("created_at")
                or item.get("createdAt"),

            "url":
                item.get("url")
                or item.get("link")

        })

    return {
        "success": True,
        "news": normalized
    }


# ============================================================
# EVENTS
# ============================================================

def parse_events(result):
    """
    Parse VTC events.
    """

    if not result["ok"]:
        return {
            "success": False,
            "events": []
        }

    event_items = extract_list(
        result["data"],
        [
            "events",
            "items"
        ]
    )

    normalized = []

    for item in event_items[:20]:

        if not isinstance(item, dict):
            continue

        normalized.append({

            "id":
                item.get("id"),

            "name":
                item.get("name")
                or item.get("title")
                or "TruckersMP Event",

            "description":
                item.get("description")
                or "",

            "start":
                item.get("start")
                or item.get("start_at")
                or item.get("startDate"),

            "end":
                item.get("end")
                or item.get("end_at")
                or item.get("endDate"),

            "url":
                item.get("url")
                or item.get("link")

        })

    return {
        "success": True,
        "events": normalized
    }


# ============================================================
# MAIN
# ============================================================

def main():

    print("==========================================")
    print(" AsphaltWolves TruckersMP Updater")
    print("==========================================")
    print(f"VTC ID: {VTC_ID}")
    print()

    # --------------------------------------------------------
    # Request all endpoints
    # --------------------------------------------------------

    print("Fetching VTC information...")

    vtc_result = request_json(
        f"/vtc/{VTC_ID}"
    )

    print(
        f"  VTC: "
        f"{'OK' if vtc_result['ok'] else 'FAILED'} "
        f"(HTTP {vtc_result['status']})"
    )

    print("Fetching members...")

    members_result = request_json(
        f"/vtc/{VTC_ID}/members"
    )

    print(
        f"  Members: "
        f"{'OK' if members_result['ok'] else 'FAILED'} "
        f"(HTTP {members_result['status']})"
    )

    print("Fetching news...")

    news_result = request_json(
        f"/vtc/{VTC_ID}/news"
    )

    print(
        f"  News: "
        f"{'OK' if news_result['ok'] else 'FAILED'} "
        f"(HTTP {news_result['status']})"
    )

    print("Fetching events...")

    events_result = request_json(
        f"/vtc/{VTC_ID}/events"
    )

    print(
        f"  Events: "
        f"{'OK' if events_result['ok'] else 'FAILED'} "
        f"(HTTP {events_result['status']})"
    )

    print()


    # --------------------------------------------------------
    # Parse
    # --------------------------------------------------------

    vtc = parse_vtc(vtc_result)

    members = parse_members(
        members_result
    )

    news = parse_news(
        news_result
    )

    events = parse_events(
        events_result
    )


    # --------------------------------------------------------
    # Determine overall status
    # --------------------------------------------------------

    results = [
        vtc_result,
        members_result,
        news_result,
        events_result
    ]

    successful = sum(
        1 for result in results
        if result["ok"]
    )

    if successful == 4:
        status = "live"

    elif successful == 0:
        status = "unavailable"

    else:
        status = "partial"


    # --------------------------------------------------------
    # Diagnostics
    # --------------------------------------------------------

    diagnostics = {

        "vtc":
            vtc_result["ok"],

        "members":
            members_result["ok"],

        "news":
            news_result["ok"],

        "events":
            events_result["ok"],

        "httpStatus": {

            "vtc":
                vtc_result["status"],

            "members":
                members_result["status"],

            "news":
                news_result["status"],

            "events":
                events_result["status"]

        }

    }


    # --------------------------------------------------------
    # Build output
    # --------------------------------------------------------

    output = {

        "success": True,

        "source": "TruckersMP",

        "status": status,

        "vtc": {

            "id": int(VTC_ID),

            "name":
                (
                    vtc["data"]["name"]
                    if vtc["data"]
                    else "AsphaltWolves"
                ),

            "url": VTC_URL,

            "driverCount":
                members["driverCount"]

        },

        "members":
            members["members"],

        "news":
            news["news"],

        "events":
            events["events"],

        "updatedAt":
            utc_now(),

        "diagnostics":
            diagnostics

    }


    # --------------------------------------------------------
    # Important safety check
    #
    # Never overwrite a known good live dataset with
    # completely unavailable data.
    # --------------------------------------------------------

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    if status == "unavailable" and OUTPUT_FILE.exists():

        print(
            "TruckersMP is unavailable."
        )

        print(
            "Keeping existing data/vtc.json."
        )

        print(
            "No fake driver count will be written."
        )

        return 0


    # --------------------------------------------------------
    # Write JSON
    # --------------------------------------------------------

    with OUTPUT_FILE.open(
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            output,
            file,
            indent=2,
            ensure_ascii=False
        )

        file.write("\n")


    # --------------------------------------------------------
    # Summary
    # --------------------------------------------------------

    print()
    print("==========================================")
    print(" Update complete")
    print("==========================================")

    print(
        f"Status: {status}"
    )

    print(
        f"Drivers: {members['driverCount']}"
    )

    print(
        f"News: {len(news['news'])}"
    )

    print(
        f"Events: {len(events['events'])}"
    )

    print(
        f"Output: {OUTPUT_FILE}"
    )

    # --------------------------------------------------------
    # Exit with error if TruckersMP is unavailable.
    #
    # This makes the GitHub Actions run clearly visible
    # as failed instead of silently pretending everything
    # worked.
    # --------------------------------------------------------

    if status == "unavailable":

        print()
        print(
            "WARNING: TruckersMP could not be reached."
        )

        print(
            "The workflow will be marked as failed."
        )

        return 1

    return 0


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":
    sys.exit(main())
