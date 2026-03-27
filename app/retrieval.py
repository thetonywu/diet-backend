import glob
import os

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

ARTICLES_DIR = os.path.join(os.path.dirname(__file__), "..", "knowledge-base", "articles")

_articles: list[dict] = []
_vectorizer: TfidfVectorizer | None = None
_tfidf_matrix = None


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
    t = article["title"]
    c = article["categories"]
    return (
        f"{t} {t} {t} "
        f"{c} {c} "
        f"{article['tldr']} "
        f"{article['key_points']} "
        f"{article['recommendations']} "
        f"{article['common_mistakes']}"
    )


def _load_and_index() -> None:
    global _articles, _vectorizer, _tfidf_matrix
    paths = sorted(glob.glob(os.path.join(ARTICLES_DIR, "*.md")))
    if not paths:
        raise RuntimeError(f"No articles found in {ARTICLES_DIR}")
    _articles = [_parse_article(p) for p in paths]
    corpus = [_build_corpus_text(a) for a in _articles]
    _vectorizer = TfidfVectorizer(stop_words="english", ngram_range=(1, 2), sublinear_tf=True)
    _tfidf_matrix = _vectorizer.fit_transform(corpus)


_load_and_index()


def get_relevant_articles(query: str, top_n: int = 3, min_score: float = 0.1) -> list[dict]:
    query_vec = _vectorizer.transform([query])
    scores = cosine_similarity(query_vec, _tfidf_matrix).flatten()
    top_indices = np.argsort(scores)[::-1][:top_n]
    return [_articles[i] for i in top_indices if scores[i] >= min_score]


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
