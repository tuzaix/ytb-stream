# Shark YouTube Manager Backend

## Setup

1.  **Environment**: Ensure you are in the `.venv311` environment.
    ```bash
    # Windows
    ..\.venv311\Scripts\activate
    ```

2.  **Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

3.  **Configuration**:
    Check `config.py` for database and file path configurations.

## Running the Server

Start the FastAPI server with Uvicorn:

```bash
uvicorn shark.main:app --reload --port 8000
```

The API documentation will be available at: http://127.0.0.1:8000/docs

## Features

*   **Authentication**: User registration and login (JWT).
*   **Membership System**: 
    *   Levels: Silver, Gold, Platinum, Diamond.
    *   Limits: YouTube accounts, FTP storage/speed.
*   **YouTube Account Management**:
    *   Create accounts (Triggers FTP user creation).
    *   Manage Material Configs (Title, Description, Tags).
    *   Schedule Uploads (Cron-based).

## Testing

Run the test script to verify the flow:

```bash
python test_api.py
```
