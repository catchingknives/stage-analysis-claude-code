# FullAnalysis Workflow

Complete Stan Weinstein Stage Analysis with all indicator sections and actionable levels.

## Steps

### 1. Load Methodology

Read `Methodology.md` for qualitative framework.

### 2. Fetch Data

```bash
python3 scripts/fetch_stage_data.py {TICKER(S)} --spx
```

Always include `--spx` for full analysis (relative strength + market context).

### 3. Emoji Summary Table (MANDATORY — output BEFORE proceeding)

**GATE: Do NOT proceed to Step 4 until the emoji summary table is output.** This is the first thing the user sees and provides a scannable overview before the deep dive. Skipping this step is a CRITICAL FAILURE.

Output the emoji summary table **before** any detailed sections. Use the exact same table format defined in `QuickAnalysis.md` Step 2 — including all emoji columns (MAs, Slope, Vol, RS, PPO, 52wH, Candle, Signal).

### 4. Full Analysis Output

For each ticker, output the full analysis report. Separate multiple tickers with a thick divider:

```
═══════════════════════════════════════════════════
```

Use the following formatting structure for each ticker:

---

```
██████████████████████████████████████████████
██  STAGE {N}  ██  {TICKER}
██████████████████████████████████████████████

{stage_detail with evidence}
- Price vs 30w EMA: {above/below} by {dist_pct}%
- 30w EMA slope: {direction} ({slope_pct}% over 4 weeks)
- 10w EMA slope: {direction} ({slope_pct}%)
- Stage transition risk: {assessment}

━━━ Market Context ━━━

- S&P 500 stage: Stage {N} — {detail}
- Market tailwind/headwind for this trade: {assessment}

━━━ Moving Averages ━━━

| MA | Value | Position | Distance |
|----|-------|----------|----------|
| 20d EMA | ${val} | {above/below} | {dist}% |
| 10w EMA | ${val} | {above/below} | {dist}% |
| 30w EMA | ${val} | {above/below} | {dist}% |

- **Power trend:** {Yes/No — price holding above 20d EMA}
- **MA alignment:** {Bullish (20d > 10w > 30w) / Bearish (30w > 10w > 20d) / Mixed}

━━━ Volume ━━━

- Current week: {vol} ({ratio}x the 60w average)
- Volume quality: {strong/above_avg/normal/light}
- Breakout confirmation: {Yes if ratio >= 2x on breakout week / No / N/A}
- Distribution signs: {assessment of recent heavy down-volume weeks}

━━━ Relative Strength vs S&P 500 ━━━

- RS ratio: {value}
- RS vs 40w MA: {above/below}
- RS direction: {rising/flat/falling} ({slope}% over 4 weeks)
- Interpretation: {outperforming/underperforming/neutral} the broad market
- RS leading price? {assessment}

━━━ PPO / Extension Risk ━━━

- PPO (1,30): {value}%
- Interpretation: {stretched/normal/oversold}
- Mean reversion risk: {low/moderate/high}

━━━ Overhead Resistance ━━━

- Distance to 52w high: {pct}%
- Prior consolidation zones: {note any visible resistance from the data}
- Assessment: {clear skies / moderate resistance / heavy overhead supply}

━━━ Candle Patterns ━━━

{List any detected patterns or "No significant patterns this week"}

━━━ Signal ━━━

┌─────────────────────────────────────────────────┐
│  {EMOJI}  {BUY / HOLD / WARNING / SELL / AVOID} │
│  {detailed signal explanation}                   │
│  {signal type context}                           │
└─────────────────────────────────────────────────┘

{Signal type if buy: Investor breakout / Trader continuation / Pullback buy}
{Signal type if warning: Stage 3 topping / Failed breakout / Distribution}
{Signal type if sell: Stage 4 breakdown / Stop hit}

━━━ Key Levels ━━━

| Level | Price | Notes |
|-------|-------|-------|
| Entry | ${val} | {condition for entry} |
| Stop Loss | ${val} | {below which MA, % risk} |
| Target 1 | ${val} | {basis — e.g., 52w high, measured move} |
| Target 2 | ${val} | {stretch target if applicable} |
```

---

### 5. Portfolio Context (if analyzing a holding)

If the ticker is in your portfolio:
- Note the current allocation weight
- Recommend action relative to MC model targets
- Flag if stage conflicts with the position (e.g., holding a Stage 4 stock)

### 6. Qualitative Assessment

Apply methodology knowledge for aspects the numbers alone can't capture:
- **Base quality:** How long was the Stage 1 base? Bigger = better.
- **Sector alignment:** Is the sector in Stage 2? Individual Stage 2 in a Stage 4 sector = risky.
- **Big winner traits:** Does this setup match the characteristics of big winners?
- **Catalyst awareness:** Note any known catalysts from MC archive if relevant.
