# pull-up

Tracker for your daily pull-ups!

## Usage

```bash
uv run pull_up/app.py
```

The pull-up target starts at one, increases by one after a consecutive day,
and decreases by one for each missed day, down to a minimum of one.
