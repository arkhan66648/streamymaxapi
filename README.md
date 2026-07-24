# Streamymax Clone - Data Source API

This repository contains the automated data pipeline that parses `sportsonline.st/prog.txt` and generates structured JSON data for the Streamymax clone project.

## Overview

This API server is designed to:
1. Fetch the `prog.txt` schedule from `sportsonline.st`
2. Parse the flat text format into structured JSON
3. Generate categorized, searchable match data
4. Serve the data via static JSON files for consumption by the frontend

## Technology Stack

- **GitHub Actions**: Runs every 30 minutes to fetch and parse schedule data
- **Python 3.11**: Parse prog.txt and generate JSON output
- **Structured JSON**: Mimics `ws.kora-api.space` API structure
- **GitHub Pages**: Hosts the JSON data as static files

## How It Works

### Data Flow

1. **Cron Trigger**: GitHub Actions runs a Python script every 30 minutes
2. **Fetch**: Downloads `https://sportsonline.st/prog.txt`
3. **Parse**: Extracts match information (time, teams, URL)
4. **Categorize**: Detects sport categories using keyword matching
5. **Generate**: Outputs structured JSON files
6. **Deploy**: Pushes JSON to GitHub Pages

### JSON Structure

```json
// api/matches.json
{
  "total": 45,
  "page": 1,
  "per_page": 100,
  "data": [
    {
      "id": "10462",
      "name": "Hungarian F1 GP: Practice 1",
      "slug": "hungarian-f1-gp-practice-1",
      "category": {
        "id": 15,
        "name": "Motor Sport",
        "sport_code": "racing",
        "image": "https://..."
      },
      "teams": ["Hungarian F1 GP", "Practice 1"],
      "stream_count": 4,
      "streams": [
        {"url": "https://stream.w1/sporttv4.php", "lang": "Portuguese"}
      ],
      "begin_at": "12:00",
      "is_live": false,
      "is_upcoming": true
    }
  ]
}

// api/categories.json
[
  {
    "id": 14,
    "name": "American Football",
    "sport_code": "Football",
    "image": "https://..."
  },
  {
    "id": 15,
    "name": "Motor Sport",
    "sport_code": "racing",
    "image": "https://..."
  }
]
```

## Categories Supported

The parser detects and categorizes sports based on keywords in event names:

| Sport Category | IDs | Keywords |
|---|---|---|
| **American Football** | 14 | nfl, american football, cfb |
| **Baseball** | 13 | mlb, baseball |
| **Basketball** | 4 | nba, basketball, wnba |
| **Boxing** | 18 | boxing, fight |
| **Fight MMA** | 17 | ufc, mma |
| **Football (Soccer)** | 9 | soccer, football, premier, liga, serie |
| **Hockey** | 16 | nhl, hockey |
| **Motor Sport** | 15 | f1, gp, grand prix, racing |
| **Tennis** | 99 | tennis, atp, wta |
| **WWE** | 20 | wwe, wrestling |

## Deployment

### GitHub Actions

The GitHub Action workflow:
1. Fetches `prog.txt` via HTTP request
2. Parses schedule using Python
3. Generates JSON files into the `output/` directory
4. Deploys to GitHub Pages via peaceiris/actions-gh-pages

### Cron Schedule

The pipeline runs every 30 minutes:
```yaml
schedule:
  - cron: "*/30 * * * *"
```

### GitHub Pages

Data is served as static JSON files:
- `api/matches.json` - Complete list of matches
- `api/categories.json` - Category information
- `api/streamed/match/{slug}.json` - Individual match for player page

## Usage with Other Layers

This repository provides the backend data for the Streamymax clone frontend:

1. **Layer 2 - Frontend Index**: Fetches `/api/matches.json`, renders schedule
2. **Layer 3 - Redirect**: Redirects to player pages with match IDs
3. **Layer 4 - Player Page**: Fetches individual match data via `/api/streamed/match/{slug}.json`

## Testing

To test the parser locally:

```bash
cd streamymax-clone/layer-1-api-server
python scripts/parser.py
```

The script will output debug information and create JSON files in the `output/` directory.

## Structure for Frontend Layer

The generated JSON files are designed to be consumed by the frontend layers:

1. **index.html** - Fetches and displays the list of matches
2. **strmd-stream.html** - Fetches individual match details for streaming
3. **frame.html** - Sandbox for streaming iframes
4. **API endpoints** - All JSON files follow RESTful conventions

## License

This project is part of the Streamymax clone project. All data is sourced from sportsonline.st.

## Contact

For issues with the data source or API, please contact the project maintainer.