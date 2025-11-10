# TZ: Batched Full-Message Analysis

## Business Goal
Process all messages for a given chat/date (not just a small window) to produce richer, less biased discussion summaries and metrics.

## Functional Requirements
- Analyze 100% of messages for the selected date (e.g., total_messages=142 → analyzed_messages=142).
- Use batching to avoid context/token limits (default batch_size=100; configurable).
- For each batch, build prompt, get LLM result, parse JSON.
- Merge batch discussion results into a consolidated set without duplicates.
- Strict output schema; no extra fields.
- Enforce valid message links (only message IDs present in input batches).
- learning_resources must include at least 1 link per discussion; otherwise exclude that discussion.
- Return up to 5 best discussions sorted by practical_value desc; if fewer valid → return fewer; if none → empty list.
- Save final result with metadata reflecting full coverage (analyzed_messages==total_messages) and accumulated tokens.

## Technical Decisions
- Batching in AnalyzerService with default batch_size=100.
- PromptBuilder: add build_for_subset(...) to format subset messages without changing existing API.
- Merge strategy:
  - Key by normalized topic (case-insensitive, trimmed). If duplicate topic appears across batches → merge.
  - Merge rules:
    - participants: union with order preserved by first-seen
    - message_links: union (deduplicate)
    - keywords: union; truncate to 5 most frequent
    - summary/expert_comment: keep the one from the batch with higher practical_value; if equal, prefer earlier batch
    - complexity, practical_value, sentiment: choose max practical_value; complexity = max; sentiment pick majority if differs
  - After merge, recalc participant_count/message_count and priority via existing functions.
- Validation: validate links against union of all message IDs across all batches.
- Observability: aggregate tokens_used across batches; keep per-batch latency logs + total latency.

## API Design
- AnalyzerService.analyze(
    chat: str,
    date: str,
    batch_size: int = 100,
    force: bool = False,
  ) -> (AnalysisResult, AnalysisMetadata)
  - When batch_size is provided, process over all messages in batches; if None, fallback to legacy window_size behavior (not recommended).
- PromptBuilder.build_for_subset(chat_name, chat_username, date, message_dump, messages_subset, format_style="json") -> str

## Implementation Plan
1. Update prompt template (`config/prompts/analysis_prompt.txt`):
   - Forbid extra fields; strict JSON only; no Markdown.
   - Require learning_resources (>=1 URL) per discussion.
   - message_links must reference IDs from input messages_json.
   - Anti-duplication note.
   - Return up to 5 best discussions sorted by practical_value.
   - Participants without emojis (optional sanitization in prompt instruction only).
2. Add PromptBuilder.build_for_subset(...).
3. Implement batching in AnalyzerService.analyze:
   - Chunk messages by batch_size.
   - For each chunk: build prompt via build_for_subset; call LLM; parse JSON; collect discussions.
   - Merge all batch discussions.
   - Validate links against union of all IDs.
   - Save with analyzed_messages==total_messages and tokens_used=sum(tokens).
4. Keep backward compatibility: if batch_size is None, keep legacy single-window flow.
5. Logs: per-batch and totals; maintain correlation_id.
6. Optional: temperature=0.2–0.3 for stability (can be parameterized later).

## Status
- [ ] In Progress
- [ ] Implemented
- [ ] Tested
