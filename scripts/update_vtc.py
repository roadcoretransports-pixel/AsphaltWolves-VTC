#!/usr/bin/env python3

"""
AsphaltWolves - TruckersMP VTC updater
VTC ID: 92769
Output: data/vtc.json
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
    return datetime.now(timezone.utc).isoformat()


def request_json(endpoint):
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


def first_nonempty(data, keys):
    if not isinstance(data, dict):
        return None

    for key in keys:
        value = data.get(key)
        if value not in (None, ""):
            return value

    return None


# ============================================================
# VTC
# ============================================================

def parse_vtc(result):
    if not result["ok"]:
        return {"success": False, "data": None}

    data = result["data"]

    if not isinstance(data, dict):
        return {"success": False, "data": None}

    vtc = data.get("response", data)

    if not isinstance(vtc, dict):
        return {"success": False, "data": None}

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
            "createdAt": (
                vtc.get("created_at")
                or vtc.get("createdAt")
            )
        }
    }


# ============================================================
# MEMBERS
# ============================================================

def parse_members(result):
    if not result["ok"]:
        return {
            "success": False,
            "driverCount": 0,
            "members": []
        }

    members = extract_list(
        result["data"],
        ["members", "users", "drivers"]
    )

    normalized = []

    for member in members:
        if not isinstance(member, dict):
            continue

        normalized.append({
            "id": member.get("id"),
            "username": (
                member.get("username")
                or member.get("name")
            ),
            "role": member.get("role"),
            "joinDate": (
                member.get("joinDate")
                or member.get("join_date")
                or member.get("joined_at")
            ),
            "steamId": (
                member.get("steam_id")
                or member.get("steamId")
            ),
            "truckersmpId": (
                member.get("truckersmp_id")
                or member.get("truckersmpId")
                or member.get("id")
            )
        })

    return {
        "success": True,
        "driverCount": len(normalized),
        "members": normalized
    }


# ============================================================
# NEWS
# ============================================================

def fetch_news_details(news_id):
    """
    Try to retrieve the full article.
    If TruckersMP blocks the request, use overview data instead.
    """

    if not news_id:
        return None

    result = request_json(
        f"/vtc/{VTC_ID}/news/{news_id}"
    )

    if not result["ok"]:
        print(
            f"    News {news_id} details unavailable "
            f"(HTTP {result['status']})"
        )
        return None

    data = result["data"]

    if isinstance(data, dict):
        article = data.get("response", data)

        if isinstance(article, dict):
            nested = article.get("news")

            if isinstance(nested, dict):
                article = nested

            return article

    return None


def parse_news(result):
    if not result["ok"]:
        return {
            "success": False,
            "news": []
        }

    news_items = extract_list(
        result["data"],
        ["news", "items"]
    )

    normalized = []

    for item in news_items[:20]:
        if not isinstance(item, dict):
            continue

        news_id = item.get("id")
        details = fetch_news_details(news_id) or {}

        title = (
            first_nonempty(details, ["title", "name"])
            or first_nonempty(item, ["title", "name"])
            or "TruckersMP News"
        )

        description = (
            first_nonempty(
                details,
                ["description", "content", "body", "text"]
            )
            or first_nonempty(
                item,
                ["description", "content", "body", "text"]
            )
            or ""
        )

        date = (
            first_nonempty(
                details,
                ["date", "created_at", "createdAt", "published_at"]
            )
            or first_nonempty(
                item,
                ["date", "created_at", "createdAt", "published_at"]
            )
        )

        url = (
            first_nonempty(details, ["url", "link"])
            or first_nonempty(item, ["url", "link"])
        )

        if not url and news_id:
            url = f"{VTC_URL}/news/{news_id}"

        normalized.append({
            "id": news_id,
            "title": title,
            "description": description,
            "date": date,
            "url": url
        })

    return {
        "success": True,
        "news": normalized
    }


# ============================================================
# EVENTS
# ============================================================

def parse_events(result):
    if not result["ok"]:
        return {
            "success": False,
            "events": []
        }

    event_items = extract_list(
        result["data"],
        ["events", "items"]
    )

    normalized = []

    for item in event_items[:20]:
        if not isinstance(item, dict):
            continue

        normalized.append({
            "id": item.get("id"),
            "name": (
                item.get("name")
                or item.get("title")
                or "TruckersMP Event"
            ),
            "description": item.get("description") or "",
            "start": (
                item.get("start")
                or item.get("start_at")
                or item.get("startDate")
            ),
            "end": (
                item.get("end")
                or item.get("end_at")
                or item.get("endDate")
            ),
            "url": (
                item.get("url")
                or item.get("link")
            )
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

    print("Fetching VTC information...")
    vtc_result = request_json(f"/vtc/{VTC_ID}")

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
    print("  Trying to retrieve full article details...")

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

    vtc = parse_vtc(vtc_result)
    members = parse_members(members_result)
    news = parse_news(news_result)
    events = parse_events(events_result)

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

    diagnostics = {
        "vtc": vtc_result["ok"],
        "members": members_result["ok"],
        "news": news_result["ok"],
        "events": events_result["ok"],
        "httpStatus": {
            "vtc": vtc_result["status"],
            "members": members_result["status"],
            "news": news_result["status"],
            "events": events_result["status"]
        }
    }

    output = {
        "success": True,
        "source": "TruckersMP",
        "status": status,
        "vtc": {
            "id": int(VTC_ID),
            "name": (
                vtc["data"]["name"]
                if vtc["data"]
                else "AsphaltWolves"
            ),
            "url": VTC_URL,
            "driverCount": members["driverCount"]
        },
        "members": members["members"],
        "news": news["news"],
        "events": events["events"],
        "updatedAt": utc_now(),
        "diagnostics": diagnostics
    }

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    # Keep existing data if every TruckersMP endpoint fails.
    if status == "unavailable" and OUTPUT_FILE.exists():
        print("TruckersMP is unavailable.")
        print("Keeping existing data/vtc.json.")
        print("No fake driver count will be written.")
        return 0

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

    print()
    print("==========================================")
    print(" Update complete")
    print("==========================================")
    print(f"Status: {status}")
    print(f"Drivers: {members['driverCount']}")
    print(f"News: {len(news['news'])}")
    print(f"Events: {len(events['events'])}")
    print(f"Output: {OUTPUT_FILE}")

    if status == "unavailable":
        print()
        print("WARNING: TruckersMP could not be reached.")
        print("The workflow will be marked as failed.")
        return 1

    return 0


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":
    sys.exit(main())
