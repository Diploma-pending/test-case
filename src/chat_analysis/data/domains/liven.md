Liven Context Document
1. Business Overview
Product/Service: Liven (theliven.com) is a mental health, well-being, and self-discovery app available on iOS, Android, and Web. It uses cognitive-behavioral therapy (CBT) principles to help users manage anxiety, procrastination, ADHD, and emotional regulation. Key features include personalized courses, a Mood Tracker, Journaling, a Habit Builder, Soundscapes, and an AI companion named "Livie." Liven also sells optional physical/digital add-on "Supplements" (e.g., "Liven up your sleep," "Jazz up your mood," "Care for your stress") and workbooks.

Target Customer: Individuals looking for self-improvement, emotional balance, stress relief, and habit building without the high costs of traditional therapy. The app is age-rated 18+.

Key Features & Pricing Tiers:

Freemium/Trial: Free download with very limited features; heavily pushes a 7-day free trial.

Weekly Plan: ~$7.99/week.

Monthly Plan: Starts around $34.99/month (special offers sometimes available at $29.99/month).

Annual Plan: Ranges from $49.99 to $89.99/year depending on trial inclusion and promotions.

Lifetime Premium: ~$99.99 one-time.

Workbooks & Bundles: Add-on digital workbooks priced at $15.99–$19.99.

Note: Physical supplements are billed separately and can be purchased as one-time orders or subscriptions.

2. Support Domain Context
Payment Issues:

Methods: Credit/Debit cards via web checkout (Stripe/Shopify), Apple App Store, and Google Play Store.

Billing Cycles: Weekly, Monthly, Annually. Auto-renewal occurs within 24 hours prior to the end of the current period.

Failed Payments: If a payment fails, access to premium features (including Livie and personalized courses) is typically restricted until the balance is paid.

Technical Errors:

Platforms: iOS (requires iOS 17.2 or later), Android, and a Web version.

Common Points of Failure: Login issues (resolved via standard "Forgot Password"), bugs with the in-app reader, message synchronization with the AI companion, and statistics failing to update. The company frequently issues "bug fix" updates (e.g., versions 1.86 - 1.88) to address performance drops.

Account Access:

Login Methods: Email/Password and Google Sign-In.

Account Creation: Accounts are generated automatically upon web purchase; users receive an email titled "Liven app login instructions." No manual registration is required post-purchase.

Suspension/Ban/Deletion: Accounts can be terminated by Customer Service at their discretion for 3 months of inactivity, Terms of Service violations, or security reasons. Users can request total erasure of their data by contacting support.

Tariff & Plan Questions:

Upgrades/Trials: The 7-day trial automatically transitions into the chosen billing cycle. App users often complain about upsells (like $19.99 workbook bundles) appearing even after buying a premium subscription.

Physical Supplements: Follow a separate subscription/auto-renewal track from the digital app.

Refunds:

Digital Subscriptions: Covered by a strict 7-day Money-Back Guarantee for new users. No guaranteed refunds after 7 days.

Apple/Google Purchases: Liven cannot refund these directly; users must be routed through Apple or Google Play refund flows.

Physical Store Purchases: A 30-day refund window exists for the first subscription order of physical items (product price only, excludes shipping/VAT). One-time purchases are only eligible for return if unopened, unused, and sealed. Return shipping is strictly non-refundable, and users must use a Liven-provided return label/QR code or the return will be rejected.

3. Support Policies & Constraints
Support Channels: * Email: support@theliven.com (or support@liven.com).

Live Chat: Available via the in-app Help Center (Profile > Settings > Help and Support > Contact Us).

SLAs & Commitments: The stated average response time is 24 hours. They specifically ask users to wait 48 hours before following up, and strictly instruct users to reply to the existing ticket rather than creating a new one.

Self-Service Options: * A comprehensive Zendesk-hosted Help Center (https://www.google.com/search?q=support.theliven.com).

In-app cancellation flow for web-based subscriptions (Settings > Membership > Turn off auto-renewal).

Users cannot self-cancel Apple or Google subscriptions within the Liven app.

Human vs. Automated Routing:

Automated: Web subscription cancellations, password resets, and trial transitions.

Human Required: Issuing digital refunds (for web purchases), generating physical return logistics labels/QR codes for supplements, account data deletion (GDPR/CCPA), and resolving technical bugs.

4. Edge Cases
Domain: Account Access

Scenario: A user purchases a web subscription but makes a typo in their email at checkout. They never receive the "Liven app login instructions" email and are locked out of the app.

Difficulty: The automated flow cannot fix this; an agent must manually locate the Stripe charge using the last 4 digits of the card, verify the user, and change the email address.

Emotion: Highly confused and frustrated.

Domain: Refunds (Physical Goods)

Scenario: A customer opens a bottle of "Liven Up Your Sleep" supplements, uses it for 4 days, experiences no benefit, and demands a refund under the 30-day guarantee.

Difficulty: The policy explicitly states that opened/used items cannot be returned due to hygiene regulations, but the user is citing the 30-day satisfaction window for first-time subscription orders.

Emotion: Argumentative and hostile.

Domain: Payment Issues

Scenario: A user deletes the Liven app from their iPhone, assuming this cancels their $34.99/month subscription. They are billed for three subsequent months and demand a full retroactive refund.

Difficulty: The subscription is managed by Apple. Liven holds none of the funds and cannot issue the refund or cancel the plan, making the agent the bearer of bad news.

Emotion: Extremely angry and accusatory ("Scam").

Domain: Tariff & Plan Questions

Scenario: A user on a $7.99 weekly plan buys an in-app Workbook Bundle for $19.99, but the workbooks won't unlock due to a syncing bug between their Liven account and the App Store receipt.

Difficulty: Requires backend troubleshooting. The user paid twice (subscription + bundle) but is blocked from the core content they just bought.

Emotion: Impatient and annoyed.

Domain: Refunds (Digital Window)

Scenario: A user submits a refund request via email on Day 6 of their 7-day trial. Because the SLA is 24-48 hours, the agent reads the ticket on Day 8, by which point the user has been auto-charged $89.99 for the annual plan.

Difficulty: The charge technically processed, but the user requested cancellation within the valid window. The agent must honor the refund but process it retroactively, which might incur processing fees or take 5-10 business days to hit the user's bank.

Emotion: Panicked and anxious.

Domain: Payment Issues

Scenario: A user initiates a chargeback with their bank for a $99.99 Lifetime Premium purchase, but simultaneously emails support asking for a bug fix for the AI companion Livie.

Difficulty: Standard policy is to immediately suspend accounts with open chargebacks, but the user actually wants to use the app and doesn't understand that a chargeback equates to forced cancellation.

Emotion: Confused and demanding.

Domain: Support Policies (Returns)

Scenario: A customer returns a sealed physical supplement by mailing it back via their own local post office instead of using the mandatory Liven-provided QR code/label.

Difficulty: The warehouse cannot identify the parcel, and the policy states unauthorized returns will be declined. The agent must deny the refund for an item the user already paid to ship back.

Emotion: Furious.

Domain: Account Access / Technical

Scenario: A user who has been inactive for 4 months returns to the app to find their account completely terminated (as per the "3 months inactivity" clause in the TOS), losing all their historic Mood Tracker and Journaling data.

Difficulty: The data has been completely erased from Liven's servers and cannot be restored.

Emotion: Devastated and betrayed.

5. Agent Pitfall Areas
Attempting to Cancel Third-Party Subscriptions: An agent might tell an iOS or Android user, "I have canceled your subscription for you," after locating their account in the CRM. Pitfall: The agent only disabled the auto-renewal in Liven's internal system; Apple/Google will still charge the user. Agents must instruct the user to navigate to their device's native Subscription settings to cancel.

Violating the Physical Return Protocol: An agent might blindly approve a refund for a physical supplement without first verifying if the product is unopened, or they might process the refund before the warehouse receives the tracking confirmation via the required logistics label.

Mishandling the 7-Day Guarantee: Agents might rigidly deny a refund for a user who was charged on Day 8, failing to check if the user actually sent their cancellation email on Day 6 or 7 (within the 48-hour SLA window). This leads to terrible Trustpilot reviews.

Telling Users to Create a New Ticket: If an issue escalates (e.g., a technical bug with Livie that requires developer input), an agent might tell the user to email support again in a week. Pitfall: Liven's policy strictly requests users to follow up on the same ticket to avoid duplicate requests and delayed response times.

Failing to Distinguish Between "Web" and "App" Customers: An agent might search the internal Shopify/Stripe database for a complaining customer's email, find nothing, and claim "We have no record of your payment." Pitfall: They failed to realize the user purchased through the App Store and has an Apple-masked email or a separate App Store receipt.