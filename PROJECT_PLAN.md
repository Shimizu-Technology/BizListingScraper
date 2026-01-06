# BizListing Scraper - Project Plan

## Client Requirements (Sam)

### Data Criteria

**Geography** - Business location must be:
- Michigan
- Connecticut

**Financial Filters** (at least ONE must be true):
- Revenue > $2,000,000
- Cash Flow / SDE > $400,000
- EBITDA > $400,000

### Fields to Capture (6 total)

| Field | Description |
|-------|-------------|
| Date Posted | When the listing was created |
| Geography | City, State |
| Revenue | Annual revenue |
| Cash Flow / SDE | Seller Discretionary Earnings |
| EBITDA | Earnings Before Interest, Taxes, Depreciation, Amortization |
| Description | Business description text |

### Output Requirements
- Daily scrape (morning)
- Excel/CSV compatible export
- Track reviewed vs new listings

---

## Target Websites

### Free Public Sites (6)
| Site | URL | Priority |
|------|-----|----------|
| BizBuySell | bizbuysell.com | ✅ Built |
| BizQuest | bizquest.com | High |
| BusinessBroker.net | businessbroker.net | High |
| DealStream | dealstream.com | Medium |
| BusinessesForSale | businessesforsale.com | Medium |
| BizBen | bizben.com | Low |

### Broker Sites (6)
| Site | URL | Notes |
|------|-----|-------|
| FCBB | fcbb.com | Franchise focused |
| Transworld | tworld.com | Large network |
| Synergy BB | synergybb.com | Regional |
| Murphy Business | murphybusiness.com | National |
| Gottesman Company | gottesman-company.com | Midwest |
| SMB Deal Hunter | app.smbdealhunter.xyz | Aggregator |

### Paid Sites (13) - Requires Subscriptions
| Site | URL |
|------|-----|
| Kairodata | kairodata.com |
| SourceScrub | sourcescrub.com |
| Kumo | withkumo.com |
| Grata | grata.com |
| Rejigg | rejigg.com |
| Acquire | acquire.com |
| ClearlyAcquired | clearlyacquired.com |
| Source Code Deals | sourcecodeals.com |
| PrivSource | privsource.com |
| Evermark | evermark.ai |
| X5 Deals | x5deals.com |
| Inven | inven.ai |
| Axial | axial.net |

---

## Development Phases

### Phase 1: Complete BizBuySell
**Status:** ✅ Complete

| Task | Status |
|------|--------|
| Basic scraping (MI) | ✅ Done |
| Anti-bot bypass (Firefox) | ✅ Done |
| Database schema | ✅ Done |
| Change tracking | ✅ Done |
| API endpoints | ✅ Done |
| React dashboard | ✅ Done |
| Add Connecticut | ✅ Done |
| Add EBITDA field | ✅ Done |
| Financial filters (UI) | ✅ Done |
| Excel (.xlsx) export | ✅ Done |
| "Reviewed" tracking | ✅ Done |
| Mobile optimization | ✅ Done |
| Detail page scraping (Revenue/EBITDA) | ✅ Built (optional) |

**BizBuySell Data (actual - Dec 19):**
- Michigan: 1,291 listings
- Connecticut: 559 listings  
- **Total: 1,850 listings**

**Scrape Performance (measured):**
| Scrape Type | MI | CT | Total | Data Coverage |
|-------------|-----|-----|-------|---------------|
| Card only | ~7 min | ~6 min | **~13 min** | Price (96%), CF (42%), Location |
| + Detail pages | ~1.5 hr | ~1.5 hr | **~3 hours** | + Revenue (70%), EBITDA (10%) |

**Technical Notes:**
- Firefox required (Chromium gets blocked on search pages)
- Rate limiting after ~50 rapid requests (wait ~5-10 min to clear)
- Always save to JSON before database insert (backup)

### Phase 2: Free Public Sites
Build one scraper at a time, test thoroughly before moving to next.

| Site | Status | Notes |
|------|--------|-------|
| BizQuest | ✅ Complete | 4,629 listings (MI: 2,573, CT: 2,056) |
| BusinessesForSale | ✅ Complete | 435 listings, **77% have Revenue!** |
| BusinessBroker.net | ❌ Blocked | Aggressive CAPTCHA (works with VPN but tedious) |
| DealStream | ❌ Blocked | Anti-automation slider CAPTCHA |
| BizBen | ⚠️ Low Priority | California-focused, only ~25 MI listings |

**BizQuest Data (actual - Dec 18):**
- Michigan: 2,573 listings
- Connecticut: 2,056 listings
- **Total: 4,629 listings**
- Scrape time: **~4 min** for both states

**BizQuest Notes:**
- Angular SPA - uses URL-based pagination (`/page-N/`)
- Cash Flow (41%) available on listing cards
- EBITDA rarely disclosed (0.3%)

**BusinessesForSale Data (Dec 18):**
- Michigan: 315 listings
- Connecticut: 120 listings
- **Total: 435 listings**
- **77% have Revenue on listing cards!** ⭐

### Phase 3: Broker Sites
More complex navigation, proprietary structures.

| Site | Status | Notes |
|------|--------|-------|
| Transworld | ✅ Complete | 101 listings (MI: 73, CT: 28), Vue SPA |
| Synergy BB | ✅ Complete | 29 listings (MI: 7, CT: 22), **has Revenue!** |
| SMB Deal Hunter | ✅ Complete | 19 listings (MI: 10, CT: 9), uses "See more" pagination |
| FCBB | ✅ Complete | 7 listings (MI: 3, CT: 4), **has Revenue!** |
| Murphy Business | ❌ Removed | National listings only (no proper MI/CT state data) |
| Gottesman Company | ⚠️ Skipped | Large M&A deals ($5M-$250M), regional only |

**FCBB Data (Dec 18):**
- Michigan: 3 listings
- Connecticut: 4 listings
- **Has Revenue AND Cash Flow on listing cards** ⭐

**Transworld Data (Dec 18):**
- Michigan: 73 listings (9 pages)
- Connecticut: 28 listings (4 pages)
- Vue SPA with `&page=X` URL pagination

**Synergy BB Data (Dec 18):**
- Michigan: 7 listings
- Connecticut: 22 listings
- **Has Revenue on listing cards** ⭐

**SMB Deal Hunter Data (Dec 19):**
- Michigan: 10 listings
- Connecticut: 9 listings
- Uses "See more" button pagination (loads 309 total, filters to MI/CT)

### Phase 4: Paid Sites
Requires Sam's credentials and active subscriptions.

| Task | Status |
|------|--------|
| Research APIs for each site | 🔲 Pending |
| Get credentials from Sam | 🔲 Pending |
| Build scrapers (or API integrations) | 🔲 Pending |

| Site | API? | Status |
|------|------|--------|
| Kairodata | TBD | 🔲 Pending |
| SourceScrub | TBD | 🔲 Pending |
| Kumo | TBD | 🔲 Pending |
| Grata | TBD | 🔲 Pending |
| Rejigg | TBD | 🔲 Pending |
| Acquire | TBD | 🔲 Pending |
| ClearlyAcquired | TBD | 🔲 Pending |
| Source Code Deals | TBD | 🔲 Pending |
| PrivSource | TBD | 🔲 Pending |
| Evermark | TBD | 🔲 Pending |
| X5 Deals | TBD | 🔲 Pending |
| Inven | TBD | 🔲 Pending |
| Axial | TBD | 🔲 Pending |

---

## Technical Architecture

```
backend/
├── app/
│   ├── main.py          # FastAPI app
│   ├── database.py      # PostgreSQL connection
│   ├── models.py        # Pydantic models
│   └── routers/
│       ├── listings.py  # Listing endpoints
│       └── stats.py     # Statistics endpoints
├── scraper/
│   ├── base.py          # Shared utilities
│   ├── stealth.py       # Anti-bot helpers
│   ├── upsert.py        # Database operations
│   ├── bizquest.py      # ✅ Complete (4,629 listings)
│   ├── bizbuysell.py    # ✅ Complete (1,850 listings)
│   ├── businessesforsale.py # ✅ Complete (435 listings)
│   ├── transworld.py    # ✅ Complete (101 listings)
│   ├── synergybb.py     # ✅ Complete (29 listings)
│   ├── smbdealhunter.py # ✅ Complete (19 listings)
│   ├── fcbb.py          # ✅ Complete (7 listings)
│   ├── murphybusiness.py # ❌ Removed (no MI/CT data)
│   └── main.py          # Scraper entry point
└── requirements.txt

frontend/
├── src/
│   ├── App.tsx          # Main dashboard
│   ├── components/      # UI components
│   ├── hooks/           # React hooks
│   └── lib/             # API helpers
└── package.json
```

---

## Scraper Interface

Each scraper follows a consistent interface:

```python
async def scrape(
    states: list[str],      # ["MI", "CT"]
    max_pages: int = 25
) -> list[dict]:
    """
    Returns list of listings with fields:
    - external_id: str
    - url: str
    - title: str
    - asking_price: float | None
    - cash_flow: float | None
    - gross_revenue: float | None
    - ebitda: float | None
    - city: str | None
    - state: str | None
    - description: str | None
    - source: str  # e.g., "bizbuysell"
    """
```

---

## Database Schema

**listings** table:
- id, external_id, source, url
- title, description
- asking_price, cash_flow, gross_revenue, ebitda
- city, state, county, zip_code
- category, subcategory
- broker_name, broker_company, broker_phone, broker_email
- first_seen_at, last_seen_at, last_updated_at
- is_active, is_reviewed (new)
- content_hash (for deduplication)

**listing_history** table:
- Tracks all changes (price updates, etc.)

**scrape_runs** table:
- Logs each scrape execution

---

## Scraping Process

**Full Scrape (~28 minutes) - 7,070 listings total:**
1. BizQuest - ~4 min (MI: 2,573 + CT: 2,056 = 4,629)
2. BizBuySell - ~13 min (MI: 1,291 + CT: 559 = 1,850)
3. BusinessesForSale - ~3 min (MI: 315 + CT: 120 = 435)
4. Transworld - ~2 min (MI: 73 + CT: 28 = 101)
5. Synergy BB - <1 min (MI: 7 + CT: 22 = 29)
6. SMB Deal Hunter - ~5 min (MI: 10 + CT: 9 = 19)
7. FCBB - <1 min (MI: 3 + CT: 4 = 7)

**Execution:**
- Scrapers run **sequentially** (one at a time)
- Each scraper opens Firefox in headless mode
- Progress tracked in `scrape_runs` table
- Stale listings (7+ days unseen) auto-deactivated

**Automation Options:**
- GitHub Actions (cron schedule)
- Render.com cron jobs
- Local crontab

---

## Next Steps

1. ✅ Review this plan with Leon
2. ✅ Complete Phase 1 (BizBuySell features)
3. ✅ Complete BizQuest scraper
4. ✅ Complete BusinessesForSale scraper
5. ✅ Complete Phase 3 broker sites (FCBB, Transworld, Synergy BB, SMB Deal Hunter)
6. ✅ Clean up data (removed 204 listings with invalid/NULL state)
7. 🔲 **Review QUESTIONS_FOR_SAM.md with Sam**
8. 🔲 Get credentials for Phase 4 paid sites
9. 🔲 Set up automated daily scraping
