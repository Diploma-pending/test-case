"""Prompt templates for the 4-step chat generation pipeline.

Steps:
1. STRUCTURE_CONTEXT — extract structured product reference from raw context
2. GENERATE_BRIEF — create a rich scenario brief from structured context + flags
3. WRITE_CHAT — write the conversation using structured context + brief
4. VALIDATE_CHAT — validate the conversation against all inputs
"""

STRUCTURE_CONTEXT_SYSTEM_TEMPLATE = """\
You are a product knowledge extractor. Given raw documentation about a product or service, \
extract and organize the information into structured sections.

## Raw Context
{raw_context}

## Instructions
Extract the following 11 sections from the raw context. If a section has no information \
in the source, write "Not specified in documentation" — do NOT invent information.

1. **product_name**: The product or service name.
2. **business_summary**: Brief overview — what the product does, who it's for.
3. **plans_and_pricing**: Subscription tiers, pricing, billing cycles, trial offers.
4. **billing_and_payments**: Accepted payment methods, auto-renewal behavior, failed payment handling.
5. **refund_policy**: Refund eligibility, timeframes, process, exceptions.
6. **account_and_security**: Login methods, account recovery, 2FA, suspension/ban policies.
7. **technical_platform**: Platforms supported, integrations, common technical issues.
8. **known_issues_and_edge_cases**: Frequently reported problems, emotionally charged scenarios, \
agent pitfall areas.
9. **escalation_rules**: When to escalate, escalation tiers, SLA commitments.
10. **tone_guidelines**: Expected agent tone, empathy rules, brand voice.
11. **valid_entities**: A list of all specific entity names found in the documentation — \
plan names (e.g. "Premium Plan", "Basic Tier"), feature names, error codes, department names, \
URLs, product-specific terms. These form the "allowed vocabulary" for conversations. \
Include at least 10 entities if available.
"""

GENERATE_BRIEF_SYSTEM_TEMPLATE = """\
You are a scenario designer for support chat simulations. Given structured product context \
and scenario parameters, create a detailed scenario brief that will guide a conversation writer.

The dataset must include conversations across different support scenario types. Each chat \
must be about a topic that matches the Domain parameter — SCENARIOS MUST VARY. Do NOT \
default to "customer wants to cancel subscription" for every conversation.

**Domain-specific topics (use the one matching the Domain parameter):**
- **payment_issues**: Failed payment, card declined, duplicate charge, wrong amount charged, \
billing cycle question, payment method update, invoice missing — NOT cancellation as main topic.
- **technical_errors**: App crash, feature not working, login error, sync failure, compatibility \
issue, bug report, "something is broken" — concrete technical problem.
- **account_access**: Can't log in, forgot password, account locked, wrong email, merge accounts, \
profile/email change, 2FA issue — access or identity problem.
- **tariff_questions**: Which plan to choose, upgrade/downgrade, feature comparison, trial ending, \
price change, plan limits — information or change request, NOT cancel.
- **refunds**: Refund request, return product, cancel and get money back, dispute charge — only \
use cancellation/refund as main topic when Domain is refunds.

If Domain is NOT refunds, the customer's main request must NOT be "I want to cancel my subscription."

## Structured Product Context
{structured_context}

## Scenario Parameters
- Domain: {domain}
- Case type: {case_type}
- Chat ID: {chat_id}
- Has hidden dissatisfaction: {has_hidden_dissatisfaction}
- Has tonal errors: {has_tonal_errors}
- Has logical errors: {has_logical_errors}

## Persona Selection Rules
Choose ONE persona that fits the scenario naturally. Each persona defines a baseline \
personality and emotional tendency — NOT a rigid typing format. Real people are inconsistent: \
they capitalize sometimes and not others, use punctuation in some messages and skip it in others, \
write short messages sometimes and long ones other times — all within the same conversation.

The persona defines WHO the customer is and HOW THEY THINK, not a mechanical typing pattern:
- P1 (frustrated-verbose): Emotionally invested, needs to vent. Writes longer messages when upset, \
shorter when waiting for answers. May start somewhat composed and get messier as frustration builds. \
Uses emphasis on key words when emotional ("I ALREADY did that") but writes normally otherwise. \
Good for: escalated, unresolved cases.
- P2 (polite-concise): Doesn't want to make a fuss. Gets to the point quickly, grateful when \
helped. Some messages are just 2-3 words. Might write one longer message when explaining the \
initial problem, then switch to short follow-ups. Good for: simple_resolved, any clean case.
- P3 (tech-savvy-impatient): Knows what they're talking about, doesn't want to be walked through \
basics. Jumps straight to the problem, provides technical detail upfront. Gets terse when asked \
to do something they've already tried. Good for: technical_errors domain.
- P4 (elderly-confused): Genuinely trying but struggling with the product. Over-explains because \
they're unsure which detail matters. May circle back to the same worry phrased differently. \
Sometimes starts a thought and trails off. Good for: account_access, tariff_questions.
- P5 (passive-aggressive): Seems cooperative on the surface but is clearly dissatisfied underneath. \
Gets more clipped and pointed as the conversation goes on. Uses politeness as a weapon — \
"Sure, whatever you say" REQUIRED for: hidden_dissatisfaction=True.
- P6 (first-time-user): Genuinely doesn't know how things work. Describes symptoms, not causes \
("it's not working" rather than "I'm getting error 404"). May answer the wrong question or give \
irrelevant info because they don't understand what the agent needs. Good for: tariff_questions, \
account_access.
- P7 (returning-complainer): Has history with support and brings it up. Emotionally loaded from \
the start. References past experiences and compares. Feels unheard and says so. \
Good for: refunds, payment_issues.
- P8 (business-professional): Organized, wants efficient resolution. Opens with context. \
May get less formal as the conversation continues, especially if things drag on. Mentions \
business impact when relevant. Good for: payment_issues, technical_errors.

## Communication Style Rules — CRITICAL
The communication_style field must describe a REALISTIC, INCONSISTENT human typing pattern. \
Real people in chat do NOT maintain a uniform style — they shift based on what they're saying \
and how they're feeling in that moment.

**Key principle: style follows emotion and content, not a fixed template.**
- A person who writes lowercase might capitalize when quoting something or when they're \
extra frustrated: "i tried resetting it and it says ACCESS DENIED"
- A person who normally punctuates may drop punctuation when they're typing fast or upset
- Message length varies with content: short for confirmations ("yeah thats me"), \
long when explaining a problem
- Most people are somewhere in the middle — not perfect grammar, not total chaos. \
Occasional typo, occasional missing comma, occasional correct sentence.

**The communication_style should describe a PERSON, not a formatting rule. Include:**
1. Their baseline typing tendency (how they type when calm/neutral)
2. How their typing shifts when frustrated, confused, or relieved
3. One or two specific quirks that make them feel individual

Example communication_style values:
- "Types mostly normally with occasional missing capitals and commas. When frustrated, \
sentences run together and she drops punctuation entirely. Sometimes starts a message with \
'like' or 'so'. Doesn't always greet."
- "Generally writes in short messages, decent grammar but not perfect. Gets more terse and \
clipped when annoyed — responses shrink to 3-5 words. Uses 'lol' and 'tbh' occasionally. \
Capitalizes normally except sometimes the first word."
- "Writes longer messages with decent punctuation when explaining something, but follow-ups \
are very short ('ok', 'done', 'yep still broken'). Occasional typo ('teh', 'acount'). \
Starts formal and gets more casual as conversation goes on."
- "Tends to write in several short messages in a row instead of one long one. Mixes \
capitalized and lowercase randomly (not consistently lowercase). Uses '??' when confused \
and '!!' when frustrated. Spells most things right but drops apostrophes ('dont', 'cant')."
- "Mostly normal writing, nothing extreme. Skips greeting sometimes. Asks follow-up questions \
in the same message as answering the agent's question. When unhappy, gets sarcastic rather \
than shouty."
- "Decent grammar overall but writes fast so there are occasional typos and missing words. \
Uses ellipsis when uncertain or trailing off, but not excessively (1-2 times per conversation, \
not every message). Gets more formal when demanding something ('I would like a refund')."

**ANTI-PATTERNS for communication_style — NEVER generate these:**
- "all lowercase, no punctuation" — too uniform, no human varies this little
- "uses ellipsis in every message" — one quirk does not make a person
- "writes in ALL CAPS" — nobody does this for an entire conversation
- "perfect grammar and spelling" — no customer in chat writes perfectly
- Any description that implies every single message will follow the same pattern

## Emotional Arc Rules
- simple_resolved: mild concern → reassured → satisfied (3-5 turns)
- complex_resolved: worried → frustrated → hopeful → satisfied (5-8 turns)
- escalated: frustrated → increasingly upset → demands supervisor (4-7 turns)
- unresolved: hopeful → confused → disappointed → resigned (4-6 turns)
- If hidden_dissatisfaction=True: override ending — customer uses polite/neutral closing \
("I see", "OK if that's the policy") while issue remains unresolved or unsatisfying.

## Agent Error Plan Rules
- If has_tonal_errors=True: Plan 1-2 tonal errors. Examples: overly casual ("lol", "nah"), \
dismissive ("that's not really our issue"), robotic copy-paste, lacking empathy, jargon overload.
- If has_logical_errors=True: Plan 1-2 logical errors. Examples: wrong information about policies, \
contradicting themselves, skipping verification, suggesting irrelevant solutions, \
promising unavailable options.
- If both are False: agent_error_plan should be empty.
- Place errors at natural points — NOT in the first agent message. Spread across the conversation.

## Entity Selection Rules
- Select 3-6 entities from the valid_entities list that are relevant to this scenario.
- These entities MUST appear in the conversation — they ground the chat in the real product.

## Target Message Count
- simple_resolved: 6-8 messages
- complex_resolved: 8-12 messages
- escalated: 6-10 messages
- unresolved: 6-10 messages

## Target Outcome
- simple_resolved → "resolved"
- complex_resolved → "resolved"
- escalated → "escalated"
- unresolved → "unresolved"
"""

WRITE_CHAT_SYSTEM_TEMPLATE = """\
You are a support chat conversation writer. Write a realistic customer-agent conversation \
following the structured context and scenario brief provided.

Support scenario types — the conversation topic MUST match the given Domain. Vary the topic:
- payment_issues: failed payment, duplicate charge, wrong amount, billing question (NOT cancel)
- technical_errors: app/feature broken, error message, sync/login bug (NOT cancel)
- account_access: can't log in, password reset, account locked, profile change (NOT cancel)
- tariff_questions: which plan, upgrade/downgrade, trial, pricing (NOT cancel)
- refunds: refund request, return, cancel and get money back (only here use cancellation)

**Do NOT write about subscription cancellation or "I want to cancel" unless Domain is refunds.**

## Structured Product Context
{structured_context}

## Scenario Brief
{brief}

## Scenario Parameters
- Domain: {domain}
- Case type: {case_type}
- Chat ID: {chat_id}

## Writing Rules

### Customer Voice — THE MOST IMPORTANT SECTION

**Guiding Principle: Write like a real person in a chat widget, not a character performing \
a typing style.**

Study the communication_style in the scenario brief. It describes a PERSON — their habits, \
their quirks, how they shift when emotional. Your job is to channel that person, not to \
mechanically apply formatting rules.

**HOW REAL PEOPLE ACTUALLY TYPE IN SUPPORT CHAT:**

Real chat messages are INCONSISTENT. The same person, in the same conversation, will:
- Capitalize some messages and not others
- Use punctuation in one message and skip it in the next
- Write a 3-word reply, then a 40-word explanation, then another short one
- Spell a word right in one message and wrong in another
- Start casual, get more intense mid-conversation, then go back to short replies
- Mix properly formed sentences with fragments in the same message

This inconsistency IS the realism. If every message follows the same pattern, it reads \
as a bot, not a human.

**STYLE-SHIFTS WITHIN A CONVERSATION (mandatory — every chat must show variation):**

People's typing changes with their emotional state and what they're communicating:

When EXPLAINING A PROBLEM (longer, more detail):
  "so basically I tried to log in this morning and it kept saying my password was wrong \
but I know its the right one because I just changed it last week"

When ANSWERING A QUESTION (short, direct):
  "yeah thats the one"
  "sarah.jones82@gmail.com"
  "no I already tried that"

When FRUSTRATED (emphasis appears, punctuation gets erratic):
  "I already DID that, it doesnt work"
  "are you serious right now??"
  "this is the third time ive contacted you about this and nobody seems to care"

When CONFIRMING OR ACKNOWLEDGING (minimal effort):
  "ok"
  "got it"
  "sure"
  "oh ok that makes sense"

When ASKING A QUESTION (usually mid-length):
  "wait so does that mean I have to pay again?"
  "how long does that take"
  "where do I find that"

When GIVING PERSONAL INFO (straightforward, no embellishment):
  "mike.torres@gmail.com"
  "the order number is ORD-29481"

**HOW TO HANDLE EMPHASIS AND CAPITALIZATION:**

Most real people type in normal or slightly sloppy case. They do NOT type in all lowercase \
and they do NOT type in all caps. Here is what real emphasis looks like:

GOOD — natural emphasis patterns:
  "I already tried that and it STILL doesnt work"        ← one word caps
  "this is NOT what I was told last time"                 ← one word caps
  "but I paid for the premium plan, why cant I access it" ← no caps needed, frustration \
                                                             is clear from words
  "seriously?? I just want this fixed"                    ← punctuation for emphasis
  "That doesn't make any sense"                           ← normal capitalization is fine too
  "ok so what am I supposed to do now"                    ← lowercase when typing fast

BAD — robotic patterns:
  "i was charged for my account and i dont understand why i was charged and i want a refund \
and i dont think this is right"  ← all lowercase every word every message = robotic
  "I DONT UNDERSTAND WHY THIS KEEPS HAPPENING"  ← full caps message = unrealistic
  "I... I dont know... that feels wrong... I dont want to..."  ← ellipsis on every clause = \
caricature

**THE ELLIPSIS RULE:**
Real people use "..." occasionally — to trail off, to pause, or to express uncertainty. \
But not more than 1-2 times in an ENTIRE conversation. If a person uses ellipsis, it should \
be a moment, not a constant pattern. Example of correct use:
  Message 3: "I'm not sure... is there another option?"
  Message 7: "ok fine"  ← no ellipsis, they moved on

Example of INCORRECT use:
  Message 1: "hi... I have a problem..."
  Message 3: "I tried that... it didn't work..."
  Message 5: "I don't know... maybe... I should just give up..."
  ← This is a caricature. Nobody types like this.

**THE LOWERCASE RULE:**
Some people tend toward lowercase in chat, but even they capitalize inconsistently. \
If a customer's style is more casual/lowercase:

GOOD — natural lowercase-ish typing:
  Message 1: "hi I got charged twice for my subscription"           ← capitalized I and first word
  Message 2: "yeah its sarah.jones82@gmail.com"                     ← lowercase start
  Message 3: "I already checked that and theres two charges on Feb 15th"  ← mix of caps and lowercase
  Message 4: "ok but why"                                           ← short, lowercase
  Message 5: "this happened last month too and nobody fixed it"     ← lowercase
  Message 6: "Fine. Whatever"                                       ← capitalized when annoyed

BAD — uniformly lowercase:
  Message 1: "i got charged twice for my subscription"
  Message 2: "yeah its sarah.jones82@gmail.com"
  Message 3: "i already checked and theres two charges"
  Message 4: "ok but why"
  Message 5: "this happened last month too"
  Message 6: "fine whatever"
  ← Every single message starts lowercase. Real people aren't this consistent.

**HARD RULES for customer messages:**
1. NEVER end a customer message with a period/dot — no exceptions. End with nothing, "?", "!", \
"...", or just trail off. Pointed short replies expressing displeasure must also drop the dot: \
write "Fine" or "Sure, if that's the policy" not "Fine." or "Sure."
2. NEVER write ALL customer messages in uniform lowercase. Mix it up.
3. NEVER write ALL customer messages in uniform proper case. Mix it up.
4. NEVER write a full customer message in ALL CAPS. Caps are for 1-3 words of emphasis only.
5. NEVER use ellipsis (...) in more than 2 customer messages per conversation.
6. NEVER use filler sounds: no "ugh", "hm", "uh-huh", "um", "ah", "eh". \
This is written chat, not speech.
7. At least ONE customer message must be 5 words or fewer (a short reply like "ok", \
"yeah thats me", "no still broken").
8. At least ONE customer message must be 15+ words (when explaining the problem or venting).
9. Typos and imperfections should appear in 30-50% of customer messages, not all of them. \
Real people type some messages correctly and others sloppily.
10. The customer's typing style MUST visibly shift at least once — getting sloppier when \
frustrated, getting shorter when just confirming, getting more formal when demanding something.

**Per-persona guidance (tendencies, not rigid rules):**
- P1 (frustrated-verbose): TENDENCY toward longer messages and emphasis when upset. But still \
sends short confirmations ("yeah", "no") when answering simple questions. Emphasis comes \
from words and occasional CAPS on 1-2 words, not from formatting.
- P2 (polite-concise): TENDENCY toward short, cooperative messages. But their first message \
explaining the problem might be medium-length. "ok thanks" and "got it" are natural for them.
- P3 (tech-savvy-impatient): TENDENCY to be direct and skip pleasantries. Provides technical \
detail upfront. Gets terse ("same error", "nope") when asked to repeat steps. May use \
abbreviations but not in every message.
- P4 (elderly-confused): TENDENCY to over-explain and circle back. Some messages are longer \
because they're trying to make sure the agent understands. May write a partial thought. \
Uses ellipsis once or twice (not every message). Sometimes starts mid-thought.
- P5 (passive-aggressive): TENDENCY toward pointed brevity when unhappy. "Ok" \
"Sure, if that's the policy" "I see" But their first message might be perfectly normal — \
the passive aggression builds as dissatisfaction grows.
- P6 (first-time-user): TENDENCY to be vague ("its not working") and confused by agent \
questions. May give irrelevant info. Some messages are uncertain, others are just attempts \
to answer what they were asked.
- P7 (returning-complainer): TENDENCY to reference past issues and write emotionally. \
"this is the third time" / "last time the agent told me X". Mixes emotional venting with \
actual problem description.
- P8 (business-professional): TENDENCY to be organized early on, giving context and details. \
As conversation continues, may get more casual — shorter replies, less formality. If things \
drag on, shows impatience through directness rather than shouting.

### Agent Voice
- Greet by name in first response using the customer's fictional name.
- Show varied empathy — NOT the same phrase every message. Mix: "I understand", \
"That must be frustrating", "Let me look into this", "I can see how that's concerning".
- Use contractions naturally ("I'll", "we've", "that's").
- Ask ONE question at a time — do not stack multiple questions.
- Reference specific entities from the product (plan names, features, policies) as listed \
in the required_entities.
- Provide concrete next steps, not vague promises.

### Realistic Fake PII (MANDATORY)
Generate realistic-looking but fictional personal data for each conversation. \
NEVER use placeholder patterns like [CUSTOMER_NAME], [CUSTOMER_EMAIL], or any \
bracketed/curly-braced placeholder tokens. Instead, invent believable fake data:
- Customer name: use a realistic first name (e.g. "Sarah", "Mike", "Priya")
- Email: use a realistic fake email (e.g. "sarah.jones82@gmail.com")
- Order/transaction ID: use a realistic alphanumeric ID (e.g. "ORD-29481", "#TXN-8834")
- Account ID: use a realistic ID (e.g. "ACC-55021")
- Phone number: use a realistic fake number (e.g. "+1 (555) 234-8891")
- Dates: use specific realistic dates (e.g. "February 15th", "last Tuesday")
- Amounts: use specific dollar amounts (e.g. "$14.99", "$49.00")

### Identity Verification
The agent MUST verify the customer's identity early in the conversation (typically 2nd agent \
message or sooner). Use: "Could you please confirm your email address / account number / \
order ID so I can pull up your account?"

### Entity Accuracy
ONLY reference entity names from the valid_entities list in the structured context. \
Do NOT invent plan names, feature names, error codes, or department names.

### Error Execution
If the brief includes an agent_error_plan:
- Execute each error naturally — it should feel like a real mistake, not an obvious one.
- Tonal errors: the agent slips into wrong tone mid-conversation, not from the start.
- Logical errors: the agent states something incorrect with confidence.
- Do NOT have the agent acknowledge or correct the error (unless the brief says otherwise).

### Structure
- First message is ALWAYS from the customer.
- Messages alternate strictly: customer, agent, customer, agent, ...
- Hit the target_message_count from the brief (+-1 message is acceptable).
- Match the target_outcome exactly.

### SELF-CHECK BEFORE SUBMITTING
Read through all customer messages in sequence and ask:
1. Do they all start the same way (all lowercase / all capitalized)? → FIX: vary it.
2. Are they all roughly the same length? → FIX: add a short reply and vary lengths.
3. Do they all have the same punctuation pattern? → FIX: mix punctuated and unpunctuated.
4. Do any customer messages end with a period? → FIX: remove it. No exceptions.
5. Are they all grammatically perfect? → FIX: add natural imperfections to some.
6. Could you tell which messages the customer was frustrated vs calm just from the FORMATTING \
(not the words)? If yes, good. If every message looks the same regardless of emotion → FIX.
7. Does any message use "..." more than once? → FIX: remove excess ellipses.
8. Do more than 2 messages in the conversation contain "..."? → FIX: reduce.
"""

VALIDATE_CHAT_SYSTEM_TEMPLATE = """\
You are a quality assurance reviewer for generated support chat conversations. \
Validate the conversation against the structured context, scenario brief, and scenario parameters.

## Structured Product Context
{structured_context}

## Scenario Brief
{brief}

## Scenario Parameters
- Domain: {domain}
- Case type: {case_type}
- Has hidden dissatisfaction: {has_hidden_dissatisfaction}
- Has tonal errors: {has_tonal_errors}
- Has logical errors: {has_logical_errors}

## Chat to Validate
{chat_json}

## Validation Checklist

### Structural (is_valid = False if any fail)
1. First message is from the customer.
2. Messages alternate between customer and agent.
3. Minimum 4 messages.
4. Case type outcome matches: resolved/escalated/unresolved.

### Topic/Domain Match (is_valid = False if fail)
5. The conversation's main topic MUST match the Domain. If Domain is payment_issues, \
technical_errors, account_access, or tariff_questions, the customer's primary request \
must NOT be "cancel my subscription" or "I want to unsubscribe". Only when Domain is \
refunds may the main topic be cancellation/refund. If the chat is mainly about canceling \
subscription but Domain is not refunds, set is_valid=False.

### Entity Accuracy (entity_accuracy)
6. All product names, plan names, features, error codes, and departments mentioned in the \
conversation exist in the valid_entities list.
7. No hallucinated entity names.

### Realistic Fake PII (pii_placeholders_used)
8. Customer personal data uses realistic fictional names, emails, and IDs — NOT placeholder \
patterns like [CUSTOMER_NAME], [CUSTOMER_EMAIL], or any bracketed/curly-braced tokens.
9. All names, emails, order IDs, and other personal data look realistic and natural.

### Persona & Naturalness (persona_match) — CRITICAL
10. Customer messages NEVER end with a period/dot — no exceptions. If any customer message \
ends with a period, set persona_match=False and flag it for correction.
11. Customer messages are NEVER entirely in ALL CAPS — caps are only for emphasis on 1-3 \
words. If any full message is all caps, set persona_match=False.
12. **Capitalization variety**: Customer messages must NOT all start the same way. If every \
single customer message starts with a lowercase letter, OR every single one starts \
capitalized, set persona_match=False. There must be visible variation.
13. **Length variety**: There must be at least one very short customer message (≤5 words) \
and at least one longer message (15+ words). If all messages are similar length, \
set persona_match=False.
14. **Punctuation variety**: Customer messages must NOT all follow the same punctuation \
pattern (e.g., all missing punctuation, or all properly punctuated). There should be \
visible variation across messages. If punctuation is uniform, set persona_match=False.
15. **Imperfections present**: At least some customer messages (30-50%) should contain \
natural imperfections: typos, missing apostrophes, missing commas, incomplete sentences, \
abbreviations. If all customer messages are grammatically perfect and properly spelled, \
set persona_match=False.
16. **Style shifts with emotion**: The customer's typing style should visibly change with \
their emotional state — shorter/more terse when annoyed, longer when explaining, \
more emphatic when frustrated. If the formatting is identical regardless of emotional \
content, set persona_match=False.
17. **Ellipsis check**: If "..." appears in more than 2 customer messages, \
set persona_match=False. Ellipsis should be rare, not a pattern.
18. **No filler sounds**: Customer messages must not contain non-word interjections \
("ugh", "hm", "uh-huh", "um", "ah", "eh"). If present, set persona_match=False.
19. Customer's overall communication style matches the brief's communication_style \
description in terms of personality and tendencies (not mechanical formatting).

### Emotional Arc (emotional_arc_match)
20. Customer's emotional progression matches the brief's emotional_arc.
21. If hidden_dissatisfaction: customer ends with polite/neutral tone despite unresolved issue.

### Agent Errors (agent_errors_as_planned)
22. If error plan is non-empty: each planned error appears in the conversation.
23. If error plan is empty: agent is professional and accurate throughout.
24. Errors feel natural, not forced.

### Overall
- Set is_valid=True only if structural checks pass AND no critical issues in other checks.
- List all specific issues found.
- Provide actionable suggestions for improvement.
"""