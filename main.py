import os
import requests
from fastapi import FastAPI, HTTPException
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
import json

app = FastAPI(title="My Personal Dashboard API")

def get_google_service(api_name: str, api_version: str, token_filename: str):
    # Check if a cloud environment variable exists for this token
    env_var_name = token_filename.replace(".json", "").upper() # e.g., TOKEN_PRIMARY
    token_data = os.environ.get(env_var_name)
    
    if token_data:
        # Load credentials directly from the Render Environment Variable string
        creds_info = json.loads(token_data)
        creds = Credentials.from_authorized_user_info(creds_info)
    else:
        # Fall back to local file if running on your laptop
        if not os.path.exists(token_filename):
            raise HTTPException(status_code=404, detail=f"Token file '{token_filename}' not found.")
        creds = Credentials.from_authorized_user_file(token_filename)
        
    return build(api_name, api_version, credentials=creds)
# --- General & Projects ---
@app.get("/", tags=["General"])
def dashboard_root():
    return {"status": "Live", "message": "My Personal API Dashboard"}

@app.get("/api/projects", tags=["Projects"])
def get_projects():
    return {
        "status": "active",
        "featured": ["movie_ticket_system", "attendance_manager", "lab_safety_occupancy"]
    }

# --- Coding Profiles (GitHub & LeetCode) ---
@app.get("/api/github/{username}", tags=["Coding"])
def get_github_profile(username: str):
    url = f"https://api.github.com/users/{username}"
    headers = {"Accept": "application/vnd.github.v3+json"}
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail="GitHub user not found")
    return response.json()

@app.get("/api/leetcode/{username}", tags=["Coding"])
def get_leetcode_stats(username: str):
    url = "https://leetcode.com/graphql"
    query = {
        "query": """
        query getUserProfile($username: String!) {
            matchedUser(username: $username) {
                username
                submitStatsGlobal {
                    acSubmissionNum {
                        difficulty
                        count
                    }
                }
            }
        }
        """,
        "variables": {"username": username}
    }
    response = requests.post(url, json=query)
    return response.json()

# --- Spotify (Single Account) ---
@app.get("/api/spotify/currently-playing", tags=["Media"])
def get_currently_playing():
    token = os.environ.get("SPOTIFY_ACCESS_TOKEN")
    if not token:
        raise HTTPException(status_code=400, detail="SPOTIFY_ACCESS_TOKEN environment variable not set.")
        
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get("https://api.spotify.com/v1/me/player/currently-playing", headers=headers)
    
    if response.status_code == 204 or not response.content:
        return {"status": "Idle", "message": "No music currently playing"}
        
    return response.json()

# --- Google Calendar & Tasks (Primary Account) ---
@app.get("/api/calendar", tags=["Productivity"])
def get_upcoming_events():
    service = get_google_service("calendar", "v3", "token_primary.json")
    events = service.events().list(calendarId="primary", maxResults=5, singleEvents=True, orderBy="startTime").execute()
    return events.get("items", [])

@app.get("/api/tasks", tags=["Productivity"])
def get_tasks():
    service = get_google_service("tasks", "v1", "token_primary.json")
    tasklists = service.tasklists().list(maxResults=5).execute()
    return tasklists.get("items", [])

# --- YouTube (Multi-Account) ---
@app.get("/api/youtube/{account_name}/liked", tags=["Media"])
def get_liked_videos(account_name: str):
    token_file = f"token_{account_name}.json"
    service = get_google_service("youtube", "v3", token_file)
    request = service.videos().list(part="snippet,contentDetails", myRating="like", maxResults=5)
    return request.execute().get("items", [])


from fastapi.responses import HTMLResponse

@app.get("/", response_class=HTMLResponse)
async def serve_dashboard():
    try:
        with open("index.html", "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return {"status": "Live", "message": "My Personal API Dashboard"}

from pathlib import Path
from fastapi.responses import HTMLResponse

# ... your other API routes (like /api/calendar, /api/tasks, etc.) are above here ...

# Get the directory where main.py is located
BASE_DIR = Path(__file__).resolve().parent



@app.get("/", response_class=HTMLResponse)
async def serve_dashboard():
    html_path = BASE_DIR / "index.html"
    if html_path.exists():
        return html_path.read_text(encoding="utf-8")
    return f"Looking for index.html here: {html_path}, but it doesn't exist!"