# DeadlineOS Known Limitations - v1.0.0

## 1. AI Rate Limiting
- **Gemini Dependency**: Because DeadlineOS relies heavily on the Gemini API for intelligence features (Vision, Docs, Command Center), users may occasionally experience rate-limiting if issuing rapid, consecutive commands. The system is designed to fallback gracefully to deterministic algorithms or provide UI alerts when quotas are exceeded.

## 2. File Upload Restrictions
- **16MB Cap**: Document and Vision intelligence file uploads are hard-capped at 16MB per file to prevent bandwidth exhaustion and API payload overflow. Large PDFs must be split prior to upload.

## 3. Real-Time WebSocket Scale
- **SocketIO Limitations**: Live real-time updates for telemetry events are supported, but massive horizontal scaling of the Flask-SocketIO eventlet server may require an external message broker (e.g., Redis) if concurrent connections exceed ~10,000 users.

## 4. Third-Party Integrations
- Currently, calendar integrations (Google Calendar, Outlook) are emulated internally. Native OAuth calendar ingestion is slated for v1.1.0.
