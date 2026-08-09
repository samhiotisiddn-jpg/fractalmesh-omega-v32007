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
python scripts/validate_tracker.py --data tracker/deepseek_v4_perf_tracker.json validate
python scripts/generate_tracker_report.py --data tracker/deepseek_v4_perf_tracker.json
python -m unittest discover -s tests -v
```

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

## Suggested execution order

1. Take quick wins first: high impact, low risk, shallow dependency depth.
2. Then work the critical path from the root blockers outward.
3. Use the blocked-items report to resolve prerequisite work before opening larger upstream contribution packets.
