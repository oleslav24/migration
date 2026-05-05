# Agent Threat Lens

This project evaluates agents through a zero-trust and ATLAS-style threat lens. The goal is not to assume that agents are malicious, but to make failures observable and bounded.

## Threats and Controls

| Threat | Example | Control |
|---|---|---|
| Prompt injection | Article text or comments instruct the agent to ignore project rules | Treat corpus text as data, never as instructions |
| Context poisoning | Malformed CSV, PDF, DOCX, or metadata changes downstream behavior | Validate schemas, log parser errors, preserve raw source references |
| Tool misuse | Agent runs broad commands outside the task scope | Exact action allowlist and forbidden-action checks |
| Data exfiltration | Agent sends private corpus text or local files to external APIs | External access denied unless explicitly declared |
| Hallucinated evidence | Agent reports claims not supported by retrieved snippets or data | Require evidence IDs, file paths, or audit references |
| Supply chain risk | Downloaded PDFs or dependencies are unsafe or unauthorized | Open-access checks, MIME validation, dependency review |
| Silent failure | Agent produces output without validation | Quality gates, stop conditions, and audit trail |
| Overwriting human work | Agent edits or deletes files outside its task | Declared write paths and git status review |

## Required Controls

Every agent must define:

- task contract;
- allowed context;
- allowed actions;
- forbidden actions;
- quality gates;
- stop conditions;
- audit trail;
- feedback sensors;
- access model;
- threat lens;
- metrics.

## Research-Specific Risks

This repository supports empirical migration research. Additional risks include:

- overinterpreting social media traces as representative of migrant populations;
- presenting automated labels as ground truth;
- losing provenance between raw comments, derived features, and exported summaries;
- mixing legally obtained open-access literature with restricted material;
- producing fluent but unsupported theoretical claims.

Agent outputs must therefore be treated as intermediate research artifacts that require human review.

