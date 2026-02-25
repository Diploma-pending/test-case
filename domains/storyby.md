Storyby Business & Support Context Document
1. Business Overview
Product & Services: Storyby is an entertainment tech company that provides a content ecosystem bridging writers and audiences through serialized storytelling. The ecosystem operates via three main products:

DramaShorts: A vertical streaming platform for cinematic, emotionally-driven short films.

AlphaNovel: A mobile-first platform for serialized fiction and immersive audiobooks with a gamified reading experience.

StorybyWriter: A publishing platform where over 28,000 authors create, publish, and monetize novels, with top-performing stories adapted into vertical films for DramaShorts.

Target Customer: - Consumers: Fans of bingeable, serialized genre fiction and short vertical dramas. The audience skews heavily toward romance, paranormal (werewolf/vampire), billionaire themes, and emotionally driven narratives.

Creators: Writers seeking an audience, community feedback, and monetization (royalties/adaptations).

Key Features & Pricing Tiers:

Soft Paywall & Microtransactions: Both DramaShorts and AlphaNovel offer initial content (first few episodes/chapters) for free. Further content is unlocked using in-app currency (Coins).

AlphaNovel Pricing: Users can unlock chapters by watching ads (3 ads per chapter) or buying coins. They offer standalone coin packs and an "AlphaNovel Plus" subscription. The subscription provides double daily coins for reading/checking in, extra coin package bonuses (up to 50%), exclusive author gifts, and a premium support badge.

DramaShorts Pricing: Offers weekly, monthly, and a-la-carte plans. Tiers include Weekly Coins ($4.99–$19.99), standard Coins packages ($3.99–$24.99), and Full Access subscriptions ($11.99, $19.99, $39.99). Subscriptions include benefits like ad-free viewing, 1080p resolution, and early access to top-rated dramas.

2. Support Domain Context
Payment Issues: - Payments are processed via native app stores (Apple App Store, Google Play) as well as directly via the web platforms.

Users frequently buy standalone Coin packages alongside recurring subscriptions.

Common payment complaints revolve around users not realizing they are billed weekly or monthly, or "Auto-unlock chapters" draining coin balances rapidly, leading to frequent top-up charges.

Technical Errors: - Known issues include purchased Coins not syncing to the user's account (e.g., buying a promo pack of 1,110 coins but only 800 registering).

Bugs with the ad-supported unlock flow (e.g., the "3 Ads to Unlock a Chapter" feature freezing on the third ad, failing to unlock the chapter).

Cross-platform syncing issues between the web interface and the mobile app.

Account Access: - Logins primarily utilize Single Sign-On (Google, Apple) to reduce friction.

Progress and coin balances are tied to the account. If a user begins reading/watching as a guest and later creates an account, they may experience "lost progress" or missing coins.

Tariff & Plan Questions: - Plan confusion is high. Users frequently complain that they purchased a DramaShorts "Full Access" subscription or an AlphaNovel subscription, only to discover that they still need to purchase Coins to unlock certain premium or exclusive episodes/chapters.

The "Free Chapter Per Hour" timer was deprecated and replaced with the "3 Ads" system, causing legacy user confusion.

Refunds: - The company states a strict policy but does offer manual refunds for web purchases. Customer support explicitly states: "We do provide refunds. Feel free to reach us at help@dramashorts.io."

For App Store/Google Play purchases, the company cannot issue refunds directly and must route the user to Apple/Google's native refund flows.

Subscriptions initiated on the web must be canceled on the web, while app subscriptions must be canceled in device settings.

3. Support Policies & Constraints
Channels: Support operates primarily via email (support@storyby.tech, support@alphanovel.io, help@dramashorts.io). They also actively monitor and respond to Trustpilot, App Store, and Google Play reviews.

SLAs & Escalation: "Premium support" is listed as an official perk for AlphaNovel Plus subscribers, meaning their tickets are likely prioritized or routed to a dedicated VIP queue.

Self-Service: AlphaNovel features an extensive Help Center (alphanovel.io/help) covering topics like auto-unlock toggles, text formatting/font adjustments, and subscription cancellation steps.

Human vs. Automated Resolution: - Automated/Self-Service: Canceling iOS/Android subscriptions, changing app settings, unlocking chapters via ads.

Human Agent Required: Processing web-based refunds, investigating missing coin allocations from database sync errors, handling author payment/royalty disputes on StorybyWriter.

4. Edge Cases
Domain: Payment

Scenario: A user subscribes to DramaShorts via the web platform but attempts to cancel via their iPhone's Apple ID Subscriptions page. Finding nothing there, they assume it's canceled, get billed the following month, and demand a refund.

Difficulty: Requires cross-referencing account creation source. The agent must locate the web stripe/payment ID rather than an Apple receipt.

Customer Emotion: Frustrated and feeling scammed.

Domain: Tariffs & Plans

Scenario: A user purchases a DramaShorts "Full Access" ($19.99) subscription, believing it provides unlimited viewing. They hit a premium exclusive series and are prompted to buy Coins to continue.

Difficulty: The agent has to explain the dual-monetization model (subscription + soft paywall for microtransactions) without sounding deceptive.

Customer Emotion: Hostile and misled.

Domain: Technical

Scenario: A user buys an AlphaNovel promo package advertised as "1,110 coins for $5", but a visual bug credits the standard 800 coins.

Difficulty: The agent's backend system might only show a "$5 coin purchase (800)". The agent has to verify if an active UI promo was running and manually credit the missing 310 coins.

Customer Emotion: Annoyed and distrustful.

Domain: Technical / Tariffs

Scenario: A legacy AlphaNovel user demands the return of the "Free Chapter Per Hour" timer, refusing to use the new "3 Ads to Unlock" system because the ads crash their older device.

Difficulty: The feature is permanently deprecated. The agent cannot restore it and must suggest buying coins to bypass the crashing ads.

Customer Emotion: Stubborn and frustrated.

Domain: Account Access

Scenario: An AlphaNovel user utilizes the "Auto-unlock chapters" feature to binge a 100-chapter werewolf novel, falls asleep, and a sibling taps through the book, draining $40 worth of auto-purchased coins.

Difficulty: The coins were technically spent legitimately on the account, making partial refunds of digital currency highly ambiguous.

Customer Emotion: Panicked and desperate.

Domain: Refunds

Scenario: A user emails support@alphanovel.io demanding a refund for an App Store purchase. The agent replies with instructions to refund via Apple. Apple denies the refund based on the user's past refund history. The user returns to Storyby support demanding a manual payout.

Difficulty: Storyby cannot override Apple's billing ecosystem and cannot directly refund an iOS purchase.

Customer Emotion: Extremely hostile.

Domain: Account Access / StorybyWriter

Scenario: An author on StorybyWriter changes their payout email address, but the platform's security flags it as a compromised account and suspends access just as their story goes viral.

Difficulty: Agent must securely verify the author's identity (KYC) while managing the creator's panic about lost royalties.

Customer Emotion: Highly anxious and urgent.

Domain: Technical

Scenario: A user is unlocking a DramaShorts episode. They are deducted 50 Coins, but the app crashes. Upon reopening, the episode is locked, but the 50 Coins are gone.

Difficulty: The agent must check server logs to verify the transaction vs. the unlock state, then manually restore the coins or unlock the episode.

Customer Emotion: Irritated.

5. Agent Pitfall Areas
Misdirecting Cancellation Flows: An agent might use a standard macro telling a user to "Cancel in your App Store settings" without verifying where the subscription originated. If the user subscribed on the DramaShorts website, they will not find the subscription on their phone, leading to unwanted renewals and escalations.

Defending the Pricing Model Inaccurately: Because of the dual-monetization model (Subscriptions + Coins), agents might incorrectly promise that a "Full Access" or "AlphaNovel Plus" tier unlocks all content. Failing to clarify that exclusive content may still require standalone coin purchases will trigger immediate chargebacks and negative Trustpilot reviews.

Mishandling iOS/Android Refund Promises: An agent might say "I have approved your refund" for an Apple/Google purchase. Support agents have zero control over Apple's native refund decisions. Promising a refund that Apple later denies creates a severe customer service failure.

Dismissing Missing Coin Claims: When a user reports receiving fewer coins than a promo promised (e.g., the 800 vs 1110 coin bug), an agent relying strictly on standard pricing sheets might dismiss the user, assuming they misread the tier. Failing to investigate caching issues or live promos will result in lost user retention for high-LTV readers.