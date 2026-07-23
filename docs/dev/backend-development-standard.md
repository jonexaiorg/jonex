# Jonex Platform Backend Development Standard

> This standard is the default creation standard for new backend sub-applications, new capabilities, and new features. The current codebase does not retain legacy compatibility constraints. Future development should follow this document first, rather than copying historical implementations.

## 1. General Principles

- **Explicit Tenant**: All business data must carry a valid `tenant_id`. Empty tenant, `default`, `default_tenant`, and `system` are not allowed.
- **Responsibility Layering**: Gateway only handles HTTP route aggregation; Sidecar only handles authentication, metering, rate limiting, and capability proxying; Capability Service carries the actual business logic.
- **Entity Unification**: Business entities use a unified mixin, repositories use a unified `BaseRepository`, and the service layer uniformly performs tenant validation and business rules.
- **Platform Shared vs Tenant Resources Separation**: Platform metadata can be shared; platform runtime data and all business data must be tenant-isolated.
- **No Tenant Injection in Body**: The tenant source for external APIs can only come from the authentication context, JWT parsing result, or Header. Ordinary business request bodies must not declare `tenant_id`; the `tenant_id` in Sidecar `/invoke` is only allowed for consistency validation.
- **LLM Egress Unified Convergence**: All LLM/Embedding calls must go through `llm-gateway:8787` and must not connect directly to upstream providers. When calling, inject metering context (tenant_id, scene, kb_id, doc_id, etc.) via `X-Jonex-*` request headers.
- **Thin Entry, Thick Service**: API routes only parse requests, extract tenants, and call services; complex logic must not be written in routes or gateway.
- **Async First**: Database, HTTP calls, and capability calls use async implementations by default.

## 2. Backend Call Chain

```text
Frontend
  -> API Gateway
    -> Sidecar
      -> Capability Service
        -> Service
          -> Repository
            -> PostgreSQL / Redis / External Engine
```

### API Gateway

- Responsible for `/api/v1/**` route aggregation, CORS, request id, logging, and exception handling.
- Does not directly implement business CRUD, does not assemble business data, and does not act as a fallback for capability permissions or tenancy.
- Calls to business capabilities should maintain readable route mappings and should not maintain legacy compatibility action tables.

### Sidecar

- Uniformly validates user JWT / API Key.
- Uniformly applies metering, rate limiting, and circuit breaker hooks.
- Uniformly issues internal service JWTs.
- The `tenant_id` in the JWT is the authoritative tenant of the authentication context; API Key only authenticates the caller, business tenants are not derived from the key text.
- `X-Tenant-ID` can supplement the business tenant for API Key requests; when both JWT and `X-Tenant-ID` are present, they must be consistent.
- Sidecar must forward the normalized `X-Tenant-ID` when proxying requests to downstream services.
- The tenant for `/invoke` is determined by the authentication context/JWT/Header; the `tenant_id` in the body is only allowed for consistency validation.
- Only non-business metering scenarios allow `tenant_id or "system"` as a platform-side fallback.

### Capability Service

- An independent business domain corresponds to one capability service, e.g., `knowledge_base`, `business_domain`, `platform`.
- Each capability service is organized internally by `api/`, `models/`, `services/`, `repository/`, `dtos/`.
- New business behavior is placed in the service layer; routes/capabilities only handle input/output orchestration.

## 3. Tenant Standard

Unified use of `jonex_core.common.tenant`:

- `extract_tenant_id(request)`: Extracts the normalized tenant from the request and validates it; test Bearer tokens are only allowed to be parsed in `dev` / `test` environments, `uat` / `prod` must reject them; formal user JWTs are parsed by Sidecar, which then propagates `X-Tenant-ID` downstream.
- `require_tenant(tenant_id)`: Enforces tenant validation at the service/repository layer.
- `TenantContext`: Passes the current tenant within the async context; it only serves as context carrier — business code should not directly depend on `TenantContext.set()` for validation.
- `tenant_scope(tenant_id)`: Used when an execution context needs to be bound; it calls `require_tenant()` first.

Forbidden business tenants:

```text
""
"default"
"default_tenant"
"system"
```

### External API Tenant Source

Ordinary business routes uniformly call `extract_tenant_id(request)`, with extraction priority:

1. `Authorization: Bearer jonex_test_{tenant_id}`, only for automated testing and local development in `dev` / `test` environments.
2. `X-Tenant-ID`.

Production security invariant: `uat` / `prod` environments must reject `jonex_test_*` tokens at the Gateway and Sidecar authentication entry points, not solely rely on the caller not using them. Related behavior must be covered by automated tests, including forged tenants, test token conflicts with Headers, and rejection paths in production environments.

Formal user JWTs are not re-parsed in ordinary routes; Sidecar is responsible for parsing the JWT, verifying `X-Tenant-ID` consistency, and forwarding the normalized tenant to downstream services via `X-Tenant-ID`.

API Key only represents the caller's identity, not the business tenant. When using API Key to call tenant-isolated interfaces, a valid `X-Tenant-ID` must be carried additionally.

New interfaces must not declare a business `tenant_id` field in the request body. The sole exception is the `tenant_id` field in the Sidecar `/invoke` contract, which is only used for consistency validation against the authentication context/Header and serves as no new tenant source. Backend interfaces requiring cross-tenant management should be explicitly named as platform management interfaces and perform permission validation in the service.

The auth bootstrap endpoint is the sole exception: `/auth/login` must not require the caller to have a tenant context beforehand. The login request body still only contains username and password and must not include `tenant_id`. During login, the tenant can be explicitly selected via `X-Tenant-ID`; when no tenant is carried, the auth service may only automatically determine the tenant if a single active, non-deleted user with the same username is found in the system. If multiple active tenant accounts exist for the same username, a clear error such as "Please select a tenant to log in" must be returned, guiding the frontend user to select a tenant and retry. Auth endpoints that depend on an already logged-in identity, such as `/auth/refresh` and `/auth/login-ticket`, must still carry a resolvable tenant.

### Service Layer Tenant Rules

```python
from jonex_core.common.tenant import require_tenant


class WidgetService:
    def __init__(self, repository):
        self.repository = repository

    async def list_widgets(self, tenant_id: str, page: int, page_size: int):
        tenant_id = require_tenant(tenant_id)
        return await self.repository.list_all(
            tenant_id=tenant_id,
            offset=(page - 1) * page_size,
            limit=page_size,
        )
```

### Repository Layer Tenant Rules

- Tenant resource calls for `get_by_id/list_all/count/update/delete_soft` must pass a valid tenant, or bind `TenantContext` in advance.
- Shared resource calls use `*_shared` methods, e.g., `list_all_shared()`, `get_required_shared()`.
- Silently filling in `default`, `system`, or empty strings inside the repository is not allowed.

## 4. Entity Standard

Unified use of `jonex_core.common.entity`:

```python
from sqlalchemy import Column, String
from jonex_core.common.database import Base
from jonex_core.common.entity import AuditMixin, SoftDeleteMixin, TenantMixin, TimestampMixin


class Widget(Base, TenantMixin, TimestampMixin, SoftDeleteMixin, AuditMixin):
    __tablename__ = "widgets"
    __table_args__ = {"schema": "my_capability"}

    id = Column(String(64), primary_key=True)
    name = Column(String(128), nullable=False)
```

### Business Entities

Business entities inherit by default:

- `TenantMixin`
- `TimestampMixin`
- `SoftDeleteMixin`
- `AuditMixin` when necessary

Scope of application:

- `knowledge_base`
- `business_domain`
- New business capabilities
- Business records requiring persistence in new domain capabilities

### Platform Shared Entities

The following entities are platform shared metadata and do not carry `tenant_id`:

- `Application`
- `ApplicationRoute`
- `Menu`
- `Permission`
- `SystemConfig`

Access them using the repository's `*_shared` methods.

### Platform Tenant Entities

The following platform runtime data must carry `tenant_id`:

- `User`
- `Role`
- `UserRole`
- `RolePermission`
- `AuditLog`
- `TaskSchedule`
- `LoginTicket`

## 5. Repository Standard

Unified inheritance from `jonex_core.common.repository.BaseRepository`:

```python
from sqlalchemy import select

from jonex_core.common.repository import BaseRepository
from jonex_core.common.tenant import require_tenant
from capabilities.my_capability.models.widget import Widget


class WidgetRepository(BaseRepository[Widget]):
    model = Widget

    async def get_by_name(self, tenant_id: str, name: str) -> Widget | None:
        tenant_id = require_tenant(tenant_id)
        result = await self.session.execute(
            select(Widget).where(
                Widget.tenant_id == tenant_id,
                Widget.name == name,
                Widget.is_deleted == 0,
            )
        )
        return result.scalar_one_or_none()
```

Custom queries must satisfy:

- Tenant entity queries must include `model.tenant_id == require_tenant(tenant_id)`.
- Soft-deleted entity queries must include `is_deleted == 0`.
- Pagination uniformly uses `page/page_size` as API parameters; the repository receives `offset/limit`.
- Use `flush()` after create/update to let the service control transaction boundaries.

## 6. Service Standard

Service is the sole owner of business rules.

Must do:

- Call `require_tenant()`.
- Validate resource ownership.
- Combine multiple repositories.
- Call atomic/domain capability clients.
- Convert low-level exceptions to business exceptions.

Should not do:

- Read FastAPI `Request`.
- Directly parse Headers/JWT.
- Return unfiltered ORM internal objects to external APIs.

Recommended form:

```python
class WidgetService:
    def __init__(self, repository: WidgetRepository):
        self.repository = repository

    async def create_widget(self, tenant_id: str, data: WidgetCreate, user_id: str | None = None):
        tenant_id = require_tenant(tenant_id)
        widget = Widget(
            id=generate_id(),
            tenant_id=tenant_id,
            name=data.name,
            created_by=user_id,
        )
        return await self.repository.create(widget)
```

## 7. API Route Standard

The Route layer only handles request parsing, tenant extraction, dependency injection, and response wrapping.

```python
from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from jonex_core.common.database import get_db
from jonex_core.common.response import success_response
from jonex_core.common.tenant import extract_tenant_id

router = APIRouter(prefix="/api/v1/widgets", tags=["widgets"])


@router.get("")
async def list_widgets(
    request: Request,
    page: int = 1,
    page_size: int = 20,
    db: AsyncSession = Depends(get_db),
):
    tenant_id = extract_tenant_id(request)
    service = build_widget_service(db)
    result = await service.list_widgets(tenant_id, page, page_size)
    return success_response(data=result)
```

Requirements:

- External interfaces must call `extract_tenant_id(request)` from `Request`.
- `/auth/login` is an auth bootstrap endpoint; it may read the optional `X-Tenant-ID` and delegate tenant resolution to the auth service, without calling `extract_tenant_id(request)` for mandatory interception.
- Request DTOs must not include `tenant_id`.
- Route naming uses resource names, not compatibility-based action dispatching.
- Do not manually commit transactions in routes for `POST/PUT/PATCH/DELETE`; use `get_db()` session management.

## 8. Exceptions and Error Codes Standard

Business code must throw `JonexException` subclasses from `jonex_core/common/exceptions.py`. **Throwing `HTTPException` or bare `ValueError` is prohibited.** The global exception handler (`jonex_core/common/exception_handler.py`) is registered in Sidecar and API Gateway, automatically mapping exceptions to a unified `StandardResponse` JSON. When creating a new FastAPI application, call `register_exception_handlers(app)` to mount all handlers.

Error code segments:

| Segment | Category | Exception Classes |
|---|---|---|
| 1xxx | General | `InternalError`, `InvalidParameterError`, `ResourceNotFoundError`, `ResourceConflictError`, `OperationNotSupportedError` |
| 2xxx | Capability | `CapabilityNotFoundError`, `CapabilityInvokeError`, `CapabilityTimeoutError`, `CapabilityValidationError`, `CapabilityIdFormatError` |
| 3xxx | Auth & Authorization | `MissingApiKeyError`, `InvalidApiKeyError`, `TokenExpiredError`, `InternalAuthError`, `TenantIsolationError`, `PermissionDeniedError`, `RateLimitExceededError` |
| 4xxx | Data | `DatabaseError`, `CacheError`, `DataIntegrityError` |
| 5xxx | Service Dependency | `ServiceUnavailableError`, `ServiceDiscoveryError`, `UpstreamServiceError`, `ServiceTimeoutError` |

Intermediate base classes `CapabilityError`, `AuthError`, `DataError`, `ServiceError` are used for categorization; business code should directly throw the concrete subclasses from the table above.

Throw example:

```python
from jonex_core.common.exceptions import ResourceNotFoundError, ResourceConflictError

if not resource:
    raise ResourceNotFoundError(
        message=f"Resource not found: {resource_id}",
        details={"resource_id": resource_id},
    )

if resource.status != expected_status:
    raise ResourceConflictError(
        message=f"Incorrect resource status, current status: {resource.status}",
        details={"current_status": resource.status},
    )
```

Requirements:

- The service layer is responsible for converting low-level exceptions (ORM, HTTP, external engine) into corresponding `JonexException` subclasses.
- Do not manually write `try/except` blocks in routes/gateway to assemble HTTP responses; leave it to the global handler.
- Tenant validation failures are uniformly thrown as `TenantIsolationError` by `require_tenant()`.
- Responses uniformly use `success_response` / `error_response` (`jonex_core/common/response.py`).

## 9. Capability Contract Standard

Capability ID format:

```text
{kind}.{name}.v{major}
```

Examples:

- `business.knowledge_base.v1`
- `business.business_domain.v1`
- `domain.rag.text.v1`
- `atomic.rag.lightrag.v1`

### Business Capability

- Corresponds to a user-perceptible business domain.
- Has its own database schema.
- Can be invoked by Gateway/Sidecar.
- Can call domain/atomic capabilities.

### Domain Capability

- Responsible for modal-level or domain-level orchestration.
- Does not directly carry sub-application CRUD.
- Can combine multiple atomic capabilities.

### Atomic Capability

- Encapsulates a single technical component, e.g., LLM, Vector, Audio, RAG.
- Provides stable client and capability invoke contracts to consumers.
- Business code must not directly depend on specific external engine SDKs; it must go through atomic clients.

## 10. Database and Migration Standard

- Each capability uses its own PostgreSQL schema.
- Table names use plural resource names or existing domain names, avoiding ambiguous abbreviations.
- Business tables must include `tenant_id` with an index.
- Regular business tables should include `created_at`, `updated_at`, `is_deleted`.
- SQL migrations are placed in `deploy/postgres/migrations/` and executed in numerical order.
- ORM model fields must be consistent with SQL migrations.
- Do not use `Base.metadata.create_all()` as a production table creation strategy.

Recommended fields:

```sql
id          varchar(64) primary key,
tenant_id   varchar(64) not null,
created_at  timestamp not null,
updated_at  timestamp not null,
is_deleted  smallint not null default 0
```

Recommended indexes:

```sql
create index idx_widgets_tenant_id on my_capability.widgets(tenant_id);
create index idx_widgets_tenant_deleted on my_capability.widgets(tenant_id, is_deleted);
```

## 11. New Sub-Application / New Capability Creation Checklist

Directory template:

```text
capabilities/my_capability/
  api/
    widgets.py
  models/
    widget.py
  repository/
    widget_repository.py
  services/
    widget_service.py
  dtos/
    widget.py
  capability.py
```

Implementation steps:

1. Define the capability ID and responsibility boundary.
2. Create a new PostgreSQL schema and migration SQL.
3. Define the ORM model; business tables inherit `TenantMixin`.
4. Define Pydantic v1 request/response DTOs; request bodies must not include `tenant_id`.
5. Define the repository, inheriting `BaseRepository`.
6. Define the service, calling `require_tenant()` at the entry point.
7. Define the API route, calling `extract_tenant_id(request)` in the route.
8. Register metadata and invoke actions in the capability.
9. Add thin route mappings in Sidecar/Gateway.
10. Add unit tests covering at least: missing tenant, default tenant, cross-tenant access, and normal CRUD.

## 12. Testing Standard

New backend features must at least cover:

- Rejection when `tenant_id` is empty.
- Rejection when `tenant_id` is `default/default_tenant/system`.
- Tenant A cannot read/modify/delete Tenant B's data.
- Shared platform resources can only be accessed via `*_shared` repository methods.
- Routes must not accept `tenant_id` in the body.
- Rejection when the body `tenant_id` in capability invoke does not match the authentication context.

Common validation commands:

```bash
python3 -m compileall api_gateway jonex_core capabilities
uv run pytest tests/unit/test_common.py tests/unit/test_imports.py tests/unit/test_rag.py
```

## 13. Prohibited Items

- Prohibited: Using `tenant_id or "default"`, `tenant_id or "system"` for business data.
- Prohibited: External APIs receiving business `tenant_id` from the body.
- Prohibited: Gateway implementing business rules.
- Prohibited: Routes directly writing complex queries or cross-table orchestration.
- Prohibited: Business/domain code directly calling LightRAG, Milvus, LLM SDK, or other specific underlying engines.
- Prohibited: New code using synchronous database sessions.
- Prohibited: Bypassing `llm-gateway` to connect directly to upstream LLM/Embedding APIs.
- Prohibited: Introducing action string dispatching for backward compatibility with legacy interfaces.

## 14. Code Review Checklist

Before submitting backend changes, confirm each item:

- Is the tenant source only from Header/JWT/request context?
- Do all business entities have `tenant_id`?
- Are platform shared entities free from mistakenly added `tenant_id`?
- Do repository queries include automatic or explicit tenant conditions?
- Is the service the sole owner of business rules?
- Are `JonexException` subclasses thrown instead of `HTTPException` / bare `ValueError`?
- Are Gateway/Sidecar kept thin?
- Are DTOs compatible with Pydantic v1?
- Are migration SQL, ORM models, and tests updated together?
