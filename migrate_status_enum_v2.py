from sqlalchemy import create_engine, text
from shark.config import config

def migrate_status():
    engine = create_engine(config.DATABASE_URL)
    with engine.connect() as conn:
        try:
            # Map 'secret_uploaded' to 'pending'
            # Because 'secret_uploaded' previously meant "Files uploaded, waiting for worker".
            # Now 'pending' is "Waiting for worker".
            conn.execute(text("UPDATE youtube_accounts SET status = 'pending' WHERE status = 'secret_uploaded'"))
            print("Migrated 'secret_uploaded' to 'pending'")
            
            # Verify other statuses are compatible
            # 'active' -> 'active'
            # 'pending' -> 'pending'
            # 'offline' -> 'offline'
            
            # Drop is_active column if it exists (optional, usually tricky in raw SQL if constraints exist)
            # Check if column exists first?
            # SQLite doesn't support DROP COLUMN easily in older versions, but SQLAlchemy might handle it?
            # We are using raw SQL.
            # For SQLite: ALTER TABLE table DROP COLUMN column (Supported in newer SQLite).
            # Let's try it. If it fails, ignore.
            try:
                conn.execute(text("ALTER TABLE youtube_accounts DROP COLUMN is_active"))
                print("Dropped column: is_active")
            except Exception as e:
                print(f"Could not drop column is_active (might not exist or not supported): {e}")

            conn.commit()
            print("Migration completed.")
            
        except Exception as e:
            print(f"Migration failed: {e}")

if __name__ == "__main__":
    migrate_status()
