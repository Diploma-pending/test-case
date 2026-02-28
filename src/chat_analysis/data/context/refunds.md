# Refunds — Domain Context

## Common Scenarios
- Requesting a refund for a recent purchase/subscription
- Partial refund request (service partially used)
- Refund status inquiry (already requested, waiting for processing)
- Refund denied — customer disputes the decision
- Refund for accidental purchase or duplicate order

## Typical Customer Language
- "I want a refund, I'm not happy with the service"
- "I was charged but I cancelled my subscription last week"
- "I requested a refund 2 weeks ago and haven't received it yet"
- "Why was my refund denied? I think that's unfair"
- "My kid accidentally purchased this, can I get my money back?"

## Agent Procedures
1. Verify the purchase (order ID, date, amount)
2. Check refund eligibility: within 30-day refund window, no prior refunds on this order
3. For eligible refunds: process immediately, confirm amount and timeline
4. For partial refunds: calculate based on usage (prorated)
5. For denied refunds: explain the reason clearly, offer alternatives (credit, extended trial)
6. Escalation path: Billing supervisor for denied refund disputes, Finance team for amounts > $200

## Key Information
- Refund policy: full refund within 30 days of purchase, no questions asked
- After 30 days: prorated refund at manager discretion
- Refund processing time: 5-10 business days back to original payment method
- Account credit: instant, can be applied to future purchases
- Maximum refund without supervisor approval: $200
- Duplicate order refunds: always approved regardless of timeframe

## Domain Boundaries — NOT This Domain
- If the customer has an initial payment failure (card declined, pending charge) → belongs to "payment_issues" domain, not here.
- If the customer asks about plan features or upgrades → belongs to "tariff_questions" domain.
- If the customer can't log in → belongs to "account_access" domain.
- If the customer reports a bug or crash → belongs to "technical_errors" domain.
- Stay focused on refund requests, refund eligibility, refund status, and refund disputes.
