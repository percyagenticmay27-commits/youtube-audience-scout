import sqlite3
import unittest
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

import story_scout as scout

NOW = datetime(2026, 11, 8, 15, tzinfo=timezone.utc)


class StoryScoutTests(unittest.TestCase):
    def test_rss_and_atom_keep_metadata_and_remove_tracking(self):
        rss = b"""<rss><channel><item><title>Buying a house with no money down</title>
        <link>https://example.com/deal?utm_source=rss&amp;id=12</link>
        <description>Do not ingest this body.</description></item></channel></rss>"""
        atom = b"""<feed xmlns="http://www.w3.org/2005/Atom"><entry><title>Section 1031 basics</title>
        <link rel="self" href="/feed"/><link rel="alternate" href="/exchange"/>
        <published>2026-11-01T00:00:00Z</published></entry></feed>"""
        self.assertEqual(scout.parse_feed(rss, "https://example.com/feed"),
                         [("Buying a house with no money down", "https://example.com/deal?id=12", "")])
        self.assertEqual(scout.parse_feed(atom, "https://example.com/feed"),
                         [("Section 1031 basics", "https://example.com/exchange", "2026-11-01T00:00:00Z")])
        with self.assertRaises(ValueError):
            scout.parse_feed(b"<!DOCTYPE rss><rss/>", "https://example.com/feed")

    def test_deduplicates_and_purges_old_youtube_metadata(self):
        with sqlite3.connect(":memory:") as conn:
            scout.initialize(conn)
            leads = [
                scout.Lead("subject-to", "RSS", "Blog", "Subject-to terms", "https://example.com/x", ""),
                scout.Lead("subject-to", "YouTube", "YouTube Data API", "Subject-to case study",
                           "https://www.youtube.com/watch?v=abc", ""),
            ]
            self.assertEqual(scout.save_leads(conn, leads, NOW), 2)
            self.assertEqual(scout.save_leads(conn, leads, NOW), 0)
            scout.purge_youtube(conn, NOW + timedelta(days=28))
            brief = scout.brief(conn, "subject-to", NOW + timedelta(days=28))
            self.assertIn("https://example.com/x", brief)
            self.assertNotIn("watch?v=abc", brief)
            self.assertIn("Research lead — evidence review required", brief)
            self.assertIn("Deal date and jurisdiction", brief)
            self.assertIn("Finding the property", brief)
            self.assertIn("Closing and control", brief)
            self.assertIn("Not disclosed", brief)
            self.assertNotIn("Fictional example", brief)
            self.assertIn("due-on-sale", brief.lower())

    def test_youtube_keeps_query_provenance_and_uses_bounded_searches(self):
        row = {"id": {"videoId": "abcdefghijk"}, "snippet": {"title": "Case study", "publishedAt": "2026-11-04"}}
        with patch.object(scout, "youtube", return_value=[row]) as api:
            batches = list(scout.video_leads("mock", NOW))
        self.assertEqual(len(batches), 4)
        self.assertTrue(all(call.args[0] == "search" and call.kwargs["maxResults"] == 5 for call in api.call_args_list))
        self.assertEqual(batches[0][1][0].url, "https://www.youtube.com/watch?v=abcdefghijk")

    def test_one_bad_feed_does_not_discard_other_leads(self):
        lead = scout.Lead("subject-to", "RSS", "Blog", "Title", "https://example.com/ok", "")
        with sqlite3.connect(":memory:") as conn:
            scout.initialize(conn)
            with patch.object(scout, "FEEDS", {"OK": "good", "Down": "bad"}), patch.object(
                scout, "read_feed", side_effect=lambda name, url: [lead] if url == "good" else
                (_ for _ in ()).throw(ValueError("invalid feed"))
            ):
                result = scout.collect(conn, NOW)
            self.assertEqual(result, 1)
            self.assertEqual(conn.execute("SELECT count(*) FROM leads").fetchone()[0], 1)
