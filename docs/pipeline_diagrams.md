# Pipeline Diagrams

## Generation Pipeline

Shows how chats are generated via `POST /groups` and background workers.

```
POST /groups (topic, context_file?, website_url?, num_chats)
│
├─── website_url provided? ─── YES ──► [gathering_context]
│                                       │
│                                       ├── validate_url()
│                                       │   └── SSRF check (block private/loopback IPs)
│                                       ├── fetch_html() ─── 15s timeout, 2 MB cap
│                                       ├── extract_text() ── strip script/style/nav/footer
│                                       ├── sanitize_text() ─ remove prompt injection patterns
│                                       ├── LLM chain: GATHER_CONTEXT_SYSTEM_TEMPLATE
│                                       │   prompt | llm | StrOutputParser → context doc
│                                       ├── _combine_contexts(file_context, website_context)
│                                       └── save context ──► proceed to generation ▼
│
├─── context_file provided? ─── YES ──► [generating]
│    (no URL)                            │
│                                        ├── validate .md extension, ≤ 1 MB
│                                        ├── sanitize_text()
│                                        ├── save context
│                                        └── proceed to generation ▼
│
└─── neither ──────────────────────────► [gathering_context]
                                         │
                                         ├── resolve_context(topic, llm)
                                         │   ├── load_domain_context(topic)
                                         │   │   ├── normalize_domain_name(topic)
                                         │   │   │   └── lowercase, replace non-alnum → '_'
                                         │   │   ├── exact match: domains/{normalized}.md
                                         │   │   └── compact match: strip '_' and compare
                                         │   │
                                         │   ├── found? → return (content, "domain_file")
                                         │   └── not found? → generate_context_from_knowledge()
                                         │       ├── LLM chain: GENERATE_CONTEXT_FROM_KNOWLEDGE_TEMPLATE
                                         │       │   prompt | llm | StrOutputParser → context doc
                                         │       └── return (content, "llm_knowledge")
                                         │
                                         ├── save context
                                         └── proceed to generation ▼

                        ┌──────────────────────────────────────┐
                        │         GENERATION (per chat)        │
                        │              [generating]            │
                        └──────────────┬───────────────────────┘
                                       │
                   build_group_scenarios(num_chats)
                   │   cycle through 5 domains × 4 case types
                   │   assign flags via idx % 4:
                   │     0 = clean, 1 = hidden_dissatisfaction,
                   │     2 = tonal_errors, 3 = logical_errors
                   │
                   ▼
          ┌─── for each scenario ───┐
          │                         │
          │  pre-create chat record (status: pending)
          │         │
          │         ▼
          │  generate_single_chat(scenario, chat_id, llm)
          │         │
          │         │  ┌────── retry loop (up to 3 attempts) ──────┐
          │         │  │                                            │
          │         │  │  Step 1: GENERATE                         │
          │         │  │  ├── build_special_requirements(scenario)  │
          │         │  │  ├── load context (override or from disk)  │
          │         │  │  ├── generate_chain:                       │
          │         │  │  │   GENERATE_SYSTEM_TEMPLATE              │
          │         │  │  │   prompt | llm.with_structured_output   │
          │         │  │  │         (GeneratedChat)                 │
          │         │  │  └── invoke → GeneratedChat                │
          │         │  │                                            │
          │         │  │  Structural validation:                    │
          │         │  │  ├── first msg must be CUSTOMER            │
          │         │  │  ├── roles must alternate                  │
          │         │  │  └── minimum 4 messages                   │
          │         │  │  fail? → retry ↩                           │
          │         │  │                                            │
          │         │  │  Step 2: VALIDATE (LLM-based)             │
          │         │  │  ├── validate_chain:                       │
          │         │  │  │   VALIDATE_SYSTEM_TEMPLATE              │
          │         │  │  │   prompt | llm.with_structured_output   │
          │         │  │  │         (ChatValidationResult)          │
          │         │  │  ├── checks topic adherence, case type,    │
          │         │  │  │   flags match scenario                  │
          │         │  │  └── is_valid?                             │
          │         │  │      ├── YES → return chat ✓               │
          │         │  │      └── NO  → retry ↩                     │
          │         │  │                                            │
          │         │  │  all retries exhausted → return last chat  │
          │         │  └───────────────────────────────────────────┘
          │         │
          │  save chat (status: generated)
          │  or on error (status: failed)
          │         │
          └─────────┘
                    │
                    ▼
          group status → "generated"
```

---

## Analysis Pipeline

Shows how chats are analyzed via `POST /groups/{group_id}/analyze`.

```
POST /groups/{group_id}/analyze
│
├── verify group status == "generated"
├── set all chat statuses → "analyzing"
├── set group status → "analyzing"
│
▼
_analyze_group_sync(group_id)
│
├── llm = get_llm()
├── load all chats from storage
│
▼
┌─── for each chat ───────────────────────────────────────────┐
│                                                              │
│  skip if no messages (status → failed)                       │
│  set status → "analyzing"                                    │
│                                                              │
│  analyze_single_chat(chat_data, llm)                         │
│  │                                                           │
│  │  format_chat_messages(messages)                           │
│  │  ├── for each message:                                    │
│  │  │   sanitize_text(msg.text)                              │
│  │  └── format: "[idx] ROLE: text"                           │
│  │                                                           │
│  │  extract domain & case_type from chat.scenario            │
│  │                                                           │
│  │  Step 1: ANALYZE                                          │
│  │  ├── analyze_chain:                                       │
│  │  │   ANALYZE_SYSTEM_TEMPLATE                              │
│  │  │   prompt | llm.with_structured_output(ChatAnalysis)    │
│  │  ├── params: chat_id, chat_messages, domain, case_type    │
│  │  └── invoke → ChatAnalysis                                │
│  │      ├── chat_id                                          │
│  │      ├── intent (str)                                     │
│  │      ├── satisfaction (SatisfactionLevel enum)             │
│  │      ├── quality_score (1-10)                              │
│  │      ├── agent_mistakes: list[AgentMistake]               │
│  │      │   ├── type (str)                                   │
│  │      │   ├── description (str)                             │
│  │      │   └── message_index (int)                           │
│  │      └── reasoning (str)                                   │
│  │                                                           │
│  │  Step 2: VALIDATE & CORRECT                               │
│  │  ├── validate_chain:                                      │
│  │  │   ANALYZE_VALIDATE_TEMPLATE                            │
│  │  │   prompt | llm.with_structured_output                  │
│  │  │         (AnalysisValidationResult)                     │
│  │  ├── params: chat_id, chat_messages, analysis_json,       │
│  │  │          domain, case_type                             │
│  │  ├── validation checks:                                   │
│  │  │   1. Intent detection accuracy                         │
│  │  │   2. Satisfaction vs. hidden dissatisfaction signals    │
│  │  │   3. Quality score reasonableness                      │
│  │  │   4. All agent mistakes identified                     │
│  │  │   5. Reasoning accuracy                                │
│  │  │   6. Topic adherence to expected domain                │
│  │  └── invoke → AnalysisValidationResult                    │
│  │      ├── is_correct (bool)                                │
│  │      ├── corrections (str)                                 │
│  │      └── corrected_analysis (ChatAnalysis)                │
│  │                                                           │
│  │  return corrected_analysis                                │
│  │                                                           │
│  save chat (status: analyzed, analysis attached)              │
│  or on error (status: failed)                                │
│                                                              │
└──────────────────────────────────────────────────────────────┘
│
▼
group status → "completed"
(or "analysis_failed" on unhandled exception)
```
