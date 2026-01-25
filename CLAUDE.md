# Claude Code Project Memory

## User Context
- User is NOT a coder - I built this entire system
- I am the engineer responsible for all code
- Always push changes after completing web modifications

## Related Projects
- **This project**: PowersBioStrikes subscription website
- **Biotech Scanner**: `/mnt/c/biotech-options-v2/` (Streamlit dashboard)
- Shares SQLite database with scanner

## Auto-Run Rules (DO THIS AUTOMATICALLY)

### After ANY file changes in this project:
```bash
git add -A && git commit -m "description" && git push
```
DO NOT ASK - just do it when changes are complete.

### After catalyst data updates (in biotech-options-v2):
```bash
python3 generate_catalyst_calendar.py
git add data/calendar.json && git commit -m "Update calendar data" && git push
```

## Data Flow
1. SQLite DB (biotech_options.db) - source of truth
2. `generate_catalyst_calendar.py` - reads DB, outputs JSON
3. `data/calendar.json` - static file served to website
4. `calendar.html` - fetches and displays JSON

## Future: Supabase Migration
- Auth already uses Supabase
- Catalyst data still static JSON
- Plan to move catalysts to Supabase for real-time API

## Key Files
- `calendar.html` - Catalyst calendar display
- `generate_catalyst_calendar.py` - JSON generator
- `data/calendar.json` - Calendar data (auto-generated)
- `js/supabase-config.js` - Auth configuration
