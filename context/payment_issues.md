# Payment Issues — Domain Context

## Common Scenarios
- Failed payment during checkout (card declined, insufficient funds, network timeout)
- Double charge / duplicate transaction
- Payment stuck in "pending" status for more than 24 hours
- Subscription auto-renewal charge dispute
- Wrong amount charged (currency conversion, promo code not applied)

## Typical Customer Language
- "My payment didn't go through but money was deducted"
- "I was charged twice for the same order"
- "The payment has been pending for 3 days now"
- "I wasn't supposed to be charged for renewal"
- "The discount code didn't apply but I was still charged full price"

## Agent Procedures
1. Verify the customer's identity (order number, email, last 4 digits of card)
2. Check payment status in the internal system
3. For failed payments: confirm if money was actually deducted or just held (authorization hold)
4. For duplicate charges: verify in the transaction log, initiate refund for the duplicate
5. For pending payments: check with the payment processor, provide estimated resolution time
6. Escalation path: Payment team (Tier 2) for amounts > $500 or cross-border issues

## Key Information
- Authorization holds are released automatically within 3-5 business days
- Refunds take 5-10 business days to appear on the statement
- Supported payment methods: Visa, Mastercard, PayPal, Apple Pay
- Currency: USD, EUR, GBP
