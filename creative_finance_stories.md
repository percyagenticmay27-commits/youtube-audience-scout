# Creative Finance Stories

Faceless episodes for small residential real estate investors. Each episode
follows a documented transaction and shows what the investor found, how they
funded it, what happened at closing, and what they actually controlled.

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

1. Choose a real deal from an investor interview, a firsthand article, or
   documentary reporting. Record the deal date, place, and source separately
   from the publication date.
2. Trace the opportunity, financing, closing, control, and outcome. Attribute
   firsthand accounts and distinguish them from independently verified
   records. Mark unavailable details as undisclosed or unverified. Hold the
   story if a missing detail is central to the title or takeaway.
3. Verify material legal, tax, and financing claims for the original
   jurisdiction and time. Present current rules or a different jurisdiction
   in a separate, sourced comparison.
4. Write original narration and analysis using the established facts. Keep
   figures and events intact. Label any reenactment or pseudonym and clear
   rights for any protected material you reuse.
5. Review the title against the evidence. Keep price, down payment, total
   cash to close, repair costs, and post-closing rights separate.

The intake stores metadata and references. It does not collect article bodies,
YouTube transcripts, or media. YouTube sources are research leads, and their
appearance in the queue does not verify the creator's claims.

- [U.S. Copyright Office on facts and expression](https://www.copyright.gov/what-is-copyright/)
- [YouTube monetization policies](https://support.google.com/youtube/answer/1311392)
- [YouTube disclosure guidance](https://support.google.com/youtube/answer/14328491)
