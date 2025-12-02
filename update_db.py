from shark.database import SessionLocal
from shark.models import MembershipLevel, MembershipType

def update_limits():
    db = SessionLocal()
    try:
        # Define the new limits as per the updated main.py
        updates = [
            {"level": MembershipType.SILVER, "max": 3},
            {"level": MembershipType.GOLD, "max": 10},
            {"level": MembershipType.PLATINUM, "max": 50},
            {"level": MembershipType.DIAMOND, "max": 100},
        ]
        
        print("Starting membership limit update...")
        for up in updates:
            # level_code is stored as string in DB, match it with Enum value
            m = db.query(MembershipLevel).filter(MembershipLevel.level_code == up["level"].value).first()
            if m:
                print(f"Updating {m.name} ({m.level_code}): max_accounts {m.max_youtube_accounts} -> {up['max']}")
                m.max_youtube_accounts = up["max"]
            else:
                print(f"Warning: Membership level {up['level']} not found in DB.")
        
        db.commit()
        print("Membership limits updated successfully in database.")
    except Exception as e:
        print(f"Error updating limits: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    update_limits()
