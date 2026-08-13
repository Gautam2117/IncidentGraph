# Contributing to IncidentGraph

Thank you for your interest in contributing to IncidentGraph!

## Development & Quality Standards

1. **Feature Freeze & Bounded Scope**: IncidentGraph is a production-style reliability demonstration platform. All PRs must maintain backward compatibility and preserve existing evidence baselines.
2. **Ground-Truth Isolation**: Never expose scenario ground-truth metadata to model contexts. All evaluation scenarios must use `ScenarioDefinition.get_safe_metadata()` to strip root-cause answers before passing metadata to agents.
3. **No Arbitrary Execution Tools**: Tools must use Pydantic models with strict validation. Do not add raw shell execution or raw SQL query endpoints.
4. **Test & Security Discipline**: Every PR must pass:
   - `pytest services/control-plane/tests --cov=app` (Minimum 80% coverage threshold)
   - `bandit -r services/control-plane/app` (0 High / 0 Medium issues)
   - `pip-audit` & `npm audit` (0 vulnerabilities)
   - Playwright E2E browser suite (`npx playwright test` in `apps/console`)

## Local Setup

```bash
cp .env.example .env
DOCKER_HOST=unix:///$HOME/.colima/default/docker.sock docker-compose up -d --build
PYTHONPATH=services/control-plane:. ./.venv/bin/pytest services/control-plane/tests
```
