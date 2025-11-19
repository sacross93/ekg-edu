# Usage Examples

This document provides real-world examples of running the NVIDIA Stock Predictor with LangGraph feedback loop.

## Table of Contents

- [Example 1: High Confidence on First Iteration](#example-1-high-confidence-on-first-iteration)
- [Example 2: Feedback Loop Improvement](#example-2-feedback-loop-improvement)
- [Example 3: Maximum Iterations Reached](#example-3-maximum-iterations-reached)
- [Understanding the Output](#understanding-the-output)
- [Interpreting Results](#interpreting-results)

---

## Example 1: High Confidence on First Iteration

### Scenario
When there's abundant, high-quality news from trusted sources, the system may achieve high confidence on the first attempt.

### Execution

```bash
$ python main.py
```

### Console Output

```
╔══════════════════════════════════════════════════════════════════════════════╗
║                    NVIDIA Stock Prediction Workflow                          ║
║                         LangGraph Feedback Loop                              ║
╚══════════════════════════════════════════════════════════════════════════════╝

Starting workflow with max 3 iterations...
Confidence threshold: 60%

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

                              🔄 ITERATION 1 / 3

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📝 Keyword Generation
   Generated 10 keywords:
   • NVIDIA quarterly earnings Q4 2025
   • Jensen Huang AI strategy announcement
   • NVDA data center revenue growth
   • Blackwell GPU production ramp
   • NVIDIA enterprise partnerships
   • AI chip demand forecast
   • NVIDIA vs AMD market share
   • GPU supply chain updates
   • NVIDIA stock analyst ratings
   • Tech sector AI investment trends

🔍 News Collection
   Fetched 45 articles from News API
   Successfully crawled 20 articles
   Total articles in state: 20

📦 News Merging
   Created 6 news packs:
   • pack_001: earnings (relevance: 0.95)
   • pack_002: product (relevance: 0.90)
   • pack_003: partnership (relevance: 0.85)
   • pack_004: policy (relevance: 0.75)
   • pack_005: stock_analysis (relevance: 0.80)
   • pack_006: general (relevance: 0.60)

📊 Sentiment Analysis
   Overall sentiment: +2.3 (Positive)
   Event scores:
   • earnings: +2.5
   • product: +1.8
   • partnership: +1.2
   • policy: -0.5
   • supply: +0.8

✅ Validation
   Confidence Score: 78% ✅
   
   Source Reliability: 85%
   Evidence Quality: 82%
   Argument Balance: 70%
   Recency: 90%

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

                           ✨ FINAL PREDICTION ✨

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Direction:     ⬆️  UP
Confidence:    78%
Timeframe:     3-7 days
Total Iterations: 1

Key Positive Factors:
  ✓ Strong Q4 earnings beat expectations by 15% (Reuters)
  ✓ Data center revenue up 217% YoY (Bloomberg)
  ✓ Blackwell GPU production ahead of schedule (Financial Times)
  ✓ Major partnership with Microsoft for AI infrastructure (CNBC)

Key Negative Factors:
  ✗ China export restrictions impact 20% of revenue (Wall Street Journal)

Summary:
NVIDIA shows strong momentum with exceptional Q4 earnings and accelerating 
data center growth. Blackwell GPU ramp-up ahead of schedule signals continued 
market dominance. Despite China headwinds, enterprise AI demand remains robust.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Results saved to: nvidia_multi_agent_20251110_143052.json
Execution time: 2m 34s
```

### Key Observations

- **Single iteration**: High confidence (78%) achieved immediately
- **Strong sources**: Reuters, Bloomberg, Financial Times (all 0.9-1.0 reliability)
- **Clear signal**: Positive earnings and product news outweigh policy concerns
- **Fast execution**: Only 2.5 minutes for complete analysis

---

## Example 2: Feedback Loop Improvement

### Scenario
Initial analysis has low confidence due to insufficient trusted sources or weak evidence. The feedback loop kicks in to improve results.

### Execution

```bash
$ python main.py
```

### Console Output

```
╔══════════════════════════════════════════════════════════════════════════════╗
║                    NVIDIA Stock Prediction Workflow                          ║
║                         LangGraph Feedback Loop                              ║
╚══════════════════════════════════════════════════════════════════════════════╝

Starting workflow with max 3 iterations...
Confidence threshold: 60%

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

                              🔄 ITERATION 1 / 3

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📝 Keyword Generation
   Generated 10 keywords:
   • NVIDIA stock prediction
   • Jensen Huang news
   • AI chip market
   • GPU sales forecast
   • NVIDIA competitors
   • Tech stock analysis
   • Semiconductor industry
   • NVIDIA partnerships
   • Data center trends
   • AI hardware demand

🔍 News Collection
   Fetched 32 articles from News API
   Successfully crawled 15 articles
   Total articles in state: 15

📦 News Merging
   Created 4 news packs:
   • pack_001: general (relevance: 0.65)
   • pack_002: stock_analysis (relevance: 0.70)
   • pack_003: product (relevance: 0.60)
   • pack_004: general (relevance: 0.50)

📊 Sentiment Analysis
   Overall sentiment: +0.8 (Weakly Positive)
   Event scores:
   • product: +1.0
   • general: +0.5

✅ Validation
   Confidence Score: 42% ❌ (Below threshold)
   
   Source Reliability: 45%
   Evidence Quality: 38%
   Argument Balance: 55%
   Recency: 30%

🔄 Feedback Analysis
   Deficiencies identified:
   • Source reliability too low - need more trusted sources (Reuters, Bloomberg)
   • Insufficient evidence for earnings impact
   • Weak product launch details
   • No recent news (most articles > 7 days old)
   • Missing data center revenue information

   Contra arguments:
   • Competition from AMD and custom chips mentioned but not quantified
   • Supply chain concerns raised without specifics

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

                              🔄 ITERATION 2 / 3

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📝 Keyword Generation (with feedback context)
   Previous confidence: 42%
   Addressing deficiencies...
   
   Generated 10 NEW keywords:
   • NVIDIA quarterly earnings report Q4
   • NVDA data center revenue growth
   • Blackwell GPU production schedule
   • NVIDIA enterprise customer wins
   • Jensen Huang earnings call transcript
   • NVIDIA vs AMD datacenter market share
   • GPU supply chain latest updates
   • NVIDIA analyst price target upgrades
   • AI infrastructure spending forecast
   • NVIDIA partnership announcements

🔍 News Collection
   Fetched 38 articles from News API
   Successfully crawled 18 articles
   Merged with previous: 28 total articles (5 duplicates removed)

📦 News Merging
   Created 7 news packs:
   • pack_001: earnings (relevance: 0.92)
   • pack_002: product (relevance: 0.88)
   • pack_003: partnership (relevance: 0.82)
   • pack_004: stock_analysis (relevance: 0.78)
   • pack_005: policy (relevance: 0.70)
   • pack_006: supply (relevance: 0.65)
   • pack_007: general (relevance: 0.55)

📊 Sentiment Analysis (with previous context)
   Overall sentiment: +2.1 (Positive)
   Event scores:
   • earnings: +2.8
   • product: +1.5
   • partnership: +1.3
   • policy: -0.3
   • supply: +0.7

✅ Validation
   Confidence Score: 72% ✅
   
   Source Reliability: 82%
   Evidence Quality: 78%
   Argument Balance: 68%
   Recency: 85%

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

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

                           ✨ FINAL PREDICTION ✨

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Direction:     ⬆️  UP
Confidence:    72%
Timeframe:     3-7 days
Total Iterations: 2

Key Positive Factors:
  ✓ Q4 earnings exceeded analyst estimates (Bloomberg)
  ✓ Data center revenue growth accelerating (Reuters)
  ✓ Blackwell GPU production on track (Financial Times)
  ✓ New enterprise partnerships announced (CNBC)

Key Negative Factors:
  ✗ Export restrictions limiting China market access (Wall Street Journal)

Summary:
Improved analysis with stronger sources reveals solid fundamentals. Q4 earnings 
strength and data center momentum support upward movement. Feedback loop 
successfully addressed initial deficiencies in source quality and evidence depth.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Results saved to: nvidia_multi_agent_20251110_145823.json
Execution time: 4m 52s
```

### Key Observations

- **Feedback loop activated**: Initial 42% confidence triggered retry
- **Targeted improvement**: Keywords specifically addressed deficiencies
- **Significant gains**: +30% confidence improvement in iteration 2
- **Article expansion**: 15 → 28 articles (87% increase)
- **Better sources**: Source reliability jumped from 45% to 82%
- **Successful outcome**: Achieved 72% confidence, exceeding threshold

---

## Example 3: Maximum Iterations Reached

### Scenario
When news is scarce or contradictory, the system may reach maximum iterations without achieving high confidence. It returns the best result found.

### Execution

```bash
$ python main.py
```

### Console Output

```
╔══════════════════════════════════════════════════════════════════════════════╗
║                    NVIDIA Stock Prediction Workflow                          ║
║                         LangGraph Feedback Loop                              ║
╚══════════════════════════════════════════════════════════════════════════════╝

Starting workflow with max 3 iterations...
Confidence threshold: 60%

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

                              🔄 ITERATION 1 / 3

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[... similar output ...]

✅ Validation
   Confidence Score: 38% ❌ (Below threshold)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

                              🔄 ITERATION 2 / 3

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[... similar output ...]

✅ Validation
   Confidence Score: 51% ❌ (Below threshold)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

                              🔄 ITERATION 3 / 3

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[... similar output ...]

✅ Validation
   Confidence Score: 56% ❌ (Below threshold)

⚠️  Maximum iterations reached (3/3)
    Returning best result from all attempts

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

                      📊 ITERATION COMPARISON

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Iteration  Confidence  Articles  Direction  Improvement
─────────  ──────────  ────────  ─────────  ───────────
    1         38%         12        UP          -
    2         51%         23        UP        +13%  ⬆️
    3         56%         31        UP         +5%  ⬆️

Best Result: Iteration 3 (56% confidence)

Improvement Trend:
  • Iteration 1→2: +13% confidence
  • Iteration 2→3: +5% confidence
  • Total improvement: +18%

⚠️  Note: Final confidence (56%) is below threshold (60%)
    Consider this prediction with caution.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

                           ✨ FINAL PREDICTION ✨

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Direction:     ⬆️  UP
Confidence:    56% ⚠️  (Below threshold)
Timeframe:     5-10 days
Total Iterations: 3 (Maximum reached)

Key Positive Factors:
  ✓ Moderate earnings growth expected (MarketWatch)
  ✓ AI demand remains strong (Yahoo Finance)

Key Negative Factors:
  ✗ Increased competition from AMD and custom chips (TechCrunch)
  ✗ Supply chain uncertainties (Investing.com)
  ✗ Mixed analyst ratings (Seeking Alpha)

Summary:
Limited high-quality news available for this period. Mixed signals from various 
sources suggest cautious optimism but lack strong conviction. Consider waiting 
for more definitive information before making investment decisions.

⚠️  CAUTION: This prediction has lower confidence than desired. Use with care.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Results saved to: nvidia_multi_agent_20251110_151245.json
Execution time: 7m 18s
```

### Key Observations

- **All iterations used**: System tried 3 times to improve confidence
- **Incremental gains**: Each iteration showed improvement (+13%, +5%)
- **Diminishing returns**: Smaller gains in later iterations
- **Best result selected**: Iteration 3 (56%) chosen despite being below threshold
- **Clear warning**: User alerted that confidence is below desired level
- **Longer execution**: 7+ minutes for 3 complete iterations

---

## Understanding the Output

### Confidence Score Components

The overall confidence score (0-100) is calculated from:

1. **Source Reliability (40% weight)**
   - Based on trusted source whitelist
   - Reuters, Bloomberg, WSJ = 1.0
   - CNBC, MarketWatch = 0.8
   - Yahoo Finance = 0.7

2. **Evidence Quality (30% weight)**
   - Number and specificity of evidence items
   - Quantitative data presence
   - Event type relevance

3. **Argument Balance (20% weight)**
   - Ratio of positive to negative factors
   - Presence of counter-arguments
   - Contradiction resolution

4. **Recency (10% weight)**
   - How recent the news articles are
   - Articles < 3 days old = 100%
   - Articles > 14 days old = 0%

### Direction Indicators

- **⬆️ UP**: Positive sentiment > +1.0
- **⬇️ DOWN**: Negative sentiment < -1.0
- **➡️ NEUTRAL**: Sentiment between -1.0 and +1.0

### Timeframe Calculation

Based on dominant event types:
- **Earnings**: 3-7 days
- **Product launches**: 5-10 days
- **Policy changes**: 7-14 days
- **General news**: 5-10 days

---

## Interpreting Results

### High Confidence (≥ 70%)

**What it means:**
- Strong consensus from trusted sources
- Clear evidence supporting the prediction
- Recent, relevant news
- Minimal contradictions

**Action:**
- Prediction is reliable for the stated timeframe
- Consider acting on the recommendation
- Still monitor for breaking news

### Medium Confidence (60-69%)

**What it means:**
- Adequate but not exceptional source quality
- Reasonable evidence base
- Some contradictory signals
- May need additional confirmation

**Action:**
- Use as one input among several
- Look for corroborating information
- Monitor closely for changes

### Low Confidence (< 60%)

**What it means:**
- Limited trusted sources
- Weak or contradictory evidence
- Significant uncertainty
- May indicate news drought

**Action:**
- Treat with caution
- Wait for more information if possible
- Consider the prediction directional only
- Do not rely solely on this analysis

### Feedback Loop Indicators

**When feedback loop activates:**
- Initial confidence < 60%
- System identifies specific deficiencies
- New keywords target gaps
- Articles accumulate across iterations

**What to watch:**
- Confidence improvement trend
- Article count growth
- Source quality enhancement
- Evidence depth increase

**Good signs:**
- Steady confidence increases
- New trusted sources found
- More specific evidence
- Contradictions resolved

**Warning signs:**
- Minimal improvement between iterations
- Same sources repeated
- Confidence plateaus
- Maximum iterations reached

---

## Next Steps

- Review [TROUBLESHOOTING.md](TROUBLESHOOTING.md) for common issues
- Check [README.md](../README.md) for configuration options
- Examine saved JSON files for detailed analysis
- Adjust thresholds in `config/settings.py` if needed
