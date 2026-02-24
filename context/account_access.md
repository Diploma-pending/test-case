# Account Access — Domain Context

## Common Scenarios
- Forgotten password, unable to reset via email
- Account locked after multiple failed login attempts
- Two-factor authentication (2FA) issues (lost phone, codes not working)
- Account compromised / unauthorized access detected
- Email change request (can't access old email)

## Typical Customer Language
- "I can't log in, it says my password is wrong but I'm sure it's correct"
- "My account got locked and I never received the unlock email"
- "I lost my phone and can't get the 2FA code"
- "Someone changed my email address, I think I was hacked"
- "I need to update my email but the old one doesn't work anymore"

## Agent Procedures
1. Verify identity through alternative means (security questions, ID verification, billing info)
2. For password reset: check if reset emails are going to spam, resend, or manually trigger
3. For locked accounts: verify lockout reason, unlock after identity confirmation
4. For 2FA issues: provide backup codes if available, or initiate 2FA reset (24-48h delay for security)
5. For compromised accounts: immediate lock, force password reset, review recent activity
6. Escalation path: Security team for compromised accounts, Account Recovery team for complex identity verification

## Key Information
- Accounts lock after 5 failed login attempts (30-minute lockout)
- 2FA reset requires manual identity verification (takes 24-48 hours)
- Backup codes: 8 one-time codes generated at 2FA setup
- Password requirements: min 8 characters, 1 uppercase, 1 number, 1 special character
- Identity verification options: government ID upload, billing address + last 4 of card, security questions
