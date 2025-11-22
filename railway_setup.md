# Railway Deployment Setup

## Database Migration

The application includes automatic database setup that runs on startup. The system uses two mechanisms:

1. **Column Migration** (`migrate_database.py`): Adds missing columns to existing tables
   - Works with both SQLite (development) and PostgreSQL (Railway production)
   - Handles columns for `optimization_records` and `feedback` tables
   - Idempotent (safe to run multiple times)

2. **Table Creation** (`db.create_all()`): Automatically creates new tables
   - Creates all tables defined in `database_models.py` if they don't exist
   - Handles: `optimization_records`, `feedback`, and `email_requests` tables
   - Runs automatically on every app startup

## Automatic Setup

Both migration and table creation run automatically when the app starts via `app/__init__.py`. No manual steps are required.

## Database Tables

The application uses three main tables:

1. **optimization_records** - Stores optimization results and inputs
2. **feedback** - Stores user feedback linked to optimization records
3. **email_requests** - Stores email requests with session tracking (NEW)

## Manual Migration (if needed)

If you need to run the migration manually on Railway:

1. Connect to your Railway service via Railway CLI or web console
2. Run: `python migrate_database.py`

## Verification

After deployment, check the Railway logs to confirm:
- "Migration complete!" message appears
- No errors related to missing columns or tables
- Optimization records save successfully with `optimization_record_id` set
- Email requests are saved to the `email_requests` table

## Notes

- The `email_requests` table is automatically created by `db.create_all()` - no migration needed
- All migrations are idempotent and safe to run multiple times
- The system gracefully handles both new deployments and updates to existing databases

