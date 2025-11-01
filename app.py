import streamlit as st
import folium
from folium import FeatureGroup, LayerControl
from folium.plugins import MarkerCluster
from streamlit_folium import st_folium
import random
from geopy.distance import geodesic
import base64
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
import hashlib
import json
import os

# Set page configuration
st.set_page_config(
    page_title="Solapur Engineering Colleges Explorer",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Authentication System ---

USER_DATA_FILE = "user_data.json"

def load_user_data():
    """Load user data from JSON file"""
    if os.path.exists(USER_DATA_FILE):
        try:
            with open(USER_DATA_FILE, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return {}
    return {}

def save_user_data(user_data):
    """Save user data to JSON file"""
    try:
        with open(USER_DATA_FILE, 'w') as f:
            json.dump(user_data, f, indent=4)
        return True
    except Exception:
        return False

def hash_password(password):
    """Hash password using SHA-256"""
    return hashlib.sha256(password.encode()).hexdigest()

def register_user(username, password, email=""):
    """Register a new user"""
    user_data = load_user_data()

    if username in user_data:
        return False, "Username already exists"

    if len(password) < 6:
        return False, "Password must be at least 6 characters long"

    user_data[username] = {
        "password": hash_password(password),
        "email": email,
        "registration_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "last_login": None,
        "login_count": 0,
        "visited_colleges": []
    }

    if save_user_data(user_data):
        return True, "Registration successful!"
    else:
        return False, "Registration failed. Please try again."

def verify_user(username, password):
    """Verify user credentials"""
    user_data = load_user_data()

    if username not in user_data:
        return False, "Invalid username or password"

    if user_data[username]["password"] == hash_password(password):
        # Update login stats
        user_data[username]["last_login"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        user_data[username]["login_count"] = user_data[username].get("login_count", 0) + 1
        save_user_data(user_data)
        return True, "Login successful!"

    return False, "Invalid username or password"

def record_college_visit(username, college_name):
    """Record when a user visits a college"""
    user_data = load_user_data()

    if username in user_data:
        visited_colleges = user_data[username].get("visited_colleges", [])

        # Add college visit with timestamp
        visit_record = {
            "college_name": college_name,
            "visit_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

        # Remove existing entry if it exists and add new one (to maintain unique recent visits)
        visited_colleges = [v for v in visited_colleges if v["college_name"] != college_name]
        visited_colleges.append(visit_record)

        # Keep only last 20 visits
        user_data[username]["visited_colleges"] = visited_colleges[-20:]
        save_user_data(user_data)

def get_user_stats(username):
    """Get user statistics"""
    user_data = load_user_data()

    if username in user_data:
        user_info = user_data[username]
        visited_count = len(user_info.get("visited_colleges", []))
        login_count = user_info.get("login_count", 0)
        registration_date = user_info.get("registration_date", "Unknown")

        return {
            "visited_colleges": visited_count,
            "login_count": login_count,
            "registration_date": registration_date,
            "recent_visits": user_info.get("visited_colleges", [])[-5:]  # Last 5 visits
        }
    return None

# --- Image Loading Function ---
def load_local_image(image_path):
    """Load local image and convert to base64 for HTML display"""
    try:
        with open(image_path, "rb") as img_file:
            encoded = base64.b64encode(img_file.read()).decode()
        return f"data:image/png;base64,{encoded}"
    except FileNotFoundError:
        # Fallback to placeholder if image not found
        return "https://via.placeholder.com/140x140/2F80ED/FFFFFF?text=Logo"

# --- Global Custom CSS for UI Enhancement ---
st.markdown("""
<style>
/* Global Font & Primary Colors */
:root {
    --primary-color: #2F80ED; /* Blue for primary actions */
    --secondary-color: #F2994A; /* Orange/Gold for accents */
    --background-light: #F8F9FA;
    --card-bg: #FFFFFF;
    --shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
    --shadow-3d: 0 10px 20px rgba(0, 0, 0, 0.15);
}

/* Auth Header */
.auth-header-container {
    background: linear-gradient(135deg, #1E40AF 0%, #2F80ED 100%);
    padding: 1rem 2rem;
    border-radius: 0 0 20px 20px;
    margin-bottom: 0;
    box-shadow: 0 4px 20px rgba(0,0,0,0.15);
}
.auth-header-content {
    display: flex;
    justify-content: space-between;
    align-items: center;
    max-width: 1200px;
    margin: 0 auto;
}
.auth-main-title {
    color: white;
    font-size: 2.2rem;
    font-weight: 800;
    margin: 0;
    text-shadow: 0 2px 4px rgba(0,0,0,0.3);
}
.auth-buttons {
    display: flex;
    gap: 15px;
    align-items: center;
}
.auth-switch-btn {
    background: rgba(255,255,255,0.2) !important;
    color: white !important;
    border: 2px solid rgba(255,255,255,0.3) !important;
    padding: 10px 20px !important;
    border-radius: 10px !important;
    font-weight: 600 !important;
    transition: all 0.3s ease !important;
}
.auth-switch-btn:hover {
    background: rgba(255,255,255,0.3) !important;
    border-color: rgba(255,255,255,0.5) !important;
    transform: translateY(-2px);
}

/* Auth Container - UPDATED TO REMOVE EXTRA SPACE */
.auth-container {
    display: flex;
    justify-content: center;
    align-items: flex-start; /* Changed from center to flex-start */
    min-height: auto; /* Changed from 70vh to auto */
    padding: 20px 20px 0 20px; /* Reduced bottom padding */
    margin-top: 0;
}
.auth-card {
    background: linear-gradient(145deg, #ffffff, #f8f9fa);
    border-radius: 24px;
    padding: 40px;
    box-shadow: 0 20px 60px rgba(0,0,0,0.15);
    border-left: 8px solid var(--primary-color);
    max-width: 500px;
    width: 100%;
    position: relative;
    overflow: hidden;
    text-align: center;
    margin-top: 0; /* Ensure no margin on top */
}
.auth-card::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 6px;
    background: linear-gradient(90deg, var(--primary-color), var(--secondary-color));
}
.auth-welcome-header {
    color: var(--primary-color);
    font-size: 2.5rem;
    font-weight: 800;
    margin-bottom: 10px;
    background: linear-gradient(135deg, #2F80ED, #1E40AF);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}
.auth-subheader {
    color: #6B7280;
    font-size: 1.2rem;
    margin-bottom: 30px;
    font-weight: 400;
}
.auth-tabs {
    display: flex;
    margin-bottom: 30px;
    background: #F1F5F9;
    border-radius: 12px;
    padding: 4px;
}
.auth-tab {
    flex: 1;
    padding: 12px;
    text-align: center;
    border-radius: 8px;
    cursor: pointer;
    font-weight: 600;
    transition: all 0.3s ease;
}
.auth-tab.active {
    background: white;
    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    color: var(--primary-color);
}
.auth-form {
    text-align: left;
}
.auth-input {
    margin-bottom: 20px;
}
.auth-input label {
    display: block;
    margin-bottom: 8px;
    font-weight: 600;
    color: #374151;
}
.auth-input input {
    width: 100%;
    padding: 14px;
    border: 2px solid #E5E7EB;
    border-radius: 10px;
    font-size: 1rem;
    transition: all 0.3s ease;
}
.auth-input input:focus {
    border-color: var(--primary-color);
    box-shadow: 0 0 0 3px rgba(47, 128, 237, 0.1);
    outline: none;
}
.auth-button {
    width: 100%;
    padding: 14px;
    background: linear-gradient(145deg, #2F80ED, #1E6BEF);
    color: white;
    border: none;
    border-radius: 10px;
    font-size: 1.1rem;
    font-weight: 700;
    cursor: pointer;
    transition: all 0.3s ease;
    box-shadow: 0 4px 0 #1E40AF;
    position: relative;
    top: 0;
    margin-top: 10px;
}
.auth-button:hover {
    transform: translateY(-2px);
    box-shadow: 0 6px 0 #1E40AF;
    background: linear-gradient(145deg, #1E6BEF, #2F80ED);
}
.auth-button:active {
    top: 4px;
    box-shadow: 0 0 0 #1E40AF;
}
.auth-switch {
    text-align: center;
    margin-top: 20px;
    color: #6B7280;
}
.auth-switch a {
    color: var(--primary-color);
    text-decoration: none;
    font-weight: 600;
    cursor: pointer;
}
.auth-switch a:hover {
    text-decoration: underline;
}

/* Profile Dropdown */
.profile-dropdown {
    position: relative;
    display: inline-block;
}
.profile-icon-btn {
    background: linear-gradient(145deg, #2F80ED, #1E6BEF) !important;
    color: white !important;
    border: none !important;
    border-radius: 50% !important;
    width: 50px !important;
    height: 50px !important;
    font-size: 1.5rem !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    box-shadow: 0 4px 12px rgba(47, 128, 237, 0.3) !important;
    transition: all 0.3s ease !important;
}
.profile-icon-btn:hover {
    transform: scale(1.1);
    box-shadow: 0 6px 20px rgba(47, 128, 237, 0.4) !important;
}
.profile-dropdown-content {
    display: none;
    position: absolute;
    right: 0;
    background: white;
    min-width: 280px;
    box-shadow: 0 8px 30px rgba(0,0,0,0.15);
    border-radius: 12px;
    padding: 20px;
    z-index: 1000;
    border: 1px solid #E5E7EB;
}
.profile-dropdown:hover .profile-dropdown-content {
    display: block;
}
.profile-header {
    color: var(--primary-color);
    font-size: 1.3rem;
    font-weight: 700;
    margin-bottom: 15px;
    display: flex;
    align-items: center;
    gap: 10px;
}
.profile-stats {
    background: #F8F9FA;
    border-radius: 8px;
    padding: 15px;
    margin: 10px 0;
}
.profile-stat-item {
    display: flex;
    justify-content: space-between;
    margin: 8px 0;
    font-size: 0.9rem;
}
.profile-recent {
    margin-top: 15px;
}
.profile-recent h4 {
    color: #374151;
    margin-bottom: 8px;
    font-size: 0.9rem;
}
.profile-recent-item {
    font-size: 0.8rem;
    color: #6B7280;
    margin: 4px 0;
    padding-left: 10px;
    border-left: 2px solid #E5E7EB;
}
.profile-logout-btn {
    width: 100%;
    background: linear-gradient(145deg, #EF4444, #DC2626) !important;
    color: white !important;
    border: none !important;
    border-radius: 8px !important;
    padding: 10px !important;
    margin-top: 15px !important;
    font-weight: 600 !important;
    transition: all 0.3s ease !important;
}
.profile-logout-btn:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(239, 68, 68, 0.3) !important;
}

/* Locked State */
.locked-feature {
    filter: blur(5px);
    pointer-events: none;
    user-select: none;
}
.locked-overlay {
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: rgba(255,255,255,0.9);
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
    z-index: 1000;
    border-radius: 16px;
}
.locked-icon {
    font-size: 4rem;
    margin-bottom: 20px;
    color: var(--primary-color);
}
.locked-text {
    font-size: 1.5rem;
    font-weight: 700;
    color: var(--primary-color);
    margin-bottom: 10px;
}
.locked-subtext {
    color: #6B7280;
    margin-bottom: 20px;
}

/* Page Header */
.main-header {
    font-size: 3.5rem;
    color: var(--primary-color);
    text-align: center;
    margin-bottom: 1.5rem;
    font-weight: 800;
    text-shadow: 0px 2px 4px rgba(0, 0, 0, 0.1);
    background: linear-gradient(135deg, #2F80ED, #1E40AF);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}
.sub-header {
    font-size: 1.6rem;
    color: #4B5563;
    text-align: center;
    margin-bottom: 2rem;
    font-weight: 400;
}

/* Login Card Styling */
.login-card {
    background: linear-gradient(145deg, #ffffff, #f8f9fa);
    border-radius: 20px;
    padding: 30px;
    margin: 20px auto;
    box-shadow: 0 15px 35px rgba(0,0,0,0.1);
    border-left: 6px solid var(--primary-color);
    max-width: 500px;
    position: relative;
    overflow: hidden;
}
.login-card::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 4px;
    background: linear-gradient(90deg, var(--primary-color), var(--secondary-color));
}
.login-header {
    text-align: center;
    color: var(--primary-color);
    font-size: 2rem;
    font-weight: 700;
    margin-bottom: 25px;
}

/* User Profile Styling */
.profile-card {
    background: linear-gradient(145deg, #ffffff, #f8f9fa);
    border-radius: 16px;
    padding: 20px;
    margin: 10px 0;
    box-shadow: 0 8px 20px rgba(0,0,0,0.08);
    border-left: 4px solid var(--secondary-color);
}
.profile-header {
    color: var(--primary-color);
    font-size: 1.3rem;
    font-weight: 700;
    margin-bottom: 15px;
    display: flex;
    align-items: center;
    gap: 10px;
}

/* 3D Button Styling */
.btn-3d {
    display: inline-block;
    padding: 14px 28px;
    font-size: 1.1rem;
    font-weight: 700;
    text-align: center;
    text-decoration: none;
    color: white;
    background: linear-gradient(145deg, #2F80ED, #1E6BEF);
    border: none;
    border-radius: 12px;
    box-shadow: 0 6px 0 #1E40AF, 0 8px 10px rgba(0,0,0,0.2);
    transition: all 0.2s ease;
    cursor: pointer;
    position: relative;
    top: 0;
    margin: 10px 5px;
}
.btn-3d:hover {
    top: 2px;
    box-shadow: 0 4px 0 #1E40AF, 0 6px 6px rgba(0,0,0,0.2);
    background: linear-gradient(145deg, #1E6BEF, #2F80ED);
    color: white;
    text-decoration: none;
}
.btn-3d:active {
    top: 6px;
    box-shadow: 0 0 0 #1E40AF, 0 2px 4px rgba(0,0,0,0.2);
}
.btn-3d-secondary {
    background: linear-gradient(145deg, #F2994A, #E67E22);
    box-shadow: 0 6px 0 #D35400, 0 8px 10px rgba(0,0,0,0.2);
}
.btn-3d-secondary:hover {
    box-shadow: 0 4px 0 #D35400, 0 6px 6px rgba(0,0,0,0.2);
    background: linear-gradient(145deg, #E67E22, #F2994A);
}
.btn-3d-success {
    background: linear-gradient(145deg, #27AE60, #219653);
    box-shadow: 0 6px 0 #1E7E34, 0 8px 10px rgba(0,0,0,0.2);
}
.btn-3d-success:hover {
    box-shadow: 0 4px 0 #1E7E34, 0 6px 6px rgba(0,0,0,0.2);
    background: linear-gradient(145deg, #219653, #27AE60);
}

/* Feature Cards (Front Page) */
.feature-card {
    background-color: var(--card-bg);
    border-radius: 16px;
    padding: 28px;
    margin-bottom: 25px;
    box-shadow: var(--shadow);
    border-left: 6px solid var(--secondary-color);
    transition: all 0.4s ease;
    position: relative;
    overflow: hidden;
}
.feature-card::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 4px;
    background: linear-gradient(90deg, var(--primary-color), var(--secondary-color));
}
.feature-card:hover {
    transform: translateY(-8px);
    box-shadow: 0 12px 24px rgba(0, 0, 0, 0.15);
}
.feature-title {
    color: #1E40AF;
    font-size: 1.5rem;
    font-weight: 700;
    margin-bottom: 12px;
    display: flex;
    align-items: center;
    gap: 10px;
}

/* Streamlit Button Styling Override */
.stButton button {
    background: linear-gradient(145deg, #2F80ED, #1E6BEF);
    color: white;
    font-size: 1.1rem;
    font-weight: 600;
    padding: 12px 24px;
    border-radius: 12px;
    border: none;
    transition: all 0.3s;
    box-shadow: 0 4px 0 #1E40AF, 0 6px 8px rgba(0,0,0,0.15);
    position: relative;
    top: 0;
}
.stButton button:hover {
    background: linear-gradient(145deg, #1E6BEF, #2F80ED);
    transform: translateY(-2px);
    box-shadow: 0 6px 0 #1E40AF, 0 8px 10px rgba(0,0,0,0.2);
    color: white;
}
.stButton button:active {
    top: 4px;
    box-shadow: 0 0 0 #1E40AF, 0 2px 4px rgba(0,0,0,0.15);
}
/* Back Button */
.stButton[key="back_btn"] button {
    background: linear-gradient(145deg, #6B7280, #4B5563);
    box-shadow: 0 4px 0 #374151, 0 6px 8px rgba(0,0,0,0.15);
}
.stButton[key="back_btn"] button:hover {
    background: linear-gradient(145deg, #4B5563, #6B7280);
    box-shadow: 0 6px 0 #374151, 0 8px 10px rgba(0,0,0,0.2);
}

/* College Detail Card (Map Page) */
.detail-card-enhanced {
    background: linear-gradient(145deg, #F0F9FF, #E1F5FE);
    border-radius: 16px;
    padding: 24px;
    box-shadow: 0 8px 20px rgba(0, 0, 0, 0.12);
    border: 1px solid #BEE3F8;
    margin-top: 10px;
    position: relative;
    overflow: hidden;
}
.detail-card-enhanced::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    width: 6px;
    height: 100%;
    background: linear-gradient(to bottom, var(--primary-color), var(--secondary-color));
}
.detail-header {
    color: var(--primary-color);
    font-size: 1.5rem;
    font-weight: 700;
    margin-bottom: 18px;
    border-bottom: 2px solid #E2E8F0;
    padding-bottom: 8px;
}

/* Sidebar Styling */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #EBF8FF, #E1F5FE);
    padding: 20px;
}
[data-testid="stSidebar"] h2 {
    color: var(--primary-color);
    font-weight: 700;
}

/* Center Images */
.stImage img {
    display: block;
    margin-left: auto;
    margin-right: auto;
    border-radius: 12px;
    box-shadow: 0 4px 12px rgba(0,0,0,0.1);
}

/* University Logo Styling */
.uni-logo {
    max-width: 140px;
    max-height: 140px;
    object-fit: contain;
    flex-shrink: 0;
    border-radius: 12px;
    border: 2px solid #E2E8F0;
    background-color: white;
    padding: 8px;
    box-shadow: 0 4px 8px rgba(0,0,0,0.1);
}

/* Tab styling */
.stTabs [data-baseweb="tab-list"] {
    gap: 40px;
    background: transparent;
    padding: 16px;
    border-radius: 16px;
    border: none;
    justify-content: center;
}
.stTabs [data-baseweb="tab"] {
    height: 60px;
    white-space: pre-wrap;
    background: linear-gradient(145deg, #f8f9fa, #e9ecef);
    border-radius: 12px;
    gap: 1px;
    padding: 16px 24px;
    font-weight: 700;
    transition: all 0.3s ease;
    box-shadow: 0 6px 0 rgba(108, 117, 125, 0.3), 0 8px 12px rgba(0,0,0,0.1);
    border: none;
    color: #495057;
    position: relative;
    top: 0;
    min-width: 180px;
    text-align: center;
}
.stTabs [data-baseweb="tab"]:hover {
    top: -2px;
    box-shadow: 0 8px 0 rgba(108, 117, 125, 0.3), 0 10px 16px rgba(0,0,0,0.15);
    background: linear-gradient(145deg, #e9ecef, #f8f9fa);
}
.stTabs [data-baseweb="tab"]:nth-child(1) { /* Interactive Map - Blue */
    background: linear-gradient(145deg, #e3f2fd, #bbdefb);
    box-shadow: 0 6px 0 #1976d2, 0 8px 12px rgba(0,0,0,0.1);
}
.stTabs [data-baseweb="tab"]:nth-child(1):hover {
    background: linear-gradient(145deg, #bbdefb, #e3f2fd);
    box-shadow: 0 8px 0 #1976d2, 0 10px 16px rgba(0,0,0,0.15);
}
.stTabs [data-baseweb="tab"]:nth-child(2) { /* Compare Colleges - Green */
    background: linear-gradient(145deg, #e8f5e8, #c8e6c9);
    box-shadow: 0 6px 0 #388e3c, 0 8px 12px rgba(0,0,0,0.1);
}
.stTabs [data-baseweb="tab"]:nth-child(2):hover {
    background: linear-gradient(145deg, #c8e6c9, #e8f5e8);
    box-shadow: 0 8px 0 #388e3c, 0 10px 16px rgba(0,0,0,0.15);
}
.stTabs [data-baseweb="tab"]:nth-child(3) { /* Cost Calculator - Orange */
    background: linear-gradient(145deg, #fff3e0, #ffcc80);
    box-shadow: 0 6px 0 #f57c00, 0 8px 12px rgba(0,0,0,0.1);
}
.stTabs [data-baseweb="tab"]:nth-child(3):hover {
    background: linear-gradient(145deg, #ffcc80, #fff3e0);
    box-shadow: 0 8px 0 #f57c00, 0 10px 16px rgba(0,0,0,0.15);
}
.stTabs [data-baseweb="tab"]:nth-child(4) { /* View Analytics - Purple */
    background: linear-gradient(145deg, #f3e5f5, #ce93d8);
    box-shadow: 0 6px 0 #7b1fa2, 0 8px 12px rgba(0,0,0,0.1);
}
.stTabs [data-baseweb="tab"]:nth-child(4):hover {
    background: linear-gradient(145deg, #ce93d8, #f3e5f5);
    box-shadow: 0 8px 0 #7b1fa2, 0 10px 16px rgba(0,0,0,0.15);
}
.stTabs [aria-selected="true"] {
    background: linear-gradient(145deg, #2F80ED, #1E6BEF);
    color: white;
    box-shadow: 0 6px 0 #1E40AF, 0 8px 12px rgba(47, 128, 237, 0.3);
    border: none;
    top: -2px;
}
.stTabs [aria-selected="true"]:nth-child(1) { /* Selected Interactive Map */
    background: linear-gradient(145deg, #1976d2, #1565c0);
    box-shadow: 0 6px 0 #0d47a1, 0 8px 12px rgba(25, 118, 210, 0.3);
}
.stTabs [aria-selected="true"]:nth-child(2) { /* Selected Compare Colleges */
    background: linear-gradient(145deg, #388e3c, #2e7d32);
    box-shadow: 0 6px 0 #1b5e20, 0 8px 12px rgba(56, 142, 60, 0.3);
}
.stTabs [aria-selected="true"]:nth-child(3) { /* Selected Cost Calculator */
    background: linear-gradient(145deg, #f57c00, #ef6c00);
    box-shadow: 0 6px 0 #bf360c, 0 8px 12px rgba(245, 124, 0, 0.3);
}
.stTabs [aria-selected="true"]:nth-child(4) { /* Selected View Analytics */
    background: linear-gradient(145deg, #7b1fa2, #6a1b9a);
    box-shadow: 0 6px 0 #4a148c, 0 8px 12px rgba(123, 31, 162, 0.3);
}

/* Metric Cards */
[data-testid="metric-container"] {
    border: 1px solid #E2E8F0;
    border-radius: 12px;
    padding: 16px;
    box-shadow: 0 4px 8px rgba(0,0,0,0.05);
    background: white;
}

/* Mobile Responsive */
@media (max-width: 768px) {
    .uni-card {
        flex-direction: column;
        text-align: center;
    }
    .feature-card {
        padding: 20px;
    }
    .main-header {
        font-size: 2.5rem;
    }
    .btn-3d {
        padding: 12px 20px;
        font-size: 1rem;
    }
    .auth-header-content {
        flex-direction: column;
        gap: 15px;
        text-align: center;
    }
}

/* Floating Animation */
@keyframes float {
    0% { transform: translateY(0px); }
    50% { transform: translateY(-10px); }
    100% { transform: translateY(0px); }
}
.floating {
    animation: float 6s ease-in-out infinite;
}

/* Glow Effect */
.glow {
    box-shadow: 0 0 15px rgba(47, 128, 237, 0.5);
}
.glow:hover {
    box-shadow: 0 0 20px rgba(47, 128, 237, 0.7);
}

/* Hero Section */
.hero-section {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    padding: 80px 40px;
    border-radius: 24px;
    text-align: center;
    color: white;
    margin-bottom: 40px;
    box-shadow: 0 20px 40px rgba(0,0,0,0.1);
    position: relative;
    overflow: hidden;
}
.hero-section::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: url('data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1000 1000"><polygon fill="rgba(255,255,255,0.05)" points="0,1000 1000,0 1000,1000"/></svg>');
}
.hero-title {
    font-size: 4rem;
    font-weight: 800;
    margin-bottom: 20px;
    text-shadow: 0 4px 8px rgba(0,0,0,0.3);
}
.hero-subtitle {
    font-size: 1.5rem;
    margin-bottom: 30px;
    opacity: 0.9;
    font-weight: 300;
}
.hero-stats {
    display: flex;
    justify-content: center;
    gap: 40px;
    margin-top: 40px;
}
.hero-stat {
    text-align: center;
}
.hero-stat-number {
    font-size: 2.5rem;
    font-weight: 700;
    display: block;
}
.hero-stat-label {
    font-size: 1rem;
    opacity: 0.8;
}

/* Enhanced Feature Cards */
.enhanced-feature-card {
    background: linear-gradient(145deg, #ffffff, #f8f9fa);
    border-radius: 20px;
    padding: 30px;
    margin: 15px 0;
    box-shadow: 0 10px 30px rgba(0,0,0,0.08);
    border: 1px solid #E5E7EB;
    transition: all 0.4s ease;
    text-align: center;
    position: relative;
    overflow: hidden;
}
.enhanced-feature-card::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 4px;
    background: linear-gradient(90deg, #2F80ED, #F2994A);
}
.enhanced-feature-card:hover {
    transform: translateY(-10px);
    box-shadow: 0 20px 40px rgba(0,0,0,0.15);
}
.enhanced-feature-icon {
    font-size: 3rem;
    margin-bottom: 20px;
    background: linear-gradient(135deg, #2F80ED, #1E40AF);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}
.enhanced-feature-title {
    font-size: 1.4rem;
    font-weight: 700;
    color: #1E40AF;
    margin-bottom: 15px;
}
.enhanced-feature-description {
    color: #6B7280;
    line-height: 1.6;
}
</style>
""", unsafe_allow_html=True)

# --- Global Data Definitions ---

# Transport Hub Coordinates
station_coords = [17.666921710311527, 75.89394143431612]  # Solapur Railway Station
bus_stand_coords = [17.680824887006022, 75.89883304182453]  # Solapur Central Bus Stand

# Load local university images
dbatu_image = load_local_image("images/dbatu_logo.png")
solapur_uni_image = load_local_image("images/solapur_university.png")

# Main Universities data
universities = {
    "DBATU": {
        "coords": [18.17005454144283, 73.33945567384438],
        "image": dbatu_image,
        "location": "Lonere, Maharashtra",
        "founded": 1989,
        "description": "A state technological university offering various engineering disciplines.",
        "website": "https://dbatu.ac.in/",
        "color": "black",
        "icon": "university",
        "region": "Raigad"
    },
    "Solapur University": {
        "coords": [17.723669534193913, 75.84224263944135],
        "image": solapur_uni_image,
        "location": "Solapur, Maharashtra",
        "founded": 2004,
        "description": "A public state university known for academic excellence and research.",
        "website": "https://su.digitaluniversity.ac/",
        "color": "gray",
        "icon": "university",
        "region": "Solapur"
    }
}

# Enhanced Colleges data
enhanced_colleges = [
    {
        "name": "Walchand Institute of Technology",
        "lat": 17.66884,
        "lon": 75.92293,
        "image": "https://i.imgur.com/wiF0DL6.jpeg",
        "website": "https://witsolapur.org/",
        "university": "Solapur University",
        "established": 1983,
        "courses": ["Computer Science & Engineering", "Electronics & Telecommunication Engineering", "Information Technology", "Mechanical & Automation Engineering", "Civil Engineering", "Electronics & Computer Engineering", "M.Tech Design Engineering", "M.Tech Structural Engineering"],
        "fees_range": "₹2.82 L – ₹5.27 L (for full duration of B.Tech) / ~₹2.09 L for M.Tech",  
        "facilities": ["Hostel (boys & girls)", "Library (includes digital library)", "Sports ground & courts", "Cafeteria", "Labs for each discipline", "WiFi campus"],
        "contact": "+ 0217 265 2700",
        "address": "634, Walchand Hirachand Marg, Ashok Chowk, Solapur, Maharashtra 413006",
        "campus_size": "Approx. large campus (specific acreage not found publicly)"
    },
    {
        "name": "N. B. Navale Sinhgad College of Engineering",
        "lat": 17.72864,
        "lon": 75.85171,
        "image": "https://i.imgur.com/SinhgadCollege.jpg",
        "website": "https://sinhgadsolapur.rbtechapps.net/",
        "university": "Solapur University",
        "established": 2010,
        "courses": ["Computer Science & Engineering", "Electrical Engineering", "Mechanical Engineering", "Civil Engineering", "Electronics & Telecommunication Engineering", "M.E./M.Tech (various)"],
        "fees_range": "≈ ₹1.38 lakh – ₹3.00 lakh (for full 4-yr B.Tech) / ~₹1.06 lakh for 2-yr M.Tech",  
        "facilities": ["Hostel (boys & girls)", "Library (24/7, digital access)", "Sports facilities", "Cafeteria", "Gymnasium", "WiFi campus", "Transport service"],
        "contact": "083800 25688",
        "address": "Gat No. 38/1B, Solapur–Pune Highway, Kegaon, Solapur, Maharashtra 413255, India",
        "campus_size": "≈ 90 acres"
    },
    {
        "name": "A. G. Patil Institute of Technology",
        "lat": 17.61455,
        "lon": 75.91839,
        "image": "https://i.imgur.com/BV2xCZF.jpeg",
        "website": "http://www.agpit.edu.in/",
        "university": "Solapur University",
        "established": 2008,
        "courses": ["Computer Science & Engineering", "Mechanical Engineering", "Civil Engineering", "Electronics & Telecommunication Engineering"],
        "fees_range": "Approx. ₹1,53,000 – ₹3,10,160 (full course) (~₹38,000 – ₹78,000 per year)",  
        "facilities": ["Hostel – boys & girls", "Library (24/7 digital access)", "Sports & gymnasium", "Cafeteria", "Labs (state-of-the-art)", "WiFi campus"],
        "contact": "0217 234 2499",
        "address": "18/[2 A2] 2, Pratap Nagar, Opp. SRP Camp, Vijapur Road, Solapur, Maharashtra 413008, India",
        "campus_size": "10 acres"
    },
    {
        "name": "Vidya Vikas Pratishthan Institute of Engineering & Technology",
        "lat": 17.66237,
        "lon": 75.91839,
        "image": "https://i.imgur.com/mz3ucUM.jpeg",
        "website": "https://vvpengineering.org/",
        "university": "Solapur University",
        "established": 2009,
        "courses": ["Computer Science & Engineering", "Electronics & Telecommunication Engineering", "Mechanical Engineering", "Civil Engineering", "Electrical Engineering"],
        "fees_range": "≈ ₹3.6 lakh (full 4-yr BE) (~₹90,000/year) for typical UG course",  
        "facilities": ["Hostel (boys & girls)", "Library", "Sports & Games", "Cafeteria", "Labs with high-speed internet", "WiFi campus"],
        "contact": "083800 30555",
        "address": "Gat No.72/2, Pratapnagar, Soregaon-Dongaon Road, Solapur, Maharashtra 413004, India",
        "campus_size": "≈ 10 acres"
    },
    {
        "name": "N.K. Orchid College of Engineering & Technology",
        "lat": 17.72018,
        "lon": 75.91949,
        "image": "https://i.imgur.com/LgZ1mcb.jpeg",
        "website": "https://www.orchidengg.ac.in/",
        "university": "Dr. Babasaheb Ambedkar Technological University (DBATU), Lonere",
        "established": 2008,
        "courses": ["Computer Science & Engineering", "Mechanical Engineering", "Civil Engineering", "Electrical Engineering", "Electronics & Telecommunication Engineering", "Artificial Intelligence & Data Science"],
        "fees_range": "≈ ₹88,780 – ₹1,10,000 per year for first year UG (2024-25) + development & other fees",  
        "facilities": ["Hostel (boys & girls)", "Library / Book Bank", "Sports & Games", "Cafeteria", "Auditorium", "Well-Equipped Labs"],
        "contact": "+0217 299 0051",
        "address": "Gat No. 16, Solapur-Tuljapur Road, Near Mushroom Ganapati Temple, Tale–Hipparaga, Solapur – 413002, Maharashtra, India",
        "campus_size": "10.6 acres"
    },
    {
        "name": "Bharatratna Indira Gandhi College of Engineering",
        "lat": 17.72318,
        "lon": 75.85525,
        "image": "https://i.imgur.com/uFBGg8o.jpeg",
        "website": "https://bigce.in/",
        "university": "Solapur University",
        "established": 2006,
        "courses": ["Computer Science & Engineering", "Mechanical Engineering", "Civil Engineering", "Electrical Engineering", "Electronics & Telecommunication Engineering", "Biomedical Engineering"],
        "fees_range": "≈ ₹2.74 lakh for full 4-yr BE (≈ ₹68,500/year) based on 2025 data",  
        "facilities": ["Library", "Hostel (boys & girls)", "Sports", "Cafeteria", "Laboratories", "WiFi campus"],
        "contact": "+0217 250 0480",
        "address": "Gat No. 58/3, Kegaon, Solapur-Pune National Highway No. 9, Solapur, Maharashtra 413255, India",
        "campus_size": "≈ 10 acres"
    },
    {
        "name": "Shree Siddheshwar Women's College of Engineering, Solapur",
        "lat": 17.68767,
        "lon": 75.91203,
        "image": "https://i.imgur.com/Fu7lASE.jpeg",
        "website": "https://sswcoe.edu.in/",
        "university": "Dr. Babasaheb Ambedkar Technological University (DBATU), Lonere",
        "established": 2019,
        "courses": ["Computer Science & Engineering","Computer Science & Engineering (AI & Data Science)","Electronics & Telecommunication Engineering","Electrical Engineering","Electronics & Computer Engineering"],
        "fees_range": "Approx. ₹60,000-₹90,000 per year (estimate)",
        "facilities": ["Hostel","Library","Cafeteria","Labs","Girls Hostel","WiFi"],
        "contact": "0217 262 7227",
        "address": "T.P.S II, Final Plot No. 74, Bhawani Peth, Rupa Bhawani Mandir Road, Solapur – 413002, Maharashtra, India",
        "campus_size": "Not publicly specified"
    },
    {
        "name": "Bramhadeo Mane Institute of Technology (BMIT), Solapur",
        "lat": 17.66808,
        "lon": 75.80463,
        "image": "https://i.imgur.com/1NMnh7N.jpeg",
        "website": "https://bmitsolapur.org/",
        "university": "Dr. Babasaheb Ambedkar Technological University (DBATU), Lonere",
        "established": 2006,
        "courses": ["Computer Science and Engineering","Mechanical Engineering","Civil Engineering","Electrical Engineering","Artificial Intelligence and Data Science"],
        "fees_range": "₹70,000 - ₹1,05,000 per year",
        "facilities": ["Hostel","Library","Sports","Cafeteria","Workshops","Transportation"],
        "contact": "+91-217-2318000",
        "address": "At Post Belati, Bhalgaon, Solapur-Pandharpur Road, Solapur – 413255, Maharashtra, India",
        "campus_size": "22 acres"
    }
]

# For backward compatibility
colleges = enhanced_colleges

# Placement Data
placement_data = {
    "Walchand Institute of Technology": {
      "average_package": "₹5 LPA",
      "highest_package": "₹12 LPA",
      "placement_rate": "75%",
      "top_recruiters": ["Infosys", "Wipro", "Byju's", "TCS"]
    },
    "N. B. Navale Sinhgad College of Engineering": {
        "average_package": "₹5.2 LPA",
        "highest_package": "₹12 LPA",
        "placement_rate": "78%",
        "top_recruiters": ["TCS", "Infosys", "Capgemini", "Cognizant"]
    },
    "A. G. Patil Institute of Technology": {
        "average_package": "₹4.8 LPA",
        "highest_package": "₹9 LPA",
        "placement_rate": "72%",
        "top_recruiters": ["Wipro", "Infosys", "L&T", "Byju's"]
    },
    "Vidya Vikas Pratishthan Institute of Engineering & Technology": {
        "average_package": "₹4.5 LPA",
        "highest_package": "₹8.5 LPA",
        "placement_rate": "70%",
        "top_recruiters": ["Infosys", "TCS", "HCL", "Mindtree"]
    },
    "N.K. Orchid College of Engineering & Technology": {
        "average_package": "₹5.0 LPA",
        "highest_package": "₹11 LPA",
        "placement_rate": "75%",
        "top_recruiters": ["TCS", "Wipro", "Accenture", "IBM"]
    },
    "Bharatratna Indira Gandhi College of Engineering": {
        "average_package": "₹4.2 LPA",
        "highest_package": "₹7.5 LPA",
        "placement_rate": "68%",
        "top_recruiters": ["Infosys", "Tech Mahindra", "Capgemini"]
    },
    "Shree Siddheshwar Women's College of Engineering, Solapur": {
        "average_package": "₹4.0 LPA",
        "highest_package": "₹7 LPA",
        "placement_rate": "65%",
        "top_recruiters": ["TCS", "Wipro", "Infosys", "HCL"]
    },
    "Bramhadeo Mane Institute of Technology (BMIT), Solapur": {
        "average_package": "₹4.6 LPA",
        "highest_package": "₹8 LPA",
        "placement_rate": "71%",
        "top_recruiters": ["Infosys", "TCS", "L&T", "Tech Mahindra"]
    }
}

# Student Reviews
college_reviews = {
    "Walchand Institute of Technology": [
        {"rating": 4.5, "comment": "Excellent faculty and infrastructure with good placement opportunities.", "author": "Rahul Sharma", "date": "2024-01-15"},
        {"rating": 4.0, "comment": "Good academic environment and supportive staff.", "author": "Priya Patel", "date": "2024-02-20"}
    ],
    "N. B. Navale Sinhgad College of Engineering": [
        {"rating": 4.2, "comment": "Great campus life and good industry connections.", "author": "Amit Kumar", "date": "2024-01-10"}
    ]
}

# Categories with icons/colors
categories = {
    "Apartment": {"icon": "building", "color": "blue"},
    "Cafe": {"icon": "coffee", "color": "purple"},
    "Restaurant": {"icon": "cutlery", "color": "orange"},
    "Medical": {"icon": "plus-square", "color": "green"},
    "Market": {"icon": "shopping-cart", "color": "cadetblue"},
    "Crime Data": {"icon": "exclamation-triangle", "color": "red"},
    "Police Station": {"icon": "shield-alt", "color": "darkred"},
    "Public Transport": {"icon": "bus", "color": "darkgreen"}
}

# --- Initialization and Navigation ---

# Initialize session state
if 'page' not in st.session_state:
    st.session_state.page = 'frontpage'

if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False

if 'username' not in st.session_state:
    st.session_state.username = None

if 'auth_tab' not in st.session_state:
    st.session_state.auth_tab = 'login'

if 'enhanced_tools_tab' not in st.session_state:
    st.session_state.enhanced_tools_tab = 'map'

# Navigation functions
def go_to_map():
    st.session_state.page = 'map'
    st.rerun()

def go_to_front():
    st.session_state.page = 'frontpage'

def set_enhanced_tools_tab(tab_name):
    st.session_state.enhanced_tools_tab = tab_name

# Authentication functions
def login_user():
    username = st.session_state.login_username
    password = st.session_state.login_password
    
    success, message = verify_user(username, password)
    if success:
        st.session_state.authenticated = True
        st.session_state.username = username
        st.success(f"Welcome back, {username}!")
        st.rerun()
    else:
        st.error(message)

def register_new_user():
    username = st.session_state.register_username
    password = st.session_state.register_password
    email = st.session_state.register_email
    
    success, message = register_user(username, password, email)
    if success:
        st.success(message)
        # Auto-login after registration
        st.session_state.authenticated = True
        st.session_state.username = username
        st.rerun()
    else:
        st.error(message)

def logout_user():
    st.session_state.authenticated = False
    st.session_state.username = None
    st.session_state.auth_tab = 'login'
    st.success("Logged out successfully!")
    st.rerun()

def set_auth_tab(tab_name):
    st.session_state.auth_tab = tab_name

# --- Enhanced Utility Functions ---

# Store fake place data
if 'map_data' not in st.session_state:
    st.session_state.map_data = {}

def generate_places(college, category, count=3, offset=0.005, include_fee=False):
    """Generates and caches fake nearby place data."""
    key = f"{college['name'].replace(' ', '*')}*{category}"
    if key not in st.session_state.map_data:
        st.session_state.map_data[key] = [
            {
                "name": f"{category} {i+1}",
                "lat": college["lat"] + random.uniform(-offset, offset),
                "lon": college["lon"] + random.uniform(-offset, offset),
                "icon": categories[category]["icon"],
                "color": categories[category]["color"],
                "fee": random.randint(4000, 12000) if include_fee else None
            } for i in range(count)
        ]
    return st.session_state.map_data[key]

def show_college_comparison():
    """Enhanced college comparison feature - FIXED PLACEMENT RATE ISSUE"""
    st.markdown('<div class="detail-card-enhanced">', unsafe_allow_html=True)
    st.subheader("🏫 College Comparison")
    
    college_options = [college["name"] for college in enhanced_colleges]
    selected_colleges = st.multiselect("Select colleges to compare:", college_options, max_selections=3)
    
    if selected_colleges:
        comparison_data = []
        for name in selected_colleges:
            college = next((c for c in enhanced_colleges if c["name"] == name), None)
            if college:
                placement = placement_data.get(name, {})
                
                # Extract placement rate as numeric value - IMPROVED VERSION
                placement_rate_str = placement.get("placement_rate", "N/A")
                placement_rate_num = 0
                
                if placement_rate_str != "N/A" and placement_rate_str is not None:
                    try:
                        # Handle cases where placement rate might be stored differently
                        if isinstance(placement_rate_str, str):
                            placement_rate_num = float(placement_rate_str.replace('%', '').strip())
                        else:
                            placement_rate_num = float(placement_rate_str)
                    except (ValueError, AttributeError):
                        placement_rate_num = 0
                
                # Extract package values for comparison
                avg_package = placement.get("average_package", "N/A")
                high_package = placement.get("highest_package", "N/A")
                
                comparison_data.append({
                    "Name": college["name"],
                    "University": college["university"],
                    "Established": college.get("established", "N/A"),
                    "Courses": len(college.get("courses", [])),
                    "Fees": college.get("fees_range", "N/A"),
                    "Avg Package": avg_package,
                    "Placement Rate": placement_rate_str,
                    "Placement Rate Num": placement_rate_num,
                    "Highest Package": high_package,
                    "Campus Size": college.get("campus_size", "N/A"),
                    "Top Recruiters": ", ".join(placement.get("top_recruiters", [])) if placement.get("top_recruiters") else "N/A"
                })
        
        if comparison_data:
            # Display comparison table
            st.dataframe(pd.DataFrame(comparison_data), use_container_width=True)
            
            # Visual comparison
            if len(selected_colleges) > 1:
                st.subheader("📊 Visual Comparison")
                df = pd.DataFrame(comparison_data)
                
                col1, col2 = st.columns(2)
                
                with col1:
                    # Number of Courses Comparison
                    fig_courses = px.bar(
                        df, 
                        x='Name', 
                        y='Courses', 
                        title='Number of Courses Offered',
                        color='Name',
                        color_discrete_sequence=px.colors.qualitative.Set3
                    )
                    fig_courses.update_layout(
                        xaxis_title="College",
                        yaxis_title="Number of Courses",
                        showlegend=False,
                        xaxis_tickangle=-45
                    )
                    st.plotly_chart(fig_courses, use_container_width=True)
                
                with col2:
                    # Placement Rate Comparison - COMPLETELY FIXED VERSION
                    # Create visualization for ALL colleges with placement data
                    valid_placement_data = []
                    
                    for _, row in df.iterrows():
                        college_name = row['Name']
                        placement_rate_str = row['Placement Rate']
                        placement_rate_num = row['Placement Rate Num']
                        
                        # Check if this college has placement data in our main dictionary
                        if college_name in placement_data:
                            placement_info = placement_data[college_name]
                            actual_rate_str = placement_info.get("placement_rate", "N/A")
                            
                            # If we have valid placement rate data, use it
                            if actual_rate_str != "N/A" and actual_rate_str is not None:
                                try:
                                    if isinstance(actual_rate_str, str):
                                        actual_rate_num = float(actual_rate_str.replace('%', '').strip())
                                    else:
                                        actual_rate_num = float(actual_rate_str)
                                    
                                    valid_placement_data.append({
                                        'Name': college_name,
                                        'Placement Rate': actual_rate_str,
                                        'Placement Rate Num': actual_rate_num
                                    })
                                except (ValueError, AttributeError):
                                    # If conversion fails, skip this college
                                    continue
                    
                    if valid_placement_data:
                        placement_vis_df = pd.DataFrame(valid_placement_data)
                        fig_placement = px.bar(
                            placement_vis_df, 
                            x='Name', 
                            y='Placement Rate Num',
                            title='Placement Rate Comparison (%)',
                            color='Name',
                            color_discrete_sequence=px.colors.qualitative.Set1,
                            text='Placement Rate'
                        )
                        fig_placement.update_layout(
                            xaxis_title="College",
                            yaxis_title="Placement Rate (%)",
                            yaxis_range=[0, 100],
                            showlegend=False,
                            xaxis_tickangle=-45
                        )
                        fig_placement.update_traces(
                            texttemplate='%{text}',
                            textposition='outside'
                        )
                        st.plotly_chart(fig_placement, use_container_width=True)
                    else:
                        # Show detailed information about missing data
                        st.warning("Placement rate data issue detected:")
                        for college_name in selected_colleges:
                            if college_name in placement_data:
                                placement_info = placement_data[college_name]
                                rate = placement_info.get("placement_rate", "NOT FOUND")
                                st.write(f"- {college_name}: {rate}")
                            else:
                                st.write(f"- {college_name}: No placement data in dictionary")
                
                # Package Comparison Chart
                st.subheader("💰 Package Comparison")
                
                # Prepare package data - IMPROVED VERSION
                package_comparison_data = []
                for college_name in selected_colleges:
                    if college_name in placement_data:
                        placement_info = placement_data[college_name]
                        
                        # Process average package
                        avg_pkg = placement_info.get("average_package", "N/A")
                        if avg_pkg != 'N/A' and avg_pkg is not None:
                            try:
                                avg_value = float(avg_pkg.replace('₹', '').replace('LPA', '').replace(' ', '').strip())
                                package_comparison_data.append({
                                    'College': college_name,
                                    'Package Type': 'Average Package',
                                    'Value (LPA)': avg_value
                                })
                            except (ValueError, AttributeError):
                                pass
                        
                        # Process highest package
                        high_pkg = placement_info.get("highest_package", "N/A")
                        if high_pkg != 'N/A' and high_pkg is not None:
                            try:
                                high_value = float(high_pkg.replace('₹', '').replace('LPA', '').replace(' ', '').strip())
                                package_comparison_data.append({
                                    'College': college_name,
                                    'Package Type': 'Highest Package',
                                    'Value (LPA)': high_value
                                })
                            except (ValueError, AttributeError):
                                pass
                
                if package_comparison_data:
                    package_df = pd.DataFrame(package_comparison_data)
                    fig_packages = px.bar(
                        package_df,
                        x='College',
                        y='Value (LPA)',
                        color='Package Type',
                        barmode='group',
                        title='Average vs Highest Packages (LPA)',
                        color_discrete_sequence=['#2E86AB', '#A23B72']
                    )
                    fig_packages.update_layout(
                        xaxis_title="College",
                        yaxis_title="Package (LPA)",
                        xaxis_tickangle=-45
                    )
                    st.plotly_chart(fig_packages, use_container_width=True)
                else:
                    st.info("Package data not available for comparison.")
                
                # Detailed placement information for each college
                st.subheader("🎯 Detailed Placement Information")
                
                for college_name in selected_colleges:
                    if college_name in placement_data:
                        placement_info = placement_data[college_name]
                        with st.expander(f"📈 {college_name}", expanded=False):
                            col_a, col_b, col_c = st.columns(3)
                            with col_a:
                                st.metric("Average Package", placement_info.get("average_package", "N/A"))
                            with col_b:
                                st.metric("Highest Package", placement_info.get("highest_package", "N/A"))
                            with col_c:
                                st.metric("Placement Rate", placement_info.get("placement_rate", "N/A"))
                            
                            recruiters = placement_info.get("top_recruiters", [])
                            if recruiters:
                                st.write("**Top Recruiters:**")
                                for recruiter in recruiters:
                                    st.write(f"• {recruiter}")
                            else:
                                st.write("**Top Recruiters:** N/A")
                    else:
                        with st.expander(f"📈 {college_name}", expanded=False):
                            st.warning("No placement data available for this college.")
    
    else:
        st.info("👆 Select colleges from the dropdown above to compare them side-by-side.")
    
    st.markdown('</div>', unsafe_allow_html=True)

def show_reviews(college_name):
    """Display student reviews for a college"""
    st.markdown('<div class="detail-card-enhanced">', unsafe_allow_html=True)
    if college_name in college_reviews and college_reviews[college_name]:
        st.subheader("💬 Student Reviews")
        for review in college_reviews[college_name]:
            with st.container():
                # Create rating stars
                stars = "⭐" * int(review['rating']) + "☆" * (5 - int(review['rating']))
                st.write(f"{stars} {review['rating']}/5")
                st.write(f"\"{review['comment']}\"")
                st.caption(f"By {review['author']} • {review['date']}")
                st.divider()
    else:
        st.info("No reviews available for this college yet.")
    st.markdown('</div>', unsafe_allow_html=True)

def show_placement_stats(college_name):
    """Display placement statistics"""
    st.markdown('<div class="detail-card-enhanced">', unsafe_allow_html=True)
    if college_name in placement_data:
        st.subheader("💼 Placement Statistics (2023-24)")
        stats = placement_data[college_name]
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Average Package", stats["average_package"])
        with col2:
            st.metric("Highest Package", stats["highest_package"])
        with col3:
            st.metric("Placement Rate", stats["placement_rate"])
        
        st.write("**Top Recruiters:**", ", ".join(stats["top_recruiters"]))
    else:
        st.info("Placement data not available for this college.")
    st.markdown('</div>', unsafe_allow_html=True)

def commute_planner(selected_college):
    """Enhanced commute planner"""
    st.markdown('<div class="detail-card-enhanced">', unsafe_allow_html=True)
    st.subheader("🚗 Commute Planner")
    
    transport_modes = ["Car", "Public Transport", "Bike", "Walk"]
    selected_mode = st.selectbox("Transport Mode:", transport_modes)
    
    # Calculate distances
    college_coords = [selected_college["lat"], selected_college["lon"]]
    rail_distance = round(geodesic(station_coords, college_coords).km, 2)
    bus_distance = round(geodesic(bus_stand_coords, college_coords).km, 2)
    
    # Calculate estimated time based on mode and distance
    avg_speed = {"Car": 40, "Public Transport": 25, "Bike": 20, "Walk": 5}
    avg_distance = (rail_distance + bus_distance) / 2
    estimated_time = round((avg_distance / avg_speed[selected_mode]) * 60)
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Distance from Station", f"{rail_distance} km")
        st.metric("Distance from Bus Stand", f"{bus_distance} km")
    with col2:
        st.metric("Estimated Travel Time", f"{estimated_time} min")
        st.metric("Transport Mode", selected_mode)
    
    # Show route suggestions
    st.write("**🚦 Route Suggestions:**")
    if rail_distance < bus_distance:
        st.write("• **Recommended:** Via Railway Station (shorter distance)")
        st.write("• **Alternative:** Via Central Bus Stand")
    else:
        st.write("• **Recommended:** Via Central Bus Stand (shorter distance)")
        st.write("• **Alternative:** Via Railway Station")
    st.markdown('</div>', unsafe_allow_html=True)

def cost_of_living_calculator():
    """Cost of living calculator"""
    st.markdown('<div class="detail-card-enhanced">', unsafe_allow_html=True)
    st.subheader("💰 Cost of Living Calculator")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**Monthly Expenses**")
        accommodation = st.selectbox("Accommodation Type:", 
                                   ["Hostel", "PG", "Apartment", "With Family"])
        food = st.selectbox("Food Preference:", 
                           ["Mess", "Self-cooking", "Restaurants"])
        transport = st.select_slider("Daily Transport:", 
                                   options=["None", "Low", "Medium", "High"])
        miscellaneous = st.number_input("Miscellaneous Expenses (₹):", 
                                      min_value=0, max_value=10000, value=1000)
    
    with col2:
        # Calculate estimated costs
        costs = {
            "Hostel": 4000, "PG": 6000, "Apartment": 9000, "With Family": 0,
            "Mess": 2500, "Self-cooking": 2000, "Restaurants": 5000,
            "None": 0, "Low": 800, "Medium": 1500, "High": 2500
        }
        
        total_cost = (costs[accommodation] + costs[food] + 
                     costs[transport] + miscellaneous)
        
        st.metric("**Total Monthly Cost**", f"₹{total_cost:,}")
        
        # Cost breakdown
        st.write("**📊 Cost Breakdown:**")
        st.write(f"• Accommodation: ₹{costs[accommodation]:,}")
        st.write(f"• Food: ₹{costs[food]:,}")
        st.write(f"• Transport: ₹{costs[transport]:,}")
        st.write(f"• Miscellaneous: ₹{miscellaneous:,}")
        
        # Annual projection
        st.write(f"**📅 Annual Estimate: ₹{total_cost * 12:,}**")
    st.markdown('</div>', unsafe_allow_html=True)

def show_analytics():
    """College analytics dashboard"""
    st.markdown('<div class="detail-card-enhanced">', unsafe_allow_html=True)
    st.subheader("📊 College Analytics Dashboard")
    
    # Create analytics data
    data = {
        'College': [college['name'] for college in enhanced_colleges],
        'Students': [random.randint(800, 2500) for _ in enhanced_colleges],
        'Faculty': [random.randint(40, 120) for _ in enhanced_colleges],
        'Placement Rate': [int(placement_data.get(college['name'], {}).get('placement_rate', '70').replace('%', '')) 
                          for college in enhanced_colleges],
        'Established': [college.get('established', 2000) for college in enhanced_colleges],
        'University': [college['university'] for college in enhanced_colleges]
    }
    df = pd.DataFrame(data)
    
    # Analytics charts
    col1, col2 = st.columns(2)
    
    with col1:
        # Student vs Faculty ratio
        fig_ratio = px.scatter(df, x='Faculty', y='Students', size='Placement Rate',
                             hover_name='College', color='University',
                             title='Faculty vs Student Ratio & Placement Rate',
                             labels={'Faculty': 'Number of Faculty', 'Students': 'Number of Students'})
        st.plotly_chart(fig_ratio, use_container_width=True)
        
        # Establishment year distribution
        fig_est = px.histogram(df, x='Established', title='College Establishment Years')
        st.plotly_chart(fig_est, use_container_width=True)
    
    with col2:
        # Placement rate by university
        fig_placement = px.box(df, x='University', y='Placement Rate',
                             title='Placement Rate Distribution by University')
        st.plotly_chart(fig_placement, use_container_width=True)
        
        # Top colleges by placement
        top_colleges = df.nlargest(5, 'Placement Rate')
        fig_top = px.bar(top_colleges, x='College', y='Placement Rate',
                        title='Top 5 Colleges by Placement Rate')
        st.plotly_chart(fig_top, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

def export_data(selected_college):
    """Export college information"""
    if st.button("📤 Export College Info", key="export_info_btn"):
        # Create comprehensive college info
        college_info = f"""
SOLAPUR ENGINEERING COLLEGES EXPLORER
=====================================

College Information Export
Generated on: {datetime.now().strftime("%Y-%m-%d %H:%M")}

BASIC INFORMATION:
-----------------
College: {selected_college['name']}
University: {selected_college['university']}
Established: {selected_college.get('established', 'N/A')}
Campus Size: {selected_college.get('campus_size', 'N/A')}

CONTACT DETAILS:
---------------
Address: {selected_college.get('address', 'N/A')}
Contact: {selected_college.get('contact', 'N/A')}
Website: {selected_college.get('website', 'N/A')}

ACADEMIC INFORMATION:
--------------------
Courses Offered: {', '.join(selected_college.get('courses', []))}
Fee Range: {selected_college.get('fees_range', 'N/A')}

FACILITIES:
----------
{', '.join(selected_college.get('facilities', []))}

PLACEMENT INFORMATION:
---------------------
{placement_data.get(selected_college['name'], {}).get('average_package', 'N/A')} - Average Package
{placement_data.get(selected_college['name'], {}).get('highest_package', 'N/A')} - Highest Package
{placement_data.get(selected_college['name'], {}).get('placement_rate', 'N/A')} - Placement Rate

Top Recruiters: {', '.join(placement_data.get(selected_college['name'], {}).get('top_recruiters', []))}

LOCATION INFORMATION:
--------------------
Latitude: {selected_college['lat']}
Longitude: {selected_college['lon']}

---
This information was generated by Solapur Engineering Colleges Explorer.
For the most up-to-date information, please visit the official college website.
        """
        
        st.download_button(
            label="Download College Information as Text",
            data=college_info,
            file_name=f"{selected_college['name'].replace(' ', '_')}_info.txt",
            mime="text/plain"
        )

def show_user_profile():
    """Display user profile and statistics"""
    if st.session_state.authenticated and st.session_state.username:
        user_stats = get_user_stats(st.session_state.username)
        if user_stats:
            st.markdown('<div class="profile-card">', unsafe_allow_html=True)
            st.markdown(f'<div class="profile-header">👤 User Profile: {st.session_state.username}</div>', unsafe_allow_html=True)
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Colleges Visited", user_stats["visited_colleges"])
                st.metric("Total Logins", user_stats["login_count"])
            with col2:
                st.write(f"**Member Since:** {user_stats['registration_date']}")
                
            if user_stats["recent_visits"]:
                st.write("**Recently Visited Colleges:**")
                for visit in reversed(user_stats["recent_visits"]):
                    st.write(f"• {visit['college_name']} - {visit['visit_time']}")
            
            st.markdown('</div>', unsafe_allow_html=True)

# --- Updated Authentication UI Components ---

def show_auth_header():
    """Show authentication header at the top"""
    if not st.session_state.authenticated:
        # Create a clean header with login/register options
        st.markdown('<div class="auth-header-container">', unsafe_allow_html=True)
        st.markdown('<div class="auth-header-content">', unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns([3, 1, 1])
        
        with col1:
            st.markdown('<h1 class="auth-main-title">🎓 Solapur Engineering Colleges Explorer</h1>', unsafe_allow_html=True)
        
        with col2:
            if st.session_state.auth_tab == 'login':
                if st.button("📝 Register", key="header_register_btn", use_container_width=True, 
                           help="Create a new account"):
                    set_auth_tab('register')
                    st.rerun()
            else:
                if st.button("🔐 Login", key="header_login_btn", use_container_width=True,
                           help="Sign in to your account"):
                    set_auth_tab('login')
                    st.rerun()
        
        with col3:
            if st.session_state.auth_tab == 'login':
                st.info("New user?")
            else:
                st.info("Existing user?")
        
        st.markdown('</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

def show_profile_dropdown():
    """Show profile dropdown in the corner"""
    if st.session_state.authenticated and st.session_state.username:
        # Create a profile icon in the top right using columns
        col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
        
        with col1:
            st.markdown('<h1 class="main-header">🎓 Solapur Engineering Colleges Explorer</h1>', unsafe_allow_html=True)
        
        with col4:
            # Profile dropdown using popover
            with st.popover("👤", use_container_width=True):
                user_stats = get_user_stats(st.session_state.username)
                if user_stats:
                    st.markdown(f'<div class="profile-header">👤 {st.session_state.username}</div>', unsafe_allow_html=True)
                    
                    # User statistics
                    st.markdown('<div class="profile-stats">', unsafe_allow_html=True)
                    st.markdown('<div class="profile-stat-item">', unsafe_allow_html=True)
                    st.write(f"**Colleges Visited:** {user_stats['visited_colleges']}")
                    st.markdown('</div>', unsafe_allow_html=True)
                    st.markdown('<div class="profile-stat-item">', unsafe_allow_html=True)
                    st.write(f"**Total Logins:** {user_stats['login_count']}")
                    st.markdown('</div>', unsafe_allow_html=True)
                    st.markdown('<div class="profile-stat-item">', unsafe_allow_html=True)
                    st.write(f"**Member Since:** {user_stats['registration_date'].split()[0]}")
                    st.markdown('</div>', unsafe_allow_html=True)
                    st.markdown('</div>', unsafe_allow_html=True)
                    
                    # Recent visits
                    if user_stats["recent_visits"]:
                        st.markdown('<div class="profile-recent">', unsafe_allow_html=True)
                        st.write("**Recently Visited:**")
                        for visit in reversed(user_stats["recent_visits"][-3:]):
                            st.markdown(f'<div class="profile-recent-item">', unsafe_allow_html=True)
                            st.write(f"• {visit['college_name']}")
                            st.markdown('</div>', unsafe_allow_html=True)
                        st.markdown('</div>', unsafe_allow_html=True)
                    
                    # Logout button
                    if st.button("🚪 Logout", key="profile_logout_btn", use_container_width=True):
                        logout_user()

def show_auth_interface():
    """Show the main authentication interface"""
    st.markdown('<div class="auth-container">', unsafe_allow_html=True)
    st.markdown('<div class="auth-card">', unsafe_allow_html=True)
    
    st.markdown('<div class="auth-welcome-header"> Welcome</div>', unsafe_allow_html=True)
    st.markdown('<div class="auth-subheader">Please authenticate to access Solapur Engineering Colleges Explorer</div>', unsafe_allow_html=True)
    
    # Login Form
    if st.session_state.auth_tab == 'login':
        with st.form("login_form"):
            st.markdown('<div class="auth-form">', unsafe_allow_html=True)
            st.markdown('<div class="auth-input"><label>👤 Username</label>', unsafe_allow_html=True)
            st.text_input("Username", key="login_username", placeholder="Enter your username", label_visibility="collapsed")
            st.markdown('</div>', unsafe_allow_html=True)
            
            st.markdown('<div class="auth-input"><label>🔑 Password</label>', unsafe_allow_html=True)
            st.text_input("Password", type="password", key="login_password", placeholder="Enter your password", label_visibility="collapsed")
            st.markdown('</div>', unsafe_allow_html=True)
            
            if st.form_submit_button("🚀 Login", use_container_width=True):
                login_user()
            st.markdown('</div>', unsafe_allow_html=True)
            
        st.markdown('<div class="auth-switch">Don\'t have an account? Click "Register" above</div>', unsafe_allow_html=True)
    
    # Registration Form
    else:
        with st.form("register_form"):
            st.markdown('<div class="auth-form">', unsafe_allow_html=True)
            st.markdown('<div class="auth-input"><label>👤 Username</label>', unsafe_allow_html=True)
            st.text_input("Username", key="register_username", placeholder="Choose a username", label_visibility="collapsed")
            st.markdown('</div>', unsafe_allow_html=True)
            
            st.markdown('<div class="auth-input"><label>📧 Email (Optional)</label>', unsafe_allow_html=True)
            st.text_input("Email", key="register_email", placeholder="Enter your email", label_visibility="collapsed")
            st.markdown('</div>', unsafe_allow_html=True)
            
            st.markdown('<div class="auth-input"><label>🔑 Password</label>', unsafe_allow_html=True)
            st.text_input("Password", type="password", key="register_password", placeholder="Choose a password (min. 6 characters)", label_visibility="collapsed")
            st.markdown('</div>', unsafe_allow_html=True)
            
            if st.form_submit_button("🎉 Create Account", use_container_width=True):
                register_new_user()
            st.markdown('</div>', unsafe_allow_html=True)
            
        st.markdown('<div class="auth-switch">Already have an account? Click "Login" above</div>', unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

# --- Main Application Logic ---

# Show authentication interface if not authenticated
if not st.session_state.authenticated:
    show_auth_header()
    show_auth_interface()
    
else:
    # User is authenticated - show the main application
    
    # Show profile dropdown in header
    show_profile_dropdown()
    
    # --- Front Page ---
    if st.session_state.page == 'frontpage':
        # Quick Stats Section
        st.markdown("""
        <div style="text-align: center; margin: 40px 0;">
            <h2 style="color: #2F80ED; margin-bottom: 30px;">🚀 Everything You Need to Choose the Right College</h2>
        </div>
        """, unsafe_allow_html=True)

        # Enhanced Features Grid
        col1, col2, col3 = st.columns(3)

        with col1:
            st.markdown("""
            <div class="enhanced-feature-card">
                <div class="enhanced-feature-icon">🗺️</div>
                <h3 class="enhanced-feature-title">Interactive College Map</h3>
                <p class="enhanced-feature-description">Explore all engineering colleges in Solapur on an interactive map with detailed location information and nearby amenities.</p>
            </div>
            """, unsafe_allow_html=True)

            st.markdown("""
            <div class="enhanced-feature-card">
                <div class="enhanced-feature-icon">💰</div>
                <h3 class="enhanced-feature-title">Cost Calculator</h3>
                <p class="enhanced-feature-description">Calculate your estimated monthly expenses including accommodation, food, transport, and miscellaneous costs.</p>
            </div>
            """, unsafe_allow_html=True)

        with col2:
            st.markdown("""
            <div class="enhanced-feature-card">
                <div class="enhanced-feature-icon">🏫</div>
                <h3 class="enhanced-feature-title">College Comparison</h3>
                <p class="enhanced-feature-description">Compare multiple colleges side-by-side based on courses, fees, placement rates, and facilities.</p>
            </div>
            """, unsafe_allow_html=True)

            st.markdown("""
            <div class="enhanced-feature-card">
                <div class="enhanced-feature-icon">📊</div>
                <h3 class="enhanced-feature-title">Data Analytics</h3>
                <p class="enhanced-feature-description">Interactive charts and analytics showing college comparisons, trends, and performance metrics.</p>
            </div>
            """, unsafe_allow_html=True)

        with col3:
            st.markdown("""
            <div class="enhanced-feature-card">
                <div class="enhanced-feature-icon">💼</div>
                <h3 class="enhanced-feature-title">Placement Analytics</h3>
                <p class="enhanced-feature-description">Detailed placement statistics including average packages, top recruiters, and placement rates.</p>
            </div>
            """, unsafe_allow_html=True)

            st.markdown("""
            <div class="enhanced-feature-card">
                <div class="enhanced-feature-icon">🚗</div>
                <h3 class="enhanced-feature-title">Commute Planner</h3>
                <p class="enhanced-feature-description">Smart commute planning with route suggestions, time estimates, and transport mode comparisons.</p>
            </div>
            """, unsafe_allow_html=True)

        # University Section
        st.markdown("<br><hr><h2 style='text-align:center; color:#2F80ED; margin-top:40px;'>🏛️ Affiliated Universities</h2><br>", unsafe_allow_html=True)
        
        uni_col1, uni_col2 = st.columns(2)

        with uni_col1:
            st.markdown(f"""
            <div class="uni-card">
                <img src="{universities['DBATU']['image']}" alt="DBATU Logo" class="uni-logo">
                <div class="uni-info">
                    <h3 class="uni-name">Dr. Babasaheb Ambedkar Technological University (DBATU)</h3>
                    <p class="uni-details">📍 {universities['DBATU']['location']} • Founded: {universities['DBATU']['founded']}</p>
                    <p class="uni-description">{universities['DBATU']['description']}</p>
                    <a href="{universities['DBATU']['website']}" target="_blank" class="uni-website">Visit Website</a>
                </div>
            </div>
            """, unsafe_allow_html=True)

        with uni_col2:
            st.markdown(f"""
            <div class="uni-card">
                <img src="{universities['Solapur University']['image']}" alt="Solapur University Logo" class="uni-logo">
                <div class="uni-info">
                    <h3 class="uni-name">Solapur University</h3>
                    <p class="uni-details">📍 {universities['Solapur University']['location']} • Founded: {universities['Solapur University']['founded']}</p>
                    <p class="uni-description">{universities['Solapur University']['description']}</p>
                    <a href="{universities['Solapur University']['website']}" target="_blank" class="uni-website">Visit Website</a>
                </div>
            </div>
            """, unsafe_allow_html=True)

        # Call to Action
        st.markdown("""
        <div style="text-align: center; margin: 50px 0;">
            <h2 style="color: #2F80ED; margin-bottom: 20px;">Ready to Explore?</h2>
            <p style="color: #6B7280; font-size: 1.2rem; margin-bottom: 30px;">Start your journey to find the perfect engineering college in Solapur</p>
        </div>
        """, unsafe_allow_html=True)

        # Main Action Button
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("🚀 Explore Colleges on Interactive Map →", key="explore_btn", use_container_width=True, type="primary"):
                go_to_map()

        # Footer
        st.markdown("---")
        st.markdown(
            "<p style='text-align:center; color:#6B7280;'>"
            "Built with ❤️ using Streamlit and Folium • Enhanced 3D UI • For demonstration purposes only"
            "</p>",
            unsafe_allow_html=True
        )

    # --- Map Page ---
    elif st.session_state.page == 'map':
        # Add a back button with 3D effect
        col1, col2, col3 = st.columns([1, 2, 1])
        with col1:
            if st.button("← Back to Overview", key="back_btn", use_container_width=True):
                go_to_front()
        
        # Create tabs for main content and enhanced tools
        tab1, tab2, tab3, tab4 = st.tabs([
            "🗺️ Interactive Map",
            "🏫 Compare Colleges", 
            "💰 Cost Calculator",
            "📊 View Analytics"
        ])
        
        # Tab 1: Interactive Map (Original Functionality)
        with tab1:
            st.markdown("## 📍 Interactive College Map & Details")
            
            # Initialize filtered_colleges in session state
            if 'filtered_colleges' not in st.session_state:
                st.session_state.filtered_colleges = enhanced_colleges

            # Enhanced Sidebar with new features
            with st.sidebar:
                st.header("⚙️ Map Controls")

                st.subheader("Filter by College")
                college_names = [c["name"] for c in enhanced_colleges]
                selected_college_name = st.selectbox("Choose College:", ["No College Selected", "All Colleges"] + college_names, index=0)

                # Adjust target colleges based on single selection
                if selected_college_name == "No College Selected":
                    st.session_state.filtered_colleges = []
                elif selected_college_name != "All Colleges":
                    st.session_state.filtered_colleges = [c for c in enhanced_colleges if c["name"] == selected_college_name]
                else:
                    st.session_state.filtered_colleges = enhanced_colleges

                st.subheader("🏛️ University Affiliation")
                col1, col2 = st.columns(2)
                with col1:
                    filter_dbat = st.checkbox("DBATU", value=True)
                with col2:
                    filter_solapur_uni = st.checkbox("Solapur University", value=True)

                # Apply university filter to the currently filtered list
                if filter_dbat and not filter_solapur_uni:
                    st.session_state.filtered_colleges = [c for c in st.session_state.filtered_colleges if c["university"] == "DBATU"]
                elif filter_solapur_uni and not filter_dbat:
                    st.session_state.filtered_colleges = [c for c in st.session_state.filtered_colleges if c["university"] == "Solapur University"]

                st.markdown("---")
                st.subheader("🏙️ Nearby Places & Routes")
                selected_categories = []
                for category in categories:
                    if st.checkbox(f"Show {category}", value=False):
                        selected_categories.append(category)

            # Determine what to show based on selection
            target_colleges = st.session_state.filtered_colleges
            show_colleges = len(target_colleges) > 0
            show_college_connections = show_colleges

            # Find the selected college for detail view (only if ONE college is selected/filtered)
            selected_college = target_colleges[0] if len(target_colleges) == 1 else None
                
            # Define bounds (for initial map fit)
            all_lats = [c["lat"] for c in enhanced_colleges] + [u["coords"][0] for u in universities.values()] + [station_coords[0], bus_stand_coords[0]]
            all_lons = [c["lon"] for c in enhanced_colleges] + [u["coords"][1] for u in universities.values()] + [station_coords[1], bus_stand_coords[1]]
            sw = [min(all_lats) - 0.05, min(all_lons) - 0.05]
            ne = [max(all_lats) + 0.05, max(all_lons) + 0.05]

            # Create map with initial settings
            m = folium.Map(location=[17.6768, 75.9216], zoom_start=12)

            # Add college markers if selected with improved clustering
            if show_colleges:
                cluster = MarkerCluster(name="Engineering Colleges")
                for college in target_colleges:
                    college_coords = [college["lat"], college["lon"]]
                    rail_distance = round(geodesic(station_coords, college_coords).km, 2)
                    bus_distance = round(geodesic(bus_stand_coords, college_coords).km, 2)
                    
                    popup_html = f"""
                    <div style='width:250px; font-family:sans-serif;'>
                        <h4 style='color:#2F80ED;'>{college['name']}</h4>
                        <b>University:</b> {college['university']}<br>
                        <b>Established:</b> {college.get('established', 'N/A')}<br>
                        <b>Rail Dist:</b> {rail_distance} km<br>
                        <b>Bus Dist:</b> {bus_distance} km<br>
                        <b>Courses:</b> {len(college.get('courses', []))}<br>
                        <a href="{college['website']}" target="_blank" style='color:#F2994A; font-weight:bold;'>Visit Website →</a>
                        {'<br><img src="' + college['image'] + '" width="240" style="margin-top:10px; border-radius:8px;">' if college['image'] else ''}
                    </div>
                    """
                    cluster.add_child(folium.Marker(
                        location=college_coords,
                        popup=folium.Popup(popup_html, max_width=300),
                        icon=folium.Icon(color="darkblue", icon="graduation-cap", prefix="fa")
                    ))
                    
                    # Record college visit if user is authenticated
                    if st.session_state.authenticated and st.session_state.username:
                        record_college_visit(st.session_state.username, college['name'])
                    
                    # Add transport connections if showing colleges and transport is selected
                    if "Public Transport" in selected_categories:
                        # Rail connection
                        folium.PolyLine(
                            locations=[station_coords, college_coords],
                            color="#2F80ED", # Blue for rail
                            weight=2,
                            opacity=0.6,
                            tooltip=f"Railway to {college['name']}: {rail_distance} km"
                        ).add_to(m)
                        
                        # Bus connection
                        folium.PolyLine(
                            locations=[bus_stand_coords, college_coords],
                            color="#219653", # Green for bus
                            weight=2,
                            opacity=0.6,
                            tooltip=f"Bus Stand to {college['name']}: {bus_distance} km"
                        ).add_to(m)
                
                m.add_child(cluster)

            # Add selected category data
            for category in selected_categories:
                if category == "Public Transport":
                    # Add transport hubs only when checkbox is selected
                    folium.Marker(
                        location=station_coords,
                        popup="Solapur Railway Station",
                        icon=folium.Icon(color="darkgreen", icon="train", prefix="fa")
                    ).add_to(m)
                    
                    folium.Marker(
                        location=bus_stand_coords,
                        popup="Solapur Central Bus Stand",
                        icon=folium.Icon(color="orange", icon="bus", prefix="fa")
                    ).add_to(m)
                    
                elif show_colleges:
                    # Use FeatureGroup for other amenities for layer control
                    fg = FeatureGroup(name=category)
                    
                    # Determine if we should show fee/distance details (Apartment is a good candidate)
                    include_details = category == "Apartment" or category == "Cafe"

                    for college in target_colleges:
                        places = generate_places(college, category, include_fee=include_details)
                        for p in places:
                            distance = round(geodesic((college["lat"], college["lon"]), (p["lat"], p["lon"])).km, 2) if include_details else None
                            
                            popup_text = f"<b>{p['name']}</b><br>"
                            if p["fee"]:
                                 popup_text += f"Avg. Rent: ₹{p['fee']:,}/month<br>"
                            if distance is not None:
                                popup_text += f"Distance to {college['name']}: {distance} km"
                                
                            folium.Marker(
                                location=[p["lat"], p["lon"]],
                                popup=popup_text,
                                icon=folium.Icon(color=p["color"], icon=p["icon"], prefix="fa")
                            ).add_to(fg)
                    m.add_child(fg)

            # Add university markers and connection lines
            university_network_fg = FeatureGroup(name="University Network")

            # Add DBATU marker and connections
            if filter_dbat:
                uni = universities["DBATU"]
                popup_html = f"<b>DBATU</b><br><a href=\"{uni['website']}\" target=\"_blank\">Visit Website</a>"
                folium.Marker(
                    location=uni["coords"],
                    popup=folium.Popup(popup_html, max_width=300),
                    icon=folium.Icon(color="black", icon="building", prefix="fa")
                ).add_to(university_network_fg)
                
                if show_colleges and show_college_connections:
                    for college in target_colleges:
                        if college["university"] == "DBATU":
                            folium.PolyLine(
                                locations=[uni["coords"], [college["lat"], college["lon"]]],
                                color="black", weight=1.5, opacity=0.5
                            ).add_to(university_network_fg)

            # Add Solapur University marker and connections
            if filter_solapur_uni:
                uni = universities["Solapur University"]
                popup_html = f"<b>Solapur University</b><br><a href=\"{uni['website']}\" target=\"_blank\">Visit Website</a>"
                folium.Marker(
                    location=uni["coords"],
                    popup=folium.Popup(popup_html, max_width=300),
                    icon=folium.Icon(color="gray", icon="building", prefix="fa")
                ).add_to(university_network_fg)

                if show_colleges and show_college_connections:
                    for college in target_colleges:
                        if college["university"] == "Solapur University":
                            folium.PolyLine(
                                locations=[uni["coords"], [college["lat"], college["lon"]]],
                                color="black", weight=1.5, opacity=0.5
                            ).add_to(university_network_fg)

            m.add_child(university_network_fg)

            LayerControl(collapsed=True).add_to(m)
            m.fit_bounds([sw, ne])
            
            # --- Dynamic Layout Rendering: Map and Details ---
            
            if selected_college:
                # Use columns for a balanced layout
                map_col, detail_col = st.columns([3, 1])

                with detail_col:
                    st.markdown(f"<div class='detail-card-enhanced'>", unsafe_allow_html=True)
                    st.markdown(f"<h3 class='detail-header'>🏛️ {selected_college['name']}</h3>", unsafe_allow_html=True)
                    
                    # Campus Image
                    if selected_college['image']:
                        st.image(selected_college['image'], caption="Campus View", use_container_width=True)

                    st.info(f"**Affiliation:** {selected_college['university']} University")
                    st.write(f"**Established:** {selected_college.get('established', 'N/A')}")
                    st.write(f"**Campus Size:** {selected_college.get('campus_size', 'N/A')}")
                    st.markdown(f"[🔗 **Visit Official Website**]({selected_college['website']})")
                    
                    # Contact Information
                    with st.expander("📞 Contact Information"):
                        st.write(f"**Address:** {selected_college.get('address', 'N/A')}")
                        st.write(f"**Contact:** {selected_college.get('contact', 'N/A')}")
                    
                    # Courses
                    with st.expander("📚 Courses Offered"):
                        for course in selected_college.get('courses', []):
                            st.write(f"• {course}")
                    
                    # Facilities
                    with st.expander("🏢 Facilities"):
                        for facility in selected_college.get('facilities', []):
                            st.write(f"• {facility}")
                    
                    st.markdown("---")
                    
                    # Calculate and display distances using metrics
                    college_coords = [selected_college["lat"], selected_college["lon"]]
                    rail_distance = round(geodesic(station_coords, college_coords).km, 2)
                    bus_distance = round(geodesic(bus_stand_coords, college_coords).km, 2)

                    st.metric(label="🚉 Rail Station Distance", value=f"{rail_distance} km")
                    st.metric(label="🚌 Bus Stand Distance", value=f"{bus_distance} km")

                    st.markdown("</div>", unsafe_allow_html=True)

                with map_col:
                    st_folium(m, height=800, width='100%', returned_objects=[], center=None)
                    
            else:
                # Full width for the map when multiple or no colleges are selected
                st_folium(m, height=800, width='100%', returned_objects=[], center=None)
        
        # Tab 2: College Comparison
        with tab2:
            show_college_comparison()
        
        # Tab 3: Cost Calculator
        with tab3:
            cost_of_living_calculator()
        
        # Tab 4: Analytics
        with tab4:
            show_analytics()