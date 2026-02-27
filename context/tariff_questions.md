# Tariff / Plan Questions — Domain Context

## Common Scenarios
- Comparing plans (Free vs Pro vs Enterprise)
- Requesting an upgrade or downgrade
- Questions about feature limits on current plan
- Billing cycle questions (monthly vs annual, proration)
- Team/organization plan setup

## Typical Customer Language
- "What's the difference between Pro and Enterprise?"
- "I want to upgrade but I'm mid-cycle, will I be charged full price?"
- "Does the Free plan include API access?"
- "Can I switch to annual billing to get the discount?"
- "How do I add team members to my plan?"

## Agent Procedures
1. Identify customer's current plan and usage
2. For comparisons: provide clear feature matrix, highlight key differences
3. For upgrades: explain proration (charged only for remaining days in cycle)
4. For downgrades: warn about feature loss, effective at end of current billing cycle
5. For annual switch: calculate savings, process immediately if requested
6. Escalation path: Sales team for Enterprise inquiries, Billing team for complex proration issues

## Key Information
- Plans: Free ($0, 100 records, no API), Pro ($29/mo, 10K records, API access), Enterprise (custom pricing, unlimited)
- Annual discount: 20% off (Pro annual = $278/year instead of $348)
- Proration: upgrade charged immediately for remaining days, downgrade credit applied to next cycle
- Team plans: Pro Team ($25/user/mo, min 3 users), Enterprise Team (custom)
- Feature comparison available at: example.com/pricing

## Domain Boundaries — NOT This Domain
- If the customer has a payment failure or charge issue → belongs to "payment_issues" domain, not here.
- If the customer wants a refund → belongs to "refunds" domain.
- If the customer can't log in → belongs to "account_access" domain.
- If the customer reports a bug or crash → belongs to "technical_errors" domain.
- Stay focused on plan comparisons, upgrades, downgrades, and billing cycles.
