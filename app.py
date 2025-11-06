# ==============================================
# 🎧 BeatBuddy — Mood-Based Music Recommender (app.py)
# ==============================================
# Paste this file as `app.py`. Replace CLIENT_ID / CLIENT_SECRET
# with your Spotify credentials or set SPOTIFY_CLIENT_ID / SPOTIFY_CLIENT_SECRET env vars.
#
# Run:
#    pip install streamlit spotipy pandas
#    streamlit run app.py
# ==============================================

import os
import streamlit as st
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import pandas as pd

# ------------------------------------------------
# 🔐 STEP 1: SPOTIFY CREDENTIALS (env vars preferred)
# ------------------------------------------------
CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID", "2e0be09b2c5e4f4aaa2965fbbe3f08e1")
CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET", "16d3a882fdf84aefac24c0e93fff5e93")

# ------------------------------------------------
# 🎨 STEP 2: SETUP STREAMLIT PAGE + STYLES
# ------------------------------------------------
st.set_page_config(page_title="BeatBuddy — Mood Recommender 🎵", page_icon="🎧", layout="wide")
st.markdown(
    """
    <style>
    .app-header {
        background: linear-gradient(90deg, #0f172a 0%, #0ea5a9 100%);
        padding: 28px;
        border-radius: 12px;
        color: white;
        margin-bottom: 16px;
    }
    .card {
        background: white;
        border-radius: 12px;
        padding: 12px;
        box-shadow: 0 6px 18px rgba(14,21,34,0.06);
        margin-bottom: 12px;
    }
    .mood-badge {
        display:inline-block;
        padding:6px 10px;
        border-radius:999px;
        background:#eef2ff;
        color:#3730a3;
        font-weight:600;
    }
    .small-muted { color: #6b7280; font-size:0.92em }
    .chat-container { display:flex; flex-direction:column; gap:10px; }
    .user-bubble { align-self: flex-end; background:#0ea5a9; color:white; padding:10px 14px; border-radius:14px; max-width:75%; }
    .bot-bubble { align-self: flex-start; background:#f3f4f6; color:#0f172a; padding:10px 14px; border-radius:14px; max-width:75%; }
    </style>
    <div class="app-header">
      <h1 style="margin:0;">🎶 BeatBuddy — Mood-Based Music Recommender</h1>
      <div style="margin-top:6px;" class="small-muted">Tell me how you feel or paste song lyrics — I'll detect the mood and recommend tracks.</div>
    </div>
    """,
    unsafe_allow_html=True,
)

st.caption("English, Hindi & Punjabi Songs — Powered by Spotify API")

# ------------------------------------------------
# Defaults
# ------------------------------------------------
DEFAULT_LANGUAGE = "English"
DEFAULT_LATEST = True
DEFAULT_NUM_RESULTS = 10
DEFAULT_MOOD = "chill"

# ------------------------------------------------
# Spotify client helper (lazy, stored in session_state)
# ------------------------------------------------
def get_sp_client():
    if st.session_state.get("sp_client"):
        return st.session_state["sp_client"]

    if not CLIENT_ID or not CLIENT_SECRET:
        st.session_state["sp_error"] = "Missing Spotify credentials. Set SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET (or edit the file)."
        return None

    try:
        auth_manager = SpotifyClientCredentials(client_id=CLIENT_ID, client_secret=CLIENT_SECRET)
        sp = spotipy.Spotify(auth_manager=auth_manager)
        st.session_state["sp_client"] = sp
        return sp
    except Exception as e:
        st.session_state["sp_error"] = f"Spotify auth error: {e}"
        return None

# ------------------------------------------------
# Fetch songs from Spotify
# ------------------------------------------------
def fetch_songs(mood, language, latest, limit=10):
    sp = get_sp_client()
    if sp is None:
        return pd.DataFrame()

    query = f"{mood} {language} song"
    if latest:
        query += " year:2022-2025"

    try:
        results = sp.search(q=query, type="track", limit=limit, market="IN")
        tracks = []
        for item in results.get("tracks", {}).get("items", []):
            album = item.get("album", {})
            images = album.get("images") or []
            track = {
                "title": item.get("name"),
                "artist": (item.get("artists") or [{}])[0].get("name"),
                "album": album.get("name"),
                "release_date": album.get("release_date"),
                "url": item.get("external_urls", {}).get("spotify"),
                "image": images[0].get("url") if images else None,
            }
            tracks.append(track)
        return pd.DataFrame(tracks)
    except Exception as e:
        st.session_state["sp_error"] = f"Error fetching tracks: {e}"
        return pd.DataFrame()


# ------------------------------------------------
# General search helper (allows arbitrary query)
# ------------------------------------------------
def search_songs(query: str, language: str, latest: bool, limit: int = 10):
    sp = get_sp_client()
    if sp is None:
        return pd.DataFrame()

    q = query.strip()
    if language:
        q = f"{q} language:{language}"
    if latest:
        q = f"{q} year:2022-2025"

    try:
        results = sp.search(q=q, type="track", limit=limit, market="IN")
        tracks = []
        for item in results.get("tracks", {}).get("items", []):
            album = item.get("album", {})
            images = album.get("images") or []
            track = {
                "title": item.get("name"),
                "artist": (item.get("artists") or [{}])[0].get("name"),
                "album": album.get("name"),
                "release_date": album.get("release_date"),
                "url": item.get("external_urls", {}).get("spotify"),
                "image": images[0].get("url") if images else None,
            }
            tracks.append(track)
        return pd.DataFrame(tracks)
    except Exception as e:
        st.session_state["sp_error"] = f"Error searching tracks: {e}"
        return pd.DataFrame()

# ------------------------------------------------
# Simple rule-based mood detector
# ------------------------------------------------
def detect_mood_from_text(text: str) -> str:
    if not text or not text.strip():
        return DEFAULT_MOOD

    t = text.lower()

    # emoji hints
    emoji_map = {
        "😊": "happy",
        "🙂": "happy",
        "😄": "happy",
        "😃": "happy",
        "😂": "happy",
        "😍": "romantic",
        "❤️": "romantic",
        "💖": "romantic",
        "😢": "sad",
        "😭": "sad",
        "😞": "sad",
        "🎉": "party",
        "🎶": "chill",
        "🔥": "energetic",
    }

    mood_keywords = {
        "happy": ["happy", "joy", "joyful", "smile", "sun", "wonderful", "blessed", "cheer", "yay", "glad"],
        "sad": ["sad", "tears", "cry", "lonely", "broken", "hurt", "goodbye", "miss you", "pain", "sorrow"],
        "romantic": ["love", "darling", "baby", "forever", "kiss", "heart", "romance", "romantic", "beloved"],
        "energetic": ["dance", "party", "pump", "energy", "run", "jump", "beat", "rock", "hype"],
        "chill": ["chill", "calm", "relax", "smooth", "easy", "breathe", "mellow", "laid back"],
        "party": ["party", "club", "night", "shots", "crowd", "celebrate", "turn up", "fest"],
    }

    scores = {k: 0 for k in mood_keywords}

    # emoji scoring
    for e, m in emoji_map.items():
        if e in text:
            scores[m] += 2

    # keyword scoring with basic negation handling
    negations = ["not ", "never ", "no ", "don't ", "cant ", "can't "]
    for mood, keys in mood_keywords.items():
        for kw in keys:
            if kw in t:
                negated = any(neg in t and t.find(neg) < t.find(kw) and t.find(kw) - t.find(neg) < 12 for neg in negations)
                scores[mood] += -1 if negated else 1

    # fallback heuristics
    if all(v == 0 for v in scores.values()):
        if any(w in t for w in ["!", "yay", "whoa", "yeah"]):
            return "happy"
        if any(w in t for w in ["sad", "cry", "tears"]):
            return "sad"
        return DEFAULT_MOOD

    best = max(scores.items(), key=lambda kv: kv[1])[0]
    return best

# ------------------------------------------------
# Views: recommendations page (open in new tab) or main chat UI
# ------------------------------------------------

# ------- User / Login UI (simple in-memory store) -------
def init_user_store():
    if "users" not in st.session_state:
        st.session_state["users"] = {"demo": "demo"}
    if "saved_tracks" not in st.session_state:
        st.session_state["saved_tracks"] = {}
    if "view_local" not in st.session_state:
        st.session_state["view_local"] = None

def register_user(username: str, password: str) -> bool:
    init_user_store()
    if not username or not password:
        return False
    if username in st.session_state["users"]:
        return False
    st.session_state["users"][username] = password
    st.session_state["saved_tracks"][username] = []
    return True

def login_user(username: str, password: str) -> bool:
    init_user_store()
    if st.session_state["users"].get(username) == password:
        st.session_state["user"] = username
        if username not in st.session_state["saved_tracks"]:
            st.session_state["saved_tracks"][username] = []
        return True
    return False

def logout_user():
    if st.session_state.get("user"):
        del st.session_state["user"]


init_user_store()


def safe_rerun():
    """Rerun the Streamlit script using the supported API when available.
    Falls back to toggling a query-param to force a rerun if experimental_rerun is missing.
    """
    try:
        if hasattr(st, "experimental_rerun"):
            st.experimental_rerun()
            return
    except Exception:
        pass
    # fallback: toggle a dummy query param to force a rerun
    try:
        qp = st.query_params or {}
        qp["_rerun"] = [str(int(pd.Timestamp.now().timestamp()))]
        st.experimental_set_query_params(**qp)
    except Exception:
        # last resort: stop the script (Streamlit will reload on user refresh)
        try:
            st.stop()
        except Exception:
            pass

# Render a compact login/register area at the top
if st.session_state.get("user"):
    user = st.session_state.get("user")
    cols = st.columns([4, 1, 1])
    with cols[0]:
        st.markdown(f"<div style='padding:8px'>Welcome back, <strong>{user}</strong> — your dashboard is available.</div>", unsafe_allow_html=True)
    with cols[1]:
        if st.button("Dashboard"):
            st.session_state["view_local"] = "dashboard"
    with cols[2]:
        if st.button("Logout"):
            logout_user()
            safe_rerun()
else:
    st.markdown("<div class='card'><strong>Login or Register</strong></div>", unsafe_allow_html=True)
    lu, lp = st.columns([2, 2])
    with lu:
        login_user_in = st.text_input("Username", key="login_user")
    with lp:
        login_pass_in = st.text_input("Password", type="password", key="login_pass")
    if st.button("Login"):
        ok = login_user(login_user_in, login_pass_in)
        if ok:
            st.success("Logged in")
            safe_rerun()
        else:
            st.error("Login failed. Try demo/demo or register.")
    if st.button("Register"):
        ok = register_user(login_user_in, login_pass_in)
        if ok:
            st.success("Registered — you can now login")
        else:
            st.error("Register failed (user exists or invalid input)")

# read query params using non-deprecated API
# After login: provide a simple search UI for logged-in users
if st.session_state.get("user"):
    st.markdown("<div class='card'><h3>Search songs</h3></div>", unsafe_allow_html=True)
    cols = st.columns([3, 1, 1])
    with cols[0]:
        search_query = st.text_input("Search (genre, keyword, artist, or mood):", key="search_query")
    with cols[1]:
        search_language = st.selectbox("Language:", ["English", "Hindi", "Punjabi"], index=0, key="search_language")
    with cols[2]:
        search_latest = st.checkbox("Latest only", value=True, key="search_latest")

    search_limit = st.slider("Results", 5, 30, 10, key="search_limit")
    if st.button("Search"):
        if not search_query or not search_query.strip():
            st.warning("Please enter a search term (genre, keyword, artist, or mood).")
        else:
            with st.spinner("Searching Spotify..."):
                sr = search_songs(search_query, search_language, search_latest, int(search_limit))
            st.session_state["search_results"] = sr

    # show search results (if any)
    if st.session_state.get("search_results") is not None:
        dfsr = st.session_state.get("search_results")
        if dfsr.empty:
            st.info("No results found for your search.")
        else:
            st.markdown(f"<div class='small-muted' style='margin-bottom:8px'>Showing {len(dfsr)} results. You can save tracks to your dashboard.</div>", unsafe_allow_html=True)
            for idx, row in dfsr.iterrows():
                st.markdown("<div class='card' style='display:flex; gap:12px; align-items:center;'>", unsafe_allow_html=True)
                cols = st.columns([1, 4])
                with cols[0]:
                    if row.get("image"):
                        st.image(row.get("image"), width=100)
                with cols[1]:
                    st.markdown(f"### {row.get('title')}")
                    st.write(f"**{row.get('artist')}** — {row.get('album')}")
                    st.write(f"📅 {row.get('release_date')}")
                    if row.get('url'):
                        st.markdown(f"[▶️ Listen on Spotify]({row.get('url')})")
                    user = st.session_state.get('user')
                    if st.button('Save to dashboard', key=f'save_search_{idx}'):
                        st.session_state['saved_tracks'].setdefault(user, []).append({
                            'title': row.get('title'),
                            'artist': row.get('artist'),
                            'album': row.get('album'),
                            'release_date': row.get('release_date'),
                            'url': row.get('url'),
                            'image': row.get('image')
                        })
                        st.success('Saved to your dashboard')
                st.markdown("</div>", unsafe_allow_html=True)

qp = st.query_params
    

# Dashboard view (local, per-browser)
if st.session_state.get("view_local") == "dashboard" and st.session_state.get("user"):
    st.markdown("<div class='card'><h2>Your Dashboard</h2></div>", unsafe_allow_html=True)
    user = st.session_state.get("user")
    saved = st.session_state.get("saved_tracks", {}).get(user, [])
    if not saved:
        st.info("You have no saved tracks yet. Save recommendations to see them here.")
    else:
        for idx, t in enumerate(saved):
            st.markdown("<div class='card' style='display:flex; gap:12px; align-items:center;'>", unsafe_allow_html=True)
            cols = st.columns([1, 4])
            with cols[0]:
                if t.get("image"):
                    st.image(t.get("image"), width=120)
            with cols[1]:
                st.markdown(f"### {t.get('title')}")
                st.write(f"**{t.get('artist')}** — {t.get('album')}")
                st.write(f"📅 {t.get('release_date')}")
                if t.get('url'):
                    st.markdown(f"[▶️ Listen on Spotify]({t.get('url')})")
                if st.button(f"Remove", key=f"remove_{idx}"):
                    st.session_state['saved_tracks'][user].pop(idx)
                    safe_rerun()
            st.markdown("</div>", unsafe_allow_html=True)

    if st.button("Back"):
        st.session_state["view_local"] = None
        safe_rerun()

if qp.get("view", [None])[0] == "recommend":
    # Recommendation view (opened in a new tab)
    mood_q = qp.get("mood", [DEFAULT_MOOD])[0]
    language_q = qp.get("language", [DEFAULT_LANGUAGE])[0]
    latest_q = qp.get("latest", [str(DEFAULT_LATEST)])[0].lower() in ("1", "true", "yes")
    try:
        num_q = int(qp.get("num_results", [str(DEFAULT_NUM_RESULTS)])[0])
    except ValueError:
        num_q = DEFAULT_NUM_RESULTS

    st.markdown(f"<div class='card'><h2>Recommendations for mood: <span class='mood-badge'>{mood_q}</span></h2></div>", unsafe_allow_html=True)
    with st.spinner("Fetching recommendations..."):
        df = fetch_songs(mood_q, language_q, latest_q, num_q)

    if df.empty:
        if st.session_state.get("sp_error"):
            st.error("Spotify authentication or network error.")
            st.write(st.session_state.get("sp_error"))
        else:
            st.warning("No songs found for the selected mood / filters.")
    else:
        for idx, row in df.iterrows():
            st.markdown("<div class='card' style='display:flex; gap:12px; align-items:center;'>", unsafe_allow_html=True)
            cols = st.columns([1, 4])
            with cols[0]:
                if row.get("image"):
                    st.image(row.get("image"), width=120)
            with cols[1]:
                st.markdown(f"### {row.get('title')}")
                st.write(f"**{row.get('artist')}** — {row.get('album')}")
                st.write(f"📅 {row.get('release_date')}")
                if row.get("url"):
                    st.markdown(f"[▶️ Listen on Spotify]({row.get('url')})")
                # Save to dashboard (requires login)
                if st.session_state.get('user'):
                    user = st.session_state.get('user')
                    if st.button('Save to dashboard', key=f'save_rec_{idx}'):
                        st.session_state['saved_tracks'].setdefault(user, []).append({
                            'title': row.get('title'),
                            'artist': row.get('artist'),
                            'album': row.get('album'),
                            'release_date': row.get('release_date'),
                            'url': row.get('url'),
                            'image': row.get('image')
                        })
                        st.success('Saved to your dashboard')
                else:
                    st.markdown("<div class='small-muted'>Login to save tracks to your dashboard.</div>", unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("[← Back to BeatBuddy](./)")

else:
    # ------------------------------
    # Main chat UI
    # ------------------------------
    if "messages" not in st.session_state:
        st.session_state["messages"] = [
            {"from": "bot", "text": "Hello! I'm BeatBuddy. How are you feeling today? Tell me in a few words or paste song lyrics."}
        ]

    def render_chat():
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.subheader("Chat with BeatBuddy")
        st.markdown("<div class='chat-container'>", unsafe_allow_html=True)
        for m in st.session_state["messages"]:
            if m["from"] == "user":
                st.markdown(f"<div class='user-bubble'>{m['text']}</div>", unsafe_allow_html=True)
            else:
                st.markdown(f"<div class='bot-bubble'>{m['text']}</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    render_chat()

    # Top prompt area (chat style)
    user_text = st.text_input("You:", value="", key="chat_input")
    col1, col2 = st.columns([1, 1])
    with col1:
        send = st.button("Send")
    with col2:
        recommend_quick = st.button("Recommend for latest mood")

    # Quick mood buttons
    st.markdown("---")
    st.markdown("**Quick moods:**")
    moods = ["happy", "sad", "romantic", "energetic", "chill", "party"]
    cols = st.columns(len(moods))
    for i, m in enumerate(moods):
        if cols[i].button(m.title()):
            st.session_state["messages"].append({"from": "user", "text": m})
            st.session_state["messages"].append({"from": "bot", "text": f"Got it — you'll get {m} songs. Open recommendations?"})
            render_chat()
            params = {"view": "recommend", "mood": m, "language": DEFAULT_LANGUAGE, "latest": str(DEFAULT_LATEST).lower(), "num_results": str(DEFAULT_NUM_RESULTS)}
            # build query string
            qs = "&".join([f"{k}={v}" for k, v in params.items()])
            recommend_url = f"./?{qs}"
            st.markdown(f"<div style='margin-top:8px'><a target='_blank' href='{recommend_url}' style='background:#0ea5a9;color:white;padding:10px 14px;border-radius:10px;text-decoration:none;'>Open recommendations in a new tab</a></div>", unsafe_allow_html=True)

    # handle send
    if send and user_text:
        st.session_state["messages"].append({"from": "user", "text": user_text})
        detected = detect_mood_from_text(user_text)
        bot_reply = f"I think you're feeling *{detected}*. Would you like me to recommend some songs for that mood?"
        st.session_state["messages"].append({"from": "bot", "text": bot_reply})
        render_chat()

        # recommend link
        params = {"view": "recommend", "mood": detected, "language": DEFAULT_LANGUAGE, "latest": str(DEFAULT_LATEST).lower(), "num_results": str(DEFAULT_NUM_RESULTS)}
        qs = "&".join([f"{k}={v}" for k, v in params.items()])
        recommend_url = f"./?{qs}"
        st.markdown(f"<div style='margin-top:8px'><a target='_blank' href='{recommend_url}' style='background:#0ea5a9;color:white;padding:10px 14px;border-radius:10px;text-decoration:none;'>Open recommendations in a new tab</a></div>", unsafe_allow_html=True)

    # quick recommend button uses the last bot-detected mood or default
    if recommend_quick:
        # find last user message
        last_user = next((m for m in reversed(st.session_state["messages"]) if m["from"] == "user"), None)
        if last_user:
            detected = detect_mood_from_text(last_user["text"])
        else:
            detected = DEFAULT_MOOD
        params = {"view": "recommend", "mood": detected, "language": DEFAULT_LANGUAGE, "latest": str(DEFAULT_LATEST).lower(), "num_results": str(DEFAULT_NUM_RESULTS)}
        qs = "&".join([f"{k}={v}" for k, v in params.items()])
        recommend_url = f"./?{qs}"
        st.markdown(f"<div style='margin-top:8px'><a target='_blank' href='{recommend_url}' style='background:#0ea5a9;color:white;padding:10px 14px;border-radius:10px;text-decoration:none;'>Open recommendations in a new tab</a></div>", unsafe_allow_html=True)

    # Main area below shows a more detailed "detect + recommend" panel
    st.markdown("---")
    left, right = st.columns([2, 3])

    with left:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.subheader("Know your mood — automatically")
        text_input = st.text_area("Describe your mood or paste lyrics:", height=140, key="d_text")
        auto_detect = st.checkbox("Auto-detect mood from text", value=True, key="auto_detect")
        language = st.selectbox("Language:", ["English", "Hindi", "Punjabi"], index=0, key="ui_language")
        latest = st.checkbox("Only latest songs (after 2022)", value=DEFAULT_LATEST, key="ui_latest")
        num_results = st.slider("Number of results", 5, 20, DEFAULT_NUM_RESULTS, key="ui_num")
        manual_mood = st.selectbox("Or choose a mood manually:", ["(auto)", "happy", "sad", "romantic", "energetic", "chill", "party"], key="manual_mood")
        detect_btn = st.button("Detect Mood & Recommend 🎯", key="detect_btn")
        st.markdown("</div>", unsafe_allow_html=True)

    with right:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.subheader("Recommendations")
        mood_to_use = None

        if detect_btn:
            if manual_mood and manual_mood != "(auto)":
                mood_to_use = manual_mood
            elif auto_detect:
                mood_to_use = detect_mood_from_text(text_input)
            else:
                mood_to_use = DEFAULT_MOOD

            st.markdown(f"<div style='margin-bottom:8px'>Detected mood: <span class='mood-badge'>{mood_to_use}</span></div>", unsafe_allow_html=True)

            with st.spinner("Fetching recommended songs..."):
                df = fetch_songs(mood_to_use, language, latest, num_results)

            if df.empty:
                if st.session_state.get("sp_error"):
                    st.error("Spotify authentication or network error.")
                    st.write(st.session_state.get("sp_error"))
                else:
                    st.warning("No songs found. Try changing the mood / language / number of results.")
            else:
                st.success(f"Found {len(df)} {language} songs for mood: {mood_to_use}")
                for idx, row in df.iterrows():
                    st.markdown("<div class='card' style='display:flex; gap:12px; align-items:center;'>", unsafe_allow_html=True)
                    cols = st.columns([1, 4])
                    with cols[0]:
                        if row.get("image"):
                            st.image(row.get("image"), width=120)
                    with cols[1]:
                        st.markdown(f"### {row.get('title')}")
                        st.write(f"**{row.get('artist')}** — {row.get('album')}")
                        st.write(f"📅 {row.get('release_date')}")
                        if row.get("url"):
                            st.markdown(f"[▶️ Listen on Spotify]({row.get('url')})")
                        if st.session_state.get('user'):
                            user = st.session_state.get('user')
                            if st.button('Save to dashboard', key=f'save_det_{idx}'):
                                st.session_state['saved_tracks'].setdefault(user, []).append({
                                    'title': row.get('title'),
                                    'artist': row.get('artist'),
                                    'album': row.get('album'),
                                    'release_date': row.get('release_date'),
                                    'url': row.get('url'),
                                    'image': row.get('image')
                                })
                                st.success('Saved to your dashboard')
                        else:
                            st.markdown("<div class='small-muted'>Login to save tracks to your dashboard.</div>", unsafe_allow_html=True)
                    st.markdown("</div>", unsafe_allow_html=True)

        else:
            st.info("Click 'Detect Mood & Recommend' to get suggestions based on your text or chosen mood.")

        st.markdown("</div>", unsafe_allow_html=True)

# End of file
