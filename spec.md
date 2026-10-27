# Agentic RAG Benchmark Workbench — Specification

Version: 0.1.0
Date: 2026-10-26
Status: Draft implementation baseline
Owner: Sinchan Patra

## 1. Purpose

Build a reproducible, deployable Agentic RAG application that compares recursive and structure-aware chunking over the same document corpus. Measure hybrid retrieval, reciprocal rank fusion (RRF), cross-encoder reranking, bounded agentic retrieval, and semantic caching independently.

The product must produce defensible engineering datapoints for a benchmark report and resume. Targets are hypotheses and release criteria, never claimed results.

Normative terms: MUST denotes a required behavior; SHOULD denotes a preferred behavior whose exceptions require a documented reason; MAY denotes an optional extension.

## 2. Scope and defaults

### In scope
- Streamlit ingestion, chat, evidence inspection, experiment, and benchmark views.
- FastAPI asynchronous API; separate ingestion/evaluation worker.
- LangGraph orchestration with bounded retries.
- Shared document parsing feeding two isolated chunking pipelines.
- PostgreSQL, pgvector dense indexes, persisted BM25 lexical indexes.
- Dense-only, BM25-only, hybrid RRF, and hybrid RRF plus cross-encoder modes.
- Exact answer caching and conservative semantic answer caching.
- LangSmith tracing and offline evaluations.
- Versioned golden dataset, controlled experiments, operational and load testing.
- Reproducible setup, configuration, migrations, deployment and recovery instructions.

### Initial assumptions
- English technical documentation, runbooks and troubleshooting guides.
- Text-native PDF, Markdown, HTML, and plain text. OCR and image interpretation are deferred.
- One repository; API and worker processes rather than microservices.
- OpenAI-compatible chat and embedding adapters; pin actual model IDs before benchmarking.
- No Docker prerequisite. Setup must work with a virtual environment and PostgreSQL.
- Local development may use one trusted user. Network-accessible deployment MUST enforce authentication and access scopes.
- No repository or deployment target has been selected. This file authorizes planning, not deployment.

### Out of scope for v1
Graph RAG, fine-tuning, autonomous external actions, arbitrary web browsing, multilingual retrieval, Kubernetes, and an unlimited autonomous agent loop.

## 3. User journeys

### FR-01: Ingest a corpus
1. User creates a corpus and uploads approved documents.
2. System validates files, parses each document once, and creates a stable parsed representation.
3. User builds both strategies or rebuilds one strategy using versioned configuration.
4. UI shows queued/running/completed/failed status and extraction warnings.
5. Completed indexes become selectable only after consistency checks.

### FR-02: Chat with a strategy
1. User selects corpus, completed index version, and Recursive or Structure-aware.
2. User selects retrieval mode and reranker/cache controls.
3. Backend pins the configuration to the conversation.
4. Answer streams with source citations; evidence and timings are inspectable.
5. Changing strategy/index/pipeline creates a new thread or requires an explicit new-thread action.
6. Both BM25 and dense results MUST come from the selected strategy.

### FR-03: Compare and evaluate
- User can compare two independent configurations using the same question.
- Evaluation runs execute in the background against an immutable dataset version.
- UI shows experiment configuration, sample counts, per-category scores, cost, latency and failures.
- A benchmark export must contain enough metadata to reproduce the run.
- Comparison mode must not share prior generated answers between configurations.

## 4. Architecture

### Components
| Component | Responsibility |
|---|---|
| Streamlit UI | Upload, job status, configuration, chat, evidence, results |
| FastAPI | Validation, authorization, SSE streaming, orchestration entry points |
| LangGraph | Context resolution, retrieval decisions, bounded retries, generation |
| Worker | Parsing, chunking, embeddings, BM25 builds, offline evaluations |
| PostgreSQL + pgvector | Metadata, chunks, vectors, sessions/checkpoints, jobs, cache, results |
| BM25 artifact store | Immutable lexical indexes keyed by index version |
| Document store | Original files and normalized parsed artifacts |
| LangSmith | Traces, datasets/experiments and evaluator feedback |

Business logic MUST live outside Streamlit. UI and evaluation runners must call the same retrieval and generation services.

### Online path
Authorization -> pinned session configuration -> resolve conversational question if needed -> exact cache -> semantic cache -> parallel dense/BM25 retrieval -> RRF -> optional reranker -> evidence sufficiency decision -> answer or one bounded retry -> cited response -> cache eligibility check -> persistence.

### Background path
Queued job -> acquire lease -> parse/build/evaluate -> persist checkpoints/status -> validate artifacts -> publish completed version or mark failed.

Job claims require atomic ownership, lease expiry, heartbeat and retry limits. Application restart must not leave jobs permanently stuck in running state.

## 5. Document representation and versioning

### ING-01: Shared parsing
Both chunkers MUST consume identical normalized parsed content. Parsing records:
- Stable document ID, content checksum, MIME type and parser version.
- Canonical text and ordered blocks: heading, paragraph, list, table, code.
- Page or section, heading path, and canonical character offsets.
- Original source URI/name, access scope, extraction warnings.
- A documented offset normalization policy.

Preserve code and tables where possible. Identify malformed/empty extraction. Repeated headers/footers may be removed only by a versioned, deterministic policy. Missing structural information in a PDF must be reported; do not invent headings.

### ING-02: Recursive chunking
- Recursively split by paragraph, line, sentence/word boundaries with token-based size enforcement.
- Initial tuning seed: 400-token target, 60-token overlap.
- Preserve offsets and provenance for each resulting chunk.

### ING-03: Structure-aware chunking
- Prefer section and semantic block boundaries.
- Include heading context in a deterministic, recorded representation.
- Avoid splitting tables/code unless too large for model constraints.
- Recursively split oversized blocks and retain parent-block IDs.
- Initial target budget: 400 tokens; hard cap: 700, subject to embedding/reranker limits.
- Any heading prefix counts toward model input tokens and is distinguishable from source evidence.

### ING-04: Identity and publication
Index identity includes corpus checksum/version, parser, strategy, chunker settings, embedding model/revision and lexical tokenizer configuration.
- Strategies MUST have disjoint chunk/index namespaces.
- Ingestion MUST be idempotent for identical content/configuration.
- Changed documents create a new immutable corpus/index version.
- Stage artifacts, validate counts/checksums, then atomically activate a version.
- Do not serve a mixture of old dense and new BM25 artifacts.
- Keep previous versions available for rollback and pinned conversations.
- Deletion/access revocation overrides pinned-version access.

## 6. Retrieval

### RET-01: Dense retrieval
Embed the resolved question using the index's embedding model. Search only authorized chunks within the selected index version. Start with top 20 candidates. Record embedding and database search timing separately.

### RET-02: Sparse retrieval
BM25 is the v1 lexical/sparse retrieval method; learned sparse vectors are not required.
- Use the exact same strategy-specific chunks as dense retrieval.
- Preserve technical identifiers via a versioned tokenizer.
- Persist artifacts; load and reuse them rather than rebuilding per request.
- Start with top 20 candidates.
- In v1, private corpora use isolated authorized indexes; do not rank unrestricted content and filter only afterward.

### RET-03: RRF
For document/chunk d:
RRF(d) = sum over retrievers r of 1 / (c + rank_r(d)).
- Ranks are 1-based; absent candidates contribute zero.
- Start with equal weights and c=60; tune c on the development split only.
- c is a smoothing parameter, not the retrieval candidate count.
- Deduplicate by chunk ID within each input list and merge across lists.
- Retain component ranks, scores, and fused score for inspection.
- Stable tie-break by chunk ID.
- Keep top 20 fused candidates initially.
- Compare c values such as 10, 30, 60; no value is assumed universally optimal.

### RET-04: Cross-encoder
- Initial English baseline: sentence-transformers CrossEncoder with cross-encoder/ms-marco-MiniLM-L6-v2.
- Process pairs of (resolved query, candidate text); no vector input and no initial training.
- Load once per inference process. Pin package/model revision.
- Batch predictions (initial batch size 8); return top 5 initially.
- Rank by cross-encoder score; do not directly add logits to RRF scores.
- Scores are relevance scores, not correctness probabilities.
- Preserve original chunk text, citation metadata and pre/post ranks.
- Deduplicate overlapping evidence and enforce final context budget.

Long inputs MUST NOT silently truncate gold evidence. Compute actual tokenizer limits for query plus passage. Apply the same deterministic scoring-window policy to both strategies, with bounded overlapping windows and documented aggregation (initially max window score). Record window count and truncation/coverage statistics. Revisit aggregation bias during evaluation.

### RET-05: Runtime and fallback
- Run independent dense and BM25 I/O concurrently.
- Move blocking BM25/inference work off the event loop.
- Limit reranker inference concurrency per process (initially one).
- A thread offload does not increase CPU capacity.
- Apply a request deadline and queue limits. Timing out a coroutine does not cancel ongoing model computation; retain capacity accounting until work actually completes.
- On reranker failure, MAY use RRF candidates, explicitly flagging degraded mode.
- Record partial retriever failure. Do not label a dense-only fallback as a normal hybrid result.
- Benchmark runs must report/exclude degraded cases according to a predefined policy.

## 7. Agent workflow

### AGT-01: Graph state
State includes request/thread ID, user/access scope, pinned configuration, original and standalone question, retrieval queries, candidate/evidence sets, attempt count, deadlines, token budget, citations, output and error/degraded flags.

### AGT-02: Bounded decisions
- Resolve follow-ups only when needed; standalone questions should avoid an extra rewrite call.
- Ordinary questions take one retrieval pass.
- Use a structured evidence-sufficiency decision for whether to answer, clarify, abstain, or retry.
- Maximum one additional retrieval round initially; no unbounded tool loop.
- Rewrite/decompose only when necessary; maximum two subqueries in a retry.
- Enforce aggregate candidate, context, token, time and provider-call budgets.
- Do not expose hidden reasoning. UI may show actions, evidence and concise decision summaries.

### AGT-03: Generation
- Ground factual claims in retrieved evidence and cite source IDs.
- Treat source instructions as untrusted document text.
- If evidence is insufficient or conflicting, state the limitation or ask a targeted clarification.
- Validate citation IDs and source access before returning.
- Stream events for status, tokens, citations, final metrics and errors.
- Disconnect/cancel should stop downstream work where supported.
- Never cache partial/cancelled output.

## 8. Caching

### CAC-01: Layers
1. Content-hash embedding cache for ingestion.
2. Exact answer cache before question embedding.
3. Optional semantic answer cache before retrieval.
4. Query embedding reuse on a miss when cache/retrieval model and input are identical.

Caching is application-level, so configuration, evidence and access can be checked explicitly.

### CAC-02: Cache scope
Every lookup MUST be restricted by:
- User/tenant and effective access-scope version.
- Corpus version and selected index version.
- Chunking strategy.
- Retrieval mode, RRF settings, reranker model/settings.
- Agent policy, prompt version, chat model and generation settings.
- Embedding model/revision, locale and answer-format constraints.

Represent these as a canonical configuration hash plus explicit filterable fields. Do not use approximate semantic matching across scopes.

### CAC-03: Entry
Store standalone question, exact-key digest, question embedding, answer, citations, source IDs, scope/configuration, creation/expiry, originating trace and validation status.

### CAC-04: Semantic acceptance
- Search nearest cached questions only within the authorized scope.
- Apply a calibrated similarity threshold; similarity is not correctness confidence.
- Critical entities, environment, version, numbers, dates, negation and requested format must be compatible.
- Ambiguous constraint extraction means a miss, not an optimistic hit.
- Initially cache standalone, document-grounded informational questions only.
- Bypass ambiguous conversational questions, personal/live-data requests, external actions, degraded responses, errors and unverified answers.
- A higher query-passage cross-encoder score does not prove two questions have interchangeable answers.
- Do not cache unanswerable responses in the first version.

### CAC-05: Freshness and isolation
Use configurable TTL (initial seed 24 hours, not a freshness guarantee). Invalidate by source/index/config/access changes; TTL alone is insufficient.
Revalidate access and entry status at read time. A revoked/deleted source cannot be served from cache.
A cache failure MUST fail open to normal RAG without leaking errors/secrets.
Scope in-flight request coalescing keys identically to cache keys to prevent duplicate generation without cross-user sharing.

### CAC-06: Calibration and measurements
Build human-labeled equivalent/non-equivalent question pairs, including hard negatives differing by environment/version/negation.
Tune on development pairs; evaluate once on held-out pairs.
Report semantic-hit precision, incorrect reuse rate, hit rate, bypass rate, lookup latency and net cost/latency savings.
Set the release threshold from development evidence and document it before held-out testing.
If no safe useful threshold is found, ship semantic caching disabled.
Cached response UI/traces must disclose hit type. Original generation cost and current serving cost remain separate.

## 9. Data entities

| Entity | Minimum fields |
|---|---|
| Corpus/version | ID, owner/scope, manifest checksum, status |
| Document | ID, version, checksum, source, MIME, access, parser |
| Parsed block | Document ID, type, heading path, page, offsets, text |
| Index version | Corpus, strategy, settings/model hashes, dense/BM25 artifact IDs, status |
| Chunk | ID, index, document, text, offsets, parent/block IDs, token count |
| Ingestion job | ID, payload, idempotency key, lease/attempt/status, progress/errors |
| Conversation/checkpoint | Thread, owner, pinned configuration, state |
| Cache entry | Fields defined in CAC-03 |
| Dataset/example | Version, split, question/context, expected facts/evidence, category |
| Experiment | Dataset/config/code version, execution environment, status |
| Prediction/metric | Example/run IDs, answer/evidence, scores, timings, usage/errors |

Use migrations, foreign keys, unique constraints and timestamps. Raw secrets and API keys must never enter these records.

## 10. API contract

Version API routes under /v1. Proposed endpoints:
| Method/path | Behavior |
|---|---|
| POST /v1/corpora | Create scoped corpus |
| POST /v1/corpora/{id}/documents | Validate and upload files |
| POST /v1/corpora/{id}/ingestions | Queue strategy builds; idempotency key |
| GET /v1/jobs/{id} | Job progress/failure |
| GET /v1/corpora/{id}/indexes | Completed/selectable versions |
| POST /v1/conversations | Pin authorized pipeline configuration |
| POST /v1/conversations/{id}/messages | SSE response stream |
| POST /v1/experiments | Queue fixed-config evaluation |
| GET /v1/experiments/{id} | Results/progress |
| GET /v1/experiments/{id}/export | JSON/CSV report |
| GET /health/live | Process liveness |
| GET /health/ready | Required dependency/index readiness |

SSE events: status, token, citations, metrics, done, error.
Use typed request/response validation, request IDs, bounded inputs, consistent error codes and explicit degraded flags. Client-supplied scope is never trusted; derive authorization server-side.

## 11. Golden dataset

### EVAL-01: Construction
Start with 50 reviewed examples; expand to 150–200. These are planned counts, not existing results.
Cover factual, exact identifier, paraphrase, table/list/code, multi-section, conversational, ambiguous, unanswerable and adversarial cases.
Record per example:
- Stable ID and category.
- Question and relevant conversation.
- Reference answer and required facts.
- Answerable flag and expected refusal/clarification behavior.
- Document IDs and canonical evidence spans/sections.
- Corpus version, split, provenance, reviewer and review status.

Gold labels MUST refer to original source spans, never one strategy's chunk IDs.
Generate drafts with an LLM only if humans validate facts and evidence.
Separate tuning and held-out testing (initial 30/70 split, stratified where possible). Keep paraphrase families together; record group IDs to prevent leakage.
Do not modify held-out labels based on observed model outputs without a versioned correction and rerun policy.

### EVAL-02: Fair retrieval scoring
Map retrieved chunks/windows back to canonical source spans.
Report both conventional chunk-level metrics and strategy-neutral evidence coverage; explain that chunk Precision@k is sensitive to chunk size.
Deduplicate overlapping gold coverage. Annotate graded relevance for nDCG when available. Recall requires a sufficiently complete relevant-evidence set; report labeling limitations.
Use k=5 and k=10 initially. Metric definitions, matching rules and denominators MUST be versioned.

## 12. Metrics

| Category | Required measurements |
|---|---|
| Retrieval | Precision@k, Recall@k, Hit Rate@k, MRR, nDCG@k |
| Evidence | Gold-span coverage, context precision/recall, redundancy |
| Answers | Correctness, required-fact completeness, relevance |
| Grounding | Faithfulness, unsupported factual claim rate |
| Citations | ID validity, attribution correctness, claim coverage |
| Abstention | Unanswerable refusal precision/recall, false refusal rate |
| Agent | Task success, retry frequency, routing/decision accuracy, budget violations |
| Latency | Parse/embed/search/fusion/rerank/generate durations; TTFT and end-to-end p50/p95 |
| Cost | Embedding, generation, judges separately; cost per successful answer |
| Reliability | Errors, timeouts, rate limits, cancellations, degraded responses |
| Ingestion | Duration, documents/tokens per second, failures, chunk distribution, index size |
| Cache | Hit precision/rate, incorrect reuse, net savings, stale-hit rate |
| Load | Throughput, p50/p95 latency, queue wait and errors by concurrency |

Use deterministic metrics for IDs, evidence overlap and format. Use fixed-rubric LLM judges for semantic quality; retain judge model/prompt/revision, uncertainty and human audit results. LLM judgments are estimates, not objective truth.
Use exact match/token F1 only where appropriate for short factual answers. Do not use BLEU/ROUGE as primary RAG correctness scores.
Never aggregate unrelated metrics into an unexplained single quality score.
Collect enough observations for meaningful percentiles; report sample size and uncertainty.

## 13. Experiment protocol

### EXP-01: Retrieval/chunking matrix
For each strategy run:
1. Dense only.
2. BM25 only.
3. Dense + BM25 + RRF.
4. Dense + BM25 + RRF + cross-encoder.

Hold parser, corpus, models, generation prompt, context budget and evaluation examples constant. Document unavoidable differences such as chunk counts.
Compare bounded agentic retrieval against single-pass retrieval separately, holding retriever settings fixed.

### EXP-02: Cache and performance
- Disable answer caches and cross-example conversational memory for quality experiments.
- Run separate cold-start/model-load, warm-model uncached, exact-cache and semantic-cache experiments.
- Use an ordered paraphrase workload for cache tests; empty/seed the cache by an explicit protocol.
- Measure cache false positives on held-out negative pairs.
- Test concurrency 1, 5 and 10 as initial load levels; do not promise throughput before measuring hardware/provider limits.
- Repeated agent/LLM runs should be reported when budget permits.
- Randomize/interleave configuration execution to reduce temporal provider bias.
- Report paired deltas, category breakdowns and bootstrap confidence intervals where meaningful.

### EXP-03: Reproduction artifact
Store dataset/corpus/config checksums, git commit, dependency lock, model revisions, prompts, judge settings, hardware, region, concurrency, timestamps, raw predictions, evidence IDs, usage, errors and aggregate results.
Cost calculations use a timestamped price manifest, not permanent hard-coded prices.

## 14. LangSmith and observability

Trace the application root and parsing, chunking, embedding, retrieval branches, RRF, reranking, evidence decision, retry, generation and cache decisions.
Metadata: request/thread/experiment ID, configuration hashes, index/strategy, candidate counts, model IDs, cache status, degraded flags.
Record duration, tokens, estimated cost, evidence/source IDs and before/after ranks.
Redact sensitive inputs and secrets; public corpus content may be traced subject to configuration.
Tracing outages must not break chat. Export asynchronously with bounded queues and documented shutdown flushing.

Developer plan verified 2026-10-26: one seat, 5,000 included base traces/month; base retention 14 days. Extra usage and model/judge calls may cost money. Recheck before implementation because plans can change.
Budget evaluator traces as well as chat traces. Do not assume one user request equals all billed usage.
Persist benchmark evidence independently of LangSmith retention. Sampling is configurable; performance experiments record sampling settings.

## 15. Performance and operational requirements

- Reuse HTTP/model clients, DB pools and warmed model instances.
- Batch embedding and reranking; bound all concurrency and queues.
- Do not run ingestion on the chat request path.
- Check deadlines before scheduling retries and provider calls.
- Retry transient idempotent operations with backoff/jitter; do not blindly retry arbitrary errors.
- Enforce per-user limits, max upload size, corpus size and context budget.
- Maintain readiness, structured logs and graceful shutdown.
- Track resident model memory per worker: multiple API workers may duplicate model memory.
- Separate model inference into a worker/service if contention measurements justify it.
- Support backup/restore of metadata, source files and immutable index artifacts.
- A deployment is ready only after documented recovery and load tests.

Absolute latency/cost SLOs remain uncommitted until an uncached baseline is measured on named hardware and provider settings. Record selected p95/TTFT/error budgets before optimization experiments; do not retroactively label measured outcomes as pre-existing targets.

## 16. Security and correctness

- Enforce authorization before retrieval/cache access and before returning sources.
- Pin access-policy versions and invalidate cached entries on revocation.
- Use environment/secret management; provide .env.example without real keys.
- Validate file type/content and sanitize HTML; prevent path traversal.
- Do not fetch arbitrary uploaded URLs in v1.
- Retrieved content cannot change system instructions or authorize external actions.
- Restrict source-link rendering to supported safe schemes.
- No chain-of-thought logging requirement; record decisions and observable actions.
- Define document deletion and trace-redaction behavior.
- Network deployment must not rely on Streamlit UI controls as an authorization boundary.

## 17. Repository structure

Proposed layout (subject to repository selection):
- spec.md
- apps/ui/
- apps/api/
- src/core/config/
- src/ingestion/{parsing,chunking,indexing}/
- src/retrieval/{dense,bm25,fusion,reranking}/
- src/agents/
- src/cache/
- src/evaluation/
- src/observability/
- src/storage/
- workers/
- migrations/
- tests/{unit,integration,acceptance}/
- datasets/manifests/
- configs/experiments/
- scripts/
- docs/decisions/

Keep generated indexes, secrets and large document collections outside git. Commit corpus manifests and reproducible fetch/import instructions.

## 18. Spec-driven delivery and acceptance

Each change MUST reference requirement IDs, implement observable behavior, and include relevant validation. Update this specification before changing agreed behavior. Record significant trade-offs as architecture decisions. Keep speculative features out of active milestones.

| Milestone | Deliverables | Acceptance evidence |
|---|---|---|
| M1 Foundation | Typed config, DB migrations, API/UI skeleton, job system | Startup/readiness checks; unauthorized access rejected; job recovery test |
| M2 Ingestion | Shared parser, both chunkers, immutable dense/BM25 versions | Same parsed checksum; stable IDs; idempotency; failure cannot publish partial index |
| M3 Baseline chat | Selected strategy, dense/BM25/RRF, citations, streaming | Recursive selection returns only recursive chunks; independent sessions; correct SSE cancellation |
| M4 Reranking/agent | Cross-encoder, windows, bounded evidence retry | Stable scores/ranks; no silent truncation; at most configured retry budget; degraded mode visible |
| M5 Evaluation | Reviewed dataset, LangSmith, matrix runner, reports | Reproducible uncached runs; gold spans independent of strategies; no split leakage |
| M6 Caching | Exact and semantic cache, invalidation, calibration | Cross-strategy/version/user misses; hard negatives rejected; revoked sources never served |
| M7 Readiness | Load/failure tests, deployment/recovery guide | Measured named-environment SLOs; backup/restore demonstration; reproducible benchmark report |

### Mandatory high-value test cases
- RRF rank indexing, absent results, duplicate IDs and deterministic ties.
- Chunk offsets round-trip to source; tables/code and oversized sections.
- Consistent dense/BM25 activation and rollback.
- Strategy and access-scope isolation for retrieval, sessions, cache and evaluation.
- Reranker input limits, original metadata preservation and timeout capacity accounting.
- Agent maximum retries, no-evidence abstention, invalid citation rejection.
- Semantic near-miss questions: production/staging, versions, numbers, negation.
- Cache invalidation after corpus/access/config changes.
- Interrupted ingestion resumes/fails cleanly; duplicate job submission is idempotent.
- LangSmith unavailable without breaking chat.
- Gold span scoring and overlapping evidence deduplication.

## 19. Definition of done

The project is complete when:
- M1–M7 requirements are implemented or explicitly deferred with reasons.
- Both chunking strategies can be independently selected and benchmarked.
- Eight baseline configurations run against a held-out reviewed dataset.
- Agentic and caching effects are measured in separate controlled experiments.
- Raw results and a reproducible report support every claimed improvement.
- Correctness, isolation, failure and operational tests pass.
- UI exposes sources, configuration, cache/degraded state and useful timings.
- Setup works without Docker and deployment/recovery instructions are verified.
- Remaining limitations and costs are documented honestly.

## 20. Decisions to finalize during implementation

These do not block planning; record actual selections before the relevant milestone:
- Corpus source, licensing, size and exact document manifest.
- Deployment machine, authentication provider and access policy.
- Chat/embedding model IDs, context limits and budget.
- Parser libraries and PDF structural extraction quality.
- Tuned chunk sizes, RRF c, candidate counts and context budget.
- Reranker runtime/window policy and CPU versus hosted inference measurements.
- Semantic threshold, TTL and release precision criterion.
- Judge models/rubrics, dataset allocation and measurable release SLOs.

## 21. Verified references

Checked during planning on 2026-10-26; recheck mutable APIs/pricing before use.
- LangSmith pricing: https://www.langchain.com/pricing
- LangSmith RAG evaluation: https://docs.langchain.com/langsmith/evaluate-rag-tutorial
- LangSmith evaluation types: https://docs.langchain.com/langsmith/evaluation-types
- RRF reference: https://www.elastic.co/docs/reference/elasticsearch/rest-apis/reciprocal-rank-fusion
- Sentence Transformers cross-encoder usage: https://www.sbert.net/docs/cross_encoder/usage/usage.html
- CrossEncoder API: https://www.sbert.net/docs/package_reference/cross_encoder/model.html
- Semantic caching patterns (TTL, metadata filters, threshold): https://redis.io/docs/latest/develop/use-cases/semantic-cache/

Redis is a reference for cache behavior, not a required project dependency. The initial implementation uses PostgreSQL/pgvector.

## 22. Change log

- 0.1.0 (2026-10-26): Consolidated agreed architecture, dual ingestion, retrieval/reranking, bounded agent, cache policy, monitoring, evaluations and spec-driven acceptance plan.


## 23. Phase-one direction and corpus amendment (2026-10-27)

- The initial corpus is the user-provided Bhagavad-gita As It Is English PDF. The supplied file reports copy restrictions; assess authorized extraction and structural quality before implementing ingestion. Keep the document and extracted text out of the public repository.
- Where extractable, preserve chapter, verse, translation versus purport, page and canonical text offsets. Treat the edition and commentary as part of source provenance. Do not assume the PDF is reliably tagged or chapter/verse structure is always recoverable.
- The user will provision and administer PostgreSQL/pgvector and manually run any future database changes. Database instructions and future migration artifacts belong under `db/`; no migrations are applied automatically.
- Phase 1 requested here is a repository scaffold only: create directories and placeholder files plus documentation, with no application code or fabricated datasets. Milestone M1 implementation and its acceptance checks remain future work.
