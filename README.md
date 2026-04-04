# Stage Analysis for Claude Code

Stan Weinstein Stage Analysis skill for [Claude Code](https://claude.ai/code). Automated stage classification (1-4), emoji summary tables, 3-tier sector breadth scanning, and actionable buy/sell signals.

## What It Does

- Classifies any stock/ETF into Weinstein Stage 1-4 using weekly data
- Computes 30w/10w/20d EMAs, slopes, volume ratios, relative strength vs S&P 500
- Generates emoji summary tables for quick visual scanning
- 3-tier sector breadth scan (market-level, sector ETF, constituent-level)
- Auto-resolves ETF holdings for constituent scans (`--etf MOO`)
- Supports UCITS European ETFs with exchange suffixes (`.DE`, `.L`, `.MI`)

## Quick Start

### Prerequisites

```bash
pip install yfinance numpy pandas
```

### Install as Claude Code Skill

```bash
mkdir -p ~/.claude/skills/StageAnalysis/Workflows

cp SKILL.md ~/.claude/skills/StageAnalysis/
cp Methodology.md ~/.claude/skills/StageAnalysis/
cp Workflows/*.md ~/.claude/skills/StageAnalysis/Workflows/
cp -r scripts/ ~/.claude/skills/StageAnalysis/scripts/
```

### Usage

Talk to Claude Code naturally:

- "Stage analysis AAPL"
- "What stage is GDX?"
- "Full stage analysis on my portfolio"
- "Sector scan depth 3 on NTR MOS CF SQM"
- "Run a level 3 check on MOO" (auto-resolves holdings)

### Direct Script Usage

```bash
# Single ticker
python3 scripts/fetch_stage_data.py AAPL

# With S&P 500 context
python3 scripts/fetch_stage_data.py AAPL MSFT --spx

# Sector breadth (11 S&P sectors)
python3 scripts/fetch_stage_data.py --sector-scan 1

# ETF constituent scan
python3 scripts/fetch_stage_data.py --etf GDX

# Specific constituents
python3 scripts/fetch_stage_data.py --sector-scan 3 NTR MOS CF SQM ICL
```

## Methodology

Based on Stan Weinstein's "Secrets for Profiting in Bull and Bear Markets." The `Methodology.md` file covers:

- Four stages and transition signals
- Moving average framework (30w, 10w, 20d EMAs)
- Volume analysis and breakout confirmation
- Relative strength vs S&P 500
- 20-day EMA as power trend and sector breadth scanner
- Coincident and divergent action for signal confirmation
- Failed breakout/breakdown pattern recognition
- 2-year resistance lookback rule
- Gap-up breakout entry patterns
- Market breadth thresholds
- Rally duration rule (3-5 month cycles)
- Risk management

## Output Format

The skill produces emoji summary tables:

```
| Ticker | Stg | Price   | MAs      | Slope | Vol | RS | PPO | 52wH | Signal   |
|--------|-----|---------|----------|-------|-----|-----|-----|------|----------|
| AAPL   |  2  | $198.50 | a]a]a]   | ^^^   | *   | +   | G   | T    | HOLD     |
| MSFT   |  3  | $380.20 | xa]a]    | ->^   | =   | !   | Y   | M    | WARN     |
```

## License

MIT
