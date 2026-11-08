# Creative Finance Stories

Faceless episodes for small residential real estate investors. Each episode puts
a fictional buyer or seller at a decision point, shows the numbers and tradeoffs,
and gives the viewer one claim they can verify.

## Run the source intake

From this repository, run the following with Python 3.10 or newer. The intake
uses the standard library and the existing Audience Scout API client.

```bash
python3 story_scout.py
python3 story_scout.py --with-youtube --key-file /path/to/protected.env
python3 story_scout.py --brief tax-auction
python3 story_scout.py --brief subject-to
python3 story_scout.py --brief 1031
python3 -m unittest -v test_story_scout
```

The default SQLite queue is `~/.local/state/youtube-story-sources/leads.sqlite3`.
An alternate path is available through `--db`. Each lead records a publisher or
source type, topic, title, public URL, publication date when provided, and first
capture time. A source link appears once per topic. A failed publisher fetch
allows other sources to finish and leaves a failing exit status for the operator.
The command purges YouTube metadata at 28 days. Keep collection data outside
the public repository. The YouTube option uses at most four searches per run
and reads the key from a protected file, environment variable, or hidden prompt.

The seven briefs cover subject-to, 1031, tax auctions, low money down, property
control, distressed sellers, and bird-dogging. Four of these topics have YouTube
searches. The remaining three have RSS and curated references.

## Turn a lead into an episode

1. Open the linked sources and verify any claim about taxes, law, or financing
   against the current rule for the stated jurisdiction.
2. For an original fictional case, build the characters, deal numbers, sequence
   of decisions, analysis, and ending independently. Label it fictional in the
   narration and on screen. If telling a real case, verify the facts, attribute
   sources, and clear rights for any protected material you plan to reuse.
3. Add a cash-to-close table or timeline, a downside scenario, and a decision.
   For a distressed seller, show the seller's alternatives and consequences.
4. Produce original or appropriately licensed diagrams, narration, and visuals.
   Review source links, disclosure, and the final script before publishing.

The intake stores metadata and references. It does not collect article bodies,
YouTube transcripts, or media. YouTube sources are research leads, and their
appearance in the queue does not verify the creator's claims.

- [U.S. Copyright Office on facts and expression](https://www.copyright.gov/what-is-copyright/)
- [YouTube monetization policies](https://support.google.com/youtube/answer/1311392)
- [YouTube disclosure guidance](https://support.google.com/youtube/answer/14328491)
