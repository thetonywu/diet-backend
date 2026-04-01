"""
Batch process YouTube videos from the checklist.

Usage:
    python scripts/batch_process_videos.py [--start N] [--count N] [--delay N]

Skips videos already processed. Marks completed ones in the checklist.
"""

import argparse
import json
import os
import re
import subprocess
import sys
import time


CHECKLIST = "knowledge-base/video-import-checklist.md"
CHUNKS_DIR = "knowledge-base/video-chunks"


def load_checklist() -> list[dict]:
    entries = []
    with open(CHECKLIST) as f:
        for line in f:
            m = re.match(r"- \[(x| )\] \[(.+?)\]\(https://www\.youtube\.com/watch\?v=([\w-]+)\)", line)
            if m:
                entries.append({
                    "done": m.group(1) == "x",
                    "title": m.group(2),
                    "video_id": m.group(3),
                })
    return entries


def mark_done(video_id: str) -> None:
    with open(CHECKLIST) as f:
        content = f.read()
    content = content.replace(
        f"- [ ] [",
        f"- [ ] [",  # no-op placeholder so we do a targeted replace below
    )
    # Replace only the specific video's checkbox
    content = re.sub(
        rf"- \[ \] (\[.+?\]\(https://www\.youtube\.com/watch\?v={re.escape(video_id)}\))",
        r"- [x] \1",
        content,
    )
    with open(CHECKLIST, "w") as f:
        f.write(content)


def already_processed(video_id: str) -> bool:
    return os.path.exists(os.path.join(CHUNKS_DIR, f"{video_id}.json"))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--start", type=int, default=1, help="1-based start index")
    parser.add_argument("--count", type=int, default=10, help="Number of videos to process")
    parser.add_argument("--delay", type=int, default=5, help="Seconds between videos")
    args = parser.parse_args()

    entries = load_checklist()
    to_process = entries[args.start - 1 : args.start - 1 + args.count]

    print(f"Processing {len(to_process)} videos (start={args.start}, delay={args.delay}s)\n")

    for i, entry in enumerate(to_process):
        vid = entry["video_id"]
        title = entry["title"]

        if already_processed(vid):
            print(f"[{i+1}/{len(to_process)}] SKIP (already done): {title}")
            mark_done(vid)
            continue

        print(f"[{i+1}/{len(to_process)}] Processing: {title} ({vid})")
        result = subprocess.run(
            [sys.executable, "scripts/chunk_youtube_transcript.py", vid],
            capture_output=True,
            text=True,
        )

        if result.returncode == 0:
            print(result.stdout.strip())
            mark_done(vid)
            print(f"  ✓ Done\n")
        else:
            err = result.stderr.strip().split("\n")[-1]
            print(f"  ✗ Failed: {err}\n")

        if i < len(to_process) - 1:
            time.sleep(args.delay)

    print("Batch complete.")
    done = sum(1 for e in load_checklist() if e["done"])
    total = len(load_checklist())
    print(f"Progress: {done}/{total} videos processed")


if __name__ == "__main__":
    main()
