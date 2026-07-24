#!/usr/bin/env python3

import re, json, hashlib, os, sys, urllib.request, urllib.error
from datetime import datetime, timedelta
from pathlib import Path

PROG_URL = "https://sportsonline.st/prog.txt"

CATEGORIES = [
    {"id": 14, "name": "American Football", "sport_code": "Football", "image": "", "keywords": ["nfl", "american football", "cfb", "ncaa football"]},
    {"id": 4,  "name": "Basketball",        "sport_code": "basketball", "image": "", "keywords": ["nba", "basketball", "wnba"]},
    {"id": 13, "name": "Baseball",           "sport_code": "Baseball",  "image": "", "keywords": ["mlb", "baseball"]},
    {"id": 16, "name": "Hockey",             "sport_code": "hockey",    "image": "", "keywords": ["nhl", "hockey"]},
    {"id": 15, "name": "Motor Sport",        "sport_code": "racing",    "image": "", "keywords": ["f1", "gp", "grand prix", "motogp", "nascar", "formula"]},
    {"id": 99, "name": "Tennis",             "sport_code": "tennis",    "image": "", "keywords": ["tennis", "atp", "wta"]},
    {"id": 18, "name": "Boxing",             "sport_code": "boxing",    "image": "", "keywords": ["boxing"]},
    {"id": 17, "name": "Fight MMA",         "sport_code": "mma",       "image": "", "keywords": ["ufc", "mma", "fight night"]},
    {"id": 20, "name": "WWE",                "sport_code": "wwe",       "image": "", "keywords": ["wwe", "wrestling"]},
    {"id": 9,  "name": "Football",           "sport_code": "Soccer",    "image": "", "keywords": ["soccer", "football", "premier", "liga", "serie", "bundesliga", "ligue", "champions", "europa", "mls", "copa", "vs", " x "]},
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
    return hashlib.md5(event_name.lower().encode()).hexdigest()[:8]


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
            match = {
                "id": get_numeric_id(event_name),
                "slug": get_slug(event_name),
                "name": event_name,
                "category": category,
                "teams": teams,
                "time": time_str,
                "day": current_day,
                "url": url,
                "is_live": False,
                "has_channels": True,
                "edges": ["a1", "a2", "a3", "a4", "a5", "a6", "a7", "a8", "a9", "a10", "a11", "a12", "a13", "a14", "a15", "a16", "a17", "a18", "a19", "a20"],
            }
            lang = detect_lang_from_url(url)
            match["streams"] = [{"url": url, "lang": lang, "quality": "HD"}]
            match["stream_count"] = 1
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


def generate_outputs(matches):
    now = datetime.now()
    today_str = now.strftime("%Y-%m-%d")

    api_matches = []
    soccer_matches = []
    live_ids = []

    for m in matches:
        date_str = day_to_date(m["day"], m["time"]) or today_str
        begin_at = f"{date_str}T{m['time']}:00"
        api_matches.append({
            "id": m["id"],
            "name": m["name"],
            "slug": m["slug"],
            "category": {"id": m["category"]["id"], "name": m["category"]["name"], "sport_code": m["category"]["sport_code"]},
            "begin_at": begin_at,
            "end_at": None,
            "is_live": False,
            "is_popular": len(m["teams"]) > 1,
            "has_channels": True,
            "edges": m["edges"],
            "streams": m["streams"],
            "stream_count": m["stream_count"],
        })

        if m["category"]["name"] == "Football":
            home = m["teams"][0] if len(m["teams"]) > 0 else m["name"]
            away = m["teams"][1] if len(m["teams"]) > 1 else ""
            league_name = m["name"].split(" vs ")[0] if " vs " in m["name"] else (m["name"].split(" x ")[0] if " x " in m["name"] else "Soccer")
            soccer_matches.append({
                "id": int(m["id"], 16) % 100000,
                "home": home,
                "away": away,
                "home_en": home,
                "away_en": away,
                "league": league_name,
                "league_en": league_name,
                "time": m["time"],
                "score": "-",
                "is_live": False,
                "active": "1" if m["has_channels"] else "0",
                "has_channels": m["has_channels"],
                "edges": m["edges"],
                "edge_domain": "w1.sportsonlinee.click",
            })

    output_dir = Path(".")
    output_dir.mkdir(exist_ok=True)

    api_dir = output_dir / "api"
    api_dir.mkdir(exist_ok=True)
    streamed_dir = api_dir / "streamed"
    streamed_dir.mkdir(exist_ok=True)

    main_payload = {
        "status": "success",
        "generated_at": now.isoformat(),
        "total": len(api_matches),
        "per_page": 200,
        "data": api_matches
    }

    with open(output_dir / "matches.json", "w", encoding="utf-8") as f:
        json.dump(main_payload, f, indent=2, ensure_ascii=False)
    print(f"matches.json: {len(api_matches)} matches")

    with open(api_dir / "matches.json", "w", encoding="utf-8") as f:
        json.dump(main_payload, f, indent=2, ensure_ascii=False)

    with open(streamed_dir / "matches.json", "w", encoding="utf-8") as f:
        json.dump(main_payload, f, indent=2, ensure_ascii=False)

    cats_out = []
    for c in CATEGORIES:
        count = len([x for x in matches if x["category"]["name"] == c["name"]])
        cats_out.append({"id": c["id"], "name": c["name"], "sport_code": c["sport_code"], "image": c["image"], "count": count})
    with open(output_dir / "categories.json", "w", encoding="utf-8") as f:
        json.dump({"status": "success", "data": cats_out}, f, indent=2, ensure_ascii=False)
    print(f"categories.json: {len(CATEGORIES)} categories")

    date_dir = api_dir / "matches" / today_str
    date_dir.mkdir(parents=True, exist_ok=True)
    with open(date_dir / "1.json", "w", encoding="utf-8") as f:
        json.dump({"matches": soccer_matches, "live_matche_ids": live_ids}, f, indent=2, ensure_ascii=False)
    print(f"api/matches/{today_str}/1.json: {len(soccer_matches)} soccer matches")

    logos_dir = output_dir / "uploads" / "logos"
    logos_dir.mkdir(parents=True, exist_ok=True)
    if not list(logos_dir.iterdir()):
        svg = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><circle cx="50" cy="50" r="45" fill="#333"/><text x="50" y="55" font-size="30" text-anchor="middle" fill="white">T</text></svg>'
        with open(logos_dir / "placeholder.svg", "w", encoding="utf-8") as f:
            f.write(svg)

    index_html = output_dir / "index.html"
    if not index_html.exists():
        html = """<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0"><title>Streamymax API</title><style>body{font-family:Arial,sans-serif;background:#282828;color:#ccc;display:flex;align-items:center;justify-content:center;min-height:100vh;margin:0;text-align:center}.card{max-width:500px;padding:40px;background:#38383f;border-radius:10px;border:1px solid #555}h1{color:#e10601}a{color:#e10601}</style></head><body><div class="card"><h1>Streamymax API</h1><p>This is the data API for Streamymax. The API is served via GitHub Pages.</p><p>Endpoints:</p><ul style="text-align:left"><li><a href="matches.json">/matches.json</a></li><li><a href="categories.json">/categories.json</a></li><li><a href="api/matches.json">/api/matches.json</a></li></ul></div></body></html>"""
        with open(index_html, "w", encoding="utf-8") as f:
            f.write(html)
        print(f"index.html created")


def main():
    print("=" * 50)
    print("UPDATE SCHEDULE - START")
    print("=" * 50)
    try:
        content = fetch_prog()
        matches = parse_prog(content)
        print(f"Parsed {len(matches)} matches")
        generate_outputs(matches)
        print("DONE")
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
