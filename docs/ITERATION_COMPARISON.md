# Iteration Comparison Guide

Understanding how the feedback loop improves predictions across iterations.

## Quick Comparison Table

| Metric | Iteration 1 | Iteration 2 | Improvement |
|--------|-------------|-------------|-------------|
| **Confidence** | 42% ❌ | 72% ✅ | +30% |
| **Articles** | 15 | 28 | +87% |
| **Source Reliability** | 45% | 82% | +37% |
| **Evidence Quality** | 38% | 78% | +40% |
| **Recency Score** | 30% | 85% | +55% |
| **News Packs** | 4 | 7 | +75% |

## What Changes Between Iterations

### Keywords Evolution

**Iteration 1 (Generic):**
```
- NVIDIA stock prediction
- Jensen Huang news
- AI chip market
- GPU sales forecast
```

**Iteration 2 (Targeted):**
```
- NVIDIA quarterly earnings report Q4
- NVDA data center revenue growth
- Blackwell GPU production schedule
- NVIDIA analyst price target upgrades
```

### Source Quality

**Iteration 1:**
- Mixed sources (blogs, aggregators)
- Average reliability: 45%
- Few trusted sources

**Iteration 2:**
- Premium sources (Reuters, Bloomberg)
- Average reliability: 82%
- Majority from trusted sources

### Evidence Depth

**Iteration 1:**
- Vague statements
- Opinion pieces
- Limited quantitative data

**Iteration 2:**
- Specific earnings numbers
- Production schedules
- Analyst price targets
- Revenue growth percentages

## Reading the Comparison Output

When the system completes multiple iterations, you'll see:

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
                      📊 ITERATION COMPARISON
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Iteration  Confidence  Articles  Direction  Improvement
─────────  ──────────  ────────  ─────────  ───────────
    1         42%         15        UP          -
    2         72%         28        UP        +30%  ⬆️

Key Improvements:
  ✓ Source reliability: 45% → 82% (+37%)
  ✓ Evidence quality: 38% → 78% (+40%)
  ✓ Article count: 15 → 28 (+87%)
  ✓ News packs: 4 → 7 (+75%)
```

## Improvement Patterns

### Good Progress
- Steady confidence increases
- New trusted sources found
- More specific evidence
- Contradictions resolved

### Diminishing Returns
- Small improvements (<10%)
- Same sources repeated
- Confidence plateaus
- May indicate news scarcity

## For More Details

See [EXAMPLES.md](EXAMPLES.md) for complete scenarios.
