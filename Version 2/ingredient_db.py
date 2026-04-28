"""
CosmIQ - Ingredient Database Module
Fetches and stores cosmetic ingredient data from PubChem and EWG.
"""

import requests
import json
import time
import csv
import os
from dataclasses import dataclass, field, asdict
from typing import Optional

PUBCHEM_BASE = "https://pubchem.ncbi.nlm.nih.gov/rest/pug"

@dataclass
class Ingredient:
    name: str
    cid: Optional[int] = None              # PubChem Compound ID
    iupac_name: Optional[str] = None
    molecular_formula: Optional[str] = None
    molecular_weight: Optional[float] = None
    canonical_smiles: Optional[str] = None
    synonyms: list = field(default_factory=list)
    # Safety flags
    is_carcinogen: bool = False
    is_endocrine_disruptor: bool = False
    is_allergen: bool = False
    is_banned_eu: bool = False
    is_banned_us: bool = False
    # Scoring
    toxicity_score: Optional[float] = None  # 0 (safe) to 10 (dangerous)
    ewg_score: Optional[int] = None         # 1–10 scale
    # Meta
    function_tags: list = field(default_factory=list)  # e.g. ["preservative", "fragrance"]
    source: str = "PubChem"
    notes: str = ""

    def to_dict(self):
        return asdict(self)


def fetch_cid(ingredient_name: str) -> Optional[int]:
    """Look up a PubChem CID by ingredient name."""
    url = f"{PUBCHEM_BASE}/compound/name/{requests.utils.quote(ingredient_name)}/cids/JSON"
    try:
        r = requests.get(url, timeout=10)
        if r.status_code == 200:
            data = r.json()
            return data["IdentifierList"]["CID"][0]
    except Exception as e:
        print(f"  [!] CID lookup failed for '{ingredient_name}': {e}")
    return None


def fetch_properties(cid: int) -> dict:
    """Fetch molecular properties from PubChem for a given CID."""
    props = "IUPACName,MolecularFormula,MolecularWeight,CanonicalSMILES"
    url = f"{PUBCHEM_BASE}/compound/cid/{cid}/property/{props}/JSON"
    try:
        r = requests.get(url, timeout=10)
        if r.status_code == 200:
            return r.json()["PropertyTable"]["Properties"][0]
    except Exception as e:
        print(f"  [!] Property fetch failed for CID {cid}: {e}")
    return {}


def fetch_synonyms(cid: int, max_synonyms: int = 5) -> list:
    """Fetch common synonyms for a compound."""
    url = f"{PUBCHEM_BASE}/compound/cid/{cid}/synonyms/JSON"
    try:
        r = requests.get(url, timeout=10)
        if r.status_code == 200:
            syns = r.json()["InformationList"]["Information"][0].get("Synonym", [])
            return syns[:max_synonyms]
    except Exception as e:
        print(f"  [!] Synonym fetch failed for CID {cid}: {e}")
    return []


def build_ingredient(name: str) -> Ingredient:
    """
    Build a full Ingredient object by querying PubChem.
    Applies known-flag overrides from KNOWN_FLAGS dict.
    """
    print(f"[→] Fetching: {name}")
    ingredient = Ingredient(name=name)

    cid = fetch_cid(name)
    if cid:
        ingredient.cid = cid
        props = fetch_properties(cid)
        ingredient.iupac_name = props.get("IUPACName")
        ingredient.molecular_formula = props.get("MolecularFormula")
        ingredient.molecular_weight = props.get("MolecularWeight")
        ingredient.canonical_smiles = props.get("CanonicalSMILES")
        ingredient.synonyms = fetch_synonyms(cid)
        time.sleep(0.5)  # be polite to the API
    else:
        print(f"  [!] No CID found for '{name}'")

    # Apply known safety flags
    flags = KNOWN_FLAGS.get(name.lower(), {})
    for key, val in flags.items():
        setattr(ingredient, key, val)

    return ingredient


# ──────────────────────────────────────────────
# Known safety flags for common ingredients
# Sources: EWG, EU Cosmetics Regulation, IARC
# ──────────────────────────────────────────────
KNOWN_FLAGS = {
    "formaldehyde": {
        "is_carcinogen": True,
        "is_allergen": True,
        "is_banned_eu": True,
        "ewg_score": 10,
        "function_tags": ["preservative"],
        "notes": "IARC Group 1 carcinogen. Banned as cosmetic ingredient in EU."
    },
    "parabens": {
        "is_endocrine_disruptor": True,
        "ewg_score": 7,
        "function_tags": ["preservative"],
        "notes": "Linked to hormonal disruption. Some parabens banned in EU."
    },
    "methylparaben": {
        "is_endocrine_disruptor": True,
        "ewg_score": 4,
        "function_tags": ["preservative"],
        "notes": "Weak estrogen mimic. Still permitted in many regions at low concentrations."
    },
    "butylparaben": {
        "is_endocrine_disruptor": True,
        "is_banned_eu": True,
        "ewg_score": 7,
        "function_tags": ["preservative"],
    },
    "titanium dioxide": {
        "is_carcinogen": False,
        "ewg_score": 2,
        "function_tags": ["sunscreen", "colorant"],
        "notes": "Generally safe in non-nano form; inhalation of powder form is a concern."
    },
    "fragrance": {
        "is_allergen": True,
        "ewg_score": 8,
        "function_tags": ["fragrance"],
        "notes": "Catch-all term hiding hundreds of undisclosed chemicals."
    },
    "oxybenzone": {
        "is_endocrine_disruptor": True,
        "ewg_score": 8,
        "function_tags": ["sunscreen"],
        "notes": "Detected in human blood and breast milk. Coral reef toxin."
    },
    "retinol": {
        "ewg_score": 3,
        "function_tags": ["anti-aging", "vitamin"],
        "notes": "Generally safe; avoid during pregnancy."
    },
    "niacinamide": {
        "ewg_score": 1,
        "function_tags": ["brightening", "vitamin"],
        "notes": "Well-tolerated; beneficial for most skin types."
    },
    "sodium lauryl sulfate": {
        "is_allergen": True,
        "ewg_score": 4,
        "function_tags": ["surfactant", "cleanser"],
        "notes": "Can irritate sensitive skin with prolonged use."
    },
    "hyaluronic acid": {
        "ewg_score": 1,
        "function_tags": ["humectant", "moisturizer"],
        "notes": "Naturally occurring; very low risk."
    },
    "lead acetate": {
        "is_carcinogen": True,
        "is_banned_eu": True,
        "ewg_score": 10,
        "function_tags": ["colorant"],
        "notes": "Known neurotoxin. Banned in EU, Canada. Still in some US hair dyes."
    },
    "coal tar": {
        "is_carcinogen": True,
        "is_banned_eu": True,
        "ewg_score": 10,
        "function_tags": ["colorant", "anti-dandruff"],
        "notes": "Known carcinogen. Found in some dandruff shampoos and hair dyes."
    },
}


def save_to_csv(ingredients: list[Ingredient], path: str = "cosmiq_ingredients.csv"):
    """Save ingredient list to a CSV file."""
    if not ingredients:
        print("[!] No ingredients to save.")
        return
    rows = [i.to_dict() for i in ingredients]
    keys = rows[0].keys()
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()
        writer.writerows(rows)
    print(f"[✓] Saved {len(ingredients)} ingredients to {path}")


def save_to_json(ingredients: list[Ingredient], path: str = "cosmiq_ingredients.json"):
    """Save ingredient list to a JSON file."""
    with open(path, "w", encoding="utf-8") as f:
        json.dump([i.to_dict() for i in ingredients], f, indent=2)
    print(f"[✓] Saved {len(ingredients)} ingredients to {path}")


# ──────────────────────────────────────────────
# Seed ingredient list to populate the database
# ──────────────────────────────────────────────
SEED_INGREDIENTS = [
    "niacinamide",
    "hyaluronic acid",
    "retinol",
    "oxybenzone",
    "titanium dioxide",
    "methylparaben",
    "butylparaben",
    "sodium lauryl sulfate",
    "fragrance",
    "formaldehyde",
    "lead acetate",
    "coal tar",
]


if __name__ == "__main__":
    print("=" * 50)
    print("CosmIQ — Ingredient Database Builder")
    print("=" * 50)

    results = []
    for name in SEED_INGREDIENTS:
        ing = build_ingredient(name)
        results.append(ing)
        print(f"  ✓ {ing.name} | CID: {ing.cid} | EWG: {ing.ewg_score}")

    save_to_json(results)
    save_to_csv(results)
    print("\nDone! Check cosmiq_ingredients.json and cosmiq_ingredients.csv")
