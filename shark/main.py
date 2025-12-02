from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from .database import engine, Base, SessionLocal
from .models import MembershipLevel, MembershipType, User, UserRole
from .routers import auth, user, youtube, admin
from .config import config
from .utils import get_password_hash
import os

# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Shark YouTube Manager")

# API Routers
app.include_router(auth.router)
app.include_router(user.router)
app.include_router(youtube.router)
app.include_router(admin.router)

# Static Files (Frontend)
static_dir = os.path.join(os.path.dirname(__file__), "static")
if not os.path.exists(static_dir):
    os.makedirs(static_dir)

app.mount("/static", StaticFiles(directory=static_dir), name="static")

@app.get("/")
async def read_index():
    return FileResponse(os.path.join(static_dir, "index.html"))

@app.on_event("startup")
def seed_data():
    db = SessionLocal()
    try:
        # Define memberships
        memberships = [
            {
                "name": "Normal",
                "level_code": MembershipType.NORMAL,
                "price_monthly": 0.0,
                "max_youtube_accounts": 0,
                "ftp_storage_mb": 0,
                "ftp_speed_kbps": 0,
                "description": "No permissions"
            },
            {
                "name": "Silver",
                "level_code": MembershipType.SILVER,
                "price_monthly": 9.9,
                "max_youtube_accounts": 1,
                "ftp_storage_mb": 256,
                "ftp_speed_kbps": 128,
                "description": "Experience Entry Level"
            },
            {
                "name": "Gold",
                "level_code": MembershipType.GOLD,
                "price_monthly": 19.9,
                "max_youtube_accounts": 1,
                "ftp_storage_mb": 2048,
                "ftp_speed_kbps": 1024, # 1 Mbps
                "description": "Personal Practical Level"
            },
            {
                "name": "Platinum",
                "level_code": MembershipType.PLATINUM,
                "price_monthly": 49.9,
                "max_youtube_accounts": 3,
                "ftp_storage_mb": 10240, # 10 GB
                "ftp_speed_kbps": 2048, # 2 Mbps
                "description": "Advanced Creative Level"
            },
            {
                "name": "Diamond",
                "level_code": MembershipType.DIAMOND,
                "price_monthly": 99.9,
                "max_youtube_accounts": 8,
                "ftp_storage_mb": 30720, # 30 GB
                "ftp_speed_kbps": 5120, # 5 Mbps
                "description": "Small Team/Enterprise Level"
            }
        ]

        for m in memberships:
            exists = db.query(MembershipLevel).filter(MembershipLevel.level_code == m["level_code"]).first()
            if not exists:
                print(f"Seeding membership: {m['name']}")
                new_m = MembershipLevel(**m)
                db.add(new_m)
        db.commit()

        # Seed Admin User
        admin_user = db.query(User).filter(User.username == "admin").first()
        if not admin_user:
            print("Seeding admin user...")
            diamond_membership = db.query(MembershipLevel).filter(MembershipLevel.level_code == MembershipType.DIAMOND).first()
            new_admin = User(
                username="admin",
                email="admin@example.com",
                hashed_password=get_password_hash("admin123"),
                role=UserRole.ADMIN,
                membership_id=diamond_membership.id if diamond_membership else None,
                is_active=True
            )
            db.add(new_admin)
            db.commit()
            print("Admin user created: admin / admin123")
            
    except Exception as e:
        print(f"Error seeding data: {e}")
    finally:
        db.close()
