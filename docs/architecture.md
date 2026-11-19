# AB-hub Architecture Notes

See the original technical specification for the full design.

## Layers

1. **CLI** (Typer + Rich) — user facing commands
2. **Services** — orchestration (scan, inspect, report, compare)
3. **Engines**
   - Discovery
   - Intelligence (analyzers)
4. **GitHub Integration** — HTTPX client, pagination, rate limits
5. **Storage** — SQLAlchemy + SQLite

## Extending

New analyzers should live under `ab_hub/analyzers/` and be called from `scan_service`.

New exporters under `ab_hub/exporters/`.
