# SaaS Metrics — Benchmarks & Definitions

## Revenue Metrics

### ARR (Annual Recurring Revenue)
- **Definition**: Annualized value of recurring subscription revenue
- **Calculation**: MRR x 12 (exclude one-time fees, services)
- **Benchmarks by stage**:
  - Seed: $0–$1M ARR
  - Series A: $1M–$5M ARR (median ~$2M)
  - Series B: $5M–$20M ARR (median ~$10M)
  - Growth: $20M+ ARR

### MRR (Monthly Recurring Revenue)
- **Components**: New MRR + Expansion MRR - Churned MRR - Contraction MRR
- **Healthy composition**: Expansion MRR > Churned + Contraction (net negative churn)

### Net Revenue Retention (NRR / NDR)
- **Definition**: Revenue from existing customers this period / Revenue from same cohort last period
- **Benchmarks**:
  - Below 90%: Problem — customers are shrinking or leaving
  - 90%–100%: Okay for SMB, concerning for enterprise
  - 100%–120%: Good
  - 120%–140%: Great (best-in-class SaaS: Snowflake 158%, Twilio 131%)
  - 140%+: Exceptional, typically usage-based pricing

### Gross Revenue Retention (GRR)
- **Definition**: Revenue retained excluding expansion (only downgrades + churn)
- **Benchmarks**: Best-in-class >95%, good >90%, concerning <85%

## Unit Economics

### CAC (Customer Acquisition Cost)
- **Definition**: Total sales & marketing spend / New customers acquired
- **Fully-loaded CAC**: Include salaries, tools, ads, events, content production
- **Benchmarks by segment**:
  - Self-serve/PLG: $50–$500
  - SMB: $500–$5,000
  - Mid-market: $5,000–$25,000
  - Enterprise: $25,000–$100,000+

### LTV (Lifetime Value)
- **Simple formula**: ARPA x Gross Margin / Monthly Churn Rate
- **Or**: ARPA x Gross Margin x Average Customer Lifetime (months)
- **LTV/CAC ratio benchmarks**:
  - Below 1x: Losing money on every customer
  - 1x–3x: Unsustainable or very early
  - 3x–5x: Healthy (3x is the standard "good" threshold)
  - 5x+: Strong, but might be under-investing in growth

### CAC Payback Period
- **Definition**: Months to recover CAC from gross margin
- **Formula**: CAC / (ARPA x Gross Margin %)
- **Benchmarks**:
  - Under 12 months: Excellent
  - 12–18 months: Good
  - 18–24 months: Acceptable for enterprise
  - 24+ months: Concerning — capital-intensive growth

## Churn Metrics

### Logo Churn (Customer Churn)
- **Definition**: Customers lost / Total customers at period start
- **Monthly benchmarks**:
  - SMB: 3–7% monthly (36–58% annual) is common
  - Mid-market: 1–2% monthly
  - Enterprise: 0.5–1% monthly
  - Best-in-class: <0.5% monthly

### Revenue Churn (Gross MRR Churn)
- **Definition**: MRR lost to downgrades + cancellations / Total MRR at period start
- **Should be lower than logo churn** (smaller customers churn more)

## Growth Metrics

### MoM Growth Rate
- **Benchmarks for "good" at each stage**:
  - Pre-Seed: 15–30% MoM (small base)
  - Seed: 10–20% MoM
  - Series A: 8–15% MoM
  - Series B: 5–10% MoM

### T2D3 Framework
- Triple revenue for 2 years, then double for 3 years
- Year 1: $1M → $3M (3x)
- Year 2: $3M → $9M (3x)
- Year 3: $9M → $18M (2x)
- Year 4: $18M → $36M (2x)
- Year 5: $36M → $72M (2x)
- Gets to ~$100M ARR in 5 years from $1M starting point

### Burn Multiple
- **Definition**: Net burn / Net new ARR
- **Benchmarks**: Below 1x = amazing, 1x–1.5x = great, 1.5x–2x = good, 2x–3x = mediocre, 3x+ = bad

### Rule of 40
- **Formula**: Revenue growth rate % + Profit margin % ≥ 40
- **Examples**: 50% growth + -10% margin = 40 (meets threshold); 20% growth + 20% margin = 40
- Applies mainly to scaled companies ($10M+ ARR)

## Efficiency Metrics

### Magic Number
- **Definition**: Net new ARR / Sales & marketing spend (prior quarter)
- **Benchmarks**: Below 0.5 = inefficient, 0.5–0.75 = okay, 0.75–1.0 = efficient, 1.0+ = very efficient (invest more)

### Gross Margin
- **SaaS benchmarks**: 70–85% (software delivery costs, hosting, support)
- Below 60%: Heavy services component, not "pure" SaaS
- Above 80%: Strong, typical for well-scaled SaaS

### Operating Margins by Stage
- Pre-Seed/Seed: -100% to -50% (investing in product/team)
- Series A: -80% to -30%
- Series B: -50% to -10%
- Growth: -20% to +10%
- Scaled: +10% to +30%
