import re
import sys

from youtube_transcript_api import YouTubeTranscriptApi


def get_video_id(url):
    m = re.search(r"(?:v=|youtu\.be/|shorts/|embed/|live/)([A-Za-z0-9_-]{11})", url)
    if m:
        return m.group(1)
    if re.fullmatch(r"[A-Za-z0-9_-]{11}", url):
        return url
    return None


def parse_youtube_timestamp(url):
    m = re.search(r"[?&#](?:t|start)=([^&#]+)", url)
    if not m:
        return None
    val = m.group(1).strip().lower()
    if re.fullmatch(r"\d+s?", val):
        return int(val.rstrip("s"))
    # formats like 1h2m3s or 28m23s
    h = re.search(r"(\d+)h", val)
    m_ = re.search(r"(\d+)m", val)
    s = re.search(r"(\d+)s", val)
    if h or m_ or s:
        hours = int(h.group(1)) if h else 0
        minutes = int(m_.group(1)) if m_ else 0
        seconds = int(s.group(1)) if s else 0
        return hours * 3600 + minutes * 60 + seconds
    return None


def fmt_time(sec):
    sec = int(sec)
    return f"{sec // 3600:02d}:{(sec % 3600) // 60:02d}:{sec % 60:02d}"


def main():
    url = input("YouTube video URL: ").strip()
    video_id = get_video_id(url)
    if not video_id:
        print("Valid YouTube URL nahi hai.")
        sys.exit(1)

    try:
        api = YouTubeTranscriptApi()
        tlist = api.list(video_id)

        # Pehle hindi/english try karo, nahi toh jo bhi available ho
        try:
            t = tlist.find_transcript(["hi", "en"])
        except Exception:
            t = next(iter(tlist))

        data = t.fetch()
        print(f"Language: {t.language_code} "
              f"({'auto-generated' if t.is_generated else 'manual'})\n")
    except Exception as e:
        print(f"Transcript nahi mila: {type(e).__name__}: {e}")
        print("Ho sakta hai video par captions band hon, ya IP block ho (VPN/cloud par aisa hota hai).")
        sys.exit(1)

    plain = " ".join(s.text.replace("\n", " ") for s in data)
    with_ts = "\n".join(f"[{fmt_time(s.start)}] {s.text.replace(chr(10), ' ')}" for s in data)

    t_start = parse_youtube_timestamp(url)
    if t_start:
        print(f"Timestamp detected: {fmt_time(t_start)} ({t_start}s)")
        section = [s for s in data if s.start >= t_start]
        if section:
            print("\n--- Preview from timestamp onwards ---")
            sec_plain = " ".join(s.text.replace("\n", " ") for s in section)
            print(sec_plain[:500] + ("..." if len(sec_plain) > 500 else ""))
            print("--------------------------------------\n")

    with open(f"{video_id}_transcript.txt", "w", encoding="utf-8") as f:
        f.write(plain)
    with open(f"{video_id}_transcript_timestamps.txt", "w", encoding="utf-8") as f:
        f.write(with_ts)

    print(plain[:500] + ("..." if len(plain) > 500 else ""))
    print(f"\nSaved: {video_id}_transcript.txt aur {video_id}_transcript_timestamps.txt")


if __name__ == "__main__":
    main()