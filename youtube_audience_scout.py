"""Scout broad YouTube audiences, then drill down with independent search terms.

Examples:
  python youtube_audience_scout.py --output audience_baseline.json
  python youtube_audience_scout.py --audience "Home and DIY" --query "home repair"
  python youtube_audience_scout.py --refresh audience_baseline.json
  python youtube_audience_scout.py --audience "Home and DIY" --comments-video VIDEO_ID

Use YOUTUBE_API_KEY, a protected --key-file, or the hidden interactive prompt.
Optional --ad-evidence JSON is a list of manually collected Keyword Planner rows.
Fields: audience, keyword, market, currency, competition, top_of_page_bid_low,
top_of_page_bid_high, as_of (date). These are Google search-ad signals.

Reports default to stdout. Keep exported public YouTube snapshots for less than
30 days, then delete them. Rechecks use the same IDs and show raw counts.
"""

import argparse
from datetime import datetime, timedelta, timezone
from getpass import getpass
import json
import os
from pathlib import Path
import shlex
import sys
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


AUDIENCES = {
    "Home and DIY": ("home repair", "home improvement"),
    "Cooking and food": ("home cooking", "easy meals"),
    "Personal finance": ("personal finance", "budgeting"),
    "Health and fitness": ("fitness", "home workouts"),
    "Careers and education": ("career development", "learning skills"),
    "Technology and software": ("tech tutorials", "software tools"),
    "History and science": ("history explained", "science explained"),
    "Travel and outdoors": ("travel guides", "outdoor recreation"),
    "Consumer products": ("product reviews", "buying guides"),
    "Hobbies and crafts": ("craft tutorials", "creative hobbies"),
}
SCHEMA = "youtube-audience-scout-v2"
V1_SCHEMA = "youtube-audience-scout-v1"
PUBLIC_METRIC_LIMITS = {
    "thumbnail_impressions_ctr": "unavailable for competing channels",
    "adsense_revenue": "unavailable for competing channels",
    "outlier_ratio_and_velocity_index": "requires approval for derived metrics",
}


class YouTubeError(RuntimeError):
    def __init__(self, endpoint, status, reason):
        self.reason = reason
        super().__init__(f"{endpoint}: HTTP {status} ({reason})")


def youtube(endpoint, key, **params):
    request = Request(f"https://www.googleapis.com/youtube/v3/{endpoint}?{urlencode(params)}")
    request.add_unredirected_header("X-Goog-Api-Key", key)
    try:
        with urlopen(request, timeout=20) as response:
            return json.load(response)["items"]
    except HTTPError as exc:
        try:
            reason = json.load(exc)["error"]["errors"][0]["reason"]
        except (ValueError, KeyError, IndexError, TypeError):
            reason = "request rejected"
        raise YouTubeError(endpoint, exc.code, reason) from None
    except (URLError, TimeoutError):
        raise RuntimeError(f"{endpoint}: connection failed or timed out") from None


def timestamp(value):
    return value.isoformat(timespec="seconds").replace("+00:00", "Z")


def read_key(path):
    if path:
        for line in path.read_text(encoding="utf-8").splitlines():
            name, separator, value = line.partition("=")
            if separator and name.strip() in {"YOUTUBE_API_KEY", "export YOUTUBE_API_KEY"}:
                try:
                    values = shlex.split(value, comments=True)
                except ValueError:
                    raise ValueError("Invalid YOUTUBE_API_KEY assignment in key file.") from None
                if len(values) == 1 and values[0]:
                    return values[0]
                break
        raise ValueError("YOUTUBE_API_KEY was not found in the key file.")
    key = os.environ.get("YOUTUBE_API_KEY", "").strip()
    if not key and sys.stdin.isatty():
        key = getpass("YouTube Data API key: ").strip()
    if not key:
        raise ValueError("Set YOUTUBE_API_KEY, use --key-file, or run in a terminal.")
    return key


def search_samples(key, now, args):
    if args.audience:
        search_terms = {args.audience: args.query or AUDIENCES[args.audience]}
    else:
        search_terms = {audience: ["|".join(terms)] for audience, terms in AUDIENCES.items()}
    samples = []
    for audience, queries in search_terms.items():
        print(f"Sampling {audience}...", file=sys.stderr)
        for query in queries:
            for cohort, days, order in (
                ("new uploads", 2, "date"), ("90-day view-ranked sample", 90, "viewCount")
            ):
                after = timestamp(now - timedelta(days=days))
                before = timestamp(now)
                rows = youtube(
                    "search", key, part="id", type="video", q=query, order=order,
                    maxResults=args.limit, publishedAfter=after, publishedBefore=before,
                    regionCode=args.region.upper(), relevanceLanguage=args.language.lower(),
                    videoDuration=args.duration,
                )
                samples.append({
                    "audience": audience, "query": query, "cohort": cohort, "order": order,
                    "published_after": after, "published_before": before,
                    "video_ids": [row["id"]["videoId"] for row in rows],
                })
    return samples


def fetch_resources(endpoint, key, ids, parts, fields):
    result = {}
    for index in range(0, len(ids), 50):
        rows = youtube(endpoint, key, part=parts, fields=fields, id=",".join(ids[index:index + 50]))
        result.update((row["id"], row) for row in rows)
    return result


def fetch_comments(key, video_ids):
    result = {}
    for video_id in video_ids:
        try:
            rows = youtube(
                "commentThreads", key, part="snippet", videoId=video_id, maxResults=10,
                order="relevance", textFormat="plainText",
                fields="items(id,snippet(topLevelComment(snippet(textDisplay,publishedAt))))",
            )
        except YouTubeError as exc:
            if exc.reason not in {"commentsDisabled", "videoNotFound"}:
                raise
            result[video_id] = {"status": exc.reason, "items": []}
        else:
            result[video_id] = {"status": "available", "items": rows}
    return result


def load_baseline(path, now):
    if not path:
        return None
    baseline = json.loads(path.read_text(encoding="utf-8"))
    if baseline.get("schema") not in {SCHEMA, V1_SCHEMA} or baseline.get("baseline_capture_started_at"):
        raise ValueError("Use an original audience snapshot for --refresh.")
    captured = datetime.fromisoformat(baseline["capture_started_at"].replace("Z", "+00:00"))
    if not timedelta(0) <= now - captured < timedelta(days=30):
        raise ValueError("Baseline must be less than 30 days old. Delete expired exports.")
    return baseline


def read_ad_evidence(path):
    if not path:
        return []
    rows = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(rows, list):
        raise ValueError("--ad-evidence expects a JSON list of Keyword Planner rows.")
    keys = ("audience", "keyword", "market", "currency", "competition",
            "top_of_page_bid_low", "top_of_page_bid_high", "as_of")
    if any(not isinstance(row, dict) or not all(key in row for key in keys) for row in rows):
        raise ValueError("Each advertiser row must include: " + ", ".join(keys))
    return [{key: row[key] for key in keys} for row in rows]


def as_count(value):
    return int(value) if str(value).isascii() and str(value).isdigit() else None


def subscriber_count(channel):
    statistics = channel.get("statistics", {})
    return None if statistics.get("hiddenSubscriberCount") else as_count(statistics.get("subscriberCount"))


def display_count(count):
    return "unavailable" if count is None else f"{count:,}"


def terminal_text(value):
    return " ".join("".join(char for char in str(value) if char.isprintable() or char.isspace()).split())


def print_report(scan, baseline):
    print(f"Audience scan | {scan['capture_started_at']} | {scan['search_region']} | "
          f"{scan['relevance_language']} | duration: {scan['search_video_duration']}")
    print(f"{len(scan['videos'])} unique public videos, {len(scan['channels'])} channels, "
          f"{scan['search_calls']} search calls. Sample results are not search volume.")
    if scan["unavailable_video_ids"]:
        print(f"Videos unavailable in this capture: {len(scan['unavailable_video_ids'])}.")
    if baseline:
        print(f"Recheck of {baseline['capture_started_at']} | paired public view counts")
    print("Competitor CTR and AdSense are private. CTR: unavailable. AdSense revenue: unavailable.")
    print("Evidence filter: at least 100,000 views and fewer than 10,000 visible subscribers.")
    print("Shortlisted evidence is based on public counts. It is not a demand or growth score.")

    shown = set()
    for sample in scan["samples"]:
        print(f"\n{sample['audience']} | {sample.get('cohort', 'original sample')} | {sample['query']}")
        candidates = [scan["videos"][vid] for vid in sample["video_ids"] if vid in scan["videos"]]
        if not candidates:
            print("  No available videos returned for this search.")
        for index, video in enumerate(candidates):
            vid = video["id"]
            snippet = video["snippet"]
            channel = scan["channels"].get(snippet["channelId"], {})
            views = as_count(video.get("statistics", {}).get("viewCount"))
            subscribers = subscriber_count(channel)
            matches = views is not None and views >= 100_000 and subscribers is not None and subscribers < 10_000
            if index >= 2 and (not matches or vid in shown):
                continue
            shown.add(vid)
            title = terminal_text(snippet.get("title", vid))
            name = terminal_text(snippet.get("channelTitle") or snippet["channelId"])
            previous = ""
            if baseline:
                prior = baseline["videos"].get(vid, {}).get("statistics", {}).get("viewCount")
                previous = f" | {display_count(as_count(prior))} views at baseline"
            print(f"  {snippet.get('publishedAt', '')[:10]} | {title} — {name}")
            print(f"  {display_count(views)} views / {display_count(subscribers)} subscribers"
                  f"{' | evidence match' if matches else ''}{previous} | https://youtu.be/{vid}")

    for video_id, record in scan["comments"].items():
        print(f"\nPublic comments | https://youtu.be/{video_id} | {record['status']}")
        for item in record["items"]:
            comment = item["snippet"]["topLevelComment"]["snippet"]
            print(f"  {terminal_text(comment['textDisplay'])[:400]}")

    print("\nKeyword Planner search-ad context (external evidence, separate from YouTube RPM)")
    if not scan["advertiser_evidence"]:
        print("  No Keyword Planner evidence supplied.")
    for row in scan["advertiser_evidence"]:
        print(terminal_text(f"  {row['audience']} | {row['keyword']} | {row['market']} | "
                            f"{row['currency']} {row['top_of_page_bid_low']}–{row['top_of_page_bid_high']} | "
                            f"competition: {row['competition']} | as of {row['as_of']}"))


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--audience", choices=AUDIENCES, help="Drill down into one broad audience.")
    parser.add_argument("--query", action="append", help="Custom drill-down term; repeat up to five times.")
    parser.add_argument("--region", default="US")
    parser.add_argument("--language", default="en")
    parser.add_argument("--duration", choices=("medium", "long"), default="medium")
    parser.add_argument("--limit", type=int, default=12, help="Results per search (1–50).")
    parser.add_argument("--comments-video", action="append", default=[], help="Video ID; repeat up to five times.")
    parser.add_argument("--key-file", type=Path)
    parser.add_argument("--ad-evidence", type=Path)
    parser.add_argument("--refresh", type=Path, help="Recheck the video IDs from a baseline JSON.")
    parser.add_argument("--output", type=Path, help="Optional new JSON export; keep for less than 30 days.")
    args = parser.parse_args()
    if args.query and (not args.audience or len(args.query) > 5):
        parser.error("--query needs --audience and can be used at most five times.")
    if args.refresh and (args.audience or args.query):
        parser.error("--refresh uses the original sample, so omit --audience and --query.")
    if len(args.comments_video) > 5 or not 1 <= args.limit <= 50:
        parser.error("Use at most five comment IDs and a search limit of 1–50.")
    if args.output and args.output.exists():
        parser.error("Output exists. Choose a new filename.")
    try:
        now = datetime.now(timezone.utc)
        baseline = load_baseline(args.refresh, now)
        ads = read_ad_evidence(args.ad_evidence)
        key = read_key(args.key_file)
        samples = baseline["samples"] if baseline else search_samples(key, now, args)
        ids = list(dict.fromkeys(vid for sample in samples for vid in sample["video_ids"]))
        captured = timestamp(datetime.now(timezone.utc))
        videos = fetch_resources(
            "videos", key, ids, "snippet,statistics,contentDetails",
            "items(id,snippet(title,channelId,channelTitle,publishedAt,defaultAudioLanguage),"
            "statistics(viewCount,likeCount,commentCount),contentDetails(duration))",
        )
        channel_ids = list(dict.fromkeys(row["snippet"]["channelId"] for row in videos.values()))
        channels = fetch_resources(
            "channels", key, channel_ids, "statistics,snippet",
            "items(id,snippet(title,publishedAt),statistics(subscriberCount,hiddenSubscriberCount,videoCount))",
        )
        scan = {
            "schema": SCHEMA,
            "capture_started_at": captured,
            "capture_finished_at": timestamp(datetime.now(timezone.utc)),
            "baseline_capture_started_at": baseline["capture_started_at"] if baseline else None,
            "search_region": baseline["search_region"] if baseline else args.region.upper(),
            "relevance_language": baseline["relevance_language"] if baseline else args.language.lower(),
            "search_video_duration": baseline["search_video_duration"] if baseline else args.duration,
            "search_calls": 0 if baseline else len(samples),
            "samples": samples,
            "videos": videos,
            "channels": channels,
            "unavailable_video_ids": [vid for vid in ids if vid not in videos],
            "comments": fetch_comments(key, dict.fromkeys(args.comments_video)),
            "advertiser_evidence": ads,
            "metric_availability": PUBLIC_METRIC_LIMITS,
        }
        if args.output:
            with open(args.output, "x", encoding="utf-8", opener=private_output) as handle:
                json.dump(scan, handle, ensure_ascii=False, indent=2)
                handle.write("\n")
        print_report(scan, baseline)
    except (RuntimeError, ValueError, OSError, KeyError, TypeError, AttributeError) as exc:
        parser.exit(1, f"Scan stopped: {exc}\n")


def private_output(path, flags):
    return os.open(path, flags, 0o600)


if __name__ == "__main__":
    main()
