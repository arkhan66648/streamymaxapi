CATEGORIES = [
    {"id": 14, "name": "American Football", "sport_code": "Football", "image": "https://kora-api.top/uploads/categories/category_14.png", "keywords": ["nfl", "american football", "cfb", "ncaa football"]},
    {"id": 13, "name": "Baseball", "sport_code": "Baseball", "image": "https://kora-api.top/uploads/categories/category_13.png", "keywords": ["mlb", "baseball"]},
    {"id": 4, "name": "Basketball", "sport_code": "basketball", "image": "https://kora-api.top/uploads/categories/category_4.png", "keywords": ["nba", "basketball", "wnba"]},
    {"id": 18, "name": "Boxing", "sport_code": "boxing", "image": "https://kora-api.top/uploads/categories/category_18.png", "keywords": ["boxing", "boxing fight"]},
    {"id": 17, "name": "Fight MMA", "sport_code": "mma", "image": "https://kora-api.top/uploads/categories/category_17.png", "keywords": ["ufc", "mma", "fight night", "basketball"]},
    {"id": 9, "name": "Football", "sport_code": "Soccer", "image": "https://kora-api.top/uploads/categories/category_9.png", "keywords": ["soccer", "football", "premier", "liga", "serie", "bundesliga", "ligue", "champions", "europa", "mls", "copa", "vs", "x "]},
    {"id": 16, "name": "Hockey", "sport_code": "hockey", "image": "https://kora-api.top/uploads/categories/category_16.png", "keywords": ["nhl", "hockey"]},
    {"id": 15, "name": "Motor Sport", "sport_code": "racing", "image": "https://kora-api.top/uploads/categories/category_15.png", "keywords": ["f1", "gp", "grand prix", "motogp", "nascar", "formula"]},
    {"id": 99, "name": "Tennis", "sport_code": "tennis", "image": "https://example.com/tennis.png", "keywords": ["tennis", "atp", "wta"]},
    {"id": 20, "name": "WWE", "sport_code": "wwe", "image": "https://kora-api.top/uploads/categories/category_20.png", "keywords": ["wwe", "wrestling"]},
]

def detect_category(event_name):
    name_lower = event_name.lower()
    for cat in CATEGORIES:
        for kw in cat["keywords"]:
            if kw in name_lower:
                return cat
    return {"id": 0, "name": "Other", "sport_code": "other", "image": "https://example.com/other.png"}
