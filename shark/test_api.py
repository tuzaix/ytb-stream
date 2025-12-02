import requests
import sys

BASE_URL = "http://127.0.0.1:8000"

def test_api():
    # 1. Register
    username = "testuser_silver"
    password = "password123"
    email = "test_silver@example.com"
    
    print(f"--- Registering {username} ---")
    resp = requests.post(f"{BASE_URL}/auth/register", json={
        "username": username,
        "password": password,
        "email": email
    })
    if resp.status_code == 200:
        print("Registered successfully.")
    elif resp.status_code == 400 and "already registered" in resp.text:
        print("User already exists, proceeding to login.")
    else:
        print(f"Registration failed: {resp.text}")
        return

    # 2. Login
    print(f"--- Logging in ---")
    resp = requests.post(f"{BASE_URL}/auth/login", data={
        "username": username,
        "password": password
    })
    if resp.status_code != 200:
        print(f"Login failed: {resp.text}")
        return
    
    token = resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    print("Login successful, got token.")

    # 3. Get Me
    print(f"--- Getting User Profile ---")
    resp = requests.get(f"{BASE_URL}/users/me", headers=headers)
    user_data = resp.json()
    print(f"User Role: {user_data['role']}")
    print(f"Membership: {user_data['membership']['name']}")

    # 4. Purchase Membership
    print(f"--- Purchasing Silver Membership ---")
    resp = requests.post(f"{BASE_URL}/users/purchase_membership", headers=headers, json={
        "membership_level_code": "silver"
    })
    if resp.status_code == 200:
        print("Purchase successful.")
        print(f"New Membership: {resp.json()['membership']['name']}")
    else:
        print(f"Purchase failed: {resp.text}")

    # 5. Create YouTube Account
    print(f"--- Creating YouTube Account 1 ---")
    resp = requests.post(f"{BASE_URL}/youtube/accounts", headers=headers, json={
        "desired_username": "ytb_acc_1"
    })
    if resp.status_code == 200:
        acc1_id = resp.json()["id"]
        print(f"Account created. ID: {acc1_id}")
    else:
        print(f"Account creation failed: {resp.text}")
        if "already exists" in resp.text:
             # fetch account to proceed
             resp = requests.get(f"{BASE_URL}/youtube/accounts", headers=headers)
             acc1_id = resp.json()[0]['id']

    # 6. Create Second YouTube Account (Should Fail for Silver)
    print(f"--- Creating YouTube Account 2 (Should Fail) ---")
    resp = requests.post(f"{BASE_URL}/youtube/accounts", headers=headers, json={
        "desired_username": "ytb_acc_2"
    })
    if resp.status_code == 403:
        print("Correctly blocked due to limit.")
    else:
        print(f"Unexpected response: {resp.status_code} {resp.text}")

    # 7. Create Material Config
    print(f"--- Creating Material Config ---")
    resp = requests.post(f"{BASE_URL}/youtube/accounts/{acc1_id}/materials", headers=headers, json={
        "group_name": "Fashion Shorts",
        "material_type": "shorts",
        "title_template": "Best Fashion #shorts",
        "description_template": "Check this out!",
        "tags": "fashion,shorts",
        "is_active": True
    })
    if resp.status_code == 200:
        mat_id = resp.json()["id"]
        print(f"Material Config created. ID: {mat_id}")
    else:
        print(f"Material Config failed: {resp.text}")
        return

    # 8. Create Schedule
    print(f"--- Creating Schedule ---")
    resp = requests.post(f"{BASE_URL}/youtube/accounts/{acc1_id}/schedules", headers=headers, json={
        "cron_expression": "*/5 * * * *", # Every 5 minutes
        "is_active": True,
        "material_config_id": mat_id
    })
    if resp.status_code == 200:
        sched_id = resp.json()["id"]
        print(f"Schedule created. ID: {sched_id}")
    else:
        print(f"Schedule creation failed: {resp.text}")

if __name__ == "__main__":
    test_api()
