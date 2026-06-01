# **Oraklet - Enterprise-Grade Data & AI Processing Platform**

**A typed, modular, fault-tolerant FastAPI system with fully orchestrated LLM pipeline, advanced data ingestion, schema/semantic drift detection, caching, circuit breakers, and comprehensice test coverage.**

---

## **Overview**
Oraklet is a production-grade backend system built on top of FastAPI, designed to ingest datasets, analyze them, and answer natural-language questions using a fully typed, multi-step LLM pipeline. It extends the original KK2 assignment into a **full enterprise-level architecture**, including:
- A robust data ingestion pipeline (CSV + Parquet)
- Schema drift detection
- Semenatic drift detection
- Column lineage tracking
- Canonical schema normalization
- Typed Runnable chain for AI reasoning 
- Circuit breaker protection
- Retry policy with exponential backoff
- ETag-based caching
- Global rate anomaly detection
- Security middleware
- Structured logging
- Comprehensive test suite (70+ tests)
- Strict type checking (mypy strict mode)

The system is engineered for reliability, observability, and extensibility, following real-world backend architecture patterns.

---

## High-Leve Architecture
                          ┌────────────────────────────┐
                          │        FastAPI App         │
                          │   (main.py + routers)      │
                          └──────────────┬─────────────┘
                                         │
                                         ▼
                    ┌────────────────────────────────────────┐
                    │              Middleware                │
                    │  - Security headers                    │
                    │  - Request ID injection                │
                    │  - GZip compression                    │
                    │  - Global rate anomaly detection       │
                    │  - Circuit breaker middleware          │
                    └───────────────────┬────────────────────┘
                                        │
                                        ▼
                   ┌──────────────────────────────────────────┐
                   │               API Layer                  │
                   │   /data/upload                           │
                   │   /data/stats                            │
                   │   /data/download/{csv,parquet}           │
                   │   /ai/ask                                │
                   │   /ai/ask/stream                         │
                   └───────────────────┬──────────────────────┘
                                       │
                                       ▼
              ┌────────────────────────────────────────────────────┐
              │                    Data Layer                      │
              │  DataService:                                      │
              │   - CSV validator                                  │
              │   - Parquet validator                              │
              │   - Schema fingerprinting                          │
              │   - Semantic fingerprinting                        │
              │   - Column lineage                                 │
              │   - Stats caching (TTL)                            │
              └──────────────────────┬─────────────────────────────┘
                                     │
                                     ▼
         ┌───────────────────────────────────────────────────────┐                                                        |
         │                     AI Pipelin (Runnable)                                              │
         │   PromptBuilder → LLMRunner → ResponseParser                                         │
         │
         │   - Typed Pydantic models                                  │
         │   - Circu it    breaker                                        │
         │   - Retry policy (exponential backoff + jitter)            │
         │   - Timeout protection                                     
         │   - Fallback strategy                                                │
         │   - Structured logging + metrics                                                  │
         └────────────────────────────────────────────────────────────┘

---

## **Feature**

### Typed Runnable Chain
Each step is a `PipelineStep[Input, Output]:`
 PromptBuilder
 - LLMRunner
 - ResponseParser

The chain is orchestrated by `PipelineOrchestrator`, which provides:
- Type validation between steps
- Structured logging
- Metrics
- Error wrapping
- Trace IDs and span IDs

---

## **Advanced Data Ingestion**
### CSV ingestion includes:
- Delimiter detection
- Unicode sanitization
- Dangerous character strpping
- Excel-formula injection protection
- Mixed-type detection
- Memory limits
- Row/column limits
- Null-column limits
- Null-column detection
- Numeric coercion
- Boolean coercion
- Date parsing 
- ID-column detection
- Canonical column normalization

### Parquet ingestion includes:
- Magic byte validation
- Arrow schema validation
- Mixed int/float detection
- Nested list consistency checks
- Mixed numeric/String detection
- Nullability enforcement
- Column normalization
- Schema fingerprinting

---

## **Schema & Semantic Drift Detection**
The system tracks:
- Canonical schema fingerprint
- Semantic fingerprint per column
- Column lineage (dtype history)

Drift can be: 
- **Blocking** (default)
- **Non-blocking** (configurable)

---

## **Enterprise Middleware Stack**
- Request ID injection
- Security headers
- GZip compression
- Global rate anomaly detection
- Circuit breaker middleware
- SlowAPI rate limiting
- Structured logging

---

## **AI Pipeline Reliability**
- Circuit breaker (OPEN -> HALF_OPEN -> CLOSED)
- Retry policy with exponential backoff
- Timeout protection
- Fallback strategy
- ETag-based caching
- Cache invalidation on dataset change
- Cache TTL expiration

---

## **API Endpoints**

### GET /healt
Health check.

---

### POST /data/upload
Upload CSV or Parquet.

Return:

```
{
  "rows": 150,
  "columns": ["city", "temp"],
  "dtypes": {"city": "object", "temp": "float64"}
}
```

---

### GET /data/stats
Returns descriptive statistics with ETag support

---

### POST /ai/ask
Runs the full AI pipeline
Returns: 
```
{
  "question": "...",
  "answer": "...",
  "reasoning": "...",
  "stats_used": {...}
}
```

Supports:
- ETag caching
- Cache invalidation
- Circuit breaker
- Retry policy

---

### POST /ai/ask/stream
Streams the answer in chunks.

---

### GET /data/download/csv
### GET /data/download/parquet
Download the dataset in normalized form.

---

## **Testing Strategy**
The project inluces 70+ tests, covering:
### AI pipeline
- Cache hit
- Cache miss
- Cache invalidation
- TTL expiration
- Circuit breaker trip
- Circuit breaker half-open recovery
- Timeout handling
- Fallback strategy

### Data ingestion
- CSV edge cases
- Parquet edge cases
- Schema drift
- Semantic drift
- Canoicalization
- Type coercion
- Nullability
- Roundtrip tests

### API
- Upload
- Stats
- Download
- Security headers
- Rate limiting

### Retry policy
- Exponential backoff
- Jitter

### Middleware
- Global rate anomaly detection
- Circuit breaker middleware

The tests suite uses:
- pytest
- monkeypatch
- TestClient
- Deterministic FakeLLMRunner
- Automatic state reset

---

## **Installation**
```
uv sync
uv run uvicorn app.main:app --reload
```

---

## **Project Setup & Development Workflow**
This project follows a clean, professional Git workflow designed for collaboration, reproducibility, and safe iteration.
Below is the recommended setup process for contributors and maintainers.

---
### 1. Fork the Repository
Create your own copy of the project under your GitHub account:
```
1. Navigate to the repository on GitHub
2. Click Fork
3. Choose your personal account or organization
4. Wait for GitHub to create your fork
```

Your fork will now live at:
https://github.com/<your-username>/oraklet

---

### 2. Clone Your Fork

Clone your fork locally:

```
git clone https://github.com/<your-username>/oraklet.git
cd oraklet
```

Add the original repository as an upstream remote to stay in sync:

```
git remote add upstream https://github.com/<original-author>/oraklet.git
```

Verify:

```
git remote -v
```

You should see:

```
origin    https://github.com/<your-username>/oraklet.git
upstream  https://github.com/<original-author>/oraklet.git
```

---

### 3. Keep Your Fork Updated
Before starting any new work:

```
git fetch upstream
git checkout main
git merge upstream/main
```

Or, if you prefer rebase:

```
git rebase upstream/main
```

---

### 4. Create a Feature Branch
Never work directly on `main`.
Create a clean feature branch:

```
git checkout -b feature/<short-description>
```

Examples:

```
feature/add-semantic-drift-tests
feature/improve-parquet-validator
fix/circuit-breaker-half-open
```

---

### 5. Install Dependencies
This project uses **uv** for environment and dependency management.

Install dependencies:

```
uv sync
```

Run the development server:

```
uv run uvicorn app.main:app --reload
```

---

### 6. Run the Test Suite
Before committing:

```
pytest -q
```

Run type checking:

```
mypy --strict
```

Optional linting (if configured):

```
ruff check .
```


---

### 7. Commit Your Changes
Use clean, descriptive commit messages:

```
feat: add semantic drift auto-recovery
fix: correct parquet mixed-type detection
refactor: extract lineage builder into separate module
test: add TTL expiration tests for AI cache
docs: update API reference for /ai/ask/stream
```


---

### 8. Push and Open a Pull Request
Push your branch:

```
git push origin feature/<short-description>
```

Then open a Pull Request on GitHub:
- Base branch: `main` (or `dev` if used)
- Compare branch: your feature branch
- Fill in the PR template (description, tests, reasoning)

A maintainer will review your changes.

--- 

### 9. Sync After Merge
After your PR is merged:

```
git checkout main
git fetch upstream
git merge upstream/main
```

Or:

```
git rebase upstream/main
```

Then delete your old feature branch:

```
git branch -d feature/<short-description>
```

---

### 10. Clean Development Environment (Optional)
If you want to reset everything:

```
git clean -fd
git reset --hard upstream/main
uv sync
```

---

## **Configuraton**
Environment variables:
- `TESTING=1` (enable mock LLM + disables rate limiting)
- `.env` for secrets (ignored by .gitignore)

---

## **Design Decisions**
### Why a Runnable chain?
- Strong typing between steps
- Replaceable components
- Testable in isolation
- Clear separation of concerns
- Production-grade orchestration

### Why circuit breakers? 
To protects the system for unstable LLM behavior.

### Why schema/semantic drift detection?
To ensure data consistency across uploads.

### Why ETag caching? 
To avoid unnecessary LLM calls and reduce latency.

### Why structured logging?
To support observability and debugging in production. 

---
## **Future Improvements**
- Distributed caching (Redis)
- Prometheus metrics export
- Horizontal scaling
- Async pipeline execution
- Pluggable model backends
- Role-based access control
- Dataset versioning

---

## **Code of Conduct**
This project follows a professional, respectful, and inclusive collaboration philosophy.
All contributors are expected to uphold the following principles:

### Respect & Professionalism
- Treat all contributors with courtesy and professionalism
- Assume good intent and communicate constructively
- Provide feedback that is actionable, specific, and kind

### Clean Communication
- No harassment, discrimination, or personal attacks
- No aggressive or hostile language
- No dismissive or belittling behavior

### Safety & Integrity
- Do not introduce malicious code, backdoors, or unsafe patterns
- Do not leak sensitive data in logs, comments, or examples
- Do not circumvent validation, security middleware, or circuit breakers

### Technical Responsibility
- Follow architectural boundaries
- Maintain test coverage
- Keep the codebase consistent with existing patterns
- Document decisions when introducing new concepts

### Reporting Issues
If you observe behavior that violates this Code of Conduct, open an issue or contact a maintainer privately.
All reports will be handled discreetly and respectfully.

---

## **Maintainers**
The following individuals are responsible for reviewing contributions, maintaining architectural integrity, and ensuring long‑term project stability.

### Primary Maintainer
**Grevendev**
- Lead architect
- Owner of the AI pipeline design
- Responsible for schema/semantic drift logic
- Oversees test suite consistency
- Approves major architectural changes

### Maintainer Responsibilities
Maintainers are expected to:
- Review pull requests in a timely manner
- Enforce architectural boundaries
- Ensure code quality and test coverage
- Provide constructive feedback
- Manage releases and versioning
- Uphold the Code of Conduct

### Becoming a Maintainer
New maintainers may be added based on:
- Consistent high‑quality contributions
- Deep understanding of the architecture
- Demonstrated responsibility in reviews
- Positive collaboration with the community

## **Contributing**
Contributions are welcome and encouraged.
This project follow an enterprise-grade workflow to ensure stability, repoducibility, and architectural consistency.

### Contribtion Principles
- Maintain strict typing (`mypy -- strict` must pass)
- Follow the existing **Clean Architecture structure**
- Preserve **pipeline contracts** (`PipleineSteps[Input, Output]`)
- Ensure **full test coverage** for new features
- Never break:
  - Schema fingerprinting
  - Semantic drift detection
  - Column lineage
  - Circuit breaker behavior
  - Retry policy guarantees
  - ETag caching semantics

### Testing Requirements
All contributions must include:
- Unit test for new logic
- Integration tests for new endpoints
- Pipeline isolation tests if modifying chain steps
- Cache behavior tests if touching `/ai/ask`
- Schema/semantic drift tests if modifying ingestion

Run the full suite:
pytest -q

### Code Quality Requirements
- `mypy --strict` must pass
- `ruff` or `flake8` must pass (if configured)
- No unused imports
- No dead code
- No silent exception swallowing
- All logs must be the central `logger`
- All new models must be Pydantic v2 BaseModels

### Branching Model
Use the following workflow:
- `main` - stable, production-ready
- `dev` - integration branch
- Feature branches:
  - `feature/<short-description>`
- Bugfix branches:
  - `fix/<issue-id-or-description>`

### Pull Request Requirements
Every PR must include:
- A clear description of the change
- Before/after behavior
- Test evidence (pytest output or screenshots)
- Architectural reasoning if modifying:
  - Pipeline steps
  - DataService
  - Circuit breaker
  - Retry policy
  - Middleware stack

### Architectural Consistency
When contributing, ensure:
- No business logic leaks into API routes
- No pipeline logic leaks into DataService
- No ingestion logic leaks into AI pipeline
- No global state mutations outside `state.py`
- No new global variables unless absolutely necessary
- All new features follow the existing enterprise patterns

### Security Expectations
- Never accept unvalidated input
- Never bypass CSV/Parquet validators
- Never disable security middleware
- Never introduce blocking I/O in async paths
- Never log sensitive data

---

## **License**
MIT 

---

## **Author** 
**Grevendev**
Enterprise backend engineer in the making. 

---