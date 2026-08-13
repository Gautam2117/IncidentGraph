# Security Policy & Vulnerability Disclosure

IncidentGraph prioritizes security across tool execution, prompt handling, authentication, and secret management.

## Security Model & Safeguards

1. **Tool Execution Bounding**: All remediation actions are strictly typed via Pydantic schemas. Arbitrary shell, SQL, or filesystem execution is prohibited.
2. **Human-in-the-Loop Safeguards**: Remediation actions set `requires_human_approval = True` and require authenticated human approval (`APPROVED` decision) before execution.
3. **Secret Hygiene**: Real API keys, credentials, and access tokens are strictly excluded from code, commits, and logs. `.env` and local credentials are ignored by Git.

## Reporting a Vulnerability

If you discover a potential security vulnerability or secret exposure in IncidentGraph:

- **Do NOT create a public GitHub issue.**
- Email details directly to `security@incidentgraph.local` or contact repository maintainers privately.
- Provide a clear reproduction guide or proof-of-concept description.
- Maintainers will acknowledge reports within 48 hours and coordinate a fix.
