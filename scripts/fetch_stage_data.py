#!/usr/bin/env python3
"""
Fetch weekly OHLCV data and compute Stan Weinstein Stage Analysis indicators.
Outputs JSON to stdout for consumption by PAI StageAnalysis skill.

Usage:
    python3 fetch_stage_data.py AAPL
    python3 fetch_stage_data.py VWCE.DE --spx
    python3 fetch_stage_data.py AAPL MSFT --spx

    # Sector scan (3-tier depth):
    python3 fetch_stage_data.py --sector-scan 1                     # Market breadth (11 S&P sector ETFs)
    python3 fetch_stage_data.py --sector-scan 2 XLE GDX SOIL        # Sector ETF 20dema check
    python3 fetch_stage_data.py --sector-scan 3 NTR MOS CF SQM ICL  # Constituent scan
    python3 fetch_stage_data.py --etf MOO                           # Auto-resolve ETF holdings → depth 3
    python3 fetch_stage_data.py NTR --spx --sector-scan 1           # Combined with regular analysis
"""

import argparse
import json
import os
import sys
import tempfile
from datetime import datetime, timedelta
from pathlib import Path

import yfinance as yf
import numpy as np

# --- Caching ---
CACHE_DIR = Path(__file__).parent / ".cache" / "stage_data"
CACHE_TTL_HOURS = 4  # current (incomplete) week cache expiry


def sanitize_ticker(ticker):
    """Make ticker safe for filenames (e.g., ^GSPC → _GSPC)."""
    return ticker.replace("^", "_").replace("/", "_")


def get_cache_path(ticker, now=None):
    """Return cache file path for a ticker based on ISO week."""
    if now is None:
        now = datetime.now()
    iso = now.isocalendar()
    year, week = iso[0], iso[1]
    # Friday = isoweekday 5. Weeks before current are "complete".
    current_iso = now.isocalendar()
    is_current_week = (year == current_iso[0] and week == current_iso[1])
    safe = sanitize_ticker(ticker)
    if is_current_week:
        return CACHE_DIR / f"{safe}_{year}_W{week:02d}_current.json"
    return CACHE_DIR / f"{safe}_{year}_W{week:02d}.json"


def read_cache(ticker):
    """Return cached dict or None on miss/expired."""
    path = get_cache_path(ticker)
    if not path.exists():
        return None
    # Current-week cache expires after CACHE_TTL_HOURS
    if path.name.endswith("_current.json"):
        age_hours = (datetime.now().timestamp() - path.stat().st_mtime) / 3600
        if age_hours > CACHE_TTL_HOURS:
            return None
    try:
        return json.loads(path.read_text())
    except (json.JSONDecodeError, OSError):
        return None


def write_cache(ticker, data):
    """Atomically save data to cache."""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    path = get_cache_path(ticker)
    fd, tmp = tempfile.mkstemp(dir=CACHE_DIR, suffix=".tmp")
    try:
        with os.fdopen(fd, "w") as f:
            json.dump(data, f, indent=2, default=str)
        os.replace(tmp, path)
    except Exception:
        if os.path.exists(tmp):
            os.unlink(tmp)
        raise


def print_cache_info():
    """Print cache statistics."""
    if not CACHE_DIR.exists():
        print("Cache directory does not exist yet.")
        return
    files = list(CACHE_DIR.glob("*.json"))
    if not files:
        print("Cache is empty.")
        return
    total_bytes = sum(f.stat().st_size for f in files)
    oldest = min(f.stat().st_mtime for f in files)
    newest = max(f.stat().st_mtime for f in files)
    print(f"Cache: {CACHE_DIR}")
    print(f"  Entries: {len(files)}")
    print(f"  Disk usage: {total_bytes / 1024:.1f} KB")
    print(f"  Oldest: {datetime.fromtimestamp(oldest).strftime('%Y-%m-%d %H:%M')}")
    print(f"  Newest: {datetime.fromtimestamp(newest).strftime('%Y-%m-%d %H:%M')}")


def ema(series, period):
    """Compute EMA over a pandas Series."""
    return series.ewm(span=period, adjust=False).mean()


def sma(series, period):
    """Compute SMA over a pandas Series."""
    return series.rolling(window=period).mean()


def fetch_and_compute(ticker_symbol, include_spx=False, no_cache=False):
    """Fetch data and compute all Stage Analysis indicators for a ticker."""
    # Check cache first
    if not no_cache:
        cached = read_cache(ticker_symbol)
        if cached is not None:
            # If we need SPX RS and it's not in cache, re-fetch
            if include_spx and cached.get("relative_strength") is None:
                pass  # fall through to live fetch
            else:
                return cached

    # Need ~80 weeks of weekly data for 60-week volume EMA + buffer
    end = datetime.now()
    start = end - timedelta(weeks=100)

    ticker = yf.Ticker(ticker_symbol)

    # Fetch weekly data
    weekly = ticker.history(start=start, end=end, interval="1wk")
    if weekly.empty or len(weekly) < 35:
        return {"error": f"Insufficient weekly data for {ticker_symbol} ({len(weekly)} weeks)"}

    # Fetch daily data (last 6 months for 20-day EMA)
    daily_start = end - timedelta(days=180)
    daily = ticker.history(start=daily_start, end=end, interval="1d")

    # --- Moving Averages (weekly) ---
    weekly["EMA_30w"] = ema(weekly["Close"], 30)
    weekly["EMA_10w"] = ema(weekly["Close"], 10)
    weekly["EMA_60w_vol"] = ema(weekly["Volume"], 60)

    # --- 20-day EMA (daily) ---
    ema_20d = None
    if not daily.empty and len(daily) >= 25:
        daily["EMA_20d"] = ema(daily["Close"], 20)
        ema_20d = round(float(daily["EMA_20d"].iloc[-1]), 4)

    # Current values
    last = weekly.iloc[-1]
    prev = weekly.iloc[-2] if len(weekly) >= 2 else last
    price = float(last["Close"])
    ema_30w = float(last["EMA_30w"])
    ema_10w = float(last["EMA_10w"])
    vol_current = float(last["Volume"])
    vol_ema_60w = float(last["EMA_60w_vol"]) if last["EMA_60w_vol"] > 0 else 1

    # --- 30w EMA Slope (% change over last 4 weeks) ---
    if len(weekly) >= 5:
        ema_30w_4ago = float(weekly["EMA_30w"].iloc[-5])
        slope_30w = ((ema_30w - ema_30w_4ago) / ema_30w_4ago) * 100 if ema_30w_4ago != 0 else 0
    else:
        slope_30w = 0

    # --- 10w EMA Slope ---
    if len(weekly) >= 5:
        ema_10w_4ago = float(weekly["EMA_10w"].iloc[-5])
        slope_10w = ((ema_10w - ema_10w_4ago) / ema_10w_4ago) * 100 if ema_10w_4ago != 0 else 0
    else:
        slope_10w = 0

    # --- Volume Ratio ---
    vol_ratio = vol_current / vol_ema_60w if vol_ema_60w > 0 else 0

    # --- PPO (1,30,1): % distance from 30w EMA ---
    ppo = ((price - ema_30w) / ema_30w) * 100 if ema_30w != 0 else 0

    # --- 52-week High/Low ---
    recent_52w = weekly.tail(52)
    high_52w = float(recent_52w["High"].max())
    low_52w = float(recent_52w["Low"].min())
    pct_from_high = ((price - high_52w) / high_52w) * 100 if high_52w != 0 else 0
    pct_from_low = ((price - low_52w) / low_52w) * 100 if low_52w != 0 else 0

    # --- Price Position ---
    above_30w = price > ema_30w
    above_10w = price > ema_10w
    above_20d = price > ema_20d if ema_20d else None
    dist_from_30w = ((price - ema_30w) / ema_30w) * 100 if ema_30w != 0 else 0
    dist_from_10w = ((price - ema_10w) / ema_10w) * 100 if ema_10w != 0 else 0

    # --- Relative Strength vs S&P 500 ---
    rs_data = None
    if include_spx:
        spx = yf.Ticker("^GSPC")
        spx_weekly = spx.history(start=start, end=end, interval="1wk")
        if not spx_weekly.empty and len(spx_weekly) >= 40:
            # Align lengths
            min_len = min(len(weekly), len(spx_weekly))
            w_aligned = weekly.tail(min_len).reset_index(drop=True)
            s_aligned = spx_weekly.tail(min_len).reset_index(drop=True)

            rs_line = w_aligned["Close"] / s_aligned["Close"]
            rs_ma_40w = sma(rs_line, 40)

            rs_current = float(rs_line.iloc[-1])
            rs_ma_current = float(rs_ma_40w.iloc[-1]) if not np.isnan(rs_ma_40w.iloc[-1]) else None

            # RS slope (4-week)
            if len(rs_line) >= 5:
                rs_4ago = float(rs_line.iloc[-5])
                rs_slope = ((rs_current - rs_4ago) / rs_4ago) * 100 if rs_4ago != 0 else 0
            else:
                rs_slope = 0

            rs_above_ma = rs_current > rs_ma_current if rs_ma_current else None

            rs_data = {
                "rs_ratio": round(rs_current, 6),
                "rs_40w_ma": round(rs_ma_current, 6) if rs_ma_current else None,
                "rs_above_40w_ma": rs_above_ma,
                "rs_slope_4w_pct": round(rs_slope, 2),
                "rs_direction": "rising" if rs_slope > 0.5 else ("falling" if rs_slope < -0.5 else "flat"),
            }

    # --- Weekly Candle Pattern Detection ---
    candle_patterns = []
    o, h, l, c = float(last["Open"]), float(last["High"]), float(last["Low"]), float(last["Close"])
    po, ph, pl, pc = float(prev["Open"]), float(prev["High"]), float(prev["Low"]), float(prev["Close"])
    body = abs(c - o)
    range_hl = h - l if h != l else 0.001

    # Bearish engulfing
    if pc > po and c < o and c < po and o > pc:
        candle_patterns.append("bearish_engulfing")
    # Bullish engulfing
    if pc < po and c > o and c > po and o < pc:
        candle_patterns.append("bullish_engulfing")
    # Doji (small body relative to range)
    if body / range_hl < 0.1:
        candle_patterns.append("doji")
    # Hammer (lower shadow > 2x body, small upper shadow)
    lower_shadow = min(o, c) - l
    upper_shadow = h - max(o, c)
    if lower_shadow > 2 * body and upper_shadow < body * 0.5 and body > 0:
        candle_patterns.append("hammer")

    # --- Stage Classification ---
    stage, stage_detail = classify_stage(
        price, ema_30w, ema_10w, slope_30w, slope_10w,
        vol_ratio, above_30w, above_10w, pct_from_high, rs_data
    )

    result = {
        "ticker": ticker_symbol,
        "date": str(last.name.date()) if hasattr(last.name, 'date') else str(last.name),
        "price": round(price, 4),
        "moving_averages": {
            "ema_30w": round(ema_30w, 4),
            "ema_10w": round(ema_10w, 4),
            "ema_20d": ema_20d,
            "price_above_30w": above_30w,
            "price_above_10w": above_10w,
            "price_above_20d": above_20d,
            "dist_from_30w_pct": round(dist_from_30w, 2),
            "dist_from_10w_pct": round(dist_from_10w, 2),
            "slope_30w_pct": round(slope_30w, 2),
            "slope_10w_pct": round(slope_10w, 2),
            "slope_30w_direction": "rising" if slope_30w > 0.3 else ("falling" if slope_30w < -0.3 else "flat"),
            "slope_10w_direction": "rising" if slope_10w > 0.3 else ("falling" if slope_10w < -0.3 else "flat"),
        },
        "volume": {
            "current_week": int(vol_current),
            "ema_60w": int(vol_ema_60w),
            "ratio_vs_60w": round(vol_ratio, 2),
            "quality": "strong" if vol_ratio >= 2.0 else ("above_avg" if vol_ratio >= 1.3 else ("normal" if vol_ratio >= 0.7 else "light")),
        },
        "ppo": round(ppo, 2),
        "high_low_52w": {
            "high": round(high_52w, 4),
            "low": round(low_52w, 4),
            "pct_from_high": round(pct_from_high, 2),
            "pct_from_low": round(pct_from_low, 2),
        },
        "relative_strength": rs_data,
        "candle_patterns": candle_patterns if candle_patterns else None,
        "stage": {
            "current": stage,
            "detail": stage_detail,
        },
    }

    # Write to cache
    if not no_cache:
        try:
            write_cache(ticker_symbol, result)
        except (OSError, IOError):
            pass  # cache write failure is non-fatal

    return result


# --- Sector Scan ---

SP500_SECTORS = {
    "XLB": "Materials",
    "XLC": "Communication Services",
    "XLE": "Energy",
    "XLF": "Financials",
    "XLI": "Industrials",
    "XLK": "Technology",
    "XLP": "Consumer Staples",
    "XLRE": "Real Estate",
    "XLU": "Utilities",
    "XLV": "Health Care",
    "XLY": "Consumer Discretionary",
}


def compute_20dema_scan(tickers, labels=None):
    """
    Batch fetch daily data for tickers and compute 20dema status for each.
    Returns dict with per-ticker results and aggregate counts.

    Args:
        tickers: list of ticker symbols
        labels: optional dict of ticker -> display name
    """
    if not tickers:
        return {"error": "No tickers provided"}

    end = datetime.now()
    start = end - timedelta(days=90)  # 3 months for stable 20dema

    # Batch download
    data = yf.download(tickers, start=start, end=end, interval="1d",
                       group_by="ticker", progress=False)
    if data.empty:
        return {"error": "No data returned from yfinance"}

    results = []
    single_ticker = len(tickers) == 1

    for t in tickers:
        try:
            if single_ticker:
                closes = data["Close"].dropna()
            else:
                closes = data[t]["Close"].dropna()

            if len(closes) < 25:
                results.append({
                    "ticker": t,
                    "name": labels.get(t, t) if labels else t,
                    "error": f"Insufficient data ({len(closes)} days)",
                })
                continue

            ema_20d = ema(closes, 20)
            price = float(closes.iloc[-1])
            ema_val = float(ema_20d.iloc[-1])
            above = price > ema_val

            # 20dema slope: % change over last 5 trading days
            if len(ema_20d) >= 6:
                ema_5ago = float(ema_20d.iloc[-6])
                slope = ((ema_val - ema_5ago) / ema_5ago) * 100 if ema_5ago != 0 else 0
            else:
                slope = 0

            slope_dir = "rising" if slope > 0.15 else ("falling" if slope < -0.15 else "flat")
            above_rising = above and slope_dir == "rising"

            results.append({
                "ticker": t,
                "name": labels.get(t, t) if labels else t,
                "price": round(price, 2),
                "ema_20d": round(ema_val, 2),
                "above_20dema": above,
                "ema_20d_slope_pct": round(slope, 3),
                "ema_20d_slope_dir": slope_dir,
                "above_rising_20dema": above_rising,
            })
        except (KeyError, IndexError):
            results.append({
                "ticker": t,
                "name": labels.get(t, t) if labels else t,
                "error": "Data extraction failed",
            })

    # Aggregate
    valid = [r for r in results if "error" not in r]
    above_count = sum(1 for r in valid if r["above_20dema"])
    above_rising_count = sum(1 for r in valid if r["above_rising_20dema"])
    total = len(valid)
    pct_above = round(above_count / total * 100, 1) if total > 0 else 0
    pct_above_rising = round(above_rising_count / total * 100, 1) if total > 0 else 0

    # Breadth label
    if pct_above_rising >= 70:
        breadth_label = "strong"
    elif pct_above_rising >= 40:
        breadth_label = "moderate"
    elif pct_above_rising >= 20:
        breadth_label = "weak"
    else:
        breadth_label = "oversold"

    return {
        "total_tickers": total,
        "above_20dema": above_count,
        "above_rising_20dema": above_rising_count,
        "pct_above_20dema": pct_above,
        "pct_above_rising_20dema": pct_above_rising,
        "breadth": breadth_label,
        "tickers": results,
    }


def sector_scan_depth1():
    """Depth 1: Market breadth via 11 S&P 500 sector ETFs."""
    return {
        "depth": 1,
        "description": "S&P 500 sector breadth — 11 sector SPDRs above/below rising 20dema",
        "scan": compute_20dema_scan(list(SP500_SECTORS.keys()), labels=SP500_SECTORS),
    }


def sector_scan_depth2(etf_tickers):
    """Depth 2: Check specific sector ETF(s) against 20dema."""
    return {
        "depth": 2,
        "description": "Sector ETF 20dema trend check",
        "scan": compute_20dema_scan(etf_tickers),
    }


def sector_scan_depth3(constituent_tickers):
    """Depth 3: Full constituent scan — batch fetch and count above 20dema."""
    return {
        "depth": 3,
        "description": "Constituent-level 20dema scan",
        "scan": compute_20dema_scan(constituent_tickers),
    }


def resolve_etf_holdings(etf_symbol, max_holdings=15):
    """
    Resolve an ETF's top holdings via yfinance funds_data.
    Returns (tickers_list, labels_dict) or raises on failure.
    """
    ticker = yf.Ticker(etf_symbol)
    fd = ticker.funds_data
    holdings = fd.top_holdings

    if holdings is None or holdings.empty:
        raise ValueError(f"No holdings data for {etf_symbol}")

    tickers = list(holdings.index[:max_holdings])
    labels = {sym: holdings.loc[sym, "Name"] for sym in tickers}
    return tickers, labels


def classify_stage(price, ema_30w, ema_10w, slope_30w, slope_10w,
                   vol_ratio, above_30w, above_10w, pct_from_high, rs_data):
    """
    Classify the current Weinstein stage based on indicators.
    Returns (stage_number, detail_string).
    """
    # Thresholds
    FLAT_THRESHOLD = 0.3  # slope % considered flat

    slope_flat = abs(slope_30w) <= FLAT_THRESHOLD
    slope_rising = slope_30w > FLAT_THRESHOLD
    slope_falling = slope_30w < -FLAT_THRESHOLD

    # Stage 4: Price below declining 30w EMA
    if not above_30w and slope_falling:
        if pct_from_high < -30:
            return 4, "Stage 4 decline — extended, price >30% from 52w high"
        elif not above_10w:
            return 4, "Stage 4 decline — below both 10w and 30w EMA, 30w EMA falling"
        else:
            return 4, "Stage 4 decline — below 30w EMA which is falling, bouncing near 10w"

    # Stage 2: Price above rising 30w EMA
    if above_30w and slope_rising:
        if above_10w and pct_from_high > -5:
            # Check for power trend
            detail = "Stage 2 advance — strong uptrend, near 52w high"
            if vol_ratio >= 2.0:
                detail = "Stage 2 advance — breakout/continuation on heavy volume"
            return 2, detail
        elif above_10w:
            return 2, "Stage 2 advance — price above rising 10w and 30w EMA"
        else:
            return 2, "Stage 2 advance — pullback to 10w EMA within uptrend"

    # Stage 3: Price near flattening 30w EMA, losing momentum
    if slope_flat or (slope_rising and not above_10w and pct_from_high < -8):
        if above_30w and not above_10w:
            return 3, "Stage 3 top — price broke below 10w EMA, 30w EMA flattening"
        if not above_30w and slope_flat:
            # Could be Stage 1 or late Stage 3 transitioning to 4
            if pct_from_high < -20:
                return 1, "Stage 1 base — price consolidating around flat 30w EMA after decline"
            return 3, "Stage 3 top — price slipped below flat 30w EMA, watching for breakdown"
        if above_30w and above_10w and slope_flat:
            if pct_from_high < -10:
                return 3, "Stage 3 top — 30w EMA flattening, momentum waning"
            return 3, "Stage 3 top — 30w EMA losing slope, watch for rollover"

    # Stage 1: Price around flat 30w EMA after decline
    if slope_flat and not slope_rising:
        if above_30w and vol_ratio >= 1.5:
            return 1, "Stage 1 base — potential breakout forming, volume increasing"
        return 1, "Stage 1 base — price consolidating around flat 30w EMA"

    # Edge cases / transition zones
    if above_30w and slope_falling:
        return 3, "Stage 3/transition — price above 30w EMA but slope still declining (potential Stage 1→2)"

    if not above_30w and slope_rising:
        return 1, "Stage 1/transition — 30w EMA turning up but price hasn't crossed above yet"

    # Fallback
    if above_30w:
        return 2, "Stage 2 (tentative) — price above 30w EMA"
    else:
        return 4, "Stage 4 (tentative) — price below 30w EMA"


def fetch_spx_context(no_cache=False):
    """Fetch S&P 500 stage data for market context."""
    return fetch_and_compute("^GSPC", include_spx=False, no_cache=no_cache)


def main():
    parser = argparse.ArgumentParser(description="Fetch Stage Analysis data")
    parser.add_argument("tickers", nargs="*", help="Ticker symbol(s) to analyze")
    parser.add_argument("--spx", action="store_true", help="Include S&P 500 relative strength and market context")
    parser.add_argument("--no-cache", action="store_true", help="Force fresh download, ignore cache")
    parser.add_argument("--cache-info", action="store_true", help="Print cache stats and exit")
    parser.add_argument("--sector-scan", type=int, choices=[1, 2, 3], metavar="DEPTH",
                        help="Sector breadth scan. Depth 1: market breadth (11 S&P sector ETFs). "
                             "Depth 2: sector ETF 20dema check (tickers = ETFs). "
                             "Depth 3: constituent scan (tickers = individual stocks).")
    parser.add_argument("--etf", type=str, metavar="SYMBOL",
                        help="Auto-resolve ETF holdings for depth 3 scan. "
                             "Fetches top holdings from yfinance and runs constituent scan.")
    args = parser.parse_args()

    if args.cache_info:
        print_cache_info()
        return

    results = {}
    no_cache = args.no_cache

    # Handle --etf flag (implies --sector-scan 3)
    if args.etf:
        if args.sector_scan and args.sector_scan != 3:
            parser.error("--etf implies --sector-scan 3; don't combine with other depths")
        args.sector_scan = 3
        try:
            etf_tickers, etf_labels = resolve_etf_holdings(args.etf)
            print(f"Resolved {args.etf} -> {len(etf_tickers)} holdings: {', '.join(etf_tickers)}", file=sys.stderr)
        except Exception as e:
            print(json.dumps({"error": f"Failed to resolve {args.etf} holdings: {e}"}))
            return
        scan_result = compute_20dema_scan(etf_tickers, labels=etf_labels)
        results["sector_scan"] = {
            "depth": 3,
            "etf": args.etf,
            "description": f"{args.etf} top {len(etf_tickers)} holdings — constituent 20dema scan",
            "scan": scan_result,
        }
        # Any positional tickers get normal stage analysis
        if args.tickers:
            if args.spx:
                results["market_context"] = fetch_spx_context(no_cache=no_cache)
            for t in args.tickers:
                results[t] = fetch_and_compute(t, include_spx=args.spx, no_cache=no_cache)

    # Handle sector scan (without --etf)
    elif args.sector_scan:
        # For depth 2 and 3, tickers are used as scan targets
        # Depth 1 passes positional args through for normal stage analysis
        stage_tickers = []

        if args.sector_scan == 1:
            # Depth 1 uses hardcoded sector ETFs, all positional args are for stage analysis
            results["sector_scan"] = sector_scan_depth1()
            stage_tickers = args.tickers
        elif args.sector_scan == 2:
            if not args.tickers:
                parser.error("--sector-scan 2 requires ETF ticker(s) as arguments")
            results["sector_scan"] = sector_scan_depth2(args.tickers)
        elif args.sector_scan == 3:
            if not args.tickers:
                parser.error("--sector-scan 3 requires constituent ticker(s) as arguments")
            results["sector_scan"] = sector_scan_depth3(args.tickers)

        # Run stage analysis on any remaining tickers (depth 1 only)
        if stage_tickers:
            if args.spx:
                results["market_context"] = fetch_spx_context(no_cache=no_cache)
            for t in stage_tickers:
                results[t] = fetch_and_compute(t, include_spx=args.spx, no_cache=no_cache)
    else:
        # Standard mode — no sector scan
        if not args.tickers:
            parser.error("tickers are required (unless using --cache-info or --sector-scan)")

        if args.spx:
            results["market_context"] = fetch_spx_context(no_cache=no_cache)

        for t in args.tickers:
            results[t] = fetch_and_compute(t, include_spx=args.spx, no_cache=no_cache)

    json.dump(results, sys.stdout, indent=2, default=str)
    print()  # trailing newline


if __name__ == "__main__":
    main()
