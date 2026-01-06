# Discussion Points for Sam

## Current Status (Updated Dec 19)

### Completed Sources

| Source | MI | CT | Total | Time | Revenue on Cards? |
|--------|-----|-----|-------|------|-------------------|
| BizQuest | 2,573 | 2,056 | 4,629 | ~4 min | No |
| BizBuySell | 1,291 | 559 | 1,850 | ~13 min | No |
| BusinessesForSale | 315 | 120 | 435 | ~3 min | **Yes ✅ (77%)** |
| Transworld | 73 | 28 | 101 | ~2 min | No |
| Synergy BB | 7 | 22 | 29 | <1 min | **Yes ✅** |
| SMB Deal Hunter | 10 | 9 | 19 | ~5 min | Yes |
| FCBB | 3 | 4 | 7 | <1 min | **Yes ✅** |
| **Total** | **4,272** | **2,798** | **7,070** | **~28 min** | |

*Note: Murphy Business removed (national listings without proper MI/CT state data)*

### Sites Investigated But Blocked

| Site | Issue | Workaround |
|------|-------|------------|
| DealStream | Anti-automation verification (slider CAPTCHA) | Requires manual solving |
| BusinessBroker.net | Aggressive CAPTCHA (5x in a row) | Works with VPN but tedious |

### Sites With Limited MI/CT Coverage

| Site | Status | Notes |
|------|--------|-------|
| BizBen | California-focused | Only ~25 MI listings, low priority |
| Gottesman Company | Large M&A deals ($5M-$250M) | Regional locations only (Southeast, USA, etc.) - no state filter |

---

## Data Availability Summary

| Field | BizBuySell | BizQuest | BusinessesForSale | FCBB | Transworld | Synergy BB | SMB Deal Hunter |
|-------|------------|----------|-------------------|------|------------|------------|-----------------|
| Asking Price | 96% | 97% | 87% | 100% | 100% | 100% | 100% |
| Cash Flow | 42% | 41% | 50% | 100% | 78% | 100% (SDE) | ~50% |
| **Revenue** | 0% | 0% | **77%** ⭐ | 100% | 0% | **100%** ⭐ | 0% |
| EBITDA | 0% | 0% | 0% | 0% | 0% | 0% | 0% |

**Key Finding:** BusinessesForSale, FCBB, and Synergy BB all show **Revenue on listing cards**!

---

## 1. Credentials Needed

We need login credentials for the **13 paid sites** in Phase 4:
- Kairodata, SourceScrub, Kumo, Grata, Rejigg, Acquire, ClearlyAcquired, Source Code Deals, PrivSource, Evermark, X5 Deals, Inven, Axial

**Which ones do you have access to?**

---

## 2. Revenue/EBITDA Data

**Good news:** We now have Revenue data from BusinessesForSale (435 listings, 77% with Revenue).

**For more Revenue data from BizBuySell/BizQuest:**
- Need to visit ~6,600+ individual detail pages
- Estimated time: **3-4 hours** (running in parallel overnight)
- Expected result: ~70% have Revenue, ~10% have EBITDA

**Question: Is more Revenue data worth the extra time?**
- If yes → We'll run detail scrapes overnight (2 AM)
- If no → We stick with card-only scrapes (~30 min)

---

## 3. EBITDA Filter

Your criteria included EBITDA > $400K, but:
- **0% of listings** disclose EBITDA on cards
- Even on detail pages, only ~10% disclose EBITDA
- Most show "Not Disclosed"

**Recommendation:** Use Cash Flow (SDE) instead of EBITDA as the primary filter.

---

## 4. Filtering Approach

Cash Flow availability: **42%** overall (~3,000 of 7,143 listings).

**Options:**
- A) Show all listings, let you filter manually ← *Recommended*
- B) Only show listings that have Cash Flow data

---

## What We Have Now

| Metric | Count |
|--------|-------|
| Total Listings | ~7,300 |
| With Asking Price | ~7,000 (96%) |
| With Cash Flow | ~3,200 (44%) |
| With Revenue | ~400 (5%) |
| Sources | 8 active |
| States | MI + CT |
| Export Format | **Excel (.xlsx)** ✅ |
| Scrape Time | ~30 min (all 8 sources, sequential) |

---

## 5. Daily Scrape Process

| Scrape Type | Time | When to Run |
|-------------|------|-------------|
| **Card-only** (current) | ~30 min | Morning (6 AM) |
| **With detail pages** | ~3-4 hrs | Overnight (2 AM) |

**What happens:**
- All 8 scrapers run one at a time
- Shows: new, updated, unchanged, failed
- Stale listings (not seen for 7 days) are hidden, not deleted
- You can view inactive listings anytime via the "Active/Inactive" filter

---

## Next Steps

1. **Your input needed:**
   - Which paid sites do you have access to?
   - Is more Revenue worth 3-4 extra hours of scraping?
   - OK to use Cash Flow instead of EBITDA?
   - **Preferred time for daily scrape?** (e.g., 6 AM EST)

2. **Done so far:**
   - ✅ BizBuySell
   - ✅ BizQuest  
   - ✅ BusinessesForSale (has Revenue!)
   - ✅ Transworld
   - ✅ FCBB
   - ✅ Synergy BB (has Revenue!)
   - ✅ SMB Deal Hunter
   - ✅ Murphy Business (national listings)

---

*Shimizu Technology*
