# Railway Deployment Setup

## Database Migration

The application now includes automatic database migration that runs on startup. The migration script (`migrate_database.py`) will:

1. Check for missing columns in the `optimization_records` table
2. Add `tax_rate` and `tax_free_allowance_remaining` columns if they don't exist
3. Work with both SQLite (development) and PostgreSQL (Railway production)

## Automatic Migration

The migration runs automatically when the app starts via `app/__init__.py`. No manual steps are required.

## Manual Migration (if needed)

If you need to run the migration manually on Railway:

1. Connect to your Railway service via Railway CLI or web console
2. Run: `python migrate_database.py`

## What Changed

- Added `migrate_database.py` - Database-agnostic migration script
- Updated `app/__init__.py` - Automatically runs migrations on startup
- The migration is idempotent (safe to run multiple times)

## Verification

After deployment, check the Railway logs to confirm:
- "Migration complete!" message appears
- No errors related to missing columns
- Optimization records save successfully with `optimization_record_id` set

