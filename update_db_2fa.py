from sqlalchemy import create_engine, text
from shark.config import config

def update_schema():
    engine = create_engine(config.DATABASE_URL)
    with engine.connect() as conn:
        try:
            conn.execute(text("ALTER TABLE users ADD COLUMN totp_secret VARCHAR(32)"))
            print("Added column: totp_secret")
        except Exception as e:
            print(f"Column totp_secret might already exist: {e}")

        try:
            conn.execute(text("ALTER TABLE users ADD COLUMN is_2fa_enabled BOOLEAN DEFAULT 0"))
            print("Added column: is_2fa_enabled")
        except Exception as e:
            print(f"Column is_2fa_enabled might already exist: {e}")

if __name__ == "__main__":
    update_schema()
