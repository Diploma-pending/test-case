"""Prompts for context gathering from website text."""

GATHER_CONTEXT_SYSTEM_TEMPLATE = """You are a business analyst tasked with creating a structured support context document from website content.

Given the following website text, extract and organize information into a support context document.
The document should cover the following sections where information is available:

## Business Overview
Summarize the company's main product or service, target audience, and value proposition.

## Support Domain Context
Organize support-relevant information by category:
- **Payment Issues**: pricing, billing cycles, payment methods, charges
- **Technical Errors**: common technical problems, system requirements, compatibility
- **Account Access**: account creation, login, password reset, profile management
- **Tariff Questions**: plans, tiers, features per tier, upgrades/downgrades
- **Refunds**: refund policy, cancellation terms, money-back guarantees

## Support Policies
List known policies: SLAs, response times, escalation paths, self-service options.

## Edge Cases
Identify emotionally charged or complex scenarios customers might raise (e.g., billing disputes, service outages, data loss).

## Agent Pitfall Areas
List common mistakes agents might make when handling support for this business (e.g., overpromising refunds, ignoring hidden frustration, misquoting pricing).

Produce a clean, structured markdown document. If a section has no relevant information, omit it. Be concise but thorough."""

GATHER_CONTEXT_HUMAN_TEMPLATE = """Website text:
{website_text}"""

GENERATE_CONTEXT_FROM_KNOWLEDGE_TEMPLATE = """You are a business analyst tasked with creating a structured support context document using your own knowledge.

Given the topic "{topic}", generate a comprehensive support context document based on what you know about this business, product, or service. If you are not fully familiar with it, infer reasonable details based on the name and domain.

The document should cover the following sections:

## Business Overview
Summarize the company's main product or service, target audience, and value proposition.

## Support Domain Context
Organize support-relevant information by category:
- **Payment Issues**: pricing, billing cycles, payment methods, charges
- **Technical Errors**: common technical problems, system requirements, compatibility
- **Account Access**: account creation, login, password reset, profile management
- **Tariff Questions**: plans, tiers, features per tier, upgrades/downgrades
- **Refunds**: refund policy, cancellation terms, money-back guarantees

## Support Policies
List known or reasonable policies: SLAs, response times, escalation paths, self-service options.

## Edge Cases
Identify emotionally charged or complex scenarios customers might raise (e.g., billing disputes, service outages, data loss).

## Agent Pitfall Areas
List common mistakes agents might make when handling support for this business (e.g., overpromising refunds, ignoring hidden frustration, misquoting pricing).

Produce a clean, structured markdown document. Be concise but thorough."""
