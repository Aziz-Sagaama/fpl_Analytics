
from pathlib import Path
import os

import joblib
import pandas as pd

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

BASE_DIR = Path(__file__).resolve().parent

# Load the existing trained model and player dataset
model = joblib.load(BASE_DIR / "random_forest_model.joblib")
players_df = pd.read_csv(BASE_DIR / "cleaned_players.csv")

FEATURES = [
    "minutes",
    "goals_scored",
    "assists",
    "yellow_cards",
    "red_cards",
    "clean_sheets",
    "now_cost",
    "selected_by_percent",
    "goals_per_min",
    "assists_per_min",
]

app = FastAPI(
    title="FPL Random Forest API",
    description="Football player recommendation using Random Forest",
    version="1.0.0",
)

# Temporary development CORS configuration.
# We will restrict this to your portfolio domain before deployment.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        origin.strip()
        for origin in os.getenv("FPL_CORS_ORIGINS", "*").split(",")
        if origin.strip()
    ],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


class RecommendationRequest(BaseModel):
    budget: float = Field(gt=0, le=200)
    position: str


POSITION_MAP = {
    "GK": "GK",
    "DEF": "DEF",
    "MID": "MID",
    "FWD": "FWD",
}

POS_BUDGET_SHARE = {
    "GK": 0.08,
    "DEF": 0.28,
    "MID": 0.38,
    "FWD": 0.26,
}

POS_PLAYERS = {
    "GK": 2,
    "DEF": 5,
    "MID": 5,
    "FWD": 3,
}

EXPLORATION_FEATURES = [
    "minutes",
    "goals_scored",
    "assists",
    "total_points",
    "ict_index",
    "influence",
    "creativity",
    "threat",
    "now_cost",
    "clean_sheets",
]


def numeric_series(column: str) -> pd.Series:
    return pd.to_numeric(players_df[column], errors="coerce").fillna(0)


def player_records(frame: pd.DataFrame) -> list[dict]:
    result = frame.copy()
    result["price"] = numeric_series("now_cost").loc[result.index] / 10
    return result.fillna("").to_dict(orient="records")


def prepare_features(df: pd.DataFrame) -> pd.DataFrame:
    X = df[
        [
            "minutes",
            "goals_scored",
            "assists",
            "yellow_cards",
            "red_cards",
            "clean_sheets",
            "now_cost",
            "selected_by_percent",
        ]
    ].copy()

    safe_minutes = X["minutes"].replace(0, 1)

    X["goals_per_min"] = X["goals_scored"] / safe_minutes
    X["assists_per_min"] = X["assists"] / safe_minutes

    return X[FEATURES]


@app.get("/")
def home():
    return {
        "message": "FPL Random Forest API is running",
        "docs": "/docs",
    }


@app.get("/api/health")
def health():
    return {
        "status": "online",
        "model_loaded": model is not None,
        "players_loaded": len(players_df),
    }


@app.get("/api/players")
def get_players():
    required = [
        "first_name",
        "second_name",
        "now_cost",
        "element_type",
    ]

    missing = [c for c in required if c not in players_df.columns]

    if missing:
        raise HTTPException(
            status_code=500,
            detail=f"Missing dataset columns: {missing}",
        )

    result = players_df[required].copy()
    result["price"] = result["now_cost"] / 10

    return result.fillna("").to_dict(orient="records")


@app.get("/api/data/overview")
def data_overview():
    return {
        "total_players": len(players_df),
        "feature_count": len(players_df.columns),
        "position_count": int(players_df["element_type"].nunique(dropna=True)),
        "average_total_points": round(float(numeric_series("total_points").mean()), 2),
        "average_price": round(float((numeric_series("now_cost") / 10).mean()), 2),
        "missing_values": int(players_df.isna().sum().sum()),
        "duplicate_records": int(players_df.duplicated().sum()),
    }


@app.get("/api/data/distribution")
def data_distribution():
    grouped = players_df.assign(
        total_points=numeric_series("total_points"),
        price=numeric_series("now_cost") / 10,
    ).groupby("element_type", dropna=False)
    position_stats = [
        {
            "position": str(position),
            "players": int(group["total_points"].count()),
            "average_total_points": round(float(group["total_points"].mean()), 2),
            "average_price": round(float(group["price"].mean()), 2),
        }
        for position, group in grouped
    ]
    points = numeric_series("total_points")
    histogram = []
    bin_width = max(1, int((points.max() - points.min()) / 10))
    start = int(points.min())
    for lower in range(start, int(points.max()) + bin_width, bin_width):
        upper = lower + bin_width
        histogram.append({
            "label": f"{lower}-{upper - 1}",
            "from": lower,
            "to": upper,
            "count": int(((points >= lower) & (points < upper)).sum()),
        })
    return {"positions": position_stats, "total_points_histogram": histogram}


@app.get("/api/data/correlations")
def data_correlations():
    available = [column for column in EXPLORATION_FEATURES if column in players_df.columns]
    numeric = players_df[available].apply(pd.to_numeric, errors="coerce").fillna(0)
    matrix = numeric.corr().fillna(0)
    relationships = []
    for column in [item for item in available if item != "total_points"]:
        relationships.append({
            "feature": column,
            "correlation_with_total_points": round(float(matrix.loc[column, "total_points"]), 3),
            "points": [
                {"x": round(float(row[column]), 2), "y": round(float(row["total_points"]), 2)}
                for _, row in numeric[[column, "total_points"]].iterrows()
            ],
        })
    return {
        "features": available,
        "matrix": [
            {"row": row, "values": [round(float(matrix.loc[row, column]), 3) for column in available]}
            for row in available
        ],
        "relationships": relationships,
    }


@app.get("/api/data/advanced")
def advanced_data():
    required = [
        "first_name", "second_name", "element_type", "minutes",
        "goals_scored", "assists", "total_points", "creativity",
        "influence", "threat", "ict_index", "now_cost", "clean_sheets",
    ]
    missing = [column for column in required if column not in players_df.columns]
    if missing:
        raise HTTPException(status_code=500, detail=f"Missing dataset columns: {missing}")

    frame = players_df[required].copy()
    numeric_columns = [column for column in required if column not in {"first_name", "second_name", "element_type"}]
    frame[numeric_columns] = frame[numeric_columns].apply(pd.to_numeric, errors="coerce").fillna(0)
    frame["full_name"] = (
        frame["first_name"].astype(str).str.strip() + " "
        + frame["second_name"].astype(str).str.strip()
    ).str.replace(r"\s+", " ", regex=True).str.strip()
    frame["cost_m"] = frame["now_cost"] / 10

    chart_columns = [
        "full_name", "element_type", "minutes", "goals_scored", "assists",
        "total_points", "creativity", "influence", "threat", "ict_index",
        "clean_sheets", "cost_m",
    ]
    numeric_chart_columns = [column for column in chart_columns if column not in {"full_name", "element_type"}]
    points = frame["total_points"]
    price = frame["cost_m"]

    def histogram(series: pd.Series, bins: int = 10) -> list[dict]:
        if series.empty or series.min() == series.max():
            return [{"label": str(round(float(series.min()), 1)), "from": float(series.min()), "to": float(series.max()), "count": len(series)}]
        edges = pd.interval_range(start=float(series.min()), end=float(series.max()), periods=bins)
        return [
            {
                "label": f"{round(interval.left, 1)}-{round(interval.right, 1)}",
                "from": round(float(interval.left), 2),
                "to": round(float(interval.right), 2),
                "count": int(((series >= interval.left) & (series <= interval.right if interval == edges[-1] else series < interval.right)).sum()),
            }
            for interval in edges
        ]

    grouped = frame.groupby("element_type", dropna=False)
    position_stats = [
        {
            "position": str(position),
            "players": int(len(group)),
            "average_total_points": round(float(group["total_points"].mean()), 2),
            "average_price": round(float(group["cost_m"].mean()), 2),
            "points": [round(float(value), 2) for value in group["total_points"]],
            "prices": [round(float(value), 2) for value in group["cost_m"]],
            "minutes": [round(float(value), 2) for value in group["minutes"]],
        }
        for position, group in grouped
    ]
    correlations = frame[numeric_chart_columns].corr().fillna(0)
    return {
        "players": [
            {column: (round(float(row[column]), 2) if column in numeric_chart_columns else row[column]) for column in chart_columns}
            for _, row in frame.iterrows()
        ],
        "top_players": [
            {"player": row["full_name"], "position": row["element_type"], "total_points": round(float(row["total_points"]), 2)}
            for _, row in frame.sort_values("total_points", ascending=False).head(20).iterrows()
        ],
        "position_stats": position_stats,
        "price_histogram": histogram(price),
        "points_histogram": histogram(points),
        "price_summary": {"mean": round(float(price.mean()), 2), "median": round(float(price.median()), 2)},
        "points_summary": {"mean": round(float(points.mean()), 2), "median": round(float(points.median()), 2)},
        "correlation_features": numeric_chart_columns,
        "correlation_matrix": [
            {"row": row, "values": [round(float(correlations.loc[row, column]), 3) for column in numeric_chart_columns]}
            for row in numeric_chart_columns
        ],
    }


@app.get("/api/data/players")
def exploration_players(
    search: str = "",
    position: str = "ALL",
    sort_by: str = "total_points",
    order: str = "desc",
    page: int = 1,
    page_size: int = 10,
):
    allowed_sort = {
        "player": "full_name",
        "position": "element_type",
        "price": "price",
        "minutes": "minutes",
        "total_points": "total_points",
        "ict_index": "ict_index",
    }
    if page < 1 or page_size not in {10, 20, 50}:
        raise HTTPException(status_code=400, detail="Invalid page or page size.")
    if position != "ALL" and position not in POSITION_MAP:
        raise HTTPException(status_code=400, detail="Position must be GK, DEF, MID, FWD or ALL.")
    frame = players_df.copy()
    frame["full_name"] = (
        frame["first_name"].fillna("").astype(str).str.strip()
        + " "
        + frame["second_name"].fillna("").astype(str).str.strip()
    ).str.replace(r"\s+", " ", regex=True).str.strip()
    frame["price"] = pd.to_numeric(frame["now_cost"], errors="coerce").fillna(0) / 10
    if search.strip():
        frame = frame[frame["full_name"].str.contains(search.strip(), case=False, regex=False, na=False)]
    if position != "ALL":
        frame = frame[frame["element_type"].astype(str).str.upper().str.strip() == position]
    sort_column = allowed_sort[sort_by] if sort_by in allowed_sort else "total_points"
    if sort_column != "full_name":
        frame[sort_column] = pd.to_numeric(frame[sort_column], errors="coerce").fillna(0)
    frame = frame.sort_values(sort_column, ascending=order == "asc", kind="stable")
    total = len(frame)
    start = (page - 1) * page_size
    visible = frame.iloc[start:start + page_size]
    columns = ["full_name", "element_type", "price", "minutes", "total_points", "ict_index"]
    return {
        "players": visible[columns].fillna("").to_dict(orient="records"),
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": max(1, (total + page_size - 1) // page_size),
    }



@app.post("/api/recommend")
def recommend_players(request: RecommendationRequest):

    position = request.position.upper().strip()

    if position not in POSITION_MAP:
        raise HTTPException(
            status_code=400,
            detail="Position must be GK, DEF, MID or FWD",
        )

    required_columns = FEATURES[:-2] + [
        "first_name",
        "second_name",
        "element_type",
        "total_points",
    ]

    missing = [
        col for col in required_columns
        if col not in players_df.columns
    ]

    if missing:
        raise HTTPException(
            status_code=500,
            detail=f"Missing dataset columns: {missing}",
        )

    # Filter players using the actual string position in the CSV
    position_players = players_df[
        players_df["element_type"]
        .astype(str)
        .str.upper()
        .str.strip()
        == POSITION_MAP[position]
    ].copy()

    # Calculate the maximum allowed price per player
    player_budget = (
        request.budget
        * POS_BUDGET_SHARE[position]
        / POS_PLAYERS[position]
    )

    # FPL prices are stored in tenths of £m
    candidates = position_players[
        pd.to_numeric(position_players["now_cost"], errors="coerce")
        <= player_budget * 10
    ].copy()

    if candidates.empty:
        return {
            "position": position,
            "budget": request.budget,
            "player_budget": round(player_budget, 2),
            "total_candidates": 0,
            "recommendations": [],
            "message": "No players found within this budget.",
        }

    # Use the existing trained Random Forest model
    X = prepare_features(candidates)
    candidates["predicted_points"] = model.predict(X)

    candidates["price"] = candidates["now_cost"] / 10

    candidates["points_per_million"] = (
        candidates["predicted_points"]
        / candidates["price"].replace(0, float("nan"))
    )

    candidates = candidates.sort_values(
        "predicted_points",
        ascending=False,
    )

    recommendations = candidates.head(10)[
        [
            "first_name",
            "second_name",
            "price",
            "total_points",
            "predicted_points",
            "points_per_million",
        ]
    ].fillna(0).to_dict(orient="records")

    return {
        "position": position,
        "budget": request.budget,
        "player_budget": round(player_budget, 2),
        "total_candidates": len(candidates),
        "recommendations": recommendations,
    }

def calculate_percentile(value, values):
    values = pd.to_numeric(values, errors="coerce").dropna()

    if values.empty:
        return 0.0

    return float((values <= float(value)).mean() * 100)


@app.get("/api/analyze-player")
def analyze_player(name: str):

    name = name.strip()

    if len(name) < 2:
        raise HTTPException(
            status_code=400,
            detail="Please enter a valid player name."
        )

    df = players_df.copy()

    # Required dataset columns
    required = [
        "first_name", "second_name", "element_type",
        "total_points", "minutes", "now_cost",
        "yellow_cards", "red_cards", "clean_sheets",
        "ict_index", "influence", "creativity", "threat"
    ]

    missing = [col for col in required if col not in df.columns]

    if missing:
        raise HTTPException(
            status_code=500,
            detail=f"Missing dataset columns: {missing}"
        )

    # Build full player names
    df["full_name"] = (
        df["first_name"].fillna("").astype(str).str.strip()
        + " "
        + df["second_name"].fillna("").astype(str).str.strip()
    ).str.strip()

    # Exact match first, then partial match
    exact_matches = df[
        df["full_name"].str.casefold() == name.casefold()
    ]

    if not exact_matches.empty:
        matches = exact_matches
    else:
        matches = df[
            df["full_name"].str.contains(
                name, case=False, regex=False, na=False
            )
        ]

    if matches.empty:
        raise HTTPException(
            status_code=404,
            detail=f"No player found matching '{name}'."
        )

    if len(matches) > 1:
        return {
            "message": "Multiple players found. Please select a specific player.",
            "matches": matches["full_name"].drop_duplicates().tolist()
        }

    player = matches.iloc[0]

    position = str(player["element_type"]).upper().strip()

    if position not in {"GK", "DEF", "MID", "FWD"}:
        raise HTTPException(
            status_code=400,
            detail="Unknown player position."
        )

    # Compare against players in the same position
    position_players = df[
        df["element_type"].astype(str).str.upper().str.strip()
        == position
    ].copy()

    # Convert relevant statistics to numeric
    numeric_columns = [
        "total_points", "minutes", "now_cost",
        "yellow_cards", "red_cards", "clean_sheets",
        "ict_index", "influence", "creativity", "threat"
    ]

    for col in numeric_columns:
        position_players[col] = pd.to_numeric(
            position_players[col], errors="coerce"
        ).fillna(0)

    # -----------------------------------------
    # 1. RANDOM FOREST PREDICTION
    # -----------------------------------------

    player_df = position_players[
        position_players["full_name"].str.casefold()
        == player["full_name"].casefold()
    ].copy()

    if player_df.empty:
        raise HTTPException(
            status_code=500,
            detail="Could not retrieve player statistics."
        )

    prediction = float(
        model.predict(prepare_features(player_df))[0]
    )

    # -----------------------------------------
    # 2. RECRUITMENT ANALYSIS
    # -----------------------------------------

    total_points = float(player_df.iloc[0]["total_points"])
    minutes = float(player_df.iloc[0]["minutes"])
    price = float(player_df.iloc[0]["now_cost"]) / 10

    points_per_million = (
        total_points / price if price > 0 else 0
    )

    MINIMUM_MINUTES = 500

    if minutes < MINIMUM_MINUTES:
        return {
            "player": player["full_name"],
            "position": position,
            "price": round(price, 1),
            "actual_total_points": total_points,
            "predicted_points": round(prediction, 2),
            "recruitment_score": None,
            "verdict": "INSUFFICIENT DATA",
            "explanation": (
                f"The player has only {minutes:.0f} minutes. "
                f"At least {MINIMUM_MINUTES} minutes are required "
                "for a recruitment evaluation."
            )
        }

    # Value compared with players in the same position
    position_prices = position_players["now_cost"] / 10

    position_players["points_per_million"] = (
        position_players["total_points"]
        / position_prices.replace(0, float("nan"))
    )

    metrics = {
        "total_points": calculate_percentile(
            total_points, position_players["total_points"]
        ),
        "minutes": calculate_percentile(
            minutes, position_players["minutes"]
        ),
        "ict_index": calculate_percentile(
            player_df.iloc[0]["ict_index"],
            position_players["ict_index"]
        ),
        "influence": calculate_percentile(
            player_df.iloc[0]["influence"],
            position_players["influence"]
        ),
        "creativity": calculate_percentile(
            player_df.iloc[0]["creativity"],
            position_players["creativity"]
        ),
        "threat": calculate_percentile(
            player_df.iloc[0]["threat"],
            position_players["threat"]
        ),
        "clean_sheets": calculate_percentile(
            player_df.iloc[0]["clean_sheets"],
            position_players["clean_sheets"]
        ),
        "value": calculate_percentile(
            points_per_million,
            position_players["points_per_million"]
        )
    }

    # Original position-specific weights
    if position in {"GK", "DEF"}:
        weights = {
            "total_points": 0.25,
            "minutes": 0.20,
            "clean_sheets": 0.20,
            "ict_index": 0.10,
            "influence": 0.10,
            "value": 0.15
        }
    else:
        weights = {
            "total_points": 0.25,
            "minutes": 0.20,
            "ict_index": 0.20,
            "creativity": 0.10,
            "threat": 0.10,
            "value": 0.15
        }

    score = sum(
        metrics[metric] * weight
        for metric, weight in weights.items()
    )

    # Discipline penalty
    yellow_penalty = float(player_df.iloc[0]["yellow_cards"]) * 0.5
    red_penalty = float(player_df.iloc[0]["red_cards"]) * 3

    discipline_penalty = min(
        10, yellow_penalty + red_penalty
    )

    score = max(
        0,
        min(100, round(score - discipline_penalty))
    )

    # Final verdict
    if score >= 75:
        verdict = "RECRUIT"
        explanation = (
            "Strong performance and good statistical value "
            "compared with players in the same position."
        )
    elif score >= 55:
        verdict = "MONITOR"
        explanation = (
            "The player has potential, but some performance "
            "or value indicators need improvement."
        )
    else:
        verdict = "AVOID"
        explanation = (
            "The player's overall statistical profile is "
            "relatively weak compared with positional alternatives."
        )

    return {
        "player": player["full_name"],
        "position": position,
        "price": round(price, 1),
        "actual_total_points": total_points,
        "predicted_points": round(prediction, 2),
        "points_per_million": round(points_per_million, 2),
        "recruitment_score": score,
        "verdict": verdict,
        "explanation": explanation,
        "metrics": {
            key: round(value, 1)
            for key, value in metrics.items()
        },
        "comparison_players": len(position_players)
    }
