# Google Cloud implementation

Fynura uses Google Cloud for application hosting, evidence storage, authentication and agentic research.

| Service | Role |
|---|---|
| Cloud Run | FastAPI backend, frontend and application APIs |
| Vertex AI | Gemini 3.7 Flash research inference |
| Google ADK and Google GenAI SDK | Research orchestration and conditional source review |
| Firestore | Evidence snapshots and application sessions |
| Cloud Scheduler | Authenticated periodic evidence-refresh requests |
| Firebase Authentication | Google sign-in and verified sessions |
| Secret Manager | Runtime configuration references |
| Cloud Build and Artifact Registry | Container build and deployment |
| Cloud Logging | Service and request logging |

See the [architecture explanation](ARCHITECTURE_EXPLANATION.md) for data flow and the [repository README](../../README.md) for configuration and deployment instructions.
