# Support Context Document: Dressly

## 1. Business Overview

* **Product & Service:** Dressly is an "AI Fashion Stylist & Smart Shopping Assistant" available as a mobile app (iOS and Android). It provides personalized style plans, virtual try-ons, and AI-driven fashion advice. Key features include an *AI Color Scanner* (to find flattering shades), a *Virtual Try-On* fitting room, an outfit scanner that rates looks, and *Capsule Wardrobe* building using curated pieces from various brands and marketplaces.
* **Target Customer:** Women of all sizes and ages who feel overwhelmed by shopping, have closets full of "nothing to wear," or struggle with impulse buying. The marketing strongly appeals to users who feel that mainstream fashion doesn't cater to their age or body type (e.g., older women, diverse body shapes).
* **Pricing & Subscription Model:** Dressly operates on a subscription model with different term options based on lifestyle, goals, and budget. Users take an initial quiz to generate their personalized style plan before subscribing.

## 2. Support Domain Context

* **Payment Issues:** - *Billing Cycles:* Subscription-based with various term lengths.
* *Payment Origins:* Users can subscribe via the Dressly website directly, or through the Apple App Store / Google Play.


* **Technical Errors:** - *Platform:* iOS App Store, Google Play, and web (for the initial quiz/login).
* *Common Failure Points:* Issues uploading photos/videos for the *Virtual Try-On* or *AI Color Scanner*, errors with the outfit scanner rating system, or glitches when trying to fetch/link curated items from external brands and marketplaces.


* **Account Access:** - *Data Privacy:* Users upload personal photos/videos and body measurements (e.g., "vertical measurements", "soft body type"). Dressly claims they use data solely to personalize styling/shopping and explicitly states they "never sell or share your personal data."
* **Tariff & Plan Questions:** - *Value Proposition:* Users often question if the app is "worth it." Support must emphasize that the plan is tailored to the individual's body/age to prevent impulse buying, rather than just providing generic fashion rules.
* **Refunds & Cancellations:** - *Cancellation Policy:* The cancellation method strictly depends on where the user purchased the subscription.
* *Web Purchases:* Can be canceled by contacting support (`support@dressly.world` / `help@dressly.world`) or directly in the app.
* *App Store / Google Play Purchases:* **In-app cancellation is not available.** Users *must* cancel directly via their device's native app store subscription settings.
* *Refunds:* Dressly has a "Money-Back Guarantee" policy (referenced in the footer), though specific day limits aren't detailed on the main page, implying standard support escalation is required to process them.



## 3. Support Policies & Constraints

* **Support Channels:** Strictly email via `support@dressly.world` (also listed as `help@dressly.world` in the footer) or a web contact form. Business inquiries go to `developer@dressly.world`. No live chat or phone support is mentioned.
* **SLAs & Escalations:** No explicit response times are guaranteed.
* **Self-Service Options:** An FAQ section is available on the website. In-app cancellation is available *only* for web-based buyers.
* **Human vs. Automated:**
* *Automated:* The initial style quiz, AI Color Scanner, and Virtual Try-On features.
* *Human Required:* Web subscription cancellations (if the user emails instead of using the app), processing the Money-Back Guarantee, and troubleshooting photo upload failures.



## 4. Edge Cases

Here are 10 realistic edge cases a support agent for Dressly might encounter:

1. **Domain: Refunds & Cancellations**
* *Scenario:* A user emails asking to cancel and refund their subscription under the "Money-Back Guarantee," but they purchased the app through the Apple App Store.
* *Why it's difficult:* Dressly support physically cannot cancel or refund an Apple subscription. The agent must instruct the user to navigate Apple's UI for both the cancellation and the refund request, which often makes the customer feel like the company is dodging the guarantee.
* *Customer Emotion:* Frustrated and suspicious.


2. **Domain: Technical Errors**
* *Scenario:* A user uploads a photo for the *Virtual Try-On*, but the AI severely distorts their body shape or applies the clothing poorly.
* *Why it's difficult:* Body image is highly sensitive (especially for Dressly's target demographic of women struggling with fashion confidence). A buggy AI rendering can be deeply insulting to the user.
* *Customer Emotion:* Insulted, insecure, and angry.


3. **Domain: Tariff & Plan Questions**
* *Scenario:* A user completes the quiz, pays for a subscription, but complains that the "curated pieces from different brands" feature is just redirecting them to expensive designer websites they can't afford.
* *Why it's difficult:* The agent must explain how to adjust budget preferences in the app to fix the AI's recommendations, while defending the initial value of the subscription.
* *Customer Emotion:* Disappointed and feeling misled about the "smart shopping" aspect.


4. **Domain: Technical Errors**
* *Scenario:* The *AI Color Scanner* assigns a user a "Winter Harmony" palette, but the user is adamant they are a "Warm Autumn" and demands the app be manually overridden.
* *Why it's difficult:* The AI's output is the core product. If the AI gets it "wrong" in the user's eyes, the agent has to navigate a technical limitation (can the agent manually change an AI result?) without invalidating the user's personal preference.
* *Customer Emotion:* Annoyed and dismissive of the app's technology.


5. **Domain: Account Access**
* *Scenario:* A user wants to delete their account and demands proof that all their uploaded body photos and videos have been wiped from Dressly's servers, citing the privacy policy.
* *Why it's difficult:* Tier-1 agents rarely have backend access to verify server-side media deletion, requiring escalation to the developer/engineering team to provide the requested proof.
* *Customer Emotion:* Paranoid and demanding.


6. **Domain: Cancellations**
* *Scenario:* A web-purchaser tries to cancel in the app, but the app crashes every time they tap the `Cancel Subscription` button.
* *Why it's difficult:* The user feels trapped by a technical bug preventing them from stopping a recurring charge. The agent must manually intervene and cancel it on the backend immediately.
* *Customer Emotion:* Panicked and hostile.


7. **Domain: Refunds**
* *Scenario:* An older user (e.g., a 66-year-old retiree, a demographic mentioned in reviews) forgets they subscribed after the quiz and gets charged for a 6-month upfront plan they didn't realize was a subscription.
* *Why it's difficult:* Navigating the "Money-Back Guarantee" for an accidental, high-ticket subscription requires empathy and clear communication with a demographic that may not be highly tech-savvy.
* *Customer Emotion:* Confused and financially stressed.


8. **Domain: Technical Errors**
* *Scenario:* The app's outfit scanner rates a user's favorite real-life outfit very poorly, and the user emails support to complain the AI is "rude" and doesn't understand their style.
* *Why it's difficult:* The agent has to de-escalate hurt feelings caused by an automated system and explain how to train or adjust the AI's feedback loop.
* *Customer Emotion:* Offended and defensive.



## 5. Agent Pitfall Areas

1. **The "App Store Trap"**
* *The Pitfall:* A user emails `support@dressly.world` saying "Cancel my account." The agent replies, "I've canceled your account, sorry to see you go!" without checking the payment gateway.
* *Why it fails:* If the user subscribed via Google Play or Apple, closing the Dressly web account does *not* stop the billing. The user will be charged again, leading to massive frustration and chargebacks. Agents *must* verify the payment source before confirming cancellation.


2. **Insensitive Tech Troubleshooting**
* *The Pitfall:* A user complains the Virtual Try-On makes them look unnaturally wide. The agent responds, "Please ensure you are standing in good lighting and wearing tight clothing so the AI can accurately measure your dimensions."
* *Why it fails:* Dressly markets to women who are self-conscious about their bodies and want to feel "seen and understood." Asking a self-conscious user to put on tight clothing to fix a buggy app completely shatters the empathetic, confidence-building brand voice.


3. **Generic Fashion Advice**
* *The Pitfall:* A user complains the "Soft Escape" capsule wardrobe isn't working for them. The agent replies with generic advice like, "Try adding a statement necklace or a black blazer!"
* *Why it fails:* Dressly's entire marketing premise is that they *don't* give generic rules and instead offer hyper-personalized, AI-driven style. Agents acting as amateur stylists undermine the app's core value proposition.


4. **Ignoring the "Money-Back Guarantee"**
* *The Pitfall:* A user asks for a refund because the app didn't work for them. The agent denies it, stating "subscriptions are non-refundable once the billing cycle starts."
* *Why it fails:* The website footer explicitly advertises a "Money-Back Guarantee." Denying a refund without evaluating the terms of that specific guarantee will result in the user pointing out the false advertising, escalating the issue to consumer protection or social media.