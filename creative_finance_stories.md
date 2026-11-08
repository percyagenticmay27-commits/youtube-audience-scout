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

### Explain how a beginner would fund the deal

Start with how the actual investor funded the deal. Then show other routes only
where they fit the property, intended use, and local rules. Identify them as
illustrative alternatives. A profitable forecast helps make the case to a
funder. It still needs written terms, sufficient cash at each stage, and a
credible repayment plan before the buyer commits.

| Funding route | What the viewer needs to know |
|---|---|
| Hard money | Ask how much the lender advances at closing, what rehab qualifies, when draws are paid, and what must be advanced before reimbursement. Include points, interest, term, and the cost of a delayed exit. |
| Community bank or credit union | Ask for an investment or rehab product that fits the use. Bring the purchase contract, contractor bids, local comps, a cash and reserve plan, and a repayment or exit plan. Ask about borrower qualifications, guarantees, and which assets would secure the loan. A pledged asset can be at risk if the loan defaults. |
| Private investor or equity partner | One person may source and run the deal while the other contributes cash. Establish who puts in how much and when, who makes decisions, who funds overruns, and how capital, profits, or losses are allocated at exit. A private loan and an equity split have different obligations. |
| Seller financing | The seller may accept a down payment and carry part of the price. Show the written terms, security, payment schedule, and how any balloon gets paid. |
| Owner-occupant financing | FHA 203(k) can combine purchase and eligible rehab for qualified borrowers buying a primary residence. USDA Section 502 is a separate homeownership route with income and eligible-area rules. For a pure flip or rental, use a financing route that permits that purpose. |

Show three separate numbers on screen. **Cash at closing**, **cash needed
before rehab draws**, and **reserves through exit**. Show earnest money as a
credit when applicable so it is counted once.

**Illustration using the Madison price and rehab budget.** Suppose an investment
lender advances 80% of the $155,000 purchase and reimburses up to $70,000 of
approved rehab in draws. That would be $124,000 advanced toward the purchase,
leaving a **$31,000 purchase contribution** before lender fees, closing costs,
and prepaids. The buyer still needs money for any contractor bills due before a
draw, plus carrying costs and a reserve. If the buyer cannot cover those amounts
under the written terms, the deal needs another funding structure or a pass.
The percentages are teaching assumptions. The reported Madison financing was
a partnership.

- [HUD FHA 203(k) program](https://www.hud.gov/program_offices/housing/sfh/203k/203k--df)
- [USDA Section 502 guaranteed loan program](https://www.rd.usda.gov/programs-services/single-family-housing-programs/single-family-housing-guaranteed-loan-program)
- [OCC lending handbook](https://www.occ.gov/publications-and-resources/publications/comptrollers-handbook/files/commercial-real-estate-lending/pub-ch-commercial-real-estate.pdf)
- [Example of a rehab lender's reimbursement process](https://fixatedfunding.com/fix-and-flip-loan-faq/)

### How to log gaps

Create a row for every material fact. Record the reported value, source link and
page or timestamp, evidence status, and the next record to check. Typical records
include the deed or purchase agreement, settlement statement, invoices, leases,
comparable rents or sales, and local permit or zoning records. Treat an
investor's account as attributed evidence and a record that independently backs
it up as documented evidence. Use **not disclosed** for an absent detail and
**not independently verified** when an attributed claim lacks corroboration.
Label projections and assumptions separately.

### Production gate

- **Ready.** The viewer can follow the actual deal from the initial goal through
  discovery, funding, closing, control, and the end result. Explain the required
  cash, counterparties, documents, timeline, full costs, and the decision points.
  Separate reported results from forecasts and disclose any immaterial gaps.
- **Hold.** A material cost, financing term, legal requirement, or outcome is
  unresolved and there is a specific record that could resolve it.
- **Skip.** Feasibility cannot be verified or the local rules for the steps
  shown cannot be established. Keep the case out of production.

Verify the original location and time. For instructions viewers can use today,
check the current rules and program terms in the jurisdiction the story names.
A story set in another jurisdiction needs a documented local deal and its own
review. Teach the process and the inputs viewers must recheck for their own
property.

### Candidate review

- **Hold — Madison, Alabama, partnership-funded flip.** Jordan Fulmer reports
  finding the seller through direct mail, renegotiating after inspection,
  funding the deal with partners, and completing the resale. His article
  reports a $155,000 purchase, $70,000 rehab, $370,000 sale, and approximately
  $120,000 of net project profit. For a production-ready recipe, look for the
  closing and holding-cost breakdown, how much cash each side needed and
  when, and supporting closing records. Confirm the applicable permit and
  jurisdiction requirements. [Investor account](https://newsilver.com/the-lender/house-flipping-before-and-after-madison-al/)
  · [City of Madison permitting](https://madisonal.gov/640/Permitting)

The intake stores metadata and references. It does not collect article bodies,
YouTube transcripts, or media. YouTube sources are research leads, and their
appearance in the queue does not verify the creator's claims.

- [U.S. Copyright Office on facts and expression](https://www.copyright.gov/what-is-copyright/)
- [YouTube monetization policies](https://support.google.com/youtube/answer/1311392)
- [YouTube disclosure guidance](https://support.google.com/youtube/answer/14328491)
