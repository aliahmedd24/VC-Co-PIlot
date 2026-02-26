# DCF Walkthrough — Step-by-Step Discounted Cash Flow Valuation

## When to Use DCF
- Company has predictable revenue (Series B+)
- Historical financials show clear trends
- Business model is well-understood
- NOT appropriate for pre-revenue or early-stage startups

## Step 1: Project Free Cash Flows (5 Years)

### Revenue Projection
Start with current revenue and apply growth rates:
```
Year 1: $10M (current) × 1.80 = $18M
Year 2: $18M × 1.50 = $27M
Year 3: $27M × 1.35 = $36.5M
Year 4: $36.5M × 1.25 = $45.6M
Year 5: $45.6M × 1.20 = $54.7M
```

### Free Cash Flow Calculation
```
Revenue
- Cost of Revenue (COGS)
= Gross Profit
- Operating Expenses (R&D, S&M, G&A)
= Operating Income (EBIT)
- Taxes (apply effective tax rate)
= NOPAT (Net Operating Profit After Tax)
+ Depreciation & Amortization
- Capital Expenditures
- Change in Working Capital
= Free Cash Flow (FCF)
```

### SaaS-Specific Adjustments
- Recognize deferred revenue properly (annual contracts paid upfront)
- Capitalize sales commissions if amortized over contract life
- R&D: estimate what portion is maintenance vs growth

## Step 2: Calculate Terminal Value

### Perpetuity Growth Method
```
Terminal Value = FCF_Year5 × (1 + g) / (r - g)
```
Where:
- g = long-term growth rate (typically 2-4%, should not exceed GDP growth)
- r = discount rate (WACC)

### Exit Multiple Method (More Common for Startups)
```
Terminal Value = EBITDA_Year5 × Exit Multiple
```
- SaaS exit multiples: 10-25x EBITDA depending on growth + profitability
- Use Rule of 40 to estimate appropriate multiple

## Step 3: Determine Discount Rate

### Startup Discount Rates by Stage
| Stage | Discount Rate | Rationale |
|-------|--------------|-----------|
| Pre-Seed | 50-70% | Maximum uncertainty |
| Seed | 40-60% | Product risk, no revenue proof |
| Series A | 30-50% | Some traction, execution risk |
| Series B | 25-40% | Proven model, scaling risk |
| Growth | 15-25% | Established, market risk |
| Pre-IPO | 10-15% | Approaching public market rates |

## Step 4: Discount to Present Value

```
PV = FCF₁/(1+r)¹ + FCF₂/(1+r)² + ... + FCF₅/(1+r)⁵ + TV/(1+r)⁵
```

## Step 5: Sensitivity Analysis

Always show a matrix varying two key inputs:
```
             Discount Rate
             25%    30%    35%    40%
Growth  2%  $45M   $38M   $32M   $27M
        3%  $52M   $43M   $36M   $31M
        4%  $60M   $49M   $41M   $34M
```

## Common Mistakes
1. Using too-low discount rate (underestimates startup risk)
2. Terminal value dominates (>75% of total) — means near-term projections are unreliable
3. Growth rate in terminal value exceeds inflation (unsustainable)
4. Not adjusting for dilution from future fundraising rounds
