# StageAnalysis — Stan Weinstein Stage Analysis for Claude Code

A [Claude Code](https://docs.anthropic.com/en/docs/claude-code) skill that performs Stan Weinstein Stage Analysis on any ticker. Determines current stage (1-4), computes moving averages, volume ratios, relative strength vs S&P 500, and generates actionable buy/sell signals.

## What It Does

Given a ticker symbol, the skill:

1. Fetches weekly OHLCV data via [yfinance](https://github.com/ranaroussi/yfinance)
2. Computes 30-week EMA, 10-week EMA, 20-day EMA, 60-week volume EMA
3. Calculates relative strength vs S&P 500 with 40-week RS moving average
4. Detects weekly candle patterns (engulfing, doji, hammer)
5. Classifies the current Weinstein stage (1-4) with detailed reasoning
6. Outputs an emoji-dense summary table + actionable signal

### Example Output

```
┌─────────┬─────┬──────────┬───────────┬────────┬──────┬──────┬──────┬──────┬────────┬──────────┐
│ Ticker  │ Stg │ Price    │ MAs       │ Slope  │ Vol  │ RS   │ PPO  │ 52wH │ Candle │ Signal   │
├─────────┼─────┼──────────┼───────────┼────────┼──────┼──────┼──────┼──────┼────────┼──────────┤
│ AAPL    │  2  │ $198.50  │ ✅ ✅ ✅  │ ↗️ ↗️  │ 🔥   │ 💪   │ 🟢   │ 🎯   │  —     │ HOLD     │
│ MSFT    │  3  │ $380.20  │ ❌ ✅ ✅  │ ➡️ ↗️  │ 📊   │ ⚠️   │ 🟡   │ 📏   │  🔻   │ ⚠️ WARN  │
└─────────┴─────┴──────────┴───────────┴────────┴──────┴──────┴──────┴──────┴────────┴──────────┘
```

## Installation

### Prerequisites

```bash
pip install yfinance numpy pandas
```

### Setup

Copy the skill into your Claude Code skills directory:

```bash
# Create the skill directory
mkdir -p ~/.claude/skills/StageAnalysis/Workflows

# Copy skill files
cp SKILL.md ~/.claude/skills/StageAnalysis/
cp Methodology.md ~/.claude/skills/StageAnalysis/
cp Workflows/*.md ~/.claude/skills/StageAnalysis/Workflows/

# Copy the data script (put it wherever you like, then update the path in SKILL.md)
cp scripts/fetch_stage_data.py /path/to/your/scripts/
```

Update the `scripts/fetch_stage_data.py` path in `SKILL.md` and the workflow files to match where you placed the script.

## Usage

In Claude Code, just say:

| Command | What You Get |
|---------|-------------|
| `stage analysis AAPL` | Summary table + quick analysis |
| `stage analysis AAPL --summary` | Emoji summary table only |
| `full stage analysis AAPL` | Complete deep-dive with all sections |
| `stage analysis AAPL MSFT GOOGL` | Multi-ticker comparison table |
| `stage analysis AAPL --market` | Includes S&P 500 market context |

### Data Script (standalone)

The Python script works independently of Claude Code:

```bash
# Single ticker
python3 scripts/fetch_stage_data.py AAPL

# With S&P 500 relative strength
python3 scripts/fetch_stage_data.py AAPL --spx

# Multiple tickers
python3 scripts/fetch_stage_data.py AAPL MSFT VWCE.DE --spx

# Cache management
python3 scripts/fetch_stage_data.py --cache-info
python3 scripts/fetch_stage_data.py AAPL --no-cache
```

Output is JSON with all computed indicators.

### Caching

Weekly data is cached locally to avoid redundant API calls:

- **Completed weeks**: cached permanently (the weekly candle is final)
- **Current week**: cached with 4-hour TTL (candle still forming)
- **`--no-cache`**: forces a fresh download
- **`--cache-info`**: prints cache statistics

Cache location: `scripts/.cache/stage_data/`

## Modes

### Quick Analysis (default)

Summary table + one-line signal per ticker. Fast and scannable.

### Summary (`--summary`)

Just the emoji table — no prose. Useful for scanning a watchlist.

### Full Analysis (`full stage analysis`)

Deep-dive with sections for:
- Moving average analysis (power trend, MA alignment)
- Volume analysis (breakout confirmation, distribution signs)
- Relative strength vs S&P 500
- PPO / extension risk
- Overhead resistance assessment
- Weekly candle patterns
- Signal box with entry/stop/target levels

## The Weinstein Framework

The four stages:

1. **Stage 1 — Basing**: Price consolidates around a flat 30w EMA after a decline
2. **Stage 2 — Advancing**: Price above a rising 30w EMA (the buy zone)
3. **Stage 3 — Topping**: 30w EMA flattens, price loses momentum
4. **Stage 4 — Declining**: Price below a falling 30w EMA (avoid/sell)

See `Methodology.md` for the complete framework reference.

## International Tickers

For non-US exchanges, use yfinance suffixes:

| Exchange | Suffix | Example |
|----------|--------|---------|
| Xetra | `.DE` | `VWCE.DE` |
| London | `.L` | `VWRL.L` |
| Milan | `.MI` | `ENI.MI` |
| Paris | `.PA` | `AI.PA` |

## License

MIT
