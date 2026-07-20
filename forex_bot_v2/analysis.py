from datetime import datetime
from typing import List
from zoneinfo import ZoneInfo

KEYWORDS_WEIGHTS = {
    "interest rate": 8,
    "rate statement": 8,
    "fomc": 8,
    "ecb": 8,
    "boe": 8,
    "cpi": 8,
    "inflation": 8,
    "nfp": 8,
    "non-farm": 8,
    "gdp": 6,
    "pmi": 6,
    "employment": 6,
    "unemployment": 6,
    "retail sales": 4,
    "speech": 3,
}

TIER1_KEYWORDS = {"interest rate", "rate statement", "fomc", "ecb", "boe", "cpi", "inflation", "nfp", "non-farm"}
TIER2_KEYWORDS = {"gdp", "pmi", "employment", "unemployment"}
TIER3_KEYWORDS = {"retail sales", "speech"}


def classify_event_tier(title: str) -> str:
    lowered = title.lower()
    if any(keyword in lowered for keyword in TIER1_KEYWORDS):
        return "Tier 1"
    if any(keyword in lowered for keyword in TIER2_KEYWORDS):
        return "Tier 2"
    if any(keyword in lowered for keyword in TIER3_KEYWORDS):
        return "Tier 3"
    return "General"


def event_weight(title: str, impact: str) -> int:
    score = 5
    lowered = title.lower()
    for keyword, weight in KEYWORDS_WEIGHTS.items():
        if keyword in lowered:
            score += weight
    if impact == "High":
        score += 12
    elif impact == "Medium":
        score += 6
    return score


def confidence_score(title: str, impact: str, stage: str) -> int:
    score = event_weight(title, impact)
    tier = classify_event_tier(title)
    if tier == "Tier 1":
        score += 30
    elif tier == "Tier 2":
        score += 12
    elif tier == "Tier 3":
        score += 5
    if stage == "final":
        score += 10
    return max(0, min(score, 100))


def bias_strength(confidence: int) -> str:
    if confidence >= 80:
        return "Strong"
    if confidence >= 60:
        return "Moderate"
    return "Mild"


def map_pair_bias(currency: str, confidence: int) -> List[str]:
    strength = bias_strength(confidence)
    if currency == "USD":
        return [
            f"DXY: bullish {strength.lower()} bias if USD expectations strengthen",
            f"EURUSD: bearish {strength.lower()} bias under USD strength scenario",
            f"GBPUSD: bearish {strength.lower()} bias under USD strength scenario",
        ]
    if currency == "EUR":
        return [
            f"EURUSD: bullish {strength.lower()} bias if release supports EUR strength",
            f"DXY: bearish mild-to-{strength.lower()} pressure if EUR strengthens broadly",
            "GBPUSD: mostly indirect effect unless USD reprices at the same time",
        ]
    if currency == "GBP":
        return [
            f"GBPUSD: bullish {strength.lower()} bias if release supports GBP strength",
            "DXY: mostly indirect effect unless USD also reprices",
            "EURUSD: limited direct impact unless broader Europe/UK macro repricing occurs",
        ]
    return ["No specific pair mapping available"]


def build_empty_events_message() -> str:
    return "No upcoming events found. The bot will retry on the next run."


def build_analysis(title: str, currency: str, impact: str, event_time_utc: str, stage: str) -> str:
    score = event_weight(title, impact)
    tier = classify_event_tier(title)
    confidence = confidence_score(title, impact, stage)
    strength = bias_strength(confidence)
    scenarios = map_pair_bias(currency, confidence)

    reasons = [
        f"Currency in focus: {currency}",
        f"Impact level: {impact}",
        f"Event tier: {tier}",
        f"Sensitivity score: {score}",
        f"Confidence score: {confidence}/100",
        f"Bias strength: {strength}",
        f"Stage: {stage}",
    ]

    event_dt_utc = datetime.fromisoformat(event_time_utc)
    event_dt_ny = event_dt_utc.astimezone(ZoneInfo("America/New_York"))

    prefix = "Preparation alert" if stage == "prepare" else "Final pre-news alert"
    lines = [
        prefix,
        "",
        f"Event: {title}",
        f"Time (UTC): {event_dt_utc.strftime('%Y-%m-%d %H:%M UTC')}",
        f"Time (New York): {event_dt_ny.strftime('%Y-%m-%d %I:%M %p %Z')}",
        f"Currency: {currency}",
        f"Impact: {impact}",
        f"Confidence: {confidence}/100",
        f"Bias strength: {strength}",
        "",
        "Scenarios:",
    ]
    lines.extend([f"- {item}" for item in scenarios])
    lines.append("")
    lines.append("Reasoning:")
    lines.extend([f"- {item}" for item in reasons])
    return "\n".join(lines)
