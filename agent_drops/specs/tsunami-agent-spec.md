# Tsunami Agent: Self-Improving Compression Scanner

## The Loop

```
OBSERVE -> SCORE -> BACKTEST -> ANALYZE MISSES -> HYPOTHESIZE -> ADD VARIABLE -> RE-SCORE -> MEASURE -> REPEAT
```

## Agent Architecture

### Core Loop (runs autonomously)

1. **SCORE**: Run all 53+ companies through the current model
2. **BACKTEST**: Compare predictions to actual outcomes (did it die or recover?)
3. **ANALYZE**: For each miss, determine WHY the model missed
   - False negative: "What variable would have caught this?"
   - False positive: "What moat signal did I miss?"
4. **HYPOTHESIZE**: Generate candidate variables that would fix the misses
5. **TEST**: Add each candidate variable, re-run backtest, measure accuracy delta
6. **ADOPT**: If accuracy improved, keep the variable. If not, discard.
7. **LOG**: Record everything -- what was tried, what worked, what didn't
8. **REPEAT**: Until accuracy plateaus (3 consecutive runs with <1% improvement)

### Variable Discovery Engine

When the agent finds a miss, it categorizes why:

| Miss Category | Agent Action |
|---------------|-------------|
| Moat too generous | Lower moat score for "feature" companies (add feature classifier) |
| Missing macro variable | Add VIX/rate/sentiment as amplifier |
| Gate too tight | Adjust gate threshold |
| Missing industry variable | Look up industry-specific factors |
| Hidden leverage | Add off-balance-sheet risk detection |
| Competitive threat not measured | Add competitor growth tracking |

### Self-Calibration Rules

- Weights adjust by max 5% per iteration (no wild swings)
- New variables must improve accuracy by >1% to be adopted
- Agent tracks "confidence" per variable (how often it helps vs hurts)
- Variables that consistently hurt accuracy get deprecated after 5 iterations
- The 53-company database is the training set
- New compressions get added to the database as they happen (living dataset)

### Real-Time Layer (future)

Once the model is calibrated on historical data:

1. **WATCH**: Monitor live tickers via yfinance every 15 minutes
2. **ALERT**: When net score crosses threshold, flag it
3. **EXPLAIN**: Generate "thesis document" per flagged company
   - Predicted drop: X% (confidence: Y%)
   - Top 3 contributing variables
   - Bull case (why thesis might be wrong)
   - Bear case (why thesis is right)
   - Comparable historical compressions
4. **TRACK**: After flagging, monitor actual price action
5. **LEARN**: Compare prediction to actual outcome, feed back into loop

### Day Trading Layer (future)

On top of the fundamental signal:

1. **Candlestick patterns**: Bearish engulfing, evening star, head-and-shoulders
2. **Volume analysis**: Unusual volume spikes, volume profile at key levels
3. **Options flow**: Put/call ratio, unusual options activity, gamma exposure
4. **Intraday momentum**: VWAP deviation, RSI divergence
5. **Earnings catalyst**: Days until earnings, estimate revision trend
6. **Macro pulse**: VIX level, Fed minutes calendar, economic data releases

These are TIMING signals on top of the fundamental THESIS.

## Implementation Plan

### Phase 1: Self-Improving Loop (next session)
- Turn the 53-company backtest into an automated scoring loop
- Add miss analysis engine
- Add variable discovery + testing
- Target: 70%+ accuracy (from current 58%)

### Phase 2: Explainability
- Prediction with confidence levels
- Per-company thesis document generation
- Variable contribution breakdown ("why I think this")

### Phase 3: Real-Time Monitoring
- Live yfinance polling
- Alert system when scores cross thresholds
- Dashboard integration

### Phase 4: Day Trading Overlay
- Candlestick reading
- Volume spike detection
- Options flow integration
- Earnings calendar alignment
