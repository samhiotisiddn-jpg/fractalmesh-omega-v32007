# Fractalmesh DeepSeek V4 Perf Tracker

This repository mirrors and operationalizes the upstream DeepSeek V4 NVIDIA performance checklist from `sgl-project/sglang#33636`.

## Updating checklist items

1. Edit `tracker/deepseek_v4_perf_tracker.json`.
2. Keep each item's `id` stable.
3. Update `status`, `blocked_by`, `owner`, `notes`, and `updated_at` as work changes.
4. Run validation and report generation locally before committing.

## Local commands

```bash
cd <repo-root>
python -m pip install -e '.[dev]'
python -m perf_tracker validate --data tracker/deepseek_v4_perf_tracker.json
python -m perf_tracker analyze --data tracker/deepseek_v4_perf_tracker.json
python -m perf_tracker report --data tracker/deepseek_v4_perf_tracker.json
python -m perf_tracker migrate
pytest
```

## CLI safety features

- JSON input loads are guarded with a maximum file size limit (default `50 MB`) and structural limits to reduce resource-exhaustion risk.
- CLI path handling rejects traversal patterns (`..`) for relative paths.
- Relative paths must resolve within this repository root.
- `analyze` and `report` support `--dry-run` to print output destinations without writing files.

## SQLite backend

Optional local storage is available via `perf_tracker.store` and CLI migration:

```bash
python -m perf_tracker migrate --db-path tracker/perf_tracker.db
```

Environment variables (see `.env.example`):
- `PERF_TRACKER_DB_PATH`
- `PERF_TRACKER_MAX_JSON_BYTES`

## Output files

- `docs/status/priorities.md` and `docs/status/priorities.json` contain critical path, quick wins, and blocked item analysis.
- `docs/status/latest.md` and `docs/status/latest.json` contain the latest executive report.

## CI workflow behavior

The `perf-tracker` GitHub Actions workflow runs on a daily schedule and via manual dispatch.

It will:
- validate the tracker schema,
- regenerate prioritization/report artifacts,
- fail if required fields or blocker references are invalid,
- optionally warn instead of fail on stale `blocked` / `in_progress` items.

## Security reporting

See `.github/SECURITY.md` for coordinated vulnerability disclosure instructions.
