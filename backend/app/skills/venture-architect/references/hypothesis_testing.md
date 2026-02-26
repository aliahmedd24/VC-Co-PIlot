# Hypothesis Testing — Experiment Design Guide

## The Hypothesis Framework

### Structure
"We believe that [target customer] will [expected behavior] because [reason]. We will know this is true when [measurable signal] reaches [threshold] within [time period]."

### Example
"We believe that mid-market SaaS CFOs will sign up for a free trial after seeing a 2-minute product demo video because they are frustrated with manual reconciliation. We will know this is true when our landing page converts at >5% within 2 weeks of launching the video."

## Experiment Types (Cheapest to Most Expensive)

### 1. Smoke Test / Landing Page ($0-100, 1-3 days)
- Create a landing page describing the product
- Drive traffic via targeted ads ($50-100)
- Measure: signup rate, email captures, "Buy" button clicks
- Best for: Validating demand before building

### 2. Concierge MVP ($0, 1-2 weeks)
- Deliver the service manually to 5-10 customers
- Learn their workflow, language, and priorities firsthand
- Measure: willingness to pay, retention, satisfaction
- Best for: Understanding the problem deeply

### 3. Wizard of Oz ($100-500, 1-2 weeks)
- Product appears automated to the user, but a human does the work behind the scenes
- Measure: Usage patterns, satisfaction, willingness to pay
- Best for: Testing whether the solution approach works before building tech

### 4. Single-Feature MVP ($500-5000, 2-4 weeks)
- Build the one core feature that delivers the main value
- Release to small group of early adopters
- Measure: Activation, retention, feedback quality
- Best for: Validating the technical approach and core value prop

### 5. A/B Test ($0-500, 1-2 weeks)
- Test two variations of a specific element (pricing, messaging, feature)
- Requires existing traffic (100+ visitors per variant for statistical significance)
- Measure: Conversion rate difference
- Best for: Optimizing an existing funnel

## Statistical Significance

### Minimum Sample Sizes
To detect a meaningful difference:
- **50%+ relative change**: ~100 samples per variant
- **20-50% relative change**: ~500 samples per variant
- **5-20% relative change**: ~2000+ samples per variant

### When to Stop an Experiment
- You've reached your sample size AND time period
- The signal is overwhelmingly positive or negative (>95% confidence)
- External factors have invalidated the experiment conditions

## Prioritizing Experiments

### ICE Score
- **Impact** (1-10): If this assumption is wrong, how much does it matter?
- **Confidence** (1-10): How confident are you in the current assumption?
- **Ease** (1-10): How easy is it to test?
- **Priority** = Impact × (10 - Confidence) × Ease

### Riskiest Assumption Test (RAT)
Identify assumptions in order of:
1. If wrong, kills the business (existential risk)
2. If wrong, requires major pivot
3. If wrong, requires moderate adjustment
4. If wrong, minor inconvenience

Test category 1 first, always.

## Documenting Results

### Experiment Card Template
```
Hypothesis: [statement]
Experiment type: [smoke test / concierge / etc.]
Duration: [X days/weeks]
Sample size: [N participants]
Success threshold: [metric > value]
Result: [VALIDATED / INVALIDATED / INCONCLUSIVE]
Actual metric: [measured value]
Key learning: [insight]
Next action: [proceed / pivot / retest with changes]
```
