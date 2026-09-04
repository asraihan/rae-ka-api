import os
import requests
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
import json

app = FastAPI(title="My Personal Dashboard API")

def get_google_service(api_name: str, api_version: str, token_filename: str):
    env_var_name = token_filename.replace(".json", "").upper()
    token_data = os.environ.get(env_var_name)
    
    if token_data:
        creds_info = json.loads(token_data)
        creds = Credentials.from_authorized_user_info(creds_info)
    else:
        if not os.path.exists(token_filename):
            raise HTTPException(status_code=404, detail=f"Token file '{token_filename}' not found.")
        creds = Credentials.from_authorized_user_file(token_filename)
        
    return build(api_name, api_version, credentials=creds)

# --- General & Projects ---
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

# --- Spotify ---
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

# --- Google Calendar & Tasks ---
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

# --- YouTube ---
@app.get("/api/youtube/{account_name}/liked", tags=["Media"])
def get_liked_videos(account_name: str):
    token_file = f"token_{account_name}.json"
    service = get_google_service("youtube", "v3", token_file)
    request = service.videos().list(part="snippet,contentDetails", myRating="like", maxResults=5)
    return request.execute().get("items", [])

# --- Apple-Styled Frontend Dashboard ---
APPLE_DASHBOARD_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Raihan — Personal Command Center</title>
    <style>
        :root {
            --bg-color: #000000;
            --card-bg: rgba(28, 28, 30, 0.7);
            --text-primary: #f5f5f7;
            --text-secondary: #86868b;
            --accent: #2997ff;
            --border: rgba(255, 255, 255, 0.1);
        }
        body {
            font-family: -apple-system, BlinkMacSystemFont, "SF Pro Display", "SF Pro Text", "Helvetica Neue", sans-serif;
            background-color: var(--bg-color);
            color: var(--text-primary);
            margin: 0;
            padding: 60px 20px;
            -webkit-font-smoothing: antialiased;
        }
        .container { max-width: 1000px; margin: 0 auto; }
        header { text-align: center; margin-bottom: 60px; }
        h1 {
            font-size: 3.5rem; font-weight: 600; letter-spacing: -0.015em; margin: 0 0 10px 0;
            background: linear-gradient(180deg, #ffffff 0%, #a1a1a6 100%);
            -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        }
        p.subtitle { font-size: 1.2rem; color: var(--text-secondary); margin: 0; }
        .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; }
        .card {
            background-color: var(--card-bg); backdrop-filter: blur(20px); -webkit-backdrop-filter: blur(20px);
            border: 1px solid var(--border); border-radius: 20px; padding: 30px; box-shadow: 0 20px 40px rgba(0,0,0,0.5);
        }
        .card h2 { font-size: 1.4rem; font-weight: 500; margin-top: 0; margin-bottom: 20px; color: var(--text-primary); }
        .metric-display { font-size: 2.5rem; font-weight: 600; color: var(--accent); margin-bottom: 15px; }
        .data-list { list-style: none; padding: 0; margin: 0; max-height: 200px; overflow-y: auto; }
        .data-list li { padding: 10px 0; border-bottom: 1px solid var(--border); font-size: 0.95rem; color: var(--text-secondary); }
        .loading { color: var(--text-secondary); font-style: italic; }
        
        /* New CSS to make the YouTube card look clickable */
        .clickable { cursor: pointer; transition: opacity 0.2s; }
        .clickable:hover { opacity: 0.8; }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>Dashboard.</h1>
            <p class="subtitle">Personal Quantified-Self & System Status</p>
        </header>
        <div class="grid">
            <div class="card">
                <h2>Google Tasks</h2>
                <div id="tasks-metric" class="loading">Loading tasks...</div>
                <ul id="tasks-list" class="data-list"></ul>
            </div>
            <div class="card">
                <h2>Upcoming Calendar</h2>
                <ul id="calendar-list" class="data-list"><li class="loading">Loading schedule...</li></ul>
            </div>
            <div class="card">
                <h2>Developer Metrics</h2>
                <div id="github-metric" class="loading">Loading profile...</div>
            </div>
            <div class="card">
                <h2>Active Projects</h2>
                <ul id="projects-list" class="data-list"><li class="loading">Loading projects...</li></ul>
            </div>
            
            <!-- NEW YOUTUBE CARD -->
            <div class="card">
                <h2>YouTube Metrics</h2>
                <div id="youtube-metric" class="loading clickable" onclick="toggleYouTubeList()">Loading videos...</div>
                <ul id="youtube-list" class="data-list" style="display: none; margin-top: 15px;"></ul>
            </div>
        </div>
    </div>
    <script>
        const API_BASE = window.location.origin;

        // The JavaScript function that handles the click!
        function toggleYouTubeList() {
            const list = document.getElementById("youtube-list");
            if (list.style.display === "none") {
                list.style.display = "block";
            } else {
                list.style.display = "none";
            }
        }

        async function loadDashboard() {
            try {
                const res = await fetch(`${API_BASE}/api/calendar`);
                const events = await res.json();
                const calList = document.getElementById("calendar-list");
                calList.innerHTML = "";
                if(events.length === 0) {
                    calList.innerHTML = "<li>No upcoming events</li>";
                } else {
                    events.forEach(ev => {
                        const li = document.createElement("li");
                        const time = ev.start.dateTime || ev.start.date;
                        li.textContent = `${ev.summary} (${new Date(time).toLocaleDateString()})`;
                        calList.appendChild(li);
                    });
                }
            } catch(e) { document.getElementById("calendar-list").innerHTML = "<li>Failed to load calendar</li>"; }

            try {
                const res = await fetch(`${API_BASE}/api/projects`);
                const data = await res.json();
                const projList = document.getElementById("projects-list");
                projList.innerHTML = "";
                data.featured.forEach(proj => {
                    const li = document.createElement("li");
                    li.textContent = proj.replaceAll("_", " ").toUpperCase();
                    projList.appendChild(li);
                });
            } catch(e) { document.getElementById("projects-list").innerHTML = "<li>Failed to load projects</li>"; }

            try {
                const res = await fetch(`${API_BASE}/api/github/asraihan`);
                const data = await res.json();
                document.getElementById("github-metric").innerHTML = `
                    <div class="metric-display">${data.public_repos}</div>
                    <div style="color: #86868b; font-size: 0.9rem;">Public Repositories on GitHub</div>
                `;
            } catch(e) { document.getElementById("github-metric").textContent = "Could not load stats"; }

            try {
                const res = await fetch(`${API_BASE}/api/tasks`);
                const data = await res.json();
                const taskMetric = document.getElementById("tasks-metric");
                const taskList = document.getElementById("tasks-list");
                taskList.innerHTML = "";
                let totalLists = data.length || 0;
                taskMetric.innerHTML = `
                    <div class="metric-display">${totalLists}</div>
                    <div style="color: #86868b; font-size: 0.9rem;">Active Task Lists Connected</div>
                `;
                data.forEach(list => {
                    const li = document.createElement("li");
                    li.textContent = `List: ${list.title}`;
                    taskList.appendChild(li);
                });
            } catch(e) { document.getElementById("tasks-metric").textContent = "Could not load tasks"; }

            // NEW YOUTUBE FETCH CODE
            try {
                // Hitting your existing YouTube liked videos route, using 'primary' as the account
                const res = await fetch(`${API_BASE}/api/youtube/primary/liked`);
                const videos = await res.json();
                
                const ytMetric = document.getElementById("youtube-metric");
                const ytList = document.getElementById("youtube-list");
                ytList.innerHTML = "";
                
                let totalVideos = videos.length || 0;
                ytMetric.innerHTML = `
                    <div class="metric-display">${totalVideos}</div>
                    <div style="color: #86868b; font-size: 0.9rem;">Liked Videos (Tap to expand list)</div>
                `;
                
                if (totalVideos === 0) {
                    ytList.innerHTML = "<li>No liked videos found</li>";
                } else {
                    videos.forEach(vid => {
                        const li = document.createElement("li");
                        // Grab the title from the YouTube snippet data
                        li.textContent = vid.snippet ? vid.snippet.title : "Unknown Video";
                        ytList.appendChild(li);
                    });
                }
            } catch(e) { 
                document.getElementById("youtube-metric").textContent = "Could not load YouTube stats"; 
            }
        }
        
        loadDashboard();
    </script>
</body>
</html>
"""
@app.get("/", response_class=HTMLResponse, tags=["General"])
async def serve_dashboard():
    return APPLE_DASHBOARD_HTML