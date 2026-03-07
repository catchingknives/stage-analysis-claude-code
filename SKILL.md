---
name: StageAnalysis
version: 1.0.0
description: Stan Weinstein Stage Analysis on any ticker. Determines current stage (1-4), computes moving averages, volume ratios, relative strength, and generates actionable buy/sell signals.
author: catchingknives
repository: https://github.com/catchingknives/stage-analysis-claude-code
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

---

## International Tickers

For ETFs on non-US exchanges, use the yfinance exchange suffix:
- Xetra: `.DE` (e.g., `VWCE.DE`, `EXX1.DE`)
- London: `.L` (e.g., `VWRL.L`)
- Milan: `.MI`
- Paris: `.PA`
