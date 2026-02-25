# Chat Analysis API — FE Integration Guide

> **Base URL**: `http://localhost:8000`
> **Auth**: None (no authentication required)
> **Interactive docs**: `http://localhost:8000/docs`

---

## Overview

The API exposes four endpoints organized around two resources: **groups** and **chats**.

A **group** is a set of AI-generated support chats built from a topic and a `.md` context file.
A **chat** is a single generated conversation within a group.

### Typical integration flow

```
POST /groups                    → get group_id, status = "generating"
    poll GET /groups/{id}/chats → wait until status = "generated"
POST /groups/{id}/analyze       → status flips to "analyzing"
    poll GET /groups/{id}/chats → chats flip to "analyzed" one by one
GET /groups/{id}/chats/{chatId} → full detail when user clicks a chat
```

---

## Status lifecycles

### Group status

| Value | Meaning |
|---|---|
| `generating` | Chats are being created by the AI (background task running) |
| `generated` | All chats created — ready to trigger analysis |
| `generation_failed` | Background generation task crashed |
| `analyzing` | Analysis is running (background task running) |
| `completed` | All chats analyzed — all data available |
| `analysis_failed` | Background analysis task crashed |

### Per-chat status

| Value | Meaning |
|---|---|
| `pending` | Queued, generation not started yet |
| `generating` | Being generated right now |
| `generated` | Chat messages ready — analysis not yet run |
| `analyzing` | Analysis in progress |
| `analyzed` | Analysis complete — all data available |
| `failed` | This individual chat errored during generation or analysis |

---

## Endpoints

---

### `POST /groups`

> **Purpose**: Upload a topic and context file; the server immediately returns a `group_id` and begins generating chats in the background.

#### Request

- **Content-Type**: `multipart/form-data`

| Field | Type | Required | Default | Validation |
|---|---|---|---|---|
| `topic` | `string` | Yes | — | Non-empty string, used as the domain label in AI prompts |
| `context_file` | `file` | Yes | — | Must be a `.md` file, max size 1 MB |
| `num_chats` | `integer` | No | `8` | Positive integer — number of chats to generate |

**Example (fetch):**
```js
const form = new FormData();
form.append("topic", "e-commerce platform");
form.append("context_file", mdFileBlob, "context.md");
form.append("num_chats", "4");

const res = await fetch("http://localhost:8000/groups", {
  method: "POST",
  body: form,
});
```

#### Success response — `202 Accepted`

```json
{
  "group_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "status": "generating",
  "num_chats": 4
}
```

| Field | Type | Description |
|---|---|---|
| `group_id` | `string (UUID)` | Store this — used in all subsequent requests |
| `status` | `string` | Always `"generating"` on creation |
| `num_chats` | `integer` | Number of chats that will be created |

#### Error responses

| Status | Condition | Response body |
|---|---|---|
| `422` | `context_file` is not a `.md` file | `{ "detail": "context_file must be a .md file" }` |
| `422` | `context_file` exceeds 1 MB | `{ "detail": "context_file must be ≤ 1 MB" }` |
| `422` | Missing required field (`topic` or `context_file`) | `{ "detail": [{ "loc": [...], "msg": "Field required", "type": "missing" }] }` |

---

### `POST /groups/{group_id}/analyze`

> **Purpose**: Trigger AI analysis for a group that has finished generating. Call this only after polling confirms `status = "generated"`.

#### Request

- **Content-Type**: none (no body)

#### Path parameters

| Parameter | Type | Required | Description |
|---|---|---|---|
| `group_id` | `string (UUID)` | Yes | The group ID returned by `POST /groups` |

**Example (fetch):**
```js
const res = await fetch(`http://localhost:8000/groups/${groupId}/analyze`, {
  method: "POST",
});
```

#### Success response — `202 Accepted`

```json
{
  "group_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "status": "analyzing"
}
```

#### Error responses

| Status | Condition | Response body |
|---|---|---|
| `404` | `group_id` does not exist | `{ "detail": "Group not found" }` |
| `409` | Group status is not `"generated"` (e.g. still generating, already analyzing, already completed) | `{ "detail": "Group is not ready for analysis. Current status: generating" }` |

> **Important**: Always check that the group status is `"generated"` before calling this endpoint. Calling it while `status = "analyzing"` or `"completed"` returns 409.

---

### `GET /groups/{group_id}/chats`

> **Purpose**: Polling endpoint. Returns the group status and a summary of all chats (no message bodies — lightweight). Use this to drive loading states and progress indicators.

#### Path parameters

| Parameter | Type | Required | Description |
|---|---|---|---|
| `group_id` | `string (UUID)` | Yes | The group ID |

**Example (fetch):**
```js
const res = await fetch(`http://localhost:8000/groups/${groupId}/chats`);
const data = await res.json();
```

#### Success response — `200 OK`

```json
{
  "group_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "topic": "e-commerce platform",
  "status": "analyzing",
  "num_chats": 4,
  "created_at": "2024-01-15T10:30:00.123456+00:00",
  "chats": [
    {
      "chat_id": "chat_001",
      "case_type": "simple_resolved",
      "status": "analyzed",
      "analysis": {
        "chat_id": "chat_001",
        "intent": "request_refund",
        "satisfaction": "satisfied",
        "quality_score": 8,
        "agent_mistakes": [],
        "reasoning": "The agent resolved the issue promptly with no errors."
      }
    },
    {
      "chat_id": "chat_002",
      "case_type": "escalated",
      "status": "analyzing",
      "analysis": null
    },
    {
      "chat_id": "chat_003",
      "case_type": "unresolved",
      "status": "pending",
      "analysis": null
    }
  ]
}
```

**Response fields:**

| Field | Type | Description |
|---|---|---|
| `group_id` | `string (UUID)` | Group identifier |
| `topic` | `string` | Topic submitted at creation |
| `status` | `string` | Current group status (see Group status lifecycle above) |
| `num_chats` | `integer` | Total number of chats in this group |
| `created_at` | `string (ISO 8601)` | UTC timestamp of group creation |
| `chats` | `array` | List of chat summaries (may be empty while first chat is being generated) |
| `chats[].chat_id` | `string` | e.g. `"chat_001"`, `"chat_002"` — sequential |
| `chats[].case_type` | `string` | One of: `simple_resolved`, `complex_resolved`, `escalated`, `unresolved` |
| `chats[].status` | `string` | Per-chat status (see Per-chat status lifecycle above) |
| `chats[].analysis` | `object \| null` | Present only when `status = "analyzed"`, otherwise `null` |
| `chats[].analysis.chat_id` | `string` | Same as `chat_id` |
| `chats[].analysis.intent` | `string` | Primary customer intent, e.g. `"request_refund"`, `"password_reset"` |
| `chats[].analysis.satisfaction` | `string` | One of: `satisfied`, `neutral`, `unsatisfied` |
| `chats[].analysis.quality_score` | `integer` | Agent quality score 1–10 (10 = perfect) |
| `chats[].analysis.agent_mistakes` | `array` | List of mistake objects (empty array if none) |
| `chats[].analysis.agent_mistakes[].type` | `string` | `"tonal"` or `"logical"` |
| `chats[].analysis.agent_mistakes[].description` | `string` | Human-readable description of the mistake |
| `chats[].analysis.agent_mistakes[].message_index` | `integer` | 0-based index of the message where the mistake occurred |
| `chats[].analysis.reasoning` | `string` | AI explanation of why this satisfaction level and score were assigned |

#### Error responses

| Status | Condition | Response body |
|---|---|---|
| `404` | `group_id` does not exist | `{ "detail": "Group not found" }` |

#### Polling guidance

```js
// Poll every 3 seconds until all chats are done
async function pollUntilComplete(groupId) {
  while (true) {
    const res = await fetch(`http://localhost:8000/groups/${groupId}/chats`);
    const data = await res.json();

    // Check group-level terminal states
    if (["completed", "generation_failed", "analysis_failed"].includes(data.status)) {
      return data;
    }

    // Or check if all chats individually reached a terminal state
    const allDone = data.chats.every(c =>
      ["analyzed", "failed"].includes(c.status)
    );
    if (allDone && data.chats.length === data.num_chats) return data;

    await new Promise(r => setTimeout(r, 3000));
  }
}
```

---

### `GET /groups/{group_id}/chats/{chat_id}`

> **Purpose**: Full detail for a single chat including the complete message transcript and analysis. Call this when the user clicks into a specific chat.

#### Path parameters

| Parameter | Type | Required | Description |
|---|---|---|---|
| `group_id` | `string (UUID)` | Yes | The group ID |
| `chat_id` | `string` | Yes | The chat ID, e.g. `"chat_001"` |

**Example (fetch):**
```js
const res = await fetch(`http://localhost:8000/groups/${groupId}/chats/chat_001`);
const data = await res.json();
```

#### Success response — `200 OK`

```json
{
  "chat_id": "chat_001",
  "case_type": "simple_resolved",
  "status": "analyzed",
  "messages": [
    { "role": "customer", "text": "Hi, I placed an order and was charged twice." },
    { "role": "agent", "text": "I'm sorry to hear that. Let me look into your account." },
    { "role": "customer", "text": "My order number is #12345." },
    { "role": "agent", "text": "I can see the duplicate charge. I'll issue a refund within 3-5 business days." },
    { "role": "customer", "text": "Thank you for resolving this quickly." },
    { "role": "agent", "text": "You're welcome! Is there anything else I can help with?" }
  ],
  "scenario": {
    "domain": "payment_issues",
    "case_type": "simple_resolved",
    "has_hidden_dissatisfaction": false,
    "has_tonal_errors": false,
    "has_logical_errors": false
  },
  "analysis": {
    "chat_id": "chat_001",
    "intent": "report_duplicate_charge",
    "satisfaction": "satisfied",
    "quality_score": 9,
    "agent_mistakes": [],
    "reasoning": "The agent promptly identified and resolved the duplicate charge. Customer expressed genuine satisfaction."
  }
}
```

**Response fields:**

| Field | Type | Description |
|---|---|---|
| `chat_id` | `string` | Chat identifier |
| `case_type` | `string` | One of: `simple_resolved`, `complex_resolved`, `escalated`, `unresolved` |
| `status` | `string` | Per-chat status |
| `messages` | `array \| null` | Full conversation transcript. `null` if generation not yet complete |
| `messages[].role` | `string` | `"customer"` or `"agent"` |
| `messages[].text` | `string` | Message content. Messages always alternate, starting with `"customer"`. Minimum 6 messages per chat |
| `scenario` | `object \| null` | Generation parameters. `null` if not yet generated |
| `scenario.domain` | `string` | Placeholder domain used internally (e.g. `"payment_issues"`) — not meaningful for custom-topic groups |
| `scenario.case_type` | `string` | Same as top-level `case_type` |
| `scenario.has_hidden_dissatisfaction` | `boolean` | Whether this chat was generated with a hidden dissatisfaction flag |
| `scenario.has_tonal_errors` | `boolean` | Whether this chat was generated with intentional tonal agent errors |
| `scenario.has_logical_errors` | `boolean` | Whether this chat was generated with intentional logical agent errors |
| `analysis` | `object \| null` | Same structure as in the list endpoint. `null` if analysis not yet complete |

#### Error responses

| Status | Condition | Response body |
|---|---|---|
| `404` | `group_id` does not exist | `{ "detail": "Group not found" }` |
| `404` | `chat_id` does not exist within the group | `{ "detail": "Chat not found" }` |

---

## Enums reference

### `case_type`

| Value | Meaning |
|---|---|
| `simple_resolved` | Straightforward issue resolved in the conversation |
| `complex_resolved` | Multi-step issue that required more effort but was resolved |
| `escalated` | Issue was escalated to another team |
| `unresolved` | Issue was not resolved by end of chat |

### `satisfaction`

| Value | Meaning |
|---|---|
| `satisfied` | Customer is clearly happy with the outcome |
| `neutral` | Customer is neither happy nor unhappy |
| `unsatisfied` | Customer is unhappy — may include hidden dissatisfaction (polite language masking unresolved issue) |

### `agent_mistakes[].type`

| Value | Meaning |
|---|---|
| `tonal` | Style or tone issue (e.g. dismissive, too informal, robotic) |
| `logical` | Factual or procedural error (e.g. wrong information, skipped steps, contradiction) |

---

## Edge cases

- **`chats` array starts empty** during generation. The array grows as each chat is created. Always compare `chats.length` to `num_chats` to know total progress.
- **Individual chat `failed`** does not fail the whole group. A group can reach `completed` even if some chats have `status = "failed"`.
- **`scenario.domain` is always `"payment_issues"`** for custom-topic groups — this is a placeholder and should be ignored by the FE. The actual topic is in the group's `topic` field.
- **Analysis context** — the `scenario.has_hidden_dissatisfaction`, `has_tonal_errors`, `has_logical_errors` flags describe what the AI was *asked* to generate. Use them to cross-reference with the analysis results.
- **`POST /groups/{id}/analyze` on a `completed` group** returns 409. If re-analysis is needed a new group must be created.
- **Calling `POST /groups/{id}/analyze` twice concurrently** — the second call returns 409 because the status is already `"analyzing"`.
