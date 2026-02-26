# Risk Scoring Rubric — How to Score and Prioritize Risks

## Risk Score Matrix

### Likelihood Scale
| Score | Label | Description |
|-------|-------|-------------|
| 1 | Very Unlikely | <10% chance in next 12 months |
| 2 | Unlikely | 10-25% chance |
| 3 | Possible | 25-50% chance |
| 4 | Likely | 50-75% chance |
| 5 | Very Likely | >75% chance |

### Impact Scale
| Score | Label | Description |
|-------|-------|-------------|
| 1 | Minimal | Minor inconvenience, easily recoverable |
| 2 | Low | Noticeable but manageable with existing resources |
| 3 | Moderate | Significant setback, may delay milestones by 1-3 months |
| 4 | High | Major setback, threatens key objectives or next fundraise |
| 5 | Critical | Existential threat, could kill the company |

### Risk Score = Likelihood × Impact

| Score Range | Priority | Action Required |
|------------|----------|----------------|
| 1-4 | Low | Monitor quarterly |
| 5-9 | Medium | Mitigation plan needed |
| 10-15 | High | Active mitigation required now |
| 16-25 | Critical | Immediate action, escalate to board |

## Detectability Factor

Add a third dimension: how early would you notice this risk materializing?

| Score | Detectability | Examples |
|-------|--------------|---------|
| 1 | Immediate | Server outage, customer complaint |
| 2 | Days | Drop in daily active users |
| 3 | Weeks | Declining conversion rates |
| 4 | Months | Gradual churn increase, talent drain |
| 5 | Silent | Technical debt, cultural erosion, market shift |

**Adjusted Risk Score** = Likelihood × Impact × (Detectability / 3)

Silent risks (detectability 4-5) deserve extra monitoring even if likelihood × impact is moderate.

## Risk Categories for Startups

### Product Risk
- Does the product solve the problem effectively?
- Can it be built with current technology?
- Will users adopt it?

### Market Risk
- Is the market large enough?
- Is the timing right?
- Will the market evolve as expected?

### Execution Risk
- Can the team build and deliver?
- Can the team scale the organization?
- Can the team execute the GTM strategy?

### Financial Risk
- Will the company run out of money?
- Will unit economics work at scale?
- Can the company raise the next round?

### External Risk
- Regulatory changes
- Economic downturns
- Platform dependency changes
- Competitive responses

## Mitigation Strategy Template

For each top risk:
```
Risk: [description]
Score: [L × I = total] (Detectability: [1-5])
Early Warning: [what metric/signal would alert us?]
Mitigation: [what can we do now to reduce L or I?]
Contingency: [what do we do if it happens anyway?]
Owner: [who monitors this?]
Review: [how often to reassess?]
```
