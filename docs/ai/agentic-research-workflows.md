# Agentic research workflows

Prescripta v0.9.3 provides two bounded templates: evidence review and study-design drafting. An agent run stores a template version, tenant/study scope, source allowlist, tool allowlist, explicit step/tool/token/cost/wall-time budgets, hashed inputs/outputs and an audit trail.

The state machine is `queued → running → waiting_human → completed/rejected`, with `abstained` and `cancelled` terminal paths. Proposal tools always stop at `waiting_human`. Human approval means **approved as draft**, never clinical, causal, terminology or protocol approval.

Shell, filesystem, raw HTTP, raw SQL, database mutation, recursive agent spawning, query execution and protocol approval are denied. Retrieved literature and tool output are untrusted data; injection markers are recorded without expanding authority. Cancellation clears the proposal. Cross-tenant studies and sources fail closed.
