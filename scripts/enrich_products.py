"""
Enrich scraped product JSON files with structured fields using OpenAI.
Populates: ingredients, key_nutrients, benefits, health_goals, format, best_for.
Writes enriched files to data/products/ (overwrites in place).
"""

import json
import os
import time
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

DATA_DIR = Path(__file__).parent.parent / "data" / "products"
FILES = ["heart_and_soil.json", "lineage_provisions.json"]

SYSTEM_PROMPT = """\
You are a nutrition data extraction assistant. Given a product name, type, tags, and description,
extract structured metadata and return valid JSON only — no markdown, no explanation.

Return exactly this shape:
{
  "format": "<one of: capsule | powder | food | liquid | bundle>",
  "ingredients": ["<ingredient 1>", "<ingredient 2>", ...],
  "key_nutrients": ["<nutrient 1>", "<nutrient 2>", ...],
  "benefits": ["<benefit 1>", "<benefit 2>", ...],
  "health_goals": ["<goal 1>", "<goal 2>", ...],
  "best_for": "<one sentence describing the ideal user or use case>"
}

Guidelines:
- format: "capsule" for organ/supplement capsules, "powder" for protein/collagen powders,
  "food" for meat sticks/bars/tallow/honey/coffee/steak, "liquid" for liquids,
  "bundle" for stacks/bundles of multiple products
- ingredients: actual organ or food ingredients (e.g. "Beef Liver", "Grass-Fed Whey", "Raw Honey")
  — omit if it's a bundle/stack with no single ingredient list
- key_nutrients: vitamins, minerals, compounds (e.g. "Vitamin A", "CoQ10", "Collagen", "Creatine")
  — omit if not applicable
- benefits: short benefit phrases (e.g. "energy", "joint support", "immune health", "hormone balance")
- health_goals: plain-language health goals a user might describe
  (e.g. "low energy", "gut issues", "hair loss", "joint pain", "fertility")
- best_for: one clear sentence. If it's merch/accessories/non-supplement, return null for all fields.
"""


def enrich_product(product: dict) -> dict:
    name = product.get("name", "")
    product_type = product.get("product_type", "")
    tags = ", ".join(product.get("tags", []))
    description = product.get("description_text", "") or ""

    # Skip non-supplement items
    skip_types = {"Hat", "T-Shirt", "Tank Top", "Gift Cards", "Delivery Guarantee", "Frother", "Coffee"}
    skip_keywords = ["sticker", "hat", "tee", "tank", "frother", "gift card", "delivery guarantee", "test product"]
    if product_type in skip_types or any(k in name.lower() for k in skip_keywords):
        return product

    user_msg = f"""Product Name: {name}
Product Type: {product_type}
Tags: {tags}
Description: {description[:1500]}"""

    try:
        resp = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_msg},
            ],
            temperature=0,
            response_format={"type": "json_object"},
        )
        extracted = json.loads(resp.choices[0].message.content)
        for field in ("format", "ingredients", "key_nutrients", "benefits", "health_goals", "best_for"):
            if field in extracted:
                product[field] = extracted[field] or None
    except Exception as e:
        print(f"    ERROR enriching {name}: {e}")

    return product


def main():
    for filename in FILES:
        path = DATA_DIR / filename
        print(f"\n{'='*60}")
        print(f"Enriching: {path.name}")
        print(f"{'='*60}")

        with open(path) as f:
            catalog = json.load(f)

        products = catalog["products"]
        for i, product in enumerate(products):
            name = product.get("name", "")
            print(f"  [{i+1}/{len(products)}] {name}")
            products[i] = enrich_product(product)
            time.sleep(0.2)  # avoid rate limits

        catalog["products"] = products
        with open(path, "w") as f:
            json.dump(catalog, f, indent=2)
        print(f"\nSaved enriched catalog → {path}")


if __name__ == "__main__":
    main()
