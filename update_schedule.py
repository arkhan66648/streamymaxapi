#!/usr/bin/env python3

import re, json, hashlib, os, sys, urllib.request, urllib.error
from datetime import datetime, timedelta, timezone
from pathlib import Path

PROG_URL = "https://sportsonline.st/prog.txt"

CATEGORIES = [
    {"id": 14, "name": "American-football", "sport_code": "American-football", "image": "https://kora-api.top/uploads/categories/category_14.png", "keywords": ["nfl", "american football", "cfb", "ncaa football"]},
    {"id": 4,  "name": "Basketball",        "sport_code": "basketball", "image": "https://kora-api.top/uploads/categories/category_4.png", "keywords": ["nba", "basketball", "wnba"]},
    {"id": 13, "name": "Baseball",           "sport_code": "Baseball",  "image": "https://kora-api.top/uploads/categories/category_13.png", "keywords": ["mlb", "baseball"]},
    {"id": 16, "name": "Hockey",             "sport_code": "hockey",    "image": "https://kora-api.top/uploads/categories/category_16.png", "keywords": ["nhl", "hockey"]},
    {"id": 15, "name": "Motor-sports",       "sport_code": "motor-sports", "image": "https://kora-api.top/uploads/categories/category_15.png", "keywords": ["f1", "gp", "grand prix", "motogp", "nascar", "formula", "rally"]},
    {"id": 99, "name": "Tennis",             "sport_code": "tennis",    "image": "https://kora-api.top/uploads/categories/category_99.png", "keywords": ["tennis", "atp", "wta"]},
    {"id": 18, "name": "Fight",              "sport_code": "Fight",     "image": "https://kora-api.top/uploads/categories/category_18.png", "keywords": ["boxing", "fight"]},
    {"id": 17, "name": "Fight",              "sport_code": "Fight",     "image": "https://kora-api.top/uploads/categories/category_17.png", "keywords": ["ufc", "mma"]},
    {"id": 20, "name": "WWE",                "sport_code": "wwe",       "image": "", "keywords": ["wwe", "wrestling"]},
    {"id": 9,  "name": "Football",           "sport_code": "Soccer",    "image": "https://static.vecteezy.com/system/resources/previews/015/720/560/non_2x/abstract-creative-football-illustration-isolated-on-transparent-background-free-png.png", "keywords": ["soccer", "football", "premier", "liga", "serie", "bundesliga", "ligue", "champions", "europa", "mls", "copa", "vs", " x "]},
]

ADMIN_CHANNELS = [
    {"id": "admin-rally-tv",       "name": "Rally TV",       "category_name": "Motor-sports", "sport_code": "motor-sports", "url": "https://embed.st/embed/admin/admin-rally-tv/1",       "lang": "English", "streams_count": 1},
    {"id": "admin-tennis-channel", "name": "Tennis Channel",  "category_name": "Tennis",       "sport_code": "tennis",       "url": "https://embed.st/embed/admin/admin-tennis-channel/1", "lang": "English", "streams_count": 2},
    {"id": "admin-willow-cricket", "name": "Willow Cricket",  "category_name": "Cricket",      "sport_code": "cricket",      "url": "https://embed.st/embed/admin/admin-willow-cricket/1", "lang": "English", "streams_count": 6},
]

DAY_HEADER = re.compile(r"^[A-Z]+$")
EVENT_LINE = re.compile(r"^(\d{2}:\d{2})\s+(.+?)\s*\|\s*(https?://\S+)$")
CHANNEL_LINE = re.compile(r"^((HD|BR)\d+)")


def detect_category(event_name):
    name_lower = event_name.lower()
    for cat in CATEGORIES:
        for kw in cat["keywords"]:
            if kw in name_lower:
                return cat
    return {"id": 0, "name": "Other", "sport_code": "other", "image": ""}


def get_numeric_id(event_name):
    n = int(hashlib.md5(event_name.lower().encode()).hexdigest()[:8], 16)
    return 10000 + (n % 90000)


def get_string_id(event_name, slug):
    return f"event-{slug}"


def get_slug(event_name):
    slug = event_name.lower()
    for p in [':', '\u2013', '-', '(', ')']:
        slug = slug.replace(p, ' ')
    slug = re.sub(r'[^a-z0-9\s]', '', slug)
    return re.sub(r'\s+', '-', slug.strip())


def extract_teams(name):
    for sep in [" vs ", " x ", " - "]:
        if sep in name:
            parts = name.split(sep)
            return [parts[0].strip(), parts[1].strip()] if len(parts) >= 2 else []
    return []


def detect_lang_from_url(url):
    url_lower = url.lower()
    if "/pt/" in url_lower or "sporttv" in url_lower:
        return "Portuguese"
    if "/bra/" in url_lower or "/br" in url_lower:
        return "Brazilian"
    if "/hd/" in url_lower:
        return "English"
    if "/it/" in url_lower:
        return "Italian"
    if "/es/" in url_lower:
        return "Spanish"
    if "/de/" in url_lower:
        return "German"
    if "/fr/" in url_lower:
        return "French"
    return "English"


def fetch_prog():
    print(f"Fetching {PROG_URL}...")
    req = urllib.request.Request(PROG_URL, headers={
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/plain, */*",
        "Referer": "https://sportsonline.st/",
    })
    with urllib.request.urlopen(req, timeout=30) as r:
        content = r.read().decode('utf-8')
    print(f"Fetched {len(content)} chars")
    return content


def parse_prog(content):
    lines = content.split('\n')
    matches = []
    current_day = None
    for line in lines:
        line = line.strip()
        if not line:
            continue
        if DAY_HEADER.match(line) and len(line) <= 20:
            current_day = line.upper()
            continue
        if CHANNEL_LINE.match(line):
            continue
        m = EVENT_LINE.match(line)
        if m and current_day:
            time_str, event_name, url = m.groups()
            event_name = event_name.strip()
            if not event_name:
                continue
            category = detect_category(event_name)
            teams = extract_teams(event_name)
            slug = get_slug(event_name)
            match = {
                "id": get_numeric_id(event_name),
                "string_id": get_string_id(event_name, slug),
                "slug": slug,
                "name": event_name,
                "category": category,
                "teams": teams,
                "time": time_str,
                "day": current_day,
                "url": url,
                "is_live": False,
            }
            lang = detect_lang_from_url(url)
            match["streams"] = [{"url": url, "lang": lang}]
            matches.append(match)
    return matches


def day_to_date(day_name, time_str):
    day_map = {
        "MONDAY": 0, "TUESDAY": 1, "WEDNESDAY": 2, "THURSDAY": 3,
        "FRIDAY": 4, "SATURDAY": 5, "SUNDAY": 6
    }
    target = day_map.get(day_name.upper())
    if target is None:
        return None
    now = datetime.now()
    today = now.weekday()
    diff = target - today
    if diff < 0:
        diff += 7
    target_date = now + timedelta(days=diff)
    return target_date.strftime("%Y-%m-%d")


""" ── PRIMARY FORMAT (api/matches.json) ──
    Matches ws.kora-api.space/api/matches
    Numeric IDs, popular field, description, game_name, logos
"""
def build_primary_matches(parsed):
    out = []
    for m in parsed:
        date_str = day_to_date(m["day"], m["time"])
        if not date_str:
            continue
        begin_at = f"{date_str}T{m['time']}:00Z"
        has_teams = len(m["teams"]) > 1
        if has_teams:
            description = f"{m['teams'][0]} at {m['teams'][1]} - {m['teams'][0][:3].upper()} @ {m['teams'][1][:3].upper()}"
            game_name = f"{m['teams'][0]} at {m['teams'][1]}"
        else:
            description = m["name"]
            game_name = None
        out.append({
            "id": m["id"],
            "name": m["name"],
            "description": description,
            "game_name": game_name,
            "category": {
                "id": m["category"]["id"],
                "name": m["category"]["name"],
                "sport_code": m["category"]["sport_code"],
                "image": m["category"]["image"],
            },
            "logo_team1": "",
            "logo_team2": "",
            "begin_at": begin_at,
            "end_at": None,
            "is_live": False,
            "popular": False,
            "streams": m["streams"],
        })
    return out


""" ── STREAMED FORMAT (api/streamed/matches.json) ──
    Matches ws.kora-api.space/api/streamed/matches
    String IDs, is_popular field, null category id/image, includes admin channels
"""
def build_streamed_matches(parsed):
    out = []
    for ch in ADMIN_CHANNELS:
        streams = [{"url": ch["url"], "lang": ch["lang"]}]
        for i in range(2, ch["streams_count"] + 1):
            parts = ch["url"].rsplit("/", 1)
            streams.append({"url": f"{parts[0]}/{i}", "lang": ch["lang"] if i <= 2 else ch["lang"]})
        out.append({
            "id": ch["id"],
            "name": ch["name"],
            "description": None,
            "game_name": None,
            "category": {"id": None, "name": ch["category_name"], "sport_code": ch["sport_code"], "image": None},
            "logo_team1": None,
            "logo_team2": None,
            "begin_at": None,
            "end_at": None,
            "is_live": False,
            "is_popular": True,
            "streams": streams,
        })
    for m in parsed:
        date_str = day_to_date(m["day"], m["time"])
        begin_at = f"{date_str}T{m['time']}:00Z" if date_str else None
        has_teams = len(m["teams"]) > 1
        out.append({
            "id": m["string_id"],
            "name": m["name"],
            "description": None,
            "game_name": None,
            "category": {"id": None, "name": m["category"]["name"], "sport_code": m["category"]["sport_code"], "image": None},
            "logo_team1": None,
            "logo_team2": None,
            "begin_at": begin_at,
            "end_at": None,
            "is_live": False,
            "is_popular": has_teams,
            "streams": m["streams"],
        })
    return out


""" ── SOCCER FORMAT (api/matches/{date}/1.json) ──
    Matches ws.kora-api.space/api/matches/YYYY-MM-DD/1
    home/away, league, score, edges
"""
def build_soccer_matches(parsed):
    matches = []
    live_ids = []
    for m in parsed:
        if m["category"]["name"] != "Football":
            continue
        home = m["teams"][0] if len(m["teams"]) > 0 else m["name"]
        away = m["teams"][1] if len(m["teams"]) > 1 else ""
        league_name = m["name"].split(" vs ")[0] if " vs " in m["name"] else (m["name"].split(" x ")[0] if " x " in m["name"] else "Soccer")
        matches.append({
            "id": m["id"],
            "home": home,
            "away": away,
            "home_en": home,
            "away_en": away,
            "league": league_name,
            "league_en": league_name,
            "time": m["time"],
            "score": "-",
            "is_live": False,
            "active": "1",
            "has_channels": True,
            "edges": [f"a{i}" for i in range(1, 21)],
            "edge_domain": "w1.sportsonlinee.click",
        })
    return matches, live_ids


def generate_outputs(parsed):
    now = datetime.now()
    today_str = now.strftime("%Y-%m-%d")

    primary = build_primary_matches(parsed)
    streamed = build_streamed_matches(parsed)
    soccer_matches, live_ids = build_soccer_matches(parsed)

    output_dir = Path(".")
    output_dir.mkdir(exist_ok=True)

    api_dir = output_dir / "api"
    api_dir.mkdir(exist_ok=True)

    streamed_dir = api_dir / "streamed"
    streamed_dir.mkdir(exist_ok=True)

    # Primary: /api/matches.json
    primary_payload = {
        "total": len(primary),
        "page": 1,
        "per_page": 50,
        "data": primary,
    }
    with open(api_dir / "matches.json", "w", encoding="utf-8") as f:
        json.dump(primary_payload, f, indent=2, ensure_ascii=False)
    print(f"api/matches.json: {len(primary)} primary matches")

    # Streamed: /api/streamed/matches.json
    streamed_payload = {
        "total": len(streamed),
        "page": 1,
        "per_page": 200,
        "data": streamed,
    }
    with open(streamed_dir / "matches.json", "w", encoding="utf-8") as f:
        json.dump(streamed_payload, f, indent=2, ensure_ascii=False)
    print(f"api/streamed/matches.json: {len(streamed)} streamed matches")

    # Root matches.json → same as primary for backward compat
    with open(output_dir / "matches.json", "w", encoding="utf-8") as f:
        json.dump(primary_payload, f, indent=2, ensure_ascii=False)

    # categories.json
    cats_out = []
    seen = set()
    for c in CATEGORIES:
        key = (c["id"], c["name"])
        if key in seen:
            continue
        seen.add(key)
        count = len([x for x in parsed if x["category"]["name"] == c["name"]])
        cats_out.append({"id": c["id"], "name": c["name"], "sport_code": c["sport_code"], "image": c["image"], "count": count})
    with open(output_dir / "categories.json", "w", encoding="utf-8") as f:
        json.dump({"status": "success", "data": cats_out}, f, indent=2, ensure_ascii=False)
    print(f"categories.json: {len(cats_out)} categories")

    # Soccer: /api/matches/{date}/1.json
    date_dir = api_dir / "matches" / today_str
    date_dir.mkdir(parents=True, exist_ok=True)
    with open(date_dir / "1.json", "w", encoding="utf-8") as f:
        json.dump({"matches": soccer_matches, "live_matche_ids": live_ids}, f, indent=2, ensure_ascii=False)
    print(f"api/matches/{today_str}/1.json: {len(soccer_matches)} soccer matches")

    # index.html
    index_html = output_dir / "index.html"
    if not index_html.exists():
        html = """<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0"><title>Streamymax API</title><style>body{font-family:Arial,sans-serif;background:#282828;color:#ccc;display:flex;align-items:center;justify-content:center;min-height:100vh;margin:0;text-align:center}.card{max-width:500px;padding:40px;background:#38383f;border-radius:10px;border:1px solid #555}h1{color:#e10601}a{color:#e10601}</style></head><body><div class="card"><h1>Streamymax API</h1><p>Data API for Streamymax, served via GitHub Pages.</p><p>Endpoints:</p><ul style="text-align:left"><li><a href="matches.json">/matches.json</a></li><li><a href="categories.json">/categories.json</a></li><li><a href="api/matches.json">/api/matches.json</a></li><li><a href="api/streamed/matches.json">/api/streamed/matches.json</a></li></ul></div></body></html>"""
        with open(index_html, "w", encoding="utf-8") as f:
            f.write(html)
        print(f"index.html created")


def main():
    print("=" * 50)
    print("UPDATE SCHEDULE - START")
    print("=" * 50)
    try:
        content = fetch_prog()
        parsed = parse_prog(content)
        print(f"Parsed {len(parsed)} events")
        generate_outputs(parsed)
        print("DONE")
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
