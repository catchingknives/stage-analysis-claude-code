---
name: StageAnalysis
description: Stan Weinstein Stage Analysis on any ticker. Determines current stage (1-4), computes moving averages, volume ratios, relative strength, and generates actionable buy/sell signals.
---

## When to Activate

**Trigger words/phrases:**
- "stage analysis [TICKER]"
- "what stage is [TICKER]"
- "weinstein [TICKER]"
- "check stage [TICKER]"
- "analyze [TICKER]" (when context is technical/stage analysis)
- "full stage analysis [TICKER]"

**Mode selection:**
- Default (no qualifier or "quick"): → `Workflows/QuickAnalysis.md`
- "full", "detailed", "complete": → `Workflows/FullAnalysis.md`
- `--summary`: → `Workflows/QuickAnalysis.md` with `--summary` (table only, no detailed sections)
- `--market` flag or "with market context": adds `--spx` to data fetch
- `--sector-scan {1,2,3}` or "sector scan", "sector breadth", "how many above 20dema": → Sector scan mode (see below)

---

## Data Script

**Path:** `scripts/fetch_stage_data.py`

```bash
# Quick — single ticker
python3 scripts/fetch_stage_data.py AAPL

# With S&P 500 relative strength + market context
python3 scripts/fetch_stage_data.py AAPL --spx

# Multiple tickers
python3 scripts/fetch_stage_data.py AAPL MSFT VWCE.DE --spx

# Force fresh download (ignore cache)
python3 scripts/fetch_stage_data.py AAPL --no-cache

# Print cache statistics
python3 scripts/fetch_stage_data.py --cache-info
```

Output: JSON with all computed indicators (MAs, slopes, volume ratios, RS, PPO, stage classification).

### Sector Scan (3-tier depth)

```bash
# Depth 1 — Market breadth: 11 S&P 500 sector SPDRs above/below rising 20dema
python3 scripts/fetch_stage_data.py --sector-scan 1

# Depth 2 — Sector ETF trend: specific ETFs above/below rising 20dema
python3 scripts/fetch_stage_data.py --sector-scan 2 XLE GDX SOIL

# Depth 3 — Constituent scan: individual stocks above/below rising 20dema
python3 scripts/fetch_stage_data.py --sector-scan 3 NTR MOS CF SQM ICL

# Depth 3 via ETF — auto-resolve ETF holdings, then scan constituents
python3 scripts/fetch_stage_data.py --etf MOO
python3 scripts/fetch_stage_data.py --etf GDX

# Combined — sector scan + regular stage analysis
python3 scripts/fetch_stage_data.py NTR --spx --sector-scan 1
```

**Depth guide:**
| Depth | What it scans | Args needed | Speed |
|-------|--------------|-------------|-------|
| 1 | 11 S&P sector SPDRs (XLB-XLY) | None — hardcoded | ~1s |
| 2 | Specific sector ETFs | ETF tickers | ~1s per 3 ETFs |
| 3 | Individual stocks in a sector | Stock tickers (up to ~20) | ~1s per 10 tickers |
| 3 (via `--etf`) | Top holdings of an ETF | ETF symbol | ~2s (resolve + scan) |

Output: JSON under `"sector_scan"` key with per-ticker 20dema status, slope direction, and aggregate breadth label (strong/moderate/weak/oversold).

### Caching

Weekly OHLCV data is cached locally at `scripts/.cache/stage_data/`.

- **Completed weeks:** cached permanently (weekly candle is final)
- **Current week:** cached with 4-hour TTL (candle still forming)
- **Cache key:** `{TICKER}_{YYYY}_W{WW}.json` (completed) or `{TICKER}_{YYYY}_W{WW}_current.json` (in-progress)
- **`--no-cache`:** force fresh yfinance download
- **`--cache-info`:** print cache stats (entry count, disk usage, oldest/newest)
- SPX data is also cached (used for RS calculations across multiple tickers)

---

## Methodology Reference

For qualitative analysis (sector context, base assessment, resistance patterns, big winner characteristics), read:
`Methodology.md`

This file contains the distilled Weinstein framework. Load it during **Full Analysis** mode.

---

## Workflow Routing

| Trigger | Workflow |
|---------|----------|
| "stage analysis AAPL", "what stage is AAPL" | `Workflows/QuickAnalysis.md` |
| "stage analysis AAPL --summary" | `Workflows/QuickAnalysis.md` (summary table only) |
| "full stage analysis AAPL", "detailed stage AAPL" | `Workflows/FullAnalysis.md` |
| "sector scan", "sector breadth", "market breadth" | `--sector-scan 1` (default) |
| "sector scan XLE GDX", "how is energy above 20dema" | `--sector-scan 2` with ETF tickers |
| "scan NTR MOS CF for 20dema", "constituent scan" | `--sector-scan 3` with stock tickers |

---

## UCITS Compatibility

For European ETFs, use the exchange suffix:
- Xetra: `.DE` (e.g., `VWCE.DE`, `EXX1.DE`)
- London: `.L` (e.g., `VWRL.L`)
- Milan: `.MI`
- Paris: `.PA`

If your portfolio uses UCITS ETFs, always use the correct exchange suffix.

---

## Portfolio Integration

When analyzing portfolio holdings:
1. Read your portfolio file for current positions
2. Run stage analysis on all holdings
3. Flag any holdings in Stage 3 (warning) or Stage 4 (sell signal)
4. Highlight holdings showing Stage 2 breakout signals (add opportunity)
