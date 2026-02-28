# Support Context Document: RiseGuide

## 1. Business Overview

* **Product & Service:** RiseGuide is an expert-powered self-improvement platform operating primarily as a mobile app (iOS and Android). It offers 15-minute daily bite-sized lessons, interactive exercises (frameworks, cheat sheets, to-do lists, quizzes, videos), and "SEEK" (Search Engine for Expert Knowledge). Learning tracks currently include *Intelligence Training*, *Communication Mastery*, and *Content Creation* (with *Timeless Leadership* coming soon).
* **Target Customer:** Ambitious individuals ranging from complete beginners to experienced professionals looking to improve cognitive skills, learn viral content creation, or master communication, body language, and storytelling.
* **Pricing & Subscription Model:** The core offering is a **fixed-term subscription** billed upfront for the full period, which automatically renews. Additionally, RiseGuide sells **one-time purchase guides** (tailored materials or individual sessions) outside the standard subscription.

## 2. Support Domain Context

* **Payment Issues:** - *Billing Cycles:* Subscriptions are paid upfront for a fixed term (e.g., annual, quarterly) and auto-renew.
* *Cancellations & Renewals:* Users must cancel **at least 24 hours before the next billing date** to avoid being charged for the next cycle.
* *Dual Payment Streams:* Accounts may feature both recurring subscription charges and standalone one-time guide purchases, which can lead to billing confusion.


* **Technical Errors:** - *Platform:* Operates via web login, the Apple App Store, and Google Play.
* *Common Failure Points:* Issues with the "SEEK" search engine fetching from its 1000+ sources, syncing daily lesson progress, downloading offline materials (cheat sheets/templates), or video buffering errors during 15-minute daily sessions.


* **Account Access:** - *Self-Service Actions:* Users manage access directly in the app. The self-service cancellation flow is specifically mapped as: `Profile tab → Settings (top right corner) → Manage Subscription → Cancel Subscription`.
* *Account Recovery:* Standard login via email/password. Users retain full access to the app until the end of their current paid period, even if they cancel mid-cycle.


* **Tariff & Plan Questions:** - *Plan Differences:* The subscription provides continuous access to all core features (SEEK, learning journeys). One-time guides are distinct, separate purchases for tailored, highly specific materials.
* **Refunds:** - *Eligibility:* RiseGuide offers a **30-day money-back guarantee**.
* *Post-30 Days:* Refund requests outside this window are handled strictly according to the Terms of Use and Subscription Policy, requiring a manual case review by the team.
* *Process:* Users cannot self-serve refunds; they must explicitly email `support@riseguide.com` to initiate the process.



## 3. Support Policies & Constraints

* **Support Channels:** Email via `support@riseguide.com`. There is no live phone or chat support explicitly offered.
* **Self-Service Options:** A comprehensive FAQ page, a dedicated "Cancel & Refund" policy page, and automated subscription cancellation inside the app settings.
* **Escalation & Approvals:** - *Automated:* Stopping auto-renewal (cancellation) is fully automated if the user follows the in-app flow.
* *Human Required:* All refunds, especially those invoking the 30-day money-back guarantee or disputing a charge after the 30-day window, must be manually reviewed and processed by a human agent.



## 4. Edge Cases

Here are 10 realistic edge cases a support agent for RiseGuide might encounter:

1. **Domain: Refunds**
* *Scenario:* A user emails `support@riseguide.com` requesting a refund on day 29 of their subscription, but the support team does not reply until day 31.
* *Why it's difficult:* The user acted within the 30-day money-back guarantee window, but the system/agent is processing it outside of it.
* *Customer Emotion:* Anxious and potentially hostile, fearing they will be denied due to the team's slow response.


2. **Domain: Payment Issues**
* *Scenario:* A user cancels their subscription 12 hours before the renewal date and is charged for the next cycle.
* *Why it's difficult:* Policy strictly states cancellation must occur *at least 24 hours* before the billing date. The user will feel they canceled "before" the renewal.
* *Customer Emotion:* Highly frustrated and feeling scammed.


3. **Domain: Tariff & Plan Questions**
* *Scenario:* A user buys a "one-time guide" expecting it to grant them access to the daily 15-minute Intelligence Training modules, hitting a paywall when they open the app.
* *Why it's difficult:* The agent must explain the difference between standalone purchases and the core subscription platform without sounding like they are upselling.
* *Customer Emotion:* Confused and cheated.


4. **Domain: Technical Errors**
* *Scenario:* A user claims the "SEEK" engine is providing hallucinated or unverified answers, contradicting the "backed by trusted research" marketing.
* *Why it's difficult:* Requires escalating a potential AI/search malfunction to the engineering team while managing the customer's trust in the "expert-powered" brand.
* *Customer Emotion:* Skeptical and disappointed.


5. **Domain: Account Access**
* *Scenario:* A user deletes the RiseGuide app from their phone, assuming this automatically cancels their fixed-term subscription, and requests a refund 6 months later.
* *Why it's difficult:* App deletion does not cancel server-side subscriptions or Apple/Google Play billing. The 30-day refund window is long gone.
* *Customer Emotion:* Angry and defensive.


6. **Domain: Refunds**
* *Scenario:* A user requests a partial refund because they completed the "Communication Mastery" track in two weeks and do not want to use the rest of their annual subscription.
* *Why it's difficult:* RiseGuide uses fixed-term subscriptions. Partial refunds for "finished" content are generally not supported.
* *Customer Emotion:* Entitled and bargaining.


7. **Domain: Payment Issues**
* *Scenario:* A user initiates a chargeback with their bank instead of emailing support for the 30-day money-back guarantee.
* *Why it's difficult:* Chargebacks freeze the funds and penalize the merchant. The agent must navigate the bank dispute process rather than just issuing a standard platform refund.
* *Customer Emotion:* Hostile and impatient.


8. **Domain: Account Access**
* *Scenario:* A user cannot find the `Profile → Settings → Manage Subscription` path because they originally subscribed via third-party billing (e.g., Apple App Store) which overrides the in-app interface.
* *Why it's difficult:* The agent cannot cancel it on their end; they must instruct the user to navigate iOS settings to cancel.
* *Customer Emotion:* Highly confused and suspicious that the company is hiding the cancel button.



## 5. Agent Pitfall Areas

1. **Confusing "Cancellation" with "Refund"**
* *The Pitfall:* A user emails asking to "cancel my account and get my money back" within 10 days of purchase. The agent simply tells them to use the app (`Profile → Settings → Cancel`) and closes the ticket.
* *Why it fails:* In-app cancellation only stops *future renewals*. It does not trigger the 30-day money-back guarantee refund, which the agent must manually process.


2. **Mismanaging the 24-Hour Renewal Rule**
* *The Pitfall:* An agent refunds a user who was charged after canceling 5 hours before their billing date, simply to be polite, thereby violating the strict 24-hour Terms of Use clause.
* *Why it fails:* It sets a precedent that ignores the company's established billing policy and creates financial leakage.


3. **Failing to Differentiate Apple/Google Billing vs. Direct Billing**
* *The Pitfall:* An agent tells a frustrated user to "log into the website to update your credit card," but the user actually purchased the subscription via the Apple App Store.
* *Why it fails:* RiseGuide has mobile apps. Subscriptions bought through app stores are managed by Apple/Google, not RiseGuide’s direct payment gateway. The agent gives impossible instructions, escalating user rage.


4. **Tone Deafness on Product Quality Complaints**
* *The Pitfall:* A user complains that the "Content Creation" track is too basic. The agent responds defensively, citing the "100+ top experts" marketing language.
* *Why it fails:* RiseGuide promises to cater to complete beginners. The agent should gracefully acknowledge the feedback, perhaps offer a one-time guide on advanced topics, or process the 30-day guarantee, rather than arguing about the experts' credentials.