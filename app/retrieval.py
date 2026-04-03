import glob
import json
import logging
import os

import numpy as np
from sentence_transformers import SentenceTransformer

ARTICLES_DIR = os.path.join(os.path.dirname(__file__), "..", "knowledge-base", "articles")
VIDEO_CHUNKS_DIR = os.path.join(os.path.dirname(__file__), "..", "knowledge-base", "video-chunks")
PRODUCTS_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "products")
EMBED_MODEL = "BAAI/bge-small-en-v1.5"

_articles: list[dict] = []
_embeddings: np.ndarray | None = None
_model: SentenceTransformer | None = None

_video_chunks: list[dict] = []
_video_embeddings: np.ndarray | None = None
_video_chunk_index: dict[str, dict] = {}  # chunk_id -> chunk

_products: list[dict] = []
_product_embeddings: np.ndarray | None = None

# Pinned chunk mappings: exact user message (lowercased) → list of chunk_ids to inject.
# Chunk ID format: {video_id}_{start_seconds}. These bypass semantic search.
# To find a chunk_id: look up the video JSON in knowledge-base/video-chunks/,
# find the chunk by title, and use its start_seconds.
_PINNED_CHUNKS: dict[str, list[str]] = {
    # "Introduction to Animal-Based Diet" (NUUq4VT9miE, 0:00)
    "what is the animal based diet?": ["NUUq4VT9miE_0"],
}


def _get_model() -> SentenceTransformer:
    global _model
    if _model is None:
        _model = SentenceTransformer(EMBED_MODEL)
    return _model


def _parse_article(path: str) -> dict:
    with open(path, encoding="utf-8") as f:
        content = f.read()

    filename = os.path.splitext(os.path.basename(path))[0]

    title = ""
    categories = ""
    sections: dict[str, str] = {}
    current_section = None
    current_lines: list[str] = []

    for line in content.splitlines():
        if not title and line.startswith("# "):
            title = line[2:].strip()
        elif not categories and line.startswith("**Categories:**"):
            categories = line.replace("**Categories:**", "").strip()
        elif line.startswith("## "):
            if current_section is not None:
                sections[current_section] = "\n".join(current_lines).strip()
            current_section = line[3:].strip()
            current_lines = []
        elif current_section is not None:
            current_lines.append(line)

    if current_section is not None:
        sections[current_section] = "\n".join(current_lines).strip()

    return {
        "filename": filename,
        "title": title,
        "categories": categories,
        "tldr": sections.get("TLDR", ""),
        "recommendations": sections.get("What Paul Saladino Recommends", ""),
        "key_points": sections.get("Key Points", ""),
        "common_mistakes": sections.get("Common Mistakes", ""),
    }


def _build_corpus_text(article: dict) -> str:
    return (
        f"{article['title']} "
        f"{article['categories']} "
        f"{article['tldr']} "
        f"{article['key_points']} "
        f"{article['recommendations']} "
        f"{article['common_mistakes']}"
    )


def _load_video_chunks() -> None:
    global _video_chunks, _video_embeddings, _video_chunk_index
    paths = sorted(glob.glob(os.path.join(VIDEO_CHUNKS_DIR, "*.json")))
    if not paths:
        logging.warning("No video chunk files found in %s", VIDEO_CHUNKS_DIR)
        return

    flat: list[dict] = []
    for path in paths:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        video_title = data.get("title", "")
        video_id = data.get("video_id", "")
        for chunk in data.get("chunks", []):
            chunk_id = f"{video_id}_{chunk['start_seconds']}"
            youtube_url = chunk.get("youtube_url") or f"https://www.youtube.com/watch?v={video_id}&t={chunk['start_seconds']}s"
            record = {
                "chunk_id": chunk_id,
                "video_title": video_title,
                "chunk_title": chunk["title"],
                "summary": chunk["summary"],
                "transcript": chunk.get("transcript", ""),
                "youtube_url": youtube_url,
            }
            flat.append(record)

    _video_chunks = flat
    _video_chunk_index = {c["chunk_id"]: c for c in flat}

    corpus = [f"{c['chunk_title']}. {c['summary']}" for c in flat]
    model = _get_model()
    logging.info("Embedding %d video chunks...", len(corpus))
    _video_embeddings = model.encode(
        ["passage: " + t for t in corpus],
        normalize_embeddings=True,
        show_progress_bar=False,
    )
    logging.info("Video chunk embeddings ready.")


def _build_product_corpus_text(p: dict) -> str:
    parts = [p.get("name", ""), p.get("product_type", ""), p.get("description_text", "") or ""]
    if p.get("benefits"):
        parts.append(" ".join(p["benefits"]))
    if p.get("health_goals"):
        parts.append(" ".join(p["health_goals"]))
    if p.get("best_for"):
        parts.append(p["best_for"])
    if p.get("ingredients"):
        parts.append(" ".join(p["ingredients"]))
    return " ".join(filter(None, parts))


def _load_products() -> None:
    global _products, _product_embeddings
    paths = sorted(glob.glob(os.path.join(PRODUCTS_DIR, "*.json")))
    if not paths:
        logging.warning("No product files found in %s", PRODUCTS_DIR)
        return

    products: list[dict] = []
    for path in paths:
        with open(path, encoding="utf-8") as f:
            catalog = json.load(f)
        brand = catalog.get("brand", "")
        brand_url = catalog.get("brand_url", "")
        for p in catalog.get("products", []):
            if not p.get("format"):  # skip unenriched (merch, stickers, etc.)
                continue
            products.append({**p, "brand": brand, "brand_url": brand_url})

    _products = products
    corpus = [_build_product_corpus_text(p) for p in products]
    model = _get_model()
    logging.info("Embedding %d products...", len(corpus))
    _product_embeddings = model.encode(
        ["passage: " + t for t in corpus],
        normalize_embeddings=True,
        show_progress_bar=False,
    )
    logging.info("Product embeddings ready.")


def get_relevant_products(query: str, top_n: int = 6) -> tuple[list[dict], float]:
    """Return top_n product candidates by semantic similarity."""
    if _product_embeddings is None or not _products:
        return [], 0.0
    model = _get_model()
    query_vec = model.encode(
        ["query: " + query],
        normalize_embeddings=True,
        show_progress_bar=False,
    )[0]
    scores = _product_embeddings @ query_vec
    top_indices = np.argsort(scores)[::-1][:top_n]
    logging.info("top product scores: %s", [(float(scores[i]), _products[i]["name"]) for i in top_indices])
    return [_products[i] for i in top_indices], float(scores.max())


def _load_and_index() -> None:
    global _articles, _embeddings
    paths = sorted(glob.glob(os.path.join(ARTICLES_DIR, "*.md")))
    if not paths:
        raise RuntimeError(f"No articles found in {ARTICLES_DIR}")
    _articles = [_parse_article(p) for p in paths]

    corpus = [_build_corpus_text(a) for a in _articles]
    logging.info("Loading embedding model %s...", EMBED_MODEL)
    model = _get_model()
    logging.info("Embedding %d articles...", len(corpus))
    _embeddings = model.encode(
        ["passage: " + t for t in corpus],
        normalize_embeddings=True,
        show_progress_bar=False,
    )
    logging.info("Article embeddings ready.")

    _load_video_chunks()
    _load_products()

    # Warm up PyTorch thread pool and JIT to avoid slow first request
    model.encode(["warmup"], normalize_embeddings=True, show_progress_bar=False)


def get_relevant_articles(query: str, top_n: int = 3, min_score: float = 0.5) -> list[dict]:
    model = _get_model()
    # bge models expect a query prefix for queries
    query_vec = model.encode(
        ["query: " + query],
        normalize_embeddings=True,
        show_progress_bar=False,
    )[0]
    scores = _embeddings @ query_vec
    top_indices = np.argsort(scores)[::-1][:top_n]
    top_scores = [(float(scores[i]), _articles[i]["filename"]) for i in top_indices]
    logging.info("top candidates: %s", top_scores)
    return [_articles[i] for i in top_indices if scores[i] >= min_score]


def get_relevant_video_chunks(query: str, top_n: int = 5, min_score: float = 0.45) -> list[dict]:
    if _video_embeddings is None or not _video_chunks:
        return []

    # Check pinned mappings first — exact match on lowercased query.
    pinned_ids = _PINNED_CHUNKS.get(query.strip().lower())
    if pinned_ids:
        pinned = [_video_chunk_index[cid] for cid in pinned_ids if cid in _video_chunk_index]
        logging.info("pinned video chunks: %s", [c["chunk_title"] for c in pinned])
        return pinned

    model = _get_model()
    query_vec = model.encode(
        ["query: " + query],
        normalize_embeddings=True,
        show_progress_bar=False,
    )[0]
    scores = _video_embeddings @ query_vec
    top_indices = np.argsort(scores)[::-1][:top_n]
    logging.info("top video chunks: %s", [(float(scores[i]), _video_chunks[i]["chunk_title"]) for i in top_indices])
    return [_video_chunks[i] for i in top_indices if scores[i] >= min_score]


def format_video_chunk_context(chunks: list[dict]) -> str:
    if not chunks:
        return ""
    lines = ["\n\n## Relevant Video Clips\n"]
    for c in chunks:
        lines.append(f"### {c['chunk_title']} (from \"{c['video_title']}\")")
        lines.append(f"[Watch clip]({c['youtube_url']})")
        lines.append(c["transcript"])
        lines.append("")
    return "\n".join(lines)


def format_article_context(articles: list[dict]) -> str:
    if not articles:
        return ""
    parts = ["\n\n## Relevant Knowledge Base Articles\n"]
    for a in articles:
        parts.append(
            f"### {a['title']}\n"
            f"**Categories:** {a['categories']}\n\n"
            f"**TLDR:** {a['tldr']}\n\n"
            f"**Key Points:**\n{a['key_points']}\n\n"
            f"**What Paul Saladino Recommends:**\n{a['recommendations']}\n\n"
            f"**Common Mistakes:**\n{a['common_mistakes']}\n"
        )
    return "\n---\n".join(parts)
