# DEADLINEOS BUSINESS OS — STORAGE & DEPLOYMENT ARCHITECTURE
**Document ID:** `B0-DOC-011`
**Status:** `B0 DESIGN DECISION`
**Classification:** Infrastructure & Cloud Architecture

---

## 1. Document Storage Strategy
### 1.1 The Ephemeral Disk Reality on Render
- Render web service containers are ephemeral; files saved to `/tmp` or local container disks are destroyed on container restarts, deployments, or scaling events.
- **Architectural Decision:** All business document uploads (PDF invoices, receipt photos, audio recordings) MUST be stored in cloud object storage via an abstract storage interface.

### 1.2 Storage Abstraction (`StorageService`)
```python
class StorageService(abc.ABC):
    @abc.abstractmethod
    def upload_file(self, workspace_id: str, file_bytes: bytes, filename: str, mime_type: str) -> str:
        """Returns storage URI (e.g. s3://bucket/ws_id/hash.pdf or supabase://...)."""
        pass

    @abc.abstractmethod
    def generate_signed_url(self, storage_uri: str, expiry_seconds: int = 900) -> str:
        """Returns short-lived presigned URL for secure browser viewing."""
        pass
```
- **Primary Driver:** **Supabase Storage** (already integrated via Supabase credentials) / S3-compatible bucket.
- **Local Dev / Testing Driver:** Mock file storage writing to deterministic temporary test fixtures.

---

## 2. Server Concurrency & Worker Evolution
- **Current Production Setup:** Gunicorn with `eventlet` worker (`render.yaml:8`).
- **Discovery Note from Pass 1:** Eventlet is currently in maintenance mode and generates deprecation warnings on Python 3.13.
- **Strategic Evolution Plan:**
  - In **Phase B0/B1 MVP:** Maintain stable Gunicorn configuration to avoid disruptive deployment side effects while Personal OS is live.
  - In **Phase B8 (Production Excellence):** Transition from Eventlet to **Gunicorn + Uvicorn workers (ASGI)** for native Python async I/O, WebSockets, and high-throughput document streaming.

---

## 3. Production Resource Profile & Limits
- **PostgreSQL Connection Pooling:** Neon Serverless PostgreSQL with pgBouncer pooling (`sslmode=require`).
- **File Upload Limits:** Max 15 MB per document; accepted formats: `application/pdf`, `image/jpeg`, `image/png`, `image/webp`, `audio/webm`, `audio/mp4`.
- **Worker Timeouts:** Standard HTTP request timeout: 30s. Async document OCR parsing exceeding 10s is handed off to background worker tasks with polling status.
