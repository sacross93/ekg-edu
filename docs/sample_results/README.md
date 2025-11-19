# Sample Results

This directory contains example output files from the NVIDIA Stock Predictor system.

## Files

### feedback_loop_example.json

A complete example showing the feedback loop in action with 2 iterations.

**Scenario:** Initial low confidence (42%) triggers feedback loop, which improves to 72% in iteration 2.

**Key Features Demonstrated:**
- Iteration history tracking
- Confidence improvement metrics
- Deficiency identification and resolution
- Keyword evolution across iterations
- Article accumulation and deduplication
- Source reliability improvement
- Evidence quality enhancement

**Structure:**
```json
{
  "timestamp": "...",
  "total_iterations": 2,
  "final_confidence": 72,
  "iteration_history": [
    {
      "iteration": 1,
      "confidence": 42,
      "deficiencies": [...],
      "keywords": [...]
    },
    {
      "iteration": 2,
      "confidence": 72,
      "improvements": {...},
      "keywords": [...]
    }
  ],
  "final_prediction": {...},
  "feedback_loop_summary": {...}
}
```

## Understanding the Output

### Top-Level Fields

- **timestamp**: When the analysis was run
- **execution_time_seconds**: Total time for all iterations
- **total_iterations**: How many iterations were needed
- **final_confidence**: Best confidence score achieved
- **confidence_threshold**: Minimum acceptable confidence (default: 60)

### Iteration History

Each iteration contains:
- **keywords**: Search terms used
- **articles_collected**: Number of articles found
- **confidence**: Confidence score for this iteration
- **validation**: Breakdown of confidence components
- **deficiencies**: What was lacking (iteration 1)
- **improvements**: What got better (iteration 2+)

### Final Prediction

- **direction**: UP, DOWN, or NEUTRAL
- **confidence**: Overall confidence (0-100)
- **timeframe**: Prediction window in days
- **positive_factors**: Supporting evidence
- **negative_factors**: Contradicting evidence
- **summary**: Natural language explanation

### Feedback Loop Summary

- **activated**: Whether feedback loop was triggered
- **reason**: Why it was triggered
- **iterations_required**: How many iterations needed
- **confidence_improvement**: Total improvement achieved
- **key_improvements**: What changed between iterations
- **deficiencies_addressed**: How gaps were filled

## Comparing Iterations

### Iteration 1 (Low Confidence)

```json
{
  "iteration": 1,
  "confidence": 42,
  "articles_collected": 15,
  "validation": {
    "source_reliability": 45,
    "evidence_quality": 38
  },
  "deficiencies": [
    "Source reliability too low",
    "Insufficient evidence for earnings"
  ]
}
```

**Problems:**
- Only 15 articles collected
- Low-reliability sources (45%)
- Weak evidence (38%)
- Generic keywords

### Iteration 2 (High Confidence)

```json
{
  "iteration": 2,
  "confidence": 72,
  "articles_total": 28,
  "validation": {
    "source_reliability": 82,
    "evidence_quality": 78
  },
  "improvements": {
    "confidence_delta": 30,
    "source_reliability_delta": 37,
    "articles_added": 13
  }
}
```

**Improvements:**
- 28 total articles (13 new)
- High-reliability sources (82%)
- Strong evidence (78%)
- Targeted keywords addressing deficiencies

## Key Metrics

### Confidence Components

1. **Source Reliability (40% weight)**
   - Iteration 1: 45% → Iteration 2: 82% (+37%)
   - More trusted sources (Reuters, Bloomberg)

2. **Evidence Quality (30% weight)**
   - Iteration 1: 38% → Iteration 2: 78% (+40%)
   - Specific earnings data, product details

3. **Argument Balance (20% weight)**
   - Iteration 1: 55% → Iteration 2: 68% (+13%)
   - Better balance of positive/negative factors

4. **Recency (10% weight)**
   - Iteration 1: 30% → Iteration 2: 85% (+55%)
   - More recent articles found

### Overall Improvement

- **Confidence**: 42% → 72% (+30 percentage points)
- **Articles**: 15 → 28 (+87%)
- **News Packs**: 4 → 7 (+75%)
- **Execution Time**: ~2.5 minutes per iteration

## Using These Examples

### For Learning

1. **Study the structure** to understand output format
2. **Compare iterations** to see how feedback loop works
3. **Review deficiencies** to understand what triggers retries
4. **Examine improvements** to see what changes

### For Testing

1. **Validate your output** against this structure
2. **Compare confidence scores** to expected ranges
3. **Check iteration logic** matches this pattern
4. **Verify JSON schema** compatibility

### For Debugging

1. **Compare your output** to this example
2. **Check missing fields** if errors occur
3. **Verify iteration history** is being tracked
4. **Ensure feedback loop** activates correctly

## Real-World Scenarios

### Scenario 1: Quick Success
- Iteration 1: 78% confidence
- Result: Immediate return, no feedback loop
- Time: ~2 minutes

### Scenario 2: Improvement (This Example)
- Iteration 1: 42% confidence → Feedback loop
- Iteration 2: 72% confidence → Success
- Time: ~5 minutes

### Scenario 3: Maximum Iterations
- Iteration 1: 38% confidence → Feedback loop
- Iteration 2: 51% confidence → Feedback loop
- Iteration 3: 56% confidence → Return best result
- Time: ~7 minutes

## Next Steps

- Review [EXAMPLES.md](../EXAMPLES.md) for detailed scenarios
- Check [TROUBLESHOOTING.md](../TROUBLESHOOTING.md) if issues arise
- Read [README.md](../../README.md) for complete documentation
- Run `python main.py` to generate your own results

## Notes

- This is a **synthetic example** for documentation purposes
- Real results will vary based on current news availability
- Confidence scores depend on source quality and evidence
- Iteration count varies with initial data quality
- Execution time depends on network speed and API response times
