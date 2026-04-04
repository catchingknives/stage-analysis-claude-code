# QuickAnalysis Workflow

Quick Stage Analysis: summary table + key levels + one-line signal.

## Steps

### 1. Fetch Data

```bash
python3 scripts/fetch_stage_data.py {TICKER(S)} {--spx if requested}
```

Parse the JSON output.

### 2. Summary Table (ALWAYS output first)

For every analysis (single or multi-ticker), output this table FIRST:

```
┌─────────┬─────┬──────────┬───────────┬────────┬──────┬──────┬──────┬──────┬────────┬──────────┐
│ Ticker  │ Stg │ Price    │ MAs       │ Slope  │ Vol  │ RS   │ PPO  │ 52wH │ Candle │ Signal   │
├─────────┼─────┼──────────┼───────────┼────────┼──────┼──────┼──────┼──────┼────────┼──────────┤
│ AAPL    │  2  │ $198.50  │ ✅ ✅ ✅  │ ↗️ ↗️  │ 🔥   │ 💪   │ 🟢   │ 🎯   │  —     │ HOLD     │
│ MSFT    │  3  │ $380.20  │ ❌ ✅ ✅  │ ➡️ ↗️  │ 📊   │ ⚠️   │ 🟡   │ 📏   │  🔻   │ ⚠️ WARN  │
└─────────┴─────┴──────────┴───────────┴────────┴──────┴──────┴──────┴──────┴────────┴──────────┘
```

#### Column Definitions

| Column | Content | Emoji Logic |
|--------|---------|-------------|
| **Stg** | Stage number (1-4) | Plain number |
| **Price** | Current price | Dollar amount |
| **MAs** | Position vs 20d / 10w / 30w | ✅ above, ❌ below (3 symbols: 20d, 10w, 30w left to right) |
| **Slope** | 30w slope / 10w slope | ↗️ rising, ➡️ flat, ↘️ falling (2 symbols: 30w then 10w) |
| **Vol** | Volume ratio vs 60w EMA | 🔥🔥 extreme (3x+), 🔥 strong (2x+), 📊 above avg (1.3x+), ➖ normal, 🪶 light |
| **RS** | Relative strength vs SPX | 💪 rising + above 40w MA, ↗️ rising + below 40w MA, ⚠️ falling + above 40w MA, ↘️ falling + below 40w MA, ➖ no data |
| **PPO** | Extension from 30w EMA | 🟢 normal (0-10%), 🟡 stretched (10-18%), 🔴 very stretched (18%+), 🔵 oversold (<0%) |
| **52wH** | Distance to 52w high | 🎯 near (<5%), 📏 moderate (5-15%), 🏔️ far (>15%) |
| **Candle** | Weekly pattern | 🔻 bearish engulfing, 🔺 bullish engulfing, ⚪ doji, 🔨 hammer, — none |
| **Signal** | Action word | **BUY**, **HOLD**, ⚠️ **WARN**, 🛑 **AVOID**, 👀 **WATCH** |

**No separate legend.** The full analysis sections below use the same emojis with prose context, making their meaning clear.

### 3. If `--summary` flag: STOP here

When invoked with `--summary`, output ONLY the summary table above. Do not output any detailed analysis sections.

### 4. Detailed Output (default — after summary table)

For each ticker, output below the summary table:

```
━━━ {TICKER} — Stage {N} ━━━

**Price:** ${price} | **30w EMA:** ${ema_30w} ({dist_from_30w_pct}%) | **10w EMA:** ${ema_10w}
**30w Slope:** {direction} ({slope_30w_pct}%) | **Volume:** {ratio}x avg ({quality})
**PPO:** {ppo} | **52w Range:** ${low} — ${high} ({pct_from_high}% from high)
{RS line if --spx: **RS:** {direction}, {above/below} 40w MA}

**Signal:** {one-line actionable signal}
```

### 5. Sector Scan Output (if `--sector-scan` data present)

When the JSON contains a `"sector_scan"` key, output this section BEFORE the per-ticker analysis:

```
━━━ SECTOR SCAN (Depth {N}) ━━━

📊 **{description}**
**Breadth:** {breadth_label} — {above_rising_count}/{total} above rising 20dema ({pct}%)

| Ticker | Name | Price | 20dEMA | Above? | Slope | Power? |
|--------|------|-------|--------|--------|-------|--------|
| XLE    | Energy | $59.25 | $58.96 | ✅ | ↗️ +1.85% | ✅ |
| XLK    | Tech   | $210.3 | $215.1 | ❌ | ↘️ -1.30% | ❌ |
```

**Column definitions:**
- **Above?**: ✅ price > 20dEMA, ❌ below
- **Slope**: ↗️ rising, ➡️ flat, ↘️ falling (with % value)
- **Power?**: ✅ above AND rising 20dEMA (power trend), ❌ otherwise

**Breadth label mapping:**
- **strong** (≥70% above rising): "Broad-based power trend — most sectors in gear"
- **moderate** (40-69%): "Mixed — selective participation"  
- **weak** (20-39%): "Narrow — few sectors driving, caution on new longs"
- **oversold** (<20%): "Deeply oversold — watch for reversal signals"

### 6. Signal Generation

Based on stage and indicators, generate ONE of:

- **Stage 1:** "Basing — watch for breakout above 30w EMA on 2x+ volume"
- **Stage 2 breakout:** "BUY — Stage 2 breakout on {vol_ratio}x volume, 30w EMA rising"
- **Stage 2 pullback:** "Pullback buy opportunity — price near rising 30w EMA"
- **Stage 2 strong:** "Strong Stage 2 — hold, price near 52w high in uptrend"
- **Stage 3:** "WARNING — Stage 3 topping, 30w EMA flattening, tighten stops"
- **Stage 4:** "AVOID — Stage 4 decline, price below falling 30w EMA"
- **Stage 4 deep:** "AVOID — deep Stage 4 decline, wait for Stage 1 base to form"
