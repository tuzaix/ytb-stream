from sqlalchemy import create_engine, text
from shark.config import config

def update_schema():
    engine = create_engine(config.DATABASE_URL)
    with engine.connect() as conn:
        # 1. Add status column
        try:
            conn.execute(text("ALTER TABLE youtube_accounts ADD COLUMN status VARCHAR(20) DEFAULT 'pending'"))
            print("Added column: status")
            
            # Update existing records to 'active' (assuming they were previously working)
            conn.execute(text("UPDATE youtube_accounts SET status = 'active'"))
            print("Updated existing accounts status to 'active'")
            
        except Exception as e:
            print(f"Column status might already exist or error: {e}")

        # 2. Add machine_ip column
        try:
            conn.execute(text("ALTER TABLE youtube_accounts ADD COLUMN machine_ip VARCHAR(50)"))
            print("Added column: machine_ip")
        except Exception as e:
            print(f"Column machine_ip might already exist: {e}")

if __name__ == "__main__":
    update_schema()
