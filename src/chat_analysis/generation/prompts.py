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
Choose ONE persona that fits the scenario naturally. Each persona has a distinct \
typing style — real customers do NOT write perfectly:
- P1 (frustrated-verbose): Long messages, repeats the problem, CAPS for emphasis, run-on sentences, \
sometimes skips punctuation when angry. Good for: escalated, unresolved cases.
- P2 (polite-concise): Short messages, sometimes just a few words ("ok thanks", "got it"). \
May not capitalize first letter. Good for: simple_resolved, any clean case.
- P3 (tech-savvy-impatient): Uses jargon and abbreviations ("btw", "fyi"), terse follow-ups, \
may skip greetings entirely. Good for: technical_errors domain.
- P4 (elderly-confused): Misuses terms, asks same question differently, over-explains, \
sometimes types in partial sentences or adds ellipses "I tried to do the thing...". \
Good for: account_access, tariff_questions.
- P5 (passive-aggressive): Polite surface but loaded phrasing, may write short clipped responses \
when unhappy. REQUIRED for: hidden_dissatisfaction=True.
- P6 (first-time-user): Vague descriptions ("it's not working"), unsure what info to provide, \
may ask unrelated questions mid-conversation. Good for: tariff_questions, account_access.
- P7 (returning-complainer): References past issues, writes emotionally, may exaggerate, \
uses "again" and "still" frequently. Good for: refunds, payment_issues.
- P8 (business-professional): More formal but still human — may abbreviate in follow-ups, \
mentions business impact. Good for: payment_issues, technical_errors.

## Communication Style Rules
Every chat must have a UNIQUE customer writing style. The communication_style field should be a \
specific, vivid description of how THIS customer types — not a generic label. \
Vary these dimensions across chats:
- Capitalization: all lowercase / normal / random caps / occasional CAPS on key words when upset
- Punctuation: no punctuation at all / excessive punctuation ("???", "!!") / ellipsis heavy ("so...")
- Grammar: broken grammar with typos / mostly correct / wild misspellings
- Message length: one-word replies / medium / walls of text
- Greeting style: no greeting at all / just "hi" / "Hello, I have a question"
- Vocabulary: slang and abbreviations ("pls", "thx", "idk", "u") / plain words / formal language
- Info-giving: vague and forces agent to ask follow-ups / dumps everything at once

Example communication_style values (each chat should get something different):
- "all lowercase, no punctuation, skips greetings, very short replies like 'yeah' or 'nope'"
- "writes in long run-on sentences without commas, uses caps when frustrated, lots of typos"
- "polite but vague, doesn't give details until asked, uses ellipsis a lot"
- "formal opening then gets increasingly casual, abbreviations in follow-ups"
- "mobile typing style, one-word answers, abbreviations like 'ur' and 'bc' and 'rn'"
- "emotional and scattered, mixes complaints with backstory, uses '??' and '!!'"

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

## Structured Product Context
{structured_context}

## Scenario Brief
{brief}

## Scenario Parameters
- Domain: {domain}
- Case type: {case_type}
- Chat ID: {chat_id}

## Writing Rules

### Customer Voice — CRITICAL
The customer's writing style is defined in the scenario brief's communication_style field. \
Follow it exactly. Each chat has a DIFFERENT customer voice — do NOT use a uniform style.

**Hard rules for ALL customer messages:**
- NEVER end a customer message with a period/dot. Real people don't do that in chat. \
End with nothing, with "?", with "!", with "...", or just trail off.
- NEVER write all customer messages as perfectly grammatical, well-structured sentences. \
Customers are real people typing fast in a chat widget.
- NEVER write entire customer messages in ALL CAPS. Caps are only for occasional emphasis \
on single words or short phrases ("I ALREADY tried that", "this is NOT working"). \
The rest of the message must be normal case or lowercase.
- Vary message lengths within the same conversation — mix very short ("ok", "yeah", "nope") \
with longer messages when the customer explains their problem.
- The customer does NOT always provide all info upfront. Often the agent must ask for details.

**Persona writing guides:**
- P1 (frustrated-verbose): Long run-on sentences, CAPS only on key words for emphasis \
("I ALREADY told you", "this is NOT okay"), skips punctuation when angry, repeats the problem
- P2 (polite-concise): Very short ("ok thanks", "got it"), may skip capitalization
- P3 (tech-savvy-impatient): No greeting, abbreviations ("btw", "fyi"), terse follow-ups \
like "nope" or "same error"
- P4 (elderly-confused): Misuses terms, ellipses everywhere ("I tried the thing..."), \
over-explains, asks same question differently
- P5 (passive-aggressive): Clipped responses, loaded phrasing ("Sure, if that's how it works")
- P6 (first-time-user): Vague ("its not working"), gives wrong info, "where do i even find that?"
- P7 (returning-complainer): Emotional, "again??", "this is the 3rd time", wild language
- P8 (business-professional): Starts formal, gets casual in follow-ups, abbreviates later

### Agent Voice
- Greet by name in first response using [CUSTOMER_NAME].
- Show varied empathy — NOT the same phrase every message. Mix: "I understand", \
"That must be frustrating", "Let me look into this", "I can see how that's concerning".
- Use contractions naturally ("I'll", "we've", "that's").
- Ask ONE question at a time — do not stack multiple questions.
- Reference specific entities from the product (plan names, features, policies) as listed \
in the required_entities.
- Provide concrete next steps, not vague promises.

### PII Placeholders (MANDATORY)
Use these placeholders — NEVER invent real personal data:
- [CUSTOMER_NAME] — customer's name
- [CUSTOMER_EMAIL] — customer's email
- [ORDER_ID] — order/transaction ID
- [ACCOUNT_ID] — account identifier
- [PHONE_NUMBER] — phone number
- [DATE] — specific dates
- [AMOUNT] — monetary amounts when referring to customer's specific transaction

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

### Entity Accuracy (entity_accuracy)
5. All product names, plan names, features, error codes, and departments mentioned in the \
conversation exist in the valid_entities list.
6. No hallucinated entity names.

### PII Placeholders (pii_placeholders_used)
7. Customer personal data uses [CUSTOMER_NAME], [CUSTOMER_EMAIL], [ORDER_ID], etc.
8. No real-looking names, emails, or IDs are used.

### Persona Match (persona_match)
9. Customer's communication style matches the brief's communication_style description.
10. Message length and vocabulary are consistent with the persona.
11. Customer messages NEVER end with a period/dot — if any do, set persona_match=False.
12. Customer messages are NEVER entirely in ALL CAPS — caps are only for emphasis on individual \
words or short phrases. If any full message is all caps, set persona_match=False.
13. Customer messages should NOT all be perfectly grammatical and well-structured — if they \
read like polished writing rather than real chat typing, set persona_match=False.

### Emotional Arc (emotional_arc_match)
14. Customer's emotional progression matches the brief's emotional_arc.
15. If hidden_dissatisfaction: customer ends with polite/neutral tone despite unresolved issue.

### Agent Errors (agent_errors_as_planned)
16. If error plan is non-empty: each planned error appears in the conversation.
17. If error plan is empty: agent is professional and accurate throughout.
18. Errors feel natural, not forced.

### Overall
- Set is_valid=True only if structural checks pass AND no critical issues in other checks.
- List all specific issues found.
- Provide actionable suggestions for improvement.
"""
