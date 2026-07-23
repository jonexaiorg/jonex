# Local Frontend with Remote Backend

> This page serves as a compatibility entry point only. For authoritative steps, refer to [Local Full-Stack Debugging Guide](local-fullstack-debugging-guide.md#frontend-with-remote-backend).

**Scenario:** Frontend and Dev Gateway run on the local machine, while the API Gateway and backend services run on a remote server.

**Do not** use `dev-backend-server` or `dev-backend-*` commands to attempt a "server infrastructure + local backend" setup. These scripts override dependency addresses and start local infrastructure.

## Quick Steps

1. In `frontends/dev-gateway/`, copy `.env.example` to `.env`.
2. Set `API_TARGET` to the server's API Gateway address, e.g. `http://your-server:8000`.
3. Start `pnpm run dev:gateway` and the required frontend applications.
4. Access via `http://localhost:8080`.

**Security:** Do not expose development backends without HTTPS and proper authentication over public networks, and never commit server credentials in configuration files.
