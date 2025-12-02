from sqlalchemy import create_engine, text
from shark.config import config

def update_schema():
    engine = create_engine(config.DATABASE_URL)
    with engine.connect() as conn:
        # Check if columns exist
        try:
            # client_secret_content
            conn.execute(text("ALTER TABLE youtube_accounts ADD COLUMN client_secret_content TEXT"))
            print("Added column: client_secret_content")
        except Exception as e:
            print(f"Column client_secret_content might already exist: {e}")

        try:
            # token_content
            conn.execute(text("ALTER TABLE youtube_accounts ADD COLUMN token_content TEXT"))
            print("Added column: token_content")
        except Exception as e:
            print(f"Column token_content might already exist: {e}")

        try:
            # membership_expire_at
            conn.execute(text("ALTER TABLE users ADD COLUMN membership_expire_at DATETIME"))
            print("Added column: membership_expire_at")
        except Exception as e:
            print(f"Column membership_expire_at might already exist: {e}")

if __name__ == "__main__":
    update_schema()
