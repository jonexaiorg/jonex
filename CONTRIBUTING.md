# Contributing to Jonex Platform

Thank you for helping improve Jonex Platform. Contributions to code, tests, documentation, examples, and issue triage are welcome.

By participating, you agree to follow `CODE_OF_CONDUCT.md`.

## Before you start

- Search existing issues and pull requests before opening a new one.
- Use the repository's issue templates for bug reports and feature requests when available.
- Use a focused issue to discuss substantial behavior or architecture changes first.
- Never include credentials, private data, internal endpoints, or production logs in issues or commits.
- Follow the architecture and development guidance in `jonex-platform-architecture.md`, `backend-development-standard.md`, and `frontend-development-standard.md`.

## Development prerequisites

- Python 3.12.13 or a compatible Python 3.12 environment
- `uv` for Python dependency management
- Node.js 20.18 or newer
- pnpm 9 or newer
- Docker with Docker Compose for infrastructure and full-stack development

Copy only the public example files when creating local configuration. Replace every `CHANGE_ME` value locally and do not commit generated `.env` files.

## Backend setup and checks

```bash
uv sync --dev
uv run pytest tests/unit
```

Run the smallest relevant test set while developing, then run the full unit suite before submitting a pull request.

## Frontend setup and checks

```bash
cd frontends
pnpm install --frozen-lockfile
pnpm run typecheck
pnpm run i18n:check
pnpm run build
```

Use the workspace scripts in `frontends/package.json`; do not add npm or Yarn lock files.

## Pull requests

- Keep each pull request focused on one problem.
- Explain the user-visible behavior and important design decisions.
- Add or update tests for changed behavior.
- Update public documentation when configuration, APIs, or deployment behavior changes.
- Mention known limitations and follow-up work explicitly.
- Confirm that no secret or environment-specific value is present in the diff.

Commit messages should be concise and use an imperative summary. Conventional Commit prefixes such as `feat:`, `fix:`, `docs:`, `test:`, and `chore:` are encouraged.

## Reporting security issues

Do not report vulnerabilities in public issues. Follow `SECURITY.md` and use GitHub Private Vulnerability Reporting when it is enabled for the repository; otherwise use the private contact documented there.

## License

By submitting a contribution, you agree that it is licensed under the Apache License 2.0 used by this repository.
