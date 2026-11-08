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
   documentary reporting. Record the transaction date, jurisdiction, and source.
2. Establish the use the investor planned **before committing** and the actual
   use or exit afterward. Confirm that the proposed use was permitted and that
   the buyer's rights, property condition, and timeline supported it.
3. Build the budget through the intended use or exit. Record acquisition and
   closing costs, financing and interest, repairs and permits, insurance,
   taxes, vacancy or holding costs, and reserves. Include selling costs when
   the exit is a sale. Separate cash invested from total project cost, and
   avoid counting borrowed principal or the same expense twice.
4. Compare costs with the intended result. For a rental, use market-supported
   rent, vacancy, operating costs, debt service, and reserves to estimate cash
   flow. For a flip, compare conservative net sale proceeds with costs through
   sale. For owner use, compare ownership with leasing comparable space over
   the same period. Stress-test repair overruns, delays, and a weaker exit.
5. Trace how the investor found, financed, closed, and controlled the property.
   Verify material rules for the place and time of the deal. Separate current
   guidance and comparisons with other jurisdictions.
6. Review the title and narration against the evidence. Label reenactments or
   pseudonyms and clear rights for any protected material you reuse.

### How to log gaps

Create a row for every material fact. Record the reported value, source link and
page or timestamp, evidence status, and the next record to check. Typical records
include the deed or purchase agreement, settlement statement, invoices, leases,
comparable rents or sales, and local permit or zoning records. Treat an
investor's account as attributed evidence and a record that independently backs
it up as documented evidence. Use **not disclosed** for an absent detail and
**not independently verified** when an attributed claim lacks corroboration.
Label projections and assumptions separately.

If a missing fact could change the conclusion, mark **feasibility unverified**.
A case can still explain a documented purchase or cost surprise. Hold it when
the missing evidence would make the title or takeaway misleading.

The intake stores metadata and references. It does not collect article bodies,
YouTube transcripts, or media. YouTube sources are research leads, and their
appearance in the queue does not verify the creator's claims.

- [U.S. Copyright Office on facts and expression](https://www.copyright.gov/what-is-copyright/)
- [YouTube monetization policies](https://support.google.com/youtube/answer/1311392)
- [YouTube disclosure guidance](https://support.google.com/youtube/answer/14328491)
