import streamlit as st
import pandas as pd
import requests
import time
import os
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv
from firestore_client import get_telemetry, get_events, db
from analytics import (
    occupancy_frequency, 
    fan_usage_time,
    led_usage_time,
    occupancy_duration,
    manual_override_stats,
    automation_efficiency,
    system_response_time
)

# Load environment variables from .env file
load_dotenv()

st.set_page_config(
    page_title="Smart Room Occupancy Monitoring and Energy Efficient Dashboard",
    layout="wide"
)

# =========================================================
# CONFIGURATION
# =========================================================
FIREBASE_API_KEY = os.environ.get("FIREBASE_API_KEY")
if not FIREBASE_API_KEY:
    st.error("FIREBASE_API_KEY not found in environment variables")
    st.stop()

REFRESH_INTERVAL_SECONDS = 3  # Auto-refresh every 3 seconds

# =========================================================
# SESSION STATE
# =========================================================
if "user" not in st.session_state:
    st.session_state.user = None

# =========================================================
# ADMIN CHECK
# =========================================================
def is_admin(uid):
    doc = db.collection("users").document(uid).get()
    return doc.exists and doc.to_dict().get("role") == "admin"

# =========================================================
# LOGIN PAGE
# =========================================================
def login():
    st.title("Dashboard Login")
    st.caption("Smart Room Occupancy and Energy Efficient System")
    st.markdown("---")
    
    with st.form("login_form"):
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            email = st.text_input("Email", placeholder="Enter your email")
            password = st.text_input("Password", type="password", placeholder="Enter your password")
            submit = st.form_submit_button("Login", width='stretch')
            
            if submit:
                payload = {
                    "email": email,
                    "password": password,
                    "returnSecureToken": True
                }
                
                try:
                    r = requests.post(
                        f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={FIREBASE_API_KEY}",
                        json=payload
                    )
                    
                    if r.status_code == 200:
                        data = r.json()
                        uid = data["localId"]
                        
                        # Check if user is admin
                        if not is_admin(uid):
                            st.error("Access denied. Admin privileges required.")
                            st.stop()
                        
                        # Set user session
                        st.session_state.user = {
                            "email": email,
                            "uid": uid
                        }
                        st.success("Login successful!")
                        st.rerun()
                    else:
                        st.error("Invalid email or password")
                except Exception as e:
                    st.error(f"Login error: {str(e)}")

# Logout function
def logout():
    st.session_state.user = None
    st.rerun()

# Check authentication - show login if not authenticated
if st.session_state.user is None:
    login()
    st.stop()

# Logout button in sidebar
with st.sidebar:
    st.markdown("### User Session")
    st.write(f"**Email:** {st.session_state.user['email']}")
    if st.button("🚪 Logout", width='stretch'):
        logout()
    
    st.divider()
    st.markdown("### 🔄 Auto-Refresh")
    st.info(f"Dashboard refreshes every {REFRESH_INTERVAL_SECONDS} seconds")

# Timezone conversion helper for Malaysia time (UTC+8)
def to_malaysia_time(timestamp_str):
    """Convert UTC timestamp to Malaysia time (UTC+8)"""
    try:
        # Parse the timestamp
        if "T" in timestamp_str:
            dt = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
        else:
            dt = datetime.fromisoformat(timestamp_str)
        
        # If timezone-naive, assume UTC
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        
        # Convert to Malaysia time (UTC+8)
        malaysia_tz = timezone(timedelta(hours=8))
        dt_malaysia = dt.astimezone(malaysia_tz)
        
        return dt_malaysia.strftime("%Y-%m-%d"), dt_malaysia.strftime("%H:%M:%S")
    except:
        return timestamp_str[:10], timestamp_str[11:19]

st.title("🏠 Smart Room Energy Dashboard")

# Room selector at the top
col1, col2 = st.columns([1, 3])
with col1:
    rooms = ["room_01"]
    selected_room = st.selectbox("📍 Select Room", rooms, index=0)

st.divider()

telemetry = get_telemetry()
events = get_events()

if not telemetry:
    st.warning("No telemetry data available yet.")
    st.stop()

# Filter data by selected room
telemetry = [t for t in telemetry if t.get("device_id") == selected_room]
events = [e for e in events if e.get("device_id") == selected_room]

if not telemetry:
    st.warning(f"No data available for {selected_room}")
    st.stop()

latest = telemetry[-1]

# Create tabs for better organization
tab1, tab2 = st.tabs(["📊 Overview", "📈 Analytics & History"])

# ===== TAB 1: OVERVIEW =====
with tab1:
    # Current Room Status
    st.subheader("Current Room Status")
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        occupancy = latest.get("occupied", 0)
        st.metric("Occupancy", 
                 "🟢 Occupied" if occupancy else "⚪ Empty",
                 delta=None)
    
    with col2:
        fan_status = latest.get("fan", 0)
        st.metric("Fan", 
                 "🟢 ON" if fan_status else "⚫ OFF")
    
    with col3:
        led_status = latest.get("led", 0)
        st.metric("Lamp", 
                 "🟢 ON" if led_status else "⚫ OFF")
    
    with col4:
        fan_override = latest.get("fan_override", 0)
        st.metric("Fan Control", 
                 "Manual" if fan_override else "Auto",
                 delta="Override" if fan_override else "Automated",
                 delta_color="off" if fan_override else "normal")
    
    with col5:
        led_override = latest.get("led_override", 0)
        st.metric("Lamp Control", 
                 "Manual" if led_override else "Auto",
                 delta="Override" if led_override else "Automated",
                 delta_color="off" if led_override else "normal")
    
    st.divider()
    
    # Key Performance Indicators
    st.subheader("Key Performance Indicators")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        visits = occupancy_frequency(telemetry)
        st.metric("Times Entered", 
                 f"{visits}",
                 help="Number of times someone entered the room")
    
    with col2:
        fan_time = fan_usage_time(telemetry)
        hours = fan_time // 3600
        mins = (fan_time % 3600) // 60
        st.metric("Total Fan Runtime", 
                 f"{hours}h {mins}m",
                 help="Total time the fan was running")
    
    with col3:
        led_time = led_usage_time(telemetry)
        hours = led_time // 3600
        mins = (led_time % 3600) // 60
        st.metric("Total LED Runtime", 
                 f"{hours}h {mins}m",
                 help="Total time the LED was on")
    
    with col4:
        auto_eff = automation_efficiency(telemetry)
        st.metric("Automation Efficiency", 
                 f"{auto_eff['auto_pct']:.1f}%",
                 delta=f"{auto_eff['auto_count']} auto vs {auto_eff['manual_count']} manual",
                 delta_color="normal",
                 help="% of time system runs in auto mode")
    
    st.divider()
    
    # System Performance
    st.subheader("System Performance")
    
    col1, col2 = st.columns(2)
    
    with col1:
        response = system_response_time(telemetry)
        st.metric("Avg Response Time", 
                 f"{response['avg_seconds']:.2f}s",
                 delta=f"out of {response['count']} responses measured",
                 help="How quickly system reacts to occupancy changes")
    
    with col2:
        st.info("💡 **Note:** 15-second manual override timeout prevents energy waste")
    
    st.divider()
    
    # Recent Activity
    st.subheader("Recent Events (Last 10)")
    if events:
        recent_events = events[-10:]
        
        # Helper function to format event descriptions
        def format_event(event_type):
            descriptions = {
                "MANUAL_LED": "💡 Manual Override: Lamp",
                "MANUAL_FAN": "🌀 Manual Override: Fan",
                "AUTO_ON": "Fan & Lamp Auto ON",
                "AUTO_OFF": "⏸️ Fan & Lamp Auto OFF"
            }
            return descriptions.get(event_type, event_type)
        
        events_data = []
        for e in reversed(recent_events):
            date_my, time_my = to_malaysia_time(e.get("timestamp", "N/A"))
            events_data.append({
                "Date": date_my,
                "Time": time_my,
                "Description": format_event(e.get("event", "N/A"))
            })
        
        events_df = pd.DataFrame(events_data)
        st.dataframe(events_df, width='stretch', hide_index=True, height=250)
    else:
        st.info("No recent events")

# ===== TAB 2: ANALYTICS & HISTORY =====
with tab2:
    
    # Occupancy Duration Analysis
    st.subheader("⏱️ Visit Duration Analysis (Completed Visits)")
    occ_data = occupancy_duration(telemetry)
    
    col1, col2, col3 = st.columns(3)
    with col1:
        total_hours = occ_data["total_seconds"] // 3600
        total_mins = (occ_data["total_seconds"] % 3600) // 60
        st.metric("Total Time Occupied", 
                 f"{total_hours}h {total_mins}m",
                 help="Total duration the room was occupied")
    with col2:
        st.metric("Quick Visits (< 5 min)", 
                 f"{occ_data['short_visits']}",
                 help="Completed visits shorter than 5 minutes")
    with col3:
        st.metric("Extended Stays (> 30 min)", 
                 f"{occ_data['long_stays']}",
                 help="Completed visits longer than 30 minutes")
    
    st.divider()
    
    # Control Behavior Analysis
    st.subheader("🎛️ Control Behavior: Manual vs Automatic")
    if events:
        override_stats = manual_override_stats(events)
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Manual LED Controls", override_stats["manual_led"])
        with col2:
            st.metric("Manual Fan Controls", override_stats["manual_fan"])
        with col3:
            st.metric("Automatic Events", override_stats["total_auto"])
        
        # Chart
        chart_data = pd.DataFrame({
            "Type": ["Manual LED", "Manual Fan", "Auto ON", "Auto OFF"],
            "Count": [override_stats["manual_led"], override_stats["manual_fan"], 
                     override_stats["auto_on"], override_stats["auto_off"]]
        })
        
        if chart_data["Count"].sum() > 0:
            import altair as alt
            chart = alt.Chart(chart_data).mark_bar(color='steelblue').encode(
                x=alt.X('Type:N', axis=alt.Axis(labelAngle=0, title='Control Type')),
                y=alt.Y('Count:Q', title='Number of Events')
            ).properties(height=300)
            st.altair_chart(chart, width='stretch')
    else:
        st.info("No event data available yet.")
    
    st.divider()
    
    # Full Event Log
    st.subheader("📋 Complete Event Log")
    if events:
        # Helper function to format event descriptions
        def format_event_detail(event_type):
            descriptions = {
                "MANUAL_LED": "💡 Manual Override: Lamp",
                "MANUAL_FAN": "🌀 Manual Override: Fan",
                "AUTO_ON": "Fan & Lamp Auto ON",
                "AUTO_OFF": "⏸️ Fan & Lamp Auto OFF"
            }
            return descriptions.get(event_type, event_type)
        
        events_data = []
        for e in reversed(events):
            date_my, time_my = to_malaysia_time(e.get("timestamp", "N/A"))
            events_data.append({
                "Device": e.get("device_id", "N/A"),
                "Action": format_event_detail(e.get("event", "N/A")),
                "Date": date_my,
                "Time": time_my
            })
        
        events_df = pd.DataFrame(events_data)
        st.dataframe(events_df, width='stretch', hide_index=True, height=400)
    else:
        st.info("No events recorded yet.")

# =========================================================
# AUTO-REFRESH (at the end so dashboard loads first)
# =========================================================
time.sleep(REFRESH_INTERVAL_SECONDS)
st.rerun()
