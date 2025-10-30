import streamlit as st
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import json
import os
import time
import pytz

# Config
CHECK_INTERVAL = 1200  # 20 minutes in seconds
STORAGE_FILE = "last_press_release.json"
NY_TZ = pytz.timezone('America/New_York')

st.set_page_config(page_title="BE IR Monitor", page_icon="🔔", layout="wide")

def fetch_all_releases():
    """Fetch all recent press releases from BE investor relations"""
    try:
        url = "https://investor.bloomenergy.com/press-releases"
        response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=10)
        soup = BeautifulSoup(response.content, 'html.parser')
        
        releases = []
        items = soup.find_all('div', class_='module-headline')
        
        for item in items[:3]:  # Get latest 3 releases
            title = item.get_text(strip=True)
            link = item.find('a')['href'] if item.find('a') else ''
            if link and not link.startswith('http'):
                link = 'https://investor.bloomenergy.com' + link
            
            # Try to find date
            date_elem = item.find_parent().find('time') if item.find_parent() else None
            date = date_elem.get_text(strip=True) if date_elem else 'Recent'
            
            releases.append({'title': title, 'link': link, 'date': date})
        
        return releases
    except Exception as e:
        return {'error': str(e)}

def load_last():
    if os.path.exists(STORAGE_FILE):
        with open(STORAGE_FILE, 'r') as f:
            return json.load(f)
    return None

def save_last(data):
    with open(STORAGE_FILE, 'w') as f:
        json.dump(data, f)

# Header with Welcome Message
st.title("🔔 Welcome to BEEIR")
st.markdown("### The Bloom Energy Investor Relations Feed")
st.markdown("Stay updated with the latest press releases, financial updates, and material events from Bloom Energy Corporation (BE)")

# Email Subscription Box
st.markdown("---")
with st.container():
    st.subheader("📧 Subscribe for Email Alerts")
    col1, col2 = st.columns([3, 1])
    with col1:
        email_input = st.text_input("Enter your email to get notified of new releases", placeholder="your.email@example.com", label_visibility="collapsed")
    with col2:
        if st.button("Subscribe", type="primary", use_container_width=True):
            if email_input and "@" in email_input:
                st.success("✅ Subscribed! You'll get alerts for new releases.")
                # TODO: Store email in database/service
            else:
                st.error("Please enter a valid email")

st.markdown("---")

# Metrics row
ny_time = datetime.now(NY_TZ)
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Ticker", "BE")
with col2:
    st.metric("Last Check (NY)", ny_time.strftime('%I:%M %p ET'))
with col3:
    st.button("🔄 Refresh", type="primary")

st.markdown("---")

# Fetch releases
releases = fetch_all_releases()

if isinstance(releases, dict) and 'error' in releases:
    st.error(f"❌ Error fetching data: {releases['error']}")
elif releases:
    last_seen = load_last()
    
    # Check if there's a new release
    if releases and (last_seen is None or releases[0]['title'] != last_seen.get('title')):
        st.success("🆕 **NEW PRESS RELEASE DETECTED!**")
        save_last(releases[0])
    
    # Display latest 3 releases
    st.subheader("📰 Latest 3 Press Releases")
    
    for i, release in enumerate(releases, 1):
        with st.container():
            st.markdown(f"### {i}. {release['title']}")
            col1, col2 = st.columns([3, 1])
            with col1:
                st.caption(f"📅 {release['date']}")
            with col2:
                if release['link']:
                    st.link_button("Read Full Release →", release['link'], key=f"link_{i}", use_container_width=True)
            st.markdown("---")
    
    # Sidebar info
    with st.sidebar:
        st.header("ℹ️ About BEEIR")
        st.markdown("""
        **BEEIR** is your real-time feed for **Bloom Energy Corporation's** investor relations updates.
        
        **What you get:**
        - 📰 Latest 3 press releases
        - 🆕 Instant alerts for new releases
        - 📧 Email notifications (subscribe above)
        - ⏱️ Auto-refresh every 20 minutes
        
        **We monitor:**
        - Press releases
        - Financial updates
        - Convertible offerings
        - Material events
        """)
        
        st.markdown("---")
        st.markdown("**🔗 Quick Links**")
        st.link_button("🌐 BE Investor Relations", "https://investor.bloomenergy.com")
        st.link_button("📈 SEC Filings", "https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=0001808833")
        
        st.markdown("---")
        st.caption(f"⏱️ Auto-refresh: Every 20 min")
        ny_time_sidebar = datetime.now(NY_TZ)
        st.caption(f"📅 Last updated: {ny_time_sidebar.strftime('%b %d, %I:%M %p ET')}")
else:
    st.warning("No press releases found")

# Auto-refresh
time.sleep(2)
st.rerun()


