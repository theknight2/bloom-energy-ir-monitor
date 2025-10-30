import streamlit as st
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import json
import os
import time

# Config
CHECK_INTERVAL = 1200  # 20 minutes in seconds
STORAGE_FILE = "last_press_release.json"

st.set_page_config(page_title="BE IR Monitor", page_icon="🔔", layout="wide")

def fetch_all_releases():
    """Fetch all recent press releases from BE investor relations"""
    try:
        url = "https://investor.bloomenergy.com/press-releases"
        response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=10)
        soup = BeautifulSoup(response.content, 'html.parser')
        
        releases = []
        items = soup.find_all('div', class_='module-headline')
        
        for item in items[:10]:  # Get latest 10
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

# Header
st.title("🔔 Bloom Energy IR Dashboard")
st.markdown("**Real-time monitoring of Bloom Energy (BE) Investor Relations**")

# Metrics row
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Ticker", "BE")
with col2:
    st.metric("Last Check", datetime.now().strftime('%I:%M %p'))
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
    
    # Display latest release prominently
    st.subheader("📰 Latest Release")
    with st.container():
        st.markdown(f"### {releases[0]['title']}")
        col1, col2 = st.columns([3, 1])
        with col1:
            st.caption(f"📅 {releases[0]['date']}")
        with col2:
            if releases[0]['link']:
                st.link_button("Read Full Release →", releases[0]['link'], use_container_width=True)
    
    st.markdown("---")
    
    # Dashboard of all releases
    st.subheader("📊 Recent Press Releases")
    
    for i, release in enumerate(releases[1:], 1):
        with st.expander(f"{i}. {release['title']}", expanded=False):
            st.caption(f"📅 {release['date']}")
            if release['link']:
                st.link_button(f"Read More", release['link'], key=f"link_{i}")
    
    # Sidebar info
    with st.sidebar:
        st.header("ℹ️ About")
        st.markdown("""
        This dashboard monitors **Bloom Energy Corporation's** investor relations page for:
        - Press releases
        - Financial updates
        - Convertible offerings
        - Material events
        """)
        
        st.markdown("---")
        st.markdown("**Links**")
        st.link_button("🌐 BE Investor Relations", "https://investor.bloomenergy.com")
        st.link_button("📈 SEC Filings", "https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=0001808833")
        
        st.markdown("---")
        st.caption(f"⏱️ Auto-refresh every 20 minutes")
        st.caption(f"Last updated: {datetime.now().strftime('%b %d, %Y')}")
else:
    st.warning("No press releases found")

# Auto-refresh
time.sleep(2)
st.rerun()


