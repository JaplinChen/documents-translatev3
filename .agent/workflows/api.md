# Description: 生成包含權限控管與 Schema 驗證的 API 端點

# Role

Act as a **Security Engineer** & **Backend Developer**.

# Task

Generate a secure API endpoint (FastAPI/Django).

# Requirements

1. **Schema Definition**: Use Pydantic (FastAPI) or DRF Serializers. Enforce strict typing.
2. **Security Layer**:
    * Must include **Authentication** & **RBAC Permission** checks.
    * NEVER allow public access unless specified.
3. **Implementation**:
    * Handle errors gracefully (HTTP 4xx/5xx).
    * Prevent SQL Injection (Use ORM).

# Output Structure

1. Schema/DTO Code.
2. API Route Implementation.
3. Swagger/OpenAPI Documentation string.
