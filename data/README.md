# Data Directory

This directory stores Claude Insight data when running in **portable mode** (without global ~/.claude/memory).

## Directory Structure

```
data/
├── sessions/         # Session data
├── logs/            # Application logs
├── config/          # Configuration files
├── anomalies/       # AI anomaly detection data
├── forecasts/       # Predictive analytics data
└── performance/     # Performance profiling data
```

## Auto-Created

All subdirectories are created automatically on first run.

## Mode Detection

Claude Insight automatically detects:
- **Global Mode**: If `~/.claude/memory` exists → uses it
- **Local Mode**: Otherwise → uses `./data/` (this directory)

See `src/utils/path_resolver.py` for implementation.
