# Security Policy

## Supported versions

| Version | Security support |
|---|---|
| Current default branch | Supported |
| Latest tagged release | Supported |
| Older releases and development snapshots | Not supported unless a release notice states otherwise |

## Reporting a vulnerability

Please do not open a public issue for a suspected vulnerability.

Use GitHub Private Vulnerability Reporting from the repository's **Security** tab. If that feature is unavailable, email [jonex@yzg.ai](mailto:jonex@yzg.ai) with the subject prefix `[SECURITY]` and ask for a secure channel before sending exploit details. Include:

- Affected version or commit
- A clear description of the impact
- Reproduction steps or a minimal proof of concept
- Relevant configuration and deployment assumptions, with all secrets removed
- Any suggested mitigation

Do not send credentials, personal data, production logs, or exploit details through a public issue or discussion. Redact secrets from every reproduction artifact.

Maintainers aim to acknowledge a complete report within three business days, assess severity, coordinate a fix, and publish an advisory when appropriate. Remediation timelines depend on impact and reproduction complexity; reporters will receive status updates through the private channel.

## Security expectations for deployments

- Replace every `CHANGE_ME` value before starting a shared or production deployment.
- Change or remove the `admin / admin123` local demo account before binding services to a non-loopback interface or sharing the deployment.
- Keep `.env` files outside version control and restrict filesystem access.
- Use independent, randomly generated values for JWT, Sidecar, LightRAG, database, Neo4j, MinIO, and upstream-provider credentials.
- Reject development test tokens such as `jonex_test_{tenant_id}` in `uat` and `prod`; this must be enforced and tested in code, not only documented as an operational convention.
- Expose only the frontend gateway publicly; keep Sidecar and capability services on trusted networks.
- Use HTTPS at the public edge.
- Disable debug endpoints, development CORS origins, mock data, and verbose error responses in production.
- Review experimental adapters and disabled-by-default extension points before enabling them.
- Review dependency licenses and known vulnerabilities for every source archive, container image, and binary release.
- Rotate any credential that may have appeared in logs, commits, screenshots, or support material.
