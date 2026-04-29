"""
CosmIQ - Greenwashing NLP Classifier
Detects misleading or unverifiable marketing claims in cosmetic products.

Pipeline:
  1. Rule-based pre-filter (keyword signals)
  2. TF-IDF + Logistic Regression classifier (trained on labeled dataset)
  3. Confidence scoring + explanation generation
"""

import re
import json
import pickle
import os
from dataclasses import dataclass, asdict
from typing import Optional

import numpy as np
from sklearn.pipeline import Pipeline
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import cross_val_score, train_test_split
from sklearn.metrics import classification_report

from claims_dataset import LABELED_CLAIMS, GREENWASHING_KEYWORDS, LEGITIMACY_SIGNALS

MODEL_PATH = "cosmiq_greenwashing_model.pkl"


# ──────────────────────────────────────────────
# Data classes
# ──────────────────────────────────────────────

@dataclass
class ClaimResult:
    claim: str
    verdict: str                  # "Greenwashing" | "Legitimate" | "Uncertain"
    confidence: float             # 0.0–1.0
    risk_score: float             # 0–10
    triggered_keywords: list
    legitimacy_signals: list
    explanation: str
    suggestions: list

    def __str__(self):
        lines = [
            f"\n{'═'*52}",
            f"  Claim: \"{self.claim[:60]}{'...' if len(self.claim)>60 else ''}\"",
            f"  Verdict:    {self.verdict}  (confidence: {self.confidence:.0%})",
            f"  Risk Score: {self.risk_score}/10",
            f"{'─'*52}",
        ]
        if self.triggered_keywords:
            lines.append(f"  ⚑ Red flags: {', '.join(self.triggered_keywords)}")
        if self.legitimacy_signals:
            lines.append(f"  ✓ Legit signals: {', '.join(self.legitimacy_signals)}")
        lines.append(f"\n  {self.explanation}")
        if self.suggestions:
            lines.append("\n  Suggestions:")
            for s in self.suggestions:
                lines.append(f"    → {s}")
        lines.append(f"{'═'*52}\n")
        return "\n".join(lines)

    def to_dict(self):
        return asdict(self)


# ──────────────────────────────────────────────
# Text preprocessing
# ──────────────────────────────────────────────

def preprocess(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^\w\s%-]", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text


def extract_rule_signals(claim: str) -> tuple[list, list]:
    """
    Extract greenwashing keyword hits and legitimacy signals from a claim.
    Returns (greenwashing_hits, legitimacy_hits).
    """
    lower = claim.lower()
    gw_hits = [kw for kw in GREENWASHING_KEYWORDS if kw in lower]
    legit_hits = [sig for sig in LEGITIMACY_SIGNALS if sig in lower]
    return gw_hits, legit_hits


# ──────────────────────────────────────────────
# Model training
# ──────────────────────────────────────────────

def build_pipeline() -> Pipeline:
    return Pipeline([
        ("tfidf", TfidfVectorizer(
            analyzer="word",
            ngram_range=(1, 3),       # unigrams, bigrams, trigrams
            max_features=5000,
            sublinear_tf=True,
            min_df=1,
        )),
        ("clf", LogisticRegression(
            C=1.0,
            class_weight="balanced",
            max_iter=1000,
            random_state=42,
        )),
    ])


def train(save: bool = True) -> Pipeline:
    """Train the classifier on the labeled dataset and optionally save it."""
    texts = [preprocess(t) for t, _ in LABELED_CLAIMS]
    labels = [l for _, l in LABELED_CLAIMS]

    model = build_pipeline()

    # Cross-validation
    scores = cross_val_score(model, texts, labels, cv=5, scoring="f1_macro")
    print(f"[✓] Cross-val F1 (macro): {scores.mean():.3f} ± {scores.std():.3f}")

    # Train/test split for full report
    X_train, X_test, y_train, y_test = train_test_split(
        texts, labels, test_size=0.2, random_state=42, stratify=labels
    )
    model.fit(X_train, y_train)
    preds = model.predict(X_test)
    print("\nClassification Report:")
    print(classification_report(y_test, preds, target_names=["Legitimate", "Greenwashing"]))

    # Refit on full dataset for production use
    model.fit(texts, labels)

    if save:
        with open(MODEL_PATH, "wb") as f:
            pickle.dump(model, f)
        print(f"[✓] Model saved to {MODEL_PATH}")

    return model


def load_model() -> Pipeline:
    """Load a saved model, or train a new one if not found."""
    if os.path.exists(MODEL_PATH):
        with open(MODEL_PATH, "rb") as f:
            return pickle.load(f)
    print("[!] No saved model found — training now...")
    return train(save=True)


# ──────────────────────────────────────────────
# Claim analysis
# ──────────────────────────────────────────────

EXPLANATION_TEMPLATES = {
    "Greenwashing": [
        "This claim uses vague or unverifiable language that cannot be independently confirmed.",
        "Terms like this are commonly used in greenwashing without regulatory definitions.",
        "This type of claim lacks scientific specificity and may mislead consumers.",
        "No third-party certification or measurable standard backs this claim.",
    ],
    "Legitimate": [
        "This claim references a verifiable standard or measurable outcome.",
        "Third-party certification or regulatory compliance makes this claim credible.",
        "Specific data or regulated terminology gives this claim credibility.",
        "This claim includes quantifiable details that can be independently verified.",
    ],
    "Uncertain": [
        "This claim contains mixed signals — some specifics but also vague language.",
        "Partially verifiable but would benefit from third-party certification.",
    ]
}

SUGGESTIONS_BY_KEYWORD = {
    "chemical-free":       "Replace with a specific ingredient list or 'free from [named ingredient]'",
    "toxin-free":          "Specify which compounds are absent and cite regulatory limits",
    "natural":             "Add certification (e.g. COSMOS, Ecocert) or specify % natural origin",
    "clean":               "Define 'clean' using an established standard (e.g. EWG Verified)",
    "eco":                 "Quantify environmental impact or cite a certification (e.g. B Corp, ISO 14001)",
    "sustainable":         "Provide LCA data or a recognized sustainability certification",
    "dermatologist tested":"Specify the number of participants, study duration, and testing lab",
    "clinically proven":   "Include study size (n=), duration, and independent lab reference",
    "scientifically proven":"Cite the specific study or peer-reviewed paper",
    "vegan":               "Add Leaping Bunny or PETA certification for credibility",
    "cruelty-free":        "Use Leaping Bunny or Choose Cruelty Free certification",
    "planet":              "Quantify the environmental benefit with verified data",
    "non-toxic":           "Specify which toxicological standards were used to assess safety",
    "free from":           "Ensure the removed ingredient is replaced with a safer, named alternative",
}


def explain(verdict: str, gw_hits: list, legit_hits: list) -> tuple[str, list]:
    """Generate a human-readable explanation and list of improvement suggestions."""
    templates = EXPLANATION_TEMPLATES[verdict]
    explanation = templates[hash(verdict + str(gw_hits)) % len(templates)]

    suggestions = []
    for kw in gw_hits:
        for sig_kw, suggestion in SUGGESTIONS_BY_KEYWORD.items():
            if sig_kw in kw and suggestion not in suggestions:
                suggestions.append(suggestion)

    if not suggestions and verdict == "Greenwashing":
        suggestions.append("Add a third-party certification or cite specific, measurable data to back this claim.")

    return explanation, suggestions[:3]  # cap at 3 suggestions


def analyze_claim(claim: str, model: Optional[Pipeline] = None) -> ClaimResult:
    """
    Analyze a single marketing claim for greenwashing.
    Returns a ClaimResult with verdict, confidence, and explanation.
    """
    if model is None:
        model = load_model()

    processed = preprocess(claim)
    gw_hits, legit_hits = extract_rule_signals(claim)

    # ML prediction
    proba = model.predict_proba([processed])[0]
    gw_prob = proba[1]    # probability of greenwashing
    legit_prob = proba[0]

    # Rule-based adjustments
    # More legitimacy signals → nudge toward legitimate
    legit_boost = min(len(legit_hits) * 0.08, 0.25)
    gw_boost = min(len(gw_hits) * 0.05, 0.20)
    adjusted_gw = min(max(gw_prob + gw_boost - legit_boost, 0), 1)

    # Verdict thresholds
    if adjusted_gw >= 0.60:
        verdict = "Greenwashing"
        confidence = adjusted_gw
    elif adjusted_gw <= 0.40:
        verdict = "Legitimate"
        confidence = 1 - adjusted_gw
    else:
        verdict = "Uncertain"
        confidence = 1 - abs(adjusted_gw - 0.5) * 2

    # Risk score 0–10
    risk_score = round(adjusted_gw * 10, 1)

    explanation, suggestions = explain(verdict, gw_hits, legit_hits)

    return ClaimResult(
        claim=claim,
        verdict=verdict,
        confidence=round(confidence, 3),
        risk_score=risk_score,
        triggered_keywords=gw_hits[:5],
        legitimacy_signals=legit_hits[:5],
        explanation=explanation,
        suggestions=suggestions,
    )


def analyze_product_claims(claims: list[str], model: Optional[Pipeline] = None) -> dict:
    """Analyze multiple claims for a product and return an overall greenwashing score."""
    if model is None:
        model = load_model()

    results = [analyze_claim(c, model) for c in claims]
    gw_count = sum(1 for r in results if r.verdict == "Greenwashing")
    avg_risk = sum(r.risk_score for r in results) / len(results)
    max_risk = max(r.risk_score for r in results)
    product_risk = round((avg_risk * 0.5) + (max_risk * 0.5), 1)

    if product_risk >= 7:
        overall = "High greenwashing risk"
    elif product_risk >= 4:
        overall = "Moderate greenwashing risk"
    else:
        overall = "Low greenwashing risk"

    return {
        "overall_verdict": overall,
        "product_risk_score": product_risk,
        "total_claims": len(results),
        "greenwashing_count": gw_count,
        "legitimate_count": sum(1 for r in results if r.verdict == "Legitimate"),
        "uncertain_count": sum(1 for r in results if r.verdict == "Uncertain"),
        "claims": [r.to_dict() for r in results],
    }


# ──────────────────────────────────────────────
# CLI demo
# ──────────────────────────────────────────────

if __name__ == "__main__":
    print("CosmIQ — Greenwashing Classifier\n")
    print("Training model...")
    model = train(save=True)

    test_claims = [
        "100% natural and chemical-free formula",
        "dermatologist tested for sensitive skin",
        "USDA Certified Organic, verified by Ecocert",
        "clinically proven to reduce wrinkles by 34% in 8-week study (n=60)",
        "eco-friendly and sustainable beauty",
        "Leaping Bunny certified cruelty-free",
        "free from parabens and sulfates",
        "contains 5% niacinamide and 1% zinc",
        "good for you and the planet",
        "SPF 50 broad spectrum UVA/UVB, FDA compliant",
    ]

    print("\n── Individual Claim Analysis ──")
    for claim in test_claims:
        result = analyze_claim(claim, model)
        print(result)

    print("\n── Product-Level Analysis ──")
    summary = analyze_product_claims(test_claims[:5], model)
    print(json.dumps({k: v for k, v in summary.items() if k != "claims"}, indent=2))
