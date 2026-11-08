"""Collect creative-finance story leads and print an editorial brief."""

import argparse
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from html import unescape
import os
from pathlib import Path
import re
import sqlite3
import sys
from urllib.parse import parse_qsl, urlencode, urljoin, urlsplit, urlunsplit
from urllib.request import Request, urlopen
from xml.etree import ElementTree as ET

from youtube_audience_scout import read_key, timestamp, youtube


FEEDS = {
    "REIClub": "https://reiclub.com/feed/",
    "Coach Carson": "https://www.coachcarson.com/feed/",
    "Wendy Patton": "https://wendypatton.com/feed/",
    "CashFlowDepot": "https://www.cashflowdepot.com/feed/",
    "LegalWiz": "https://www.legalwiz.com/feed/",
    "1031 CORP.": "https://www.1031corp.com/exchanging-thoughts-blog/rss.xml",
}

DUE_ON_SALE = "https://uscode.house.gov/view.xhtml?req=granuleid:USC-prelim-title12-section1701j-3"
IRS = "https://www.irs.gov/publications/p544"
COUNTY = "https://www.jccal.org/660/Tax-Lien-Info"
CFPB = "https://www.consumerfinance.gov/consumer-tools/mortgages/how-to-avoid-foreclosure/"
AREC = "https://arec.alabama.gov/docs/forms/edu/Case%202.pdf"


@dataclass(frozen=True)
class Topic:
    title: str
    pattern: str
    premise: str
    checks: str
    references: tuple[str, ...]


TOPICS = {
    "subject-to": Topic(
        "Subject-to purchases", r"subject[ -]to|\bsub[ -]?2\b",
        "A seller needs to move before their listing sells. A buyer compares a subject-to offer with a conventional sale and the seller chooses what fits.",
        "Check the note and due-on-sale clause, lender-consent options, seller liability, insurance, payment servicing, and the buyer's exit.",
        (DUE_ON_SALE,),
    ),
    "1031": Topic(
        "1031 exchanges", r"\b1031\b|like[ -]kind exchange|qualified intermediary",
        "A landlord sells a small rental and has three possible replacements. One falls through while the exchange clock is running.",
        "Check eligible use, intermediary involvement before closing, identification and completion deadlines, and potential taxable boot.",
        (IRS,),
    ),
    "tax-auction": Topic(
        "Tax lien and tax deed auctions", r"tax[ -]?(?:lien|deed|sale|auction)|delinquent property tax",
        "A first-time bidder has a $3,000 budget and stops when they learn the county is auctioning a lien on the house.",
        "Verify the jurisdiction, auction type, what the winning bidder receives, redemption, title, and possession before writing claims.",
        (COUNTY, "https://www.revenue.alabama.gov/faqs/what-is-a-lien/"),
    ),
    "low-down": Topic(
        "Low or no money down", r"(?:\bno\b|\blow\b|\bzero\b|\$0)[ -](?:money[ -])?down|seller financ|owner financ|creative financ",
        "A buyer negotiates a seller-financed purchase and itemizes how much cash is still needed for closing, repairs, and reserves.",
        "Verify cash to close, liens, balloon date, payment schedule, financing rules, and the downside case if refinancing fails.",
        ("https://www.consumerfinance.gov/ask-cfpb/what-is-a-balloon-payment-when-is-one-allowed-en-104/",),
    ),
    "property-control": Topic(
        "Lease options and property control", r"lease[ -]?(?:option|purchase)|master[ -]lease|rent[ -]to[ -]own",
        "An owner wants stable rent. A renter-investor compares a master lease with a separate option and faces a repair before the option expires.",
        "Check the lease, consent to sublet, option dates and price, allocation of repairs, and local rules before describing the structure.",
        ("https://www.legalwiz.com/lease-options-and-alternative-financing/",),
    ),
    "distressed-sellers": Topic(
        "Options for distressed sellers", r"distressed (?:seller|owner|property)|motivated sellers?|foreclos|short sale|loss mitigation",
        "An owner behind on payments compares a servicer workout, a conventional sale, and an investor's offer using a side-by-side timeline.",
        "Show the owner's alternatives and actual deadlines. Verify facts with the servicer or relevant authority and avoid promises of foreclosure relief.",
        (CFPB,),
    ),
    "bird-dogging": Topic(
        "Bird-dogging and deal sourcing", r"bird[ -]?dog|driving for dollars|off[ -]market|wholesal",
        "A local investor spots an empty house and distinguishes public-record research from activity that may require a license.",
        "Verify the state's licensing rules, what services are performed, and who can receive compensation before suggesting a referral model.",
        (AREC,),
    ),
}

ARCHIVE = (
    ("subject-to", "Coach Carson", "Buying subject-to an existing mortgage", "https://www.coachcarson.com/subject-to-a-simple-profitable-explanation/"),
    ("1031", "1031 CORP.", "1031 exchange basics", "https://www.1031corp.com/1031-exchange-basics"),
    ("tax-auction", "Jefferson County, Alabama", "Tax lien auction information", COUNTY),
    ("low-down", "REIClub", "Seller financing with low cash down", "https://reiclub.com/articles/seller-financing-key-closing-no-money-down/"),
    ("property-control", "CashFlowDepot", "Options article archive", "https://www.cashflowdepot.com/topic-blog/options/"),
    ("distressed-sellers", "CFPB", "Homeowner options to avoid foreclosure", CFPB),
    ("bird-dogging", "REIClub", "Bird-dogging versus wholesaling", "https://reiclub.com/articles/bird-dogging-versus-wholesaling/"),
)
QUERIES = {
    "subject-to": "subject to mortgage real estate deal walkthrough",
    "1031": "1031 exchange rental property case study",
    "tax-auction": "Alabama tax lien auction real estate",
    "low-down": "seller financing real estate low money down case study",
}
DEFAULT_DB = Path.home() / ".local/state/youtube-story-sources/leads.sqlite3"


@dataclass(frozen=True)
class Lead:
    topic: str
    kind: str
    source: str
    title: str
    url: str
    published: str


def clean(value, limit=250):
    return " ".join(unescape(value).split())[:limit]


def canonical_url(base, link):
    parsed = urlsplit(urljoin(base, link.strip()))
    if parsed.scheme not in {"https", "http"} or not parsed.hostname or parsed.username is not None:
        return ""
    if any(char.isspace() or char in '<>"' or ord(char) < 32 for char in parsed.geturl()):
        return ""
    query = [(key, value) for key, value in parse_qsl(parsed.query, keep_blank_values=True)
             if not key.lower().startswith("utm_") and key.lower() not in {"fbclid", "gclid", "mc_cid", "mc_eid"}]
    return urlunsplit((parsed.scheme, parsed.netloc.lower(), parsed.path or "/", urlencode(query), ""))


def parse_feed(data, base):
    # Reject entity declarations even in UTF-16/32, before XML parsing.
    if re.search(rb"<!\s*(?:DOCTYPE|ENTITY)\b", data.replace(b"\0", b""), re.I):
        raise ValueError("XML declarations for entities or DTDs are unsupported")
    root = ET.fromstring(data)
    local_name = lambda tag: tag.rsplit("}", 1)[-1]
    if local_name(root.tag).lower() not in {"rss", "feed", "rdf"}:
        raise ValueError("response is not an RSS or Atom feed")
    entries = []
    for node in root.iter():
        if local_name(node.tag) not in {"item", "entry"}:
            continue
        fields = {local_name(child.tag): child for child in node if local_name(child.tag) != "link"}
        title_element = fields.get("title")
        title = clean("".join(title_element.itertext())) if title_element is not None else ""
        links = [child for child in node if local_name(child.tag) == "link"
                 and child.get("rel", "alternate") == "alternate"]
        link = next((child.get("href") or child.text for child in links if child.get("href") or child.text), "")
        url = canonical_url(base, link) if link else ""
        if not title or not url:
            continue
        published = next((fields[key].text for key in ("published", "pubDate", "updated", "date")
                          if key in fields and fields[key].text), "")
        entries.append((title, url, clean(published, 100)))
    return entries


def normalized_date(value):
    for parse in (datetime.fromisoformat, parsedate_to_datetime):
        try:
            result = parse(value)
            return timestamp(result.replace(tzinfo=result.tzinfo or timezone.utc).astimezone(timezone.utc))
        except (ValueError, TypeError, OverflowError):
            continue
    return ""


def read_feed(name, url):
    request = Request(url, headers={"User-Agent": "CreativeFinanceStoryScout/1.0 (RSS reader)",
                                    "Accept": "application/rss+xml, application/atom+xml, application/xml, text/xml"})
    with urlopen(request, timeout=15) as response:
        body = response.read(2_000_001)
        if len(body) > 2_000_000:
            raise ValueError("feed exceeds 2 MB")
        entries = parse_feed(body, response.geturl())
    return [Lead(topic, "RSS", name, title, link, normalized_date(date))
            for title, link, date in entries
            for topic, rules in TOPICS.items() if re.search(rules.pattern, title, re.I)]


def video_leads(key, now):
    for topic, query in QUERIES.items():
        rows = youtube("search", key, part="snippet", type="video", q=query, order="relevance",
                       publishedAfter=timestamp(now - timedelta(days=30)), maxResults=5,
                       regionCode="US", relevanceLanguage="en", videoDuration="medium")
        leads = []
        for row in rows:
            vid = row.get("id", {}).get("videoId", "")
            if re.fullmatch(r"[A-Za-z0-9_-]{11}", vid):
                snippet = row["snippet"]
                leads.append(Lead(topic, "YouTube", "YouTube Data API", clean(snippet["title"]),
                                  f"https://www.youtube.com/watch?v={vid}",
                                  normalized_date(snippet.get("publishedAt", ""))))
        yield topic, leads


def initialize(conn):
    conn.execute("PRAGMA secure_delete = ON")
    conn.execute("""CREATE TABLE IF NOT EXISTS leads (
        topic TEXT NOT NULL, kind TEXT NOT NULL, source TEXT NOT NULL, title TEXT NOT NULL,
        url TEXT NOT NULL, published TEXT NOT NULL, seen TEXT NOT NULL,
        PRIMARY KEY (topic, url)
    )""")


def save_leads(conn, leads, now):
    count = 0
    for lead in leads:
        result = conn.execute("INSERT OR IGNORE INTO leads VALUES (?, ?, ?, ?, ?, ?, ?)",
                              (lead.topic, lead.kind, lead.source, lead.title, lead.url,
                               lead.published, timestamp(now)))
        count += result.rowcount
    return count


def purge_youtube(conn, now):
    conn.execute("DELETE FROM leads WHERE kind = 'YouTube' AND seen <= ?",
                 (timestamp(now - timedelta(days=28)),))


def collect(conn, now, key=None):
    errors = 0
    with ThreadPoolExecutor(max_workers=4) as pool:
        reads = {name: pool.submit(read_feed, name, url) for name, url in FEEDS.items()}
        for name, job in reads.items():
            try:
                leads = job.result()
            except (OSError, ValueError, ET.ParseError) as exc:
                print(f"ERROR {name}: {exc}", file=sys.stderr)
                errors += 1
                continue
            with conn:
                added = save_leads(conn, leads, now)
            print(f"RSS {name}: {len(leads)} relevant matches, {added} new")
    if key:
        try:
            for topic, leads in video_leads(key, now):
                with conn:
                    added = save_leads(conn, leads, now)
                print(f"YouTube {topic}: {len(leads)} results, {added} new")
        except (RuntimeError, ValueError, KeyError) as exc:
            print(f"ERROR YouTube discovery: {exc}", file=sys.stderr)
            errors += 1
    return errors


def brief(conn, topic, now):
    rules = TOPICS[topic]
    lines = [f"# {rules.title}", "", "**Fictional example — editorial draft**", "",
             rules.premise, "", "## What to verify", "", rules.checks, "",
             "## Verification references", ""]
    lines += [f"- <{url}>" for url in rules.references]
    lines += ["", "## Research leads", ""]
    cutoff = timestamp(now - timedelta(days=28))
    # Reserve space for each type of source, so a busy feed can't hide the others.
    for kind, maximum in (("Archive", 2), ("RSS", 4), ("YouTube", 3)):
        rows = conn.execute("""SELECT source, title, url FROM leads
            WHERE topic = ? AND kind = ? AND (kind <> 'YouTube' OR seen > ?)
            ORDER BY published DESC, seen DESC, url LIMIT ?""", (topic, kind, cutoff, maximum))
        lines.extend(f"- {source}: {title} — <{url}>" for source, title, url in rows)
    lines += ["", "## Story beats", "", "1. Open on the decision and what is at stake.",
              "2. Show the deal terms, cash needed, and realistic alternatives.",
              "3. Introduce one plausible setback and show how it changes the outcome.",
              "4. Close with the verification checklist and distinguish assumptions from facts.", "",
              "Use original characters, numbers, analysis, and visuals. Keep this example labeled fictional.",
              "Treat linked stories as research leads. Review claims, attribution, and applicable disclosures before recording."]
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    parser.add_argument("--with-youtube", action="store_true", help="Run four official YouTube Data API searches.")
    parser.add_argument("--key-file", type=Path)
    parser.add_argument("--brief", choices=TOPICS, help="Print a brief from the queue without fetching new sources.")
    args = parser.parse_args()
    if args.brief and (args.with_youtube or args.key_file):
        parser.error("--brief reads the queue without YouTube credentials or requests")
    os.umask(0o077)
    args.db.parent.mkdir(parents=True, exist_ok=True)
    now = datetime.now(timezone.utc)
    conn = sqlite3.connect(args.db, timeout=30)
    try:
        with conn:
            initialize(conn)
            purge_youtube(conn, now)
            added = save_leads(conn, (Lead(topic, "Archive", source, title, url, "")
                                     for topic, source, title, url in ARCHIVE), now)
        if args.brief:
            print(brief(conn, args.brief, now))
            return 0
        if added:
            print(f"Archive: {added} new reference leads")
        key_error = False
        key = None
        if args.with_youtube:
            try:
                key = read_key(args.key_file)
            except (OSError, ValueError) as exc:
                print(f"ERROR YouTube credentials: {exc}", file=sys.stderr)
                key_error = True
        errors = collect(conn, now, key)
        count = conn.execute("SELECT count(*) FROM leads").fetchone()[0]
        print(f"Queue: {count} topic-linked leads")
        return int(bool(errors or key_error))
    finally:
        conn.close()


if __name__ == "__main__":
    raise SystemExit(main())
