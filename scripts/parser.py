#!/usr/bin/env python3

"""
Streamymax Schedule Parser

Fetches prog.txt from sportsonline.st and converts it to structured JSON data.
This script runs on GitHub Actions every 30 minutes to update the API data.
"""

import re
import json
import hashlib
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any
import os
import sys
import urllib.request
import urllib.error

# Import categorizer module
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import categories data
from scripts.categorizer import CATEGORIES, detect_category

# Configuration
PROGRESS_TXT_URL = "https://sportsonline.st/prog.txt"
OUTPUT_DIR = Path("output")

# Ensure output directory exists
OUTPUT_DIR.mkdir(exist_ok=True)
# Ensure api directory exists
(OUTPUT_DIR / "api").mkdir(exist_ok=True)

# Regex patterns for parsing prog.txt
DAY_HEADER_PATTERN = re.compile(r"^[A-Z]+$", re.MULTILINE)
EVENT_LINE_PATTERN = re.compile(r"^(\d{2}:\d{2})\s+(.+?)\s*\|\s*(https?://\S+)$")
CHANNEL_LINE_PATTERN = re.compile(r"^((HD|BR)\d+)")

# Counters for ID generation
ID_COUNTER = {}
def get_numeric_id(event_name: str) -> str:
    """Generate a stable numeric ID from the event name"""
    # Use MD5 hash to create a stable ID
    name_hash = hashlib.md5(event_name.lower().encode()).hexdigest()[:8]
    return name_hash
def get_slug_id(event_name: str) -> str:
    """Generate URL-friendly slug for the event"""
    slug = event_name.lower()
    # Replace punctuation with spaces
    for punctuation in [':', '–', '-', '(', ')']:
        slug = slug.replace(punctuation, ' ')
    # Remove any characters that aren't alphanumeric or whitespace
    slug = re.sub(r'[^a-z0-9\s]', '', slug)
    # Replace multiple spaces with single hyphens
    slug = re.sub(r'\s+', '-', slug.strip())
    return slug

def format_team_name(name: str) -> str:
    """Format team name for display"""
    return name.strip()

def extract_teams_from_event(event_name: str) -> List[str]:
    """Extract team names from event name"""
    teams = []
    if " vs " in event_name:
        teams = event_name.split(" vs ")
    elif " x " in event_name:
        teams = event_name.split(" x ")
    elif " - " in event_name:
        teams = event_name.split(" - ")
    return [t.strip() for t in teams]

def extract_league_from_event(event_name: str) -> str:
    """Extract league name from event name"""
    if "ATP World Tour" in event_name:
        return "ATP"
    elif "League" in event_name:
        return event_name.split(" League")[0].strip()
    elif event_name.startswith("Hungarian F1 GP"):
        return "Formula 1"
    elif "Weekly" in event_name:
        return "Weekly Tournament"
    elif "Euroleague" in event_name.lower():
        return "Euroleague"
    elif "MLS" in event_name:
        return "MLS"
    else:
        return "Other"
def fetch_prog_txt() -> str:
    """Fetch the prog.txt file from sportsonline.st"""
    try:
        print(f"Fetching prog.txt from {PROGRESS_TXT_URL}...")
        with urllib.request.urlopen(PROGRESS_TXT_URL, timeout=30) as response:
            content = response.read().decode('utf-8')
            print(f"✓ Fetched prog.txt ({len(content)} characters)")
            return content
    except Exception as e:
        print(f"✗ Failed to fetch prog.txt: {e}")
        raise

def parse_prog_txt(content: str) -> tuple:
    """Parse the prog.txt content and extract events"""
    lines = content.split('\n')
    
    matches = []
    scanned_categories = set()
    
    current_day = None
    current_time = None
    
    for i, line in enumerate(lines):
        line = line.strip()
        if not line:
            continue
            
        # Check if line is a day header (e.g., MONDAY)
        if DAY_HEADER_PATTERN.match(line) and len(line) <= 20:
            current_day = line.upper()
            current_time = None
            continue
            
        # Check if line is a channel header (HD1, BR2, etc.)
        if CHANNEL_LINE_PATTERN.match(line):
            continue
            
        # Try to parse as an event line (time | event name | url)
        event_match = EVENT_LINE_PATTERN.match(line)
        if event_match and current_day:
            time_str, event_name, url = event_match.groups()
            
            # Clean up event name
            event_name = event_name.strip()
            if not event_name:
                continue
                
            # Generate IDs
            numeric_id = get_numeric_id(event_name)
            slug_id = get_slug_id(event_name)
            
            # Extract teams and league
            teams = extract_teams_from_event(event_name)
            league = extract_league_from_event(event_name)
            
            # Detect category from event name
            category = detect_category(event_name)
            scanned_categories.add(category["name"])
            
            # Create match object
            match = {
                "id": numeric_id,
                "slug": slug_id,
                "name": event_name,
                "category": category,
                "teams": teams,
                "league": league,
                "time": time_str,
                "date": f"{current_day} {time_str}",
                "url": url,
                "is_live": False,
                "is_upcoming": True,
                "is_hot": len(teams) > 1,
                "stream_count": 1,
                "streams": [
                    {
                        "url": url,
                        "lang": "English",
                        "quality": "HD",
                        "source": "w1.sportsonlinee.click"
                    }
                ],
                "has_channels": True,
                "edges": ["a1", "a2", "a3", "a4", "a5", "a6", "a7", "a8", "a9", "a10", "a11", "a12", "a13", "a14", "a15", "a16", "a17", "a18", "a19", "a20"],
                "logo_team1": f"https://example.com/logos/team1.png",
                "logo_team2": f"https://example.com/logos/team2.png"
            }
            
            # Determine stream count based on URL pattern
            if "hd/" in url:
                match["stream_count"] = 4
                match["streams"] = [
                    {"url": url, "lang": "English", "quality": "HD"},
                    {"url": url.replace("/hd/", "/hd/2.php"), "lang": "Italian", "quality": "HD"},
                    {"url": url.replace("/hd/", "/hd/8.php"), "lang": "Spanish", "quality": "HD"},
                    {"url": url.replace("/hd/", "/bra/br6.php"), "lang": "Portuguese", "quality": "HD"}
                ]
            elif "sporttv" in url:
                if "1.php" in url:
                    match["stream_count"] = 1
                    match["streams"] = [{"url": url, "lang": "Portuguese"}]
                else:
                    match["stream_count"] = 2
                    match["streams"] = [
                        {"url": url, "lang": "Spanish"},
                        {"url": url.replace("/sporttv", "/sporttv1"), "lang": "Portuguese"}
                    ]
            elif "br" in url:
                match["stream_count"] = 1
                match["streams"] = [{"url": url, "lang": "Brazilian"}]
                
            matches.append(match)
            
            current_time = time_str
    
    return matches, list(scanned_categories)
def create_json_structure(matches: List[Dict], scanned_categories: List[str]) -> Dict[str, Any]:
    """Create the output JSON structure matching ws.kora-api.space API format"""
    now = datetime.now()
    
    # Prepare matches for output
    output_matches = []
    for match in matches:
        output_match = {
            "id": match["id"],
            "name": match["name"],
            "slug": match["slug"],
            "category": match["category"],
            "logo_team1": match["logo_team1"],
            "logo_team2": match["logo_team2"],
            "begin_at": match["time"],
            "end_at": None,
            "is_live": match["is_live"],
            "is_popular": match["is_hot"],
            "streams": [
                {"url": stream["url"], "lang": stream["lang"]}
                for stream in match["streams"]
            ],
            "has_channels": match["has_channels"],
            "edges": match["edges"]
        }
        output_matches.append(output_match)
    
    # Create categories list with updated counts
    categories = []
    for cat in CATEGORIES:
        cat_count = len([m for m in matches if m["category"]["name"] == cat["name"]])
        categories.append({
            "id": cat["id"],
            "name": cat["name"],
            "sport_code": cat["sport_code"],
            "image": cat["image"],
            "count": cat_count
        })
    
    return {
        "status": "success",
        "generated_at": now.isoformat(),
        "version": "1.0.0",
        "total_matches": len(matches),
        "matches": output_matches,
        "categories": categories,
        "stats": {
            "total_categories": len(CATEGORIES),
            "matches_with_streams": len([m for m in matches if m.get("streams")]),
            "live_matches": len([m for m in matches if m["is_live"]]),
            "upcoming_matches": len([m for m in matches if m["is_upcoming"]])
        }
    }
def save_json_data(data: Dict[str, Any], filename: str):
    """Save JSON data to a file in the output directory"""
    filepath = OUTPUT_DIR / filename
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"✓ Saved: {filepath}")
def save_individual_match_json(match: Dict):
    """Save individual match data as a separate JSON file"""
    filename = f"match_{match['slug']}.json"
    filepath = OUTPUT_DIR / "api" / filename
    filepath.parent.mkdir(exist_ok=True)
    
    output_match = {
        "id": match["id"],
        "name": match["name"],
        "slug": match["slug"],
        "category": match["category"],
        "teams": match["teams"],
        "league": match["league"],
        "time": match["time"],
        "date": match["date"],
        "is_live": match["is_live"],
        "is_upcoming": match["is_upcoming"],
        "is_hot": match["is_hot"],
        "stream_count": match["stream_count"],
        "streams": match["streams"],
        "has_channels": match["has_channels"],
        "edges": match["edges"]
    }
    
    save_json_data(output_match, f"api/streamed/{filename}")
def create_readme():
    """Create README.md file"""
    readme_content = f"""# Streamymax Clone - Schedule Data API

This repository contains the automated schedule data from sportsonline.st/prog.txt, processed and formatted as a JSON API for the Streamymax clone project.

## Overview

This API serves structured match data including:
- Match details (teams, categories, times)
- Stream URLs for multiple languages and quality levels
- Category classifications matching the Streamymax frontend
- Metadata for individual matches

## Categories Supported

The parser supports the following sport categories:

| Category | ID | Description |
|----------|----|-------------|
| **American Football** | 14 | NFL and college football |
| **Baseball** | 13 | MLB baseball |
| **Basketball** | 4 | NBA, WNBA basketball |
| **Boxing** | 18 | Boxing events |
| **Fight MMA** | 17 | UFC, MMA events |
| **Football** | 9 | Soccer, premier league, international |
| **Hockey** | 16 | NHL ice hockey |
| **Motor Sport** | 15 | F1, Formula 1 racing |
| **Tennis** | 99 | ATP, WTA tennis events |
| **WWE** | 20 | WWE wrestling events |

## Data Structure

### matches.json
Returns a paginated list of matches with:
- Match ID and slug for unique identification
- Categorized data (team names, league, date/time)
- Stream URLs for various languages and quality levels
- Metadata for live/upcoming matches

### categories.json
Returns category information used for filtering:
- Category IDs matching frontend requirements
- Sport codes for frontend filtering
- Stream counts for each category

### streamed/match/{{slug}}.json
Returns individual match details for the player page.

## API Endpoints

Your API is available at:
- GitHub Pages: https://yourusername.github.io/streamymax-api/api/matches.json
- Categories: https://yourusername.github.io/streamymax-api/api/categories.json
- Individual match: https://yourusername.github.io/streamymax-api/api/streamed/match/{{slug}}.json

## Usage

### Frontend Integration
The frontend can fetch match data using:
```javascript
// Get all matches
fetch('/api/matches.json')
  .then(response => response.json())
  .then(data => {{
    // Process matches for display
    console.log(`Total matches: ${{data.total}}`);
  }});

// Get category information
fetch('/api/categories.json')
  .then(response => response.json())
  .then(categories => {{
    // Use categories for filtering
  }});

// Get individual match for player page
fetch(`/api/streamed/match/${{matchId}}`)
  .then(response => response.json())
  .then(match => {{
    // Load player with match streams
  }});
```

### Data Refresh
The data is automatically refreshed every 30 minutes via GitHub Actions:
- New matches and updates are fetched from sportsonline.st
- Data is re-parsed and regenerated
- JSON files are updated in the output directory

## Generated on
{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
    
    readme_path = Path("README.md")
    with open(readme_path, 'w', encoding='utf-8') as f:
        f.write(readme_content)
    print(f"✓ Saved: {readme_path}")
def main():
    """Main function to run the entire pipeline"""
    print("=" * 60)
    print("STREAMEAST SCHEDULE PARSER - STARTING")
    print("=" * 60)
    
    try:
        # Step 1: Fetch prog.txt from sportsonline.st
        print("\n1. Fetching prog.txt from sportsonline.st...")
        prog_content = fetch_prog_txt()
        
        # Step 2: Parse prog.txt content
        print("\n2. Parsing prog.txt content...")
        matches, scanned_categories = parse_prog_txt(prog_content)
        
        if not matches:
            print("\n⚠ WARNING: No matches found in prog.txt")
            print("This could mean the format has changed or there are no current events.")
            return
        
        print(f"✓ Parsed {len(matches)} matches")
        print(f"✓ Scanned categories: {', '.join(scanned_categories)}")
        
        # Step 3: Create JSON structure
        print("\n3. Creating JSON structure...")
        json_data = create_json_structure(matches, scanned_categories)
        
        # Step 4: Save main JSON files
        print("\n4. Saving main JSON files...")
        save_json_data(json_data, "api/matches.json")
        save_json_data({"data": json_data["categories"]}, "api/categories.json")
        
        # Step 5: Save individual match files (first 50 for testing)
        print(f"\n5. Saving {min(50, len(matches))} individual match files...")
        for match in matches[:50]:
            save_individual_match_json(match)
        
        # Step 6: Create README
        print("\n6. Creating README.md...")
        create_readme()
        
        # Step 7: Create fake 404 page
        print("\n7. Creating fake 404 page...")
        fake_404_path = OUTPUT_DIR / "index.html"
        create_fake_404_page(fake_404_path)
        
        # Summary
        print("\n" + "=" * 60)
        print("PIPELINE COMPLETED SUCCESSFULLY")
        print("=" * 60)
        print(f"Total matches parsed: {len(matches)}")
        print(f"Total categories found: {len(scanned_categories)}")
        print(f"JSON files saved to: {OUTPUT_DIR}")
        print(f"GitHub Pages URL: https://yourusername.github.io/streamymax-api")
        print("\nThe data is now ready for use by the frontend layers!")
        
    except Exception as e:
        print(f"\n❌ ERROR in pipeline: {e}")
        import traceback
        traceback.print_exc()
        raise
def create_fake_404_page(filepath):
    """Create a fake 404 page that looks like a seized domain"""
    html_content = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Access Denied - Service Temporarily Unavailable</title>
    <meta name="robots" content="noindex, nofollow">
    <style>
        body {
            font-family: Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            margin: 0;
            padding: 0;
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            text-align: center;
        }
        .container {
            max-width: 600px;
            padding: 40px;
            background: rgba(255, 255, 255, 0.1);
            border-radius: 20px;
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.2);
            box-shadow: 0 20px 40px rgba(0, 0, 0, 0.3);
        }
        h1 {
            font-size: 3em;
            margin-bottom: 20px;
            text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.5);
        }
        p {
            font-size: 1.2em;
            margin-bottom: 30px;
            line-height: 1.6;
        }
        .error-code {
            font-size: 6em;
            font-weight: bold;
            color: #ff6b6b;
            margin-bottom: 20px;
        }
        .message {
            background: rgba(255, 255, 255, 0.05);
            padding: 20px;
            border-radius: 10px;
            margin: 20px 0;
            border-left: 4px solid #ff6b6b;
        }
        .home-btn {
            background: rgba(255, 255, 255, 0.2);
            color: white;
            padding: 12px 30px;
            border: 2px solid white;
            border-radius: 30px;
            text-decoration: none;
            font-weight: bold;
            transition: all 0.3s ease;
            display: inline-block;
            margin-top: 20px;
        }
        .home-btn:hover {
            background: white;
            color: #667eea;
            transform: translateY(-2px);
            box-shadow: 0 10px 20px rgba(0, 0, 0, 0.2);
        }
        .lock-icon {
            font-size: 4em;
            margin-bottom: 20px;
            opacity: 0.8;
        }
        @media (max-width: 480px) {
            h1 { font-size: 2em; }
            .container { padding: 20px; }
            .error-code { font-size: 4em; }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="lock-icon">🔒</div>
        <h1>Access Denied</h1>
        <div class="error-code">404 ERROR</div>
        
        <div class="message">
            <strong>This domain has been seized by authorized authorities.</strong><br>
            The requested service is temporarily unavailable.
        </div>
        
        <p>
            This service has been protected by security measures for unauthorized access.<br>
            Please contact your system administrator for assistance.
        </p>
        
        <div class="message">
            <strong>Important Notice:</strong> This page may show a domain seizure banner.
            Such displays are legally mandated to inform users of ongoing investigations
            related to intellectual property rights and anti-piracy efforts.
        </div>
        
        <a href="javascript:history.back()" class="home-btn">Go Back</a>
    </div>
</body>
</html>"""
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(html_content)
    print(f"✓ Created fake 404 page: {filepath}")
if __name__ == "__main__":
    main()