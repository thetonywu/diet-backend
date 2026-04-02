"""
Scrape product catalogs from Heart and Soil and Lineage Provisions Shopify stores.
Outputs structured JSON files to data/products/.
"""

import json
import re
import time
from pathlib import Path
import httpx
from html.parser import HTMLParser

OUTPUT_DIR = Path(__file__).parent.parent / "data" / "products"

BRANDS = [
    {
        "brand": "Heart and Soil",
        "brand_slug": "heart-and-soil",
        "base_url": "https://shop.heartandsoil.co",
        "output_file": "heart_and_soil.json",
    },
    {
        "brand": "Lineage Provisions",
        "brand_slug": "lineage-provisions",
        "base_url": "https://lineageprovisions.com",
        "output_file": "lineage_provisions.json",
    },
]

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json, text/html, */*",
    "Accept-Language": "en-US,en;q=0.9",
}


class HTMLStripper(HTMLParser):
    def __init__(self):
        super().__init__()
        self.reset()
        self.fed = []

    def handle_data(self, d):
        self.fed.append(d)

    def get_text(self):
        return " ".join(self.fed)


def strip_html(html: str) -> str:
    s = HTMLStripper()
    s.feed(html)
    text = s.get_text()
    # Collapse whitespace
    return re.sub(r"\s+", " ", text).strip()


def fetch_all_products(client: httpx.Client, base_url: str) -> list[dict]:
    """Fetch all products from Shopify /products.json endpoint."""
    products = []
    page = 1
    while True:
        url = f"{base_url}/products.json?limit=250&page={page}"
        print(f"  Fetching {url}")
        resp = client.get(url, headers=HEADERS)
        resp.raise_for_status()
        data = resp.json()
        batch = data.get("products", [])
        if not batch:
            break
        products.extend(batch)
        print(f"  Got {len(batch)} products (total so far: {len(products)})")
        if len(batch) < 250:
            break
        page += 1
        time.sleep(0.5)
    return products


def fetch_product_detail(client: httpx.Client, base_url: str, handle: str) -> dict:
    """Fetch full product detail from Shopify /products/{handle}.json."""
    url = f"{base_url}/products/{handle}.json"
    resp = client.get(url, headers=HEADERS)
    resp.raise_for_status()
    return resp.json().get("product", {})


def extract_tags(tags) -> list[str]:
    if isinstance(tags, list):
        return [t.strip() for t in tags if t.strip()]
    if isinstance(tags, str):
        return [t.strip() for t in tags.split(",") if t.strip()]
    return []


def build_product(detail: dict) -> dict:
    """Map Shopify product detail to our catalog schema."""
    variants = detail.get("variants", [])
    images = detail.get("images", [])

    # Price: use lowest variant price
    prices = []
    for v in variants:
        try:
            prices.append(float(v["price"]))
        except (KeyError, ValueError):
            pass
    price = min(prices) if prices else None

    # Variants summary (only include if more than one)
    variants_summary = []
    if len(variants) > 1:
        for v in variants:
            variants_summary.append({
                "title": v.get("title", ""),
                "price_usd": float(v["price"]) if v.get("price") else None,
                "sku": v.get("sku", ""),
                "available": v.get("available", True),
            })

    description_text = strip_html(detail.get("body_html", "") or "")

    return {
        "id": detail.get("handle", ""),
        "name": detail.get("title", ""),
        "slug": detail.get("handle", ""),
        "product_type": detail.get("product_type", ""),
        "tags": extract_tags(detail.get("tags", [])),
        "price_usd": price,
        "variants": variants_summary if variants_summary else None,
        "url": None,  # filled in by caller
        "image_url": images[0]["src"] if images else None,
        "description_text": description_text or None,
        "published_at": detail.get("published_at", ""),
        # Fields to be enriched manually or via AI post-processing:
        "ingredients": None,
        "key_nutrients": None,
        "benefits": None,
        "health_goals": None,
        "format": None,
        "best_for": None,
        "pairs_with": None,
    }


def scrape_brand(brand_cfg: dict) -> dict:
    base_url = brand_cfg["base_url"]
    print(f"\n{'='*60}")
    print(f"Scraping: {brand_cfg['brand']} ({base_url})")
    print(f"{'='*60}")

    with httpx.Client(timeout=30, follow_redirects=True) as client:
        raw_products = fetch_all_products(client, base_url)
        print(f"\nFetching full details for {len(raw_products)} products...")

        products = []
        for i, p in enumerate(raw_products):
            handle = p.get("handle", "")
            print(f"  [{i+1}/{len(raw_products)}] {handle}")
            try:
                detail = fetch_product_detail(client, base_url, handle)
                product = build_product(detail)
                product["url"] = f"{base_url}/products/{handle}"
                products.append(product)
            except Exception as e:
                print(f"    ERROR: {e}")
                # Fall back to summary data
                product = build_product(p)
                product["url"] = f"{base_url}/products/{handle}"
                products.append(product)
            time.sleep(0.3)

    return {
        "brand": brand_cfg["brand"],
        "brand_slug": brand_cfg["brand_slug"],
        "brand_url": base_url,
        "product_count": len(products),
        "products": products,
    }


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    for brand_cfg in BRANDS:
        catalog = scrape_brand(brand_cfg)
        out_path = OUTPUT_DIR / brand_cfg["output_file"]
        with open(out_path, "w") as f:
            json.dump(catalog, f, indent=2)
        print(f"\nSaved {catalog['product_count']} products → {out_path}")


if __name__ == "__main__":
    main()
