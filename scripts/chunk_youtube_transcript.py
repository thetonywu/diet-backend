"""
Fetches a YouTube transcript and uses an LLM to chunk it into topic segments.
Each chunk gets a timestamp link.

Usage:
    python scripts/chunk_youtube_transcript.py <video_id>
"""

import json
import os
import sys
import time

import yt_dlp
from openai import OpenAI
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import IpBlocked, NoTranscriptFound, TranscriptsDisabled


def fetch_video_metadata(video_id: str) -> dict:
    url = f"https://www.youtube.com/watch?v={video_id}"
    with yt_dlp.YoutubeDL({"quiet": True}) as ydl:
        info = ydl.extract_info(url, download=False)
    raw_date = info.get("upload_date", "")  # YYYYMMDD
    date_posted = f"{raw_date[:4]}-{raw_date[4:6]}-{raw_date[6:]}" if raw_date else ""
    return {"title": info.get("title", ""), "date_posted": date_posted}


def fetch_transcript(video_id: str) -> list[dict]:
    api = YouTubeTranscriptApi()
    for attempt in range(3):
        try:
            snippets = api.fetch(video_id)
            return [{"text": s.text, "start": s.start} for s in snippets]
        except IpBlocked:
            if attempt < 2:
                print(f"IP blocked, waiting 30s before retry {attempt + 2}/3...")
                time.sleep(30)
            else:
                raise
        except (NoTranscriptFound, TranscriptsDisabled) as e:
            raise RuntimeError(f"No transcript available: {e}") from e


def build_raw_text(segments: list[dict]) -> str:
    """Combine segments into a single string with timestamps for LLM context."""
    lines = []
    for s in segments:
        t = int(s["start"])
        mins, secs = divmod(t, 60)
        text = s["text"].encode("ascii", errors="ignore").decode()
        lines.append(f"[{mins:02d}:{secs:02d} / {t}s] {text}")
    return "\n".join(lines)


def chunk_with_llm(raw_text: str, video_id: str) -> list[dict]:
    client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])

    prompt = f"""You are analyzing a YouTube transcript about animal-based diet / nutrition.

Below is a transcript with timestamps in the format [MM:SS / Xs].

Your job: identify distinct topic segments in this video. For each segment:
1. Give it a short, descriptive title (the topic being discussed)
2. Write a 2-3 sentence summary of what's covered
3. Note the start timestamp (seconds) from the first line of that segment
4. Note the end timestamp (seconds) from the last line of that segment

Return a JSON array of objects with these fields:
- title: string
- summary: string
- start_seconds: number
- end_seconds: number

Aim for 6-12 segments — not too granular, not too broad. Group closely related content together.

TRANSCRIPT:
{raw_text}

Return only valid JSON, no commentary."""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"},
        max_tokens=2000,
    )

    content = response.choices[0].message.content
    parsed = json.loads(content)

    # Handle both {"segments": [...]} and plain [...]
    if isinstance(parsed, list):
        return parsed
    for key in parsed:
        if isinstance(parsed[key], list):
            return parsed[key]
    raise ValueError(f"Unexpected JSON shape: {list(parsed.keys())}")


def main():
    if len(sys.argv) < 2:
        print("Usage: python scripts/chunk_youtube_transcript.py <video_id>")
        sys.exit(1)

    video_id = sys.argv[1]
    print(f"Fetching metadata for {video_id}...")
    metadata = fetch_video_metadata(video_id)
    print(f"Title: {metadata['title']} ({metadata['date_posted']})")

    print(f"Fetching transcript for {video_id}...")
    segments = fetch_transcript(video_id)
    print(f"Got {len(segments)} segments, ~{int(segments[-1]['start'] / 60)} minutes")

    raw_text = build_raw_text(segments)

    print("Chunking by topic with LLM...")
    chunks = chunk_with_llm(raw_text, video_id)

    out_path = f"knowledge-base/video-chunks/{video_id}.json"
    os.makedirs("knowledge-base/video-chunks", exist_ok=True)
    # Attach transcript text and youtube_url to each chunk
    for chunk in chunks:
        start = chunk["start_seconds"]
        end = chunk["end_seconds"]
        chunk["transcript"] = " ".join(
            s["text"] for s in segments if start <= s["start"] < end
        )
        chunk["youtube_url"] = f"https://www.youtube.com/watch?v={video_id}&t={start}s"

    with open(out_path, "w") as f:
        json.dump({
            "video_id": video_id,
            "title": metadata["title"],
            "date_posted": metadata["date_posted"],
            "chunks": chunks,
        }, f, indent=2)

    print(f"\nSaved {len(chunks)} chunks to {out_path}\n")
    for c in chunks:
        mins, secs = divmod(c["start_seconds"], 60)
        print(f"  [{mins:02d}:{secs:02d}] {c['title']}")
        print(f"          {c['summary'][:80]}...")
        print(f"          {c['youtube_url']}\n")


if __name__ == "__main__":
    main()
