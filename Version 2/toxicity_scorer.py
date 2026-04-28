"""
CosmIQ - Toxicity Scoring Engine
Computes a composite risk score (0–10) for cosmetic ingredients
based on multiple safety signals.
"""

from dataclasses import dataclass
from typing import Optional
import json


# ──────────────────────────────────────────────
# Scoring weights (must sum to 1.0)
# ──────────────────────────────────────────────
WEIGHTS = {
    "ewg_score":              0.35,   # EWG 1–10 (most trusted consumer DB)
    "is_carcinogen":          0.25,   # Binary flag → maps to 10 if True
    "is_endocrine_disruptor": 0.20,   # Binary flag → maps to 8 if True
    "is_allergen":            0.10,   # Binary flag → maps to 6 if True
    "is_banned_eu":           0.10,   # Binary flag → maps to 9 if True
}

assert abs(sum(WEIGHTS.values()) - 1.0) < 1e-6, "Weights must sum to 1.0"


@dataclass
class ScoreBreakdown:
    ingredient_name: str
    final_score: float          # 0–10, rounded to 1 decimal
    risk_label: str             # "Safe", "Low", "Moderate", "High", "Critical"
    risk_emoji: str
    ewg_contribution: float
    carcinogen_contribution: float
    endocrine_contribution: float
    allergen_contribution: float
    ban_contribution: float
    flags: list                 # Human-readable active flags
    recommendation: str

    def __str__(self):
        lines = [
            f"\n{'═'*46}",
            f"  {self.risk_emoji}  {self.ingredient_name.upper()}",
            f"  Risk Score: {self.final_score}/10  [{self.risk_label}]",
            f"{'─'*46}",
            f"  EWG contribution:          {self.ewg_contribution:.2f}",
            f"  Carcinogen contribution:   {self.carcinogen_contribution:.2f}",
            f"  Endocrine disruptor:       {self.endocrine_contribution:.2f}",
            f"  Allergen:                  {self.allergen_contribution:.2f}",
            f"  Regulatory ban:            {self.ban_contribution:.2f}",
            f"{'─'*46}",
        ]
        if self.flags:
            lines.append(f"  ⚑ Flags: {', '.join(self.flags)}")
        lines.append(f"  💡 {self.recommendation}")
        lines.append(f"{'═'*46}\n")
        return "\n".join(lines)


def _risk_label(score: float) -> tuple[str, str]:
    """Map a 0–10 score to a risk label and emoji."""
    if score <= 2:
        return "Safe", "🟢"
    elif score <= 4:
        return "Low Risk", "🟡"
    elif score <= 6:
        return "Moderate", "🟠"
    elif score <= 8:
        return "High Risk", "🔴"
    else:
        return "Critical", "☠️"


def _recommendation(score: float, flags: list) -> str:
    """Generate a plain-English recommendation based on the score."""
    if score <= 2:
        return "Generally safe for most users. Well-tolerated ingredient."
    elif score <= 4:
        return "Low concern. Monitor if you have sensitive skin or known allergies."
    elif score <= 6:
        if "Allergen" in flags:
            return "Moderate concern. Patch-test recommended, especially for sensitive skin."
        return "Moderate concern. Consider alternatives if using frequently."
    elif score <= 8:
        if "Carcinogen" in flags or "Endocrine Disruptor" in flags:
            return "High concern. Avoid if possible — linked to serious health effects."
        return "High concern. Limit exposure and check for safer substitutes."
    else:
        return "Critical risk. Avoid entirely. This ingredient is banned in multiple jurisdictions."


def score_ingredient(ingredient: dict) -> ScoreBreakdown:
    """
    Compute a composite toxicity score for an ingredient dict.

    Expected keys (all optional except 'name'):
        name, ewg_score, is_carcinogen, is_endocrine_disruptor,
        is_allergen, is_banned_eu
    """
    name = ingredient.get("name", "Unknown")

    # ── EWG score (1–10, already on our scale)
    ewg_raw = ingredient.get("ewg_score") or 5   # default mid if unknown
    ewg_norm = float(ewg_raw)
    ewg_contrib = ewg_norm * WEIGHTS["ewg_score"]

    # ── Binary flags → convert to severity value on 0–10 scale
    carcinogen_val = 10.0 if ingredient.get("is_carcinogen") else 0.0
    carcinogen_contrib = carcinogen_val * WEIGHTS["is_carcinogen"]

    endocrine_val = 8.0 if ingredient.get("is_endocrine_disruptor") else 0.0
    endocrine_contrib = endocrine_val * WEIGHTS["is_endocrine_disruptor"]

    allergen_val = 6.0 if ingredient.get("is_allergen") else 0.0
    allergen_contrib = allergen_val * WEIGHTS["is_allergen"]

    ban_val = 9.0 if ingredient.get("is_banned_eu") else 0.0
    ban_contrib = ban_val * WEIGHTS["is_banned_eu"]

    # ── Final composite score
    final = ewg_contrib + carcinogen_contrib + endocrine_contrib + allergen_contrib + ban_contrib
    final = round(min(final, 10.0), 1)

    # ── Collect active flags
    flags = []
    if ingredient.get("is_carcinogen"):       flags.append("Carcinogen")
    if ingredient.get("is_endocrine_disruptor"): flags.append("Endocrine Disruptor")
    if ingredient.get("is_allergen"):         flags.append("Allergen")
    if ingredient.get("is_banned_eu"):        flags.append("EU Banned")
    if ingredient.get("is_banned_us"):        flags.append("US Banned")

    label, emoji = _risk_label(final)
    rec = _recommendation(final, flags)

    return ScoreBreakdown(
        ingredient_name=name,
        final_score=final,
        risk_label=label,
        risk_emoji=emoji,
        ewg_contribution=round(ewg_contrib, 2),
        carcinogen_contribution=round(carcinogen_contrib, 2),
        endocrine_contribution=round(endocrine_contrib, 2),
        allergen_contribution=round(allergen_contrib, 2),
        ban_contribution=round(ban_contrib, 2),
        flags=flags,
        recommendation=rec,
    )


def score_product(ingredient_list: list[dict]) -> dict:
    """
    Score an entire product by its ingredient list.
    Returns a product-level summary with per-ingredient breakdowns.
    """
    breakdowns = [score_ingredient(ing) for ing in ingredient_list]
    scores = [b.final_score for b in breakdowns]

    # Product score = weighted average biased toward the worst ingredients
    if not scores:
        return {"error": "No ingredients provided"}

    avg = sum(scores) / len(scores)
    worst = max(scores)
    product_score = round((avg * 0.5) + (worst * 0.5), 1)  # bias toward max risk
    label, emoji = _risk_label(product_score)

    flagged = [b for b in breakdowns if b.flags]

    return {
        "product_score": product_score,
        "risk_label": label,
        "risk_emoji": emoji,
        "ingredient_count": len(breakdowns),
        "flagged_ingredient_count": len(flagged),
        "flagged_ingredients": [
            {"name": b.ingredient_name, "score": b.final_score, "flags": b.flags}
            for b in flagged
        ],
        "all_scores": [
            {"name": b.ingredient_name, "score": b.final_score, "label": b.risk_label}
            for b in sorted(breakdowns, key=lambda x: x.final_score, reverse=True)
        ],
    }


def score_from_json(path: str):
    """Load the ingredient JSON from ingredient_db.py output and score all of them."""
    with open(path, "r") as f:
        ingredients = json.load(f)

    print(f"\n CosmIQ Toxicity Report — {len(ingredients)} ingredients\n")
    for ing in ingredients:
        result = score_ingredient(ing)
        print(result)


if __name__ == "__main__":
    # ── Quick demo with hardcoded sample ingredients
    sample_product = [
        {"name": "niacinamide",      "ewg_score": 1, "is_carcinogen": False, "is_endocrine_disruptor": False, "is_allergen": False, "is_banned_eu": False},
        {"name": "fragrance",        "ewg_score": 8, "is_carcinogen": False, "is_endocrine_disruptor": False, "is_allergen": True,  "is_banned_eu": False},
        {"name": "methylparaben",    "ewg_score": 4, "is_carcinogen": False, "is_endocrine_disruptor": True,  "is_allergen": False, "is_banned_eu": False},
        {"name": "hyaluronic acid",  "ewg_score": 1, "is_carcinogen": False, "is_endocrine_disruptor": False, "is_allergen": False, "is_banned_eu": False},
        {"name": "oxybenzone",       "ewg_score": 8, "is_carcinogen": False, "is_endocrine_disruptor": True,  "is_allergen": False, "is_banned_eu": False},
    ]

    print("\n── Per-Ingredient Scores ──")
    for ing in sample_product:
        print(score_ingredient(ing))

    print("\n── Product-Level Summary ──")
    summary = score_product(sample_product)
    print(json.dumps(summary, indent=2))
