# Technical Errors — Domain Context

## Common Scenarios
- App crashes on launch or during specific actions
- Error codes displayed to the user (e.g., ERR-500, ERR-403, TIMEOUT-001)
- Features not loading (blank screen, infinite spinner)
- Sync issues between mobile and web versions
- Performance degradation (slow loading, high latency)

## Typical Customer Language
- "The app keeps crashing every time I try to open my dashboard"
- "I'm getting error code ERR-500 when I try to save"
- "The page just shows a blank white screen"
- "My data on the app doesn't match what I see on the website"
- "Everything is super slow today, is there an outage?"

## Agent Procedures
1. Ask for device/browser info, OS version, app version
2. Request a screenshot of the error if applicable
3. Check system status page for known outages
4. Common fixes: clear cache, update app, try incognito mode, reinstall
5. If issue persists: collect logs, create a ticket for the engineering team
6. Escalation path: Technical Support (Tier 2) for reproducible bugs, Engineering for server-side issues

## Key Information
- Current app version: 4.2.1 (iOS), 4.2.0 (Android), Web is evergreen
- Known issue: ERR-500 on dashboard for accounts with > 10,000 records (fix in v4.3)
- Status page: status.example.com
- Log collection: Settings > Help > Send Diagnostic Report

## Domain Boundaries — NOT This Domain
- If the customer is locked out of their account → belongs to "account_access" domain, not here.
- If the customer has a payment failure → belongs to "payment_issues" domain.
- If the customer wants a refund → belongs to "refunds" domain.
- If the customer asks about plan features → belongs to "tariff_questions" domain.
- Stay focused on app crashes, error codes, bugs, sync issues, and performance problems.
