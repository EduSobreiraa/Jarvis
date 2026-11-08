# Memory v2

`memory.py` keeps SQLite as the source of truth and preserves the original
`MemoryStore` methods. The migration is additive (`user_version=2`): existing
`messages` and `memories` rows stay in place. New tables track runs and
checkpoints, structured episodes with message evidence, editable profile facts,
retrieval references, embeddings, and deletion tombstones. FTS5 is detected at
runtime and rebuilt from the legacy memories table; if SQLite lacks FTS5, search
uses the built-in lexical fallback.

Retrieval fuses FTS/lexical rankings and optional Ollama embedding rankings with
reciprocal-rank fusion. The default embedding model is `nomic-embed-text`, but it
is never downloaded or presumed installed: `/api/tags` is checked first. Missing
models, Ollama errors, and incompatible vectors fall back to lexical retrieval.
Vectors are stored as SQLite blobs keyed by record and model. No sqlite-vec,
LangChain, or new Python dependency is required.

`consolidate(run_id)` processes messages after `checkpoint_message_id` only.
When Ollama is available, Qwen3 returns schema-constrained JSON with source
message IDs. Facts without valid evidence, facts marked implicit/sensitive, and
malicious instruction-like text are rejected. If Ollama is down, only the prior
narrow explicit “lembre/guarde que …” phrase is retained as a compatibility
fallback; there is no generated summary. `consolidate_async` runs this work on a
dedicated worker with its own SQLite connection. The chat loop should call that
method after persisting its response instead of calling the synchronous method.

Deleting a memory creates a normalized tombstone. Automatic consolidation will
not restore the deleted content; an explicit user `remember()` call can. Deleting
a run removes its raw messages and episodes. Memory records are separate data:
call `forget_run(run_id, forget_memories=True)` to also forget episodic summaries
derived from that run. Semantic profile entries have `profile`, `explain`,
`update`, and `delete` operations. Sensitive inferred data is rejected.

For meaning-based search, install and start Ollama locally, then explicitly pull
an embedding model if desired, for example `ollama pull nomic-embed-text`.
This is optional; no model download is performed by Jarvis. The chat model remains
`qwen3:8b`.
