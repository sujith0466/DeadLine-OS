# DEADLINEOS BUSINESS OS — B8 SECURITY HARDENING CONTRACT
**Document ID:** `B8-DOC-005`
**Status:** `BINDING SPECIFICATION`
**Classification:** Security Engineering

---

## 1. Multi-Tenant Penetration Hardening

1. **Universal Workspace Middleware:** Every business route must be protected by `@require_workspace` or `@require_auth`.
2. **5-Tier RBAC:** `VIEWER` and `ACCOUNTANT` roles are restricted from unauthorized creation/modification operations.
3. **IDOR Defense:** Cross-workspace entity or partner references are rejected with HTTP 404 or HTTP 403.
