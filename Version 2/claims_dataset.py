"""
CosmIQ - Greenwashing Claims Dataset
Labeled training data for the greenwashing NLP classifier.

Labels:
  0 = Legitimate / verifiable claim
  1 = Greenwashing / misleading / vague
"""

LABELED_CLAIMS = [
    # ── GREENWASHING (label=1) ─────────────────────────────────────────────
    # Vague "natural" claims
    ("100% natural ingredients", 1),
    ("made with natural extracts", 1),
    ("all natural formula", 1),
    ("nature-inspired ingredients", 1),
    ("naturally derived formula", 1),
    ("pure and natural", 1),
    ("from nature, for you", 1),
    ("harnessing the power of nature", 1),
    ("natural beauty solution", 1),
    ("nature knows best", 1),

    # "Chemical-free" (scientifically impossible)
    ("chemical-free formula", 1),
    ("free from harsh chemicals", 1),
    ("no chemicals added", 1),
    ("chemical-free skincare", 1),
    ("free of synthetic chemicals", 1),
    ("toxin-free ingredients", 1),
    ("free from toxins", 1),

    # Vague "clean" claims
    ("clean beauty formula", 1),
    ("clean ingredients", 1),
    ("clean skincare", 1),
    ("cleaner beauty", 1),
    ("made with clean actives", 1),
    ("the clean beauty standard", 1),

    # Unverified eco claims
    ("eco-friendly packaging", 1),
    ("environmentally friendly formula", 1),
    ("planet-conscious beauty", 1),
    ("green beauty", 1),
    ("sustainable beauty", 1),
    ("earth-friendly ingredients", 1),
    ("eco-conscious formula", 1),
    ("good for the planet", 1),
    ("low environmental impact", 1),

    # Unverified vegan/cruelty-free (without certification)
    ("vegan formula", 1),
    ("cruelty-free beauty", 1),
    ("never tested on animals", 1),
    ("vegan and cruelty-free", 1),
    ("100% vegan ingredients", 1),
    ("compassionate beauty", 1),

    # Unverified dermatological claims
    ("dermatologist tested", 1),
    ("dermatologist approved", 1),
    ("clinically tested for safety", 1),
    ("tested by dermatologists", 1),
    ("doctor recommended", 1),
    ("scientifically proven formula", 1),
    ("clinically proven results", 1),
    ("laboratory tested", 1),

    # Misleading "free-from" claims
    ("paraben-free formula", 1),
    ("sulfate-free shampoo", 1),
    ("free from parabens and sulfates", 1),
    ("silicone-free moisturizer", 1),
    ("free from artificial fragrances", 1),
    ("no harmful preservatives", 1),
    ("free from nasties", 1),

    # Vague wellness/purity claims
    ("pure beauty", 1),
    ("wholesome ingredients", 1),
    ("honest ingredients", 1),
    ("transparent beauty", 1),
    ("good-for-you ingredients", 1),
    ("mindful beauty", 1),
    ("conscious cosmetics", 1),
    ("clean and green", 1),
    ("safe for you and the planet", 1),
    ("non-toxic beauty", 1),

    # ── LEGITIMATE (label=0) ───────────────────────────────────────────────
    # Certified organic
    ("USDA Certified Organic", 0),
    ("certified organic by USDA NOP", 0),
    ("COSMOS organic certified", 0),
    ("Ecocert certified organic formula", 0),
    ("certified organic ingredients by Ecocert", 0),

    # Certified cruelty-free
    ("Leaping Bunny certified cruelty-free", 0),
    ("PETA certified cruelty-free and vegan", 0),
    ("certified by Choose Cruelty Free", 0),
    ("cruelty-free certified by Leaping Bunny program", 0),

    # EWG / third-party safety
    ("EWG Verified for safety", 0),
    ("verified by Environmental Working Group", 0),
    ("EWG Verified product", 0),

    # Specific SPF / UV claims
    ("SPF 50 broad spectrum UVA/UVB protection", 0),
    ("tested to SPF 30 per FDA monograph", 0),
    ("broad spectrum SPF 50 PA++++", 0),

    # Regulated ingredient disclosures
    ("contains 2% salicylic acid", 0),
    ("formulated with 10% niacinamide", 0),
    ("active ingredient: 1% retinol", 0),
    ("contains hyaluronic acid 1% w/v", 0),
    ("5% glycolic acid exfoliant", 0),

    # Specific sustainability data
    ("packaging made from 100% post-consumer recycled plastic", 0),
    ("carbon neutral certified by Climate Partner", 0),
    ("B Corp certified company", 0),
    ("FSC certified paper packaging", 0),
    ("ISO 14001 environmental management certified", 0),

    # Clinical study references
    ("shown to reduce wrinkles by 32% in an 8-week clinical study of 60 participants", 0),
    ("clinically proven to improve hydration by 47% after 4 weeks, n=45", 0),
    ("tested by independent dermatologists, 94% reported reduced irritation", 0),

    # Allergen transparency
    ("contains known allergens: linalool, limonene, geraniol", 0),
    ("fragrance-free, no added perfume or masking fragrance", 0),
    ("free from the 26 EU-listed fragrance allergens", 0),

    # Regulatory compliance
    ("EU Cosmetics Regulation 1223/2009 compliant", 0),
    ("meets FDA OTC sunscreen monograph requirements", 0),
    ("complies with California Prop 65", 0),
    ("registered with the EU Cosmetic Products Notification Portal", 0),
]


# ── Greenwashing keyword signals (for rule-based pre-filter) ──────────────
GREENWASHING_KEYWORDS = [
    "natural", "chemical-free", "toxin-free", "clean", "pure",
    "green", "eco", "sustainable", "planet", "earth", "honest",
    "wholesome", "mindful", "conscious", "non-toxic", "free from",
    "no harsh", "nasties", "good for you", "nature-inspired",
    "dermatologist tested", "clinically proven", "scientifically proven",
    "doctor recommended", "laboratory tested",
]

# ── Legitimacy signals (certifications, specificity) ─────────────────────
LEGITIMACY_SIGNALS = [
    "usda", "ecocert", "cosmos", "leaping bunny", "peta certified",
    "ewg verified", "b corp", "fsc", "iso ", "carbon neutral certified",
    "spf", "broad spectrum", "active ingredient", "w/v", "n=",
    "clinical study", "independent", "post-consumer recycled",
    "regulation 1223", "prop 65", "fda", "eu ", "cpnp",
    "% ", "participants", "weeks",
]

if __name__ == "__main__":
    total = len(LABELED_CLAIMS)
    gw = sum(1 for _, l in LABELED_CLAIMS if l == 1)
    legit = sum(1 for _, l in LABELED_CLAIMS if l == 0)
    print(f"Dataset: {total} claims | {gw} greenwashing | {legit} legitimate")
