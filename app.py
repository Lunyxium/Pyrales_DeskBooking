"""
BIIS Desk Booking System - Main Application (GORGEOUS USER SELECTION LAYOUT)
Author: [Your Name]
Date: [Date]
Description: GORGEOUS compact user selection with perfect positioning

GORGEOUS FEATURES ADDED:
- Compact centered user selection under week navigation
- Beautiful mini-title design
- Half-width controls, perfectly centered
- Sidebar user selection at top
- "Klein und süss" styling throughout

INDEX:
1. IMPORTS & CONFIGURATION
2. SESSION STATE & INITIALIZATION
3. OPTIMIZED CSS & UI MANAGEMENT
4. DATA MANAGEMENT FUNCTIONS (FIXED)
5. HELPER FUNCTIONS
6. DESK RENDERING & BOOKING LOGIC
7. ROOM BLOCKER FUNCTIONS
8. DIALOG DEFINITIONS
9. MAIN APPLICATION RENDERING
10. FOOTER
"""

# ============================================================================
# 1. IMPORTS & CONFIGURATION
# ============================================================================

import streamlit as st
import json
import os
from datetime import datetime, timedelta
from PIL import Image
import pandas as pd
import uuid

# Import our modular sidebar
from sidebar_settings import create_sidebar

# Import shared utilities
from shared_functions import get_user_colors, save_data_utility, save_avatar_utility

# Page configuration - must be first streamlit command
st.set_page_config(
    page_title="BIIS Desk Booking",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ============================================================================
# 2. SESSION STATE & INITIALIZATION
# ============================================================================

# Define all session state defaults with smart week calculation
def initialize_session_state():
    """Initialize session state with optimized defaults"""
    today = datetime.now()

    # Smart week logic: Friday after 2pm or weekend shows next week
    if (today.weekday() == 4 and today.hour >= 14) or today.weekday() >= 5:
        days_until_monday = (7 - today.weekday()) % 7
        if days_until_monday == 0:
            days_until_monday = 7
        next_monday = today + timedelta(days=days_until_monday)
        current_week_start = next_monday.date()
        current_tab = 0
        is_viewing_next_week_as_current = True
    else:
        # Normal week: show current Monday
        days_since_monday = today.weekday()
        monday = today - timedelta(days=days_since_monday)
        current_week_start = monday.date()
        current_tab = today.weekday() if today.weekday() < 5 else 0
        is_viewing_next_week_as_current = False

    # Session state defaults
    session_defaults = {
        'current_week_start': current_week_start,
        'current_tab': current_tab,
        'is_viewing_next_week_as_current': is_viewing_next_week_as_current,
        'users': {},
        'bookings': {},
        'team_news': "",
        'desk_names': {},
        'holidays': {},
        # User session selection - PREMIUM UX FEATURE
        'selected_user_for_session': None,
        # UI state
        'show_streamlit_header': False,
        'debug_mode': False,
        # Dialog states
        'show_add_user': False,
        'show_manage_users': False,
        'show_all_users': False,
        'editing_user': None,
        'show_settings': False,
        'show_desk_naming': False,
        'show_holidays': False,
        'show_room_blocker': False,
        'blocking_room': None,
        'show_sidebar_menu': False,
        'booking_desk': None
    }

    # Initialize only missing keys
    for key, default_value in session_defaults.items():
        if key not in st.session_state:
            st.session_state[key] = default_value

# Initialize session state on startup
initialize_session_state()

# ============================================================================
# 3. OPTIMIZED CSS & UI MANAGEMENT
# ============================================================================

@st.cache_data
def load_css_content():
    """Load CSS content once and cache it"""
    try:
        with open('style/custom.css', 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        st.warning("Custom CSS file not found at 'style/custom.css'")
        return ""

def apply_css_always():
    """Apply CSS on every run to ensure dialog compatibility"""
    # Dynamic header visibility based on toggle state
    if st.session_state.show_streamlit_header:
        hide_streamlit_style = """
        <style>
        footer {visibility: hidden;}
        </style>
        """
    else:
        hide_streamlit_style = """
        <style>
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
        .stDeployButton {visibility: hidden;}
        div[data-testid="stToolbar"] {visibility: hidden;}
        .stActionButton {visibility: hidden;}
        
        /* Remove header anchor links and image expand buttons */
        .stMarkdown h1 a, .stMarkdown h2 a, .stMarkdown h3 a { display: none !important; }
        button[title="View fullscreen"] { display: none !important; }
        div[data-testid="stImage"] button { display: none !important; }
        [data-testid="StyledLinkIconContainer"] { display: none !important; }
        </style>
        """
    st.markdown(hide_streamlit_style, unsafe_allow_html=True)

    # Load custom CSS - cached but applied every run for dialog compatibility
    css_content = load_css_content()
    if css_content:
        st.markdown(f'<style>{css_content}</style>', unsafe_allow_html=True)

# Apply CSS on every run (but content is cached)
apply_css_always()

# ============================================================================
# 4. DATA MANAGEMENT FUNCTIONS (FIXED)
# ============================================================================

@st.cache_data
def load_data_cached():
    """Load data with caching for better performance"""
    data = {'users': {}, 'bookings': {}, 'settings': {}}

    try:
        # Load user data
        if os.path.exists('data/users.json'):
            with open('data/users.json', 'r', encoding='utf-8') as f:
                data['users'] = json.load(f)

        # Load booking data
        if os.path.exists('data/bookings.json'):
            with open('data/bookings.json', 'r', encoding='utf-8') as f:
                data['bookings'] = json.load(f)

        # Load settings
        if os.path.exists('data/settings.json'):
            with open('data/settings.json', 'r', encoding='utf-8') as f:
                data['settings'] = json.load(f)
        elif os.path.exists('data/team_news.json'):  # Fallback
            with open('data/team_news.json', 'r', encoding='utf-8') as f:
                news_data = json.load(f)
                data['settings'] = {'team_news': news_data.get('news', '')}

    except Exception as e:
        st.error(f"Error loading data: {e}")

    return data

def load_data():
    """Load all application data from JSON files with caching - FIXED to not override session state"""
    data = load_data_cached()

    # FIXED: Don't override session state if it already has data (prevents cache override problem)
    if 'users' not in st.session_state or not st.session_state.users:
        st.session_state.users = data['users']

    if 'bookings' not in st.session_state or not st.session_state.bookings:
        st.session_state.bookings = data['bookings']

    # Handle settings
    settings = data['settings']
    st.session_state.team_news = settings.get('team_news', '')
    st.session_state.desk_names = settings.get('desk_names', {})
    st.session_state.holidays = settings.get('holidays', {})

def save_data():
    """Save all application data using shared utility"""
    save_data_utility(
        st.session_state.users,
        st.session_state.bookings,
        st.session_state.team_news,
        st.session_state.desk_names,
        st.session_state.holidays
    )
    # Clear cache to ensure fresh data on next load
    load_data_cached.clear()

def force_reload_data():
    """FORCE reload data from JSON - used after template changes"""
    # Clear cache first
    load_data_cached.clear()

    # Load fresh data
    data = load_data_cached()

    # Force update session state with fresh data
    st.session_state.users = data['users']
    st.session_state.bookings = data['bookings']

    # Handle settings
    settings = data.get('settings', {})
    st.session_state.team_news = settings.get('team_news', '')
    st.session_state.desk_names = settings.get('desk_names', {})
    st.session_state.holidays = settings.get('holidays', {})

# ============================================================================
# 5. HELPER FUNCTIONS
# ============================================================================

def get_desk_name(room, desk_num):
    """Get custom desk name or fallback to default naming"""
    desk_key = f"{room}_{desk_num}"
    return st.session_state.desk_names.get(desk_key, f"Desk {desk_num}")

def set_desk_name(room, desk_num, name):
    """Set custom desk name with 20 character limit"""
    if len(name) > 20:
        name = name[:20]
    desk_key = f"{room}_{desk_num}"

    if name.strip():
        st.session_state.desk_names[desk_key] = name.strip()
    else:
        # Remove custom name if empty
        if desk_key in st.session_state.desk_names:
            del st.session_state.desk_names[desk_key]
    save_data()

def get_week_dates(start_date):
    """Generate list of 5 weekday dates from Monday start date"""
    return [start_date + timedelta(days=i) for i in range(5)]

def format_date_key(date):
    """Convert date to string key for booking storage"""
    return date.strftime('%Y-%m-%d')

def generate_user_id():
    """Generate unique 8-character user ID"""
    return str(uuid.uuid4())[:8]

@st.cache_data
def get_logo_base64():
    """Get logo as base64 with caching"""
    try:
        if os.path.exists('media/images/logo.png'):
            with open('media/images/logo.png', 'rb') as f:
                import base64
                return base64.b64encode(f.read()).decode()
    except:
        pass
    return None

def save_avatar(uploaded_file, user_id):
    """Save and resize uploaded avatar file"""
    return save_avatar_utility(uploaded_file, user_id)

# ============================================================================
# 6. DESK RENDERING & BOOKING LOGIC
# ============================================================================

def get_booking_key(date, room, desk_num):
    """Generate unique key for booking storage"""
    return f"{format_date_key(date)}_{room}_{desk_num}"

def get_desk_status(date, room, desk_num):
    """Get current booking status for specific desk"""
    booking_key = get_booking_key(date, room, desk_num)
    return st.session_state.bookings.get(booking_key)

def create_booking(date, room, desk_num, user_id, booking_type):
    """Create new desk booking"""
    booking_key = get_booking_key(date, room, desk_num)

    booking_data = {
        'user_id': user_id,
        'booking_type': booking_type,
        'created_at': datetime.now().isoformat(),
        'date': format_date_key(date),
        'room': room,
        'desk_num': desk_num,
        'entry_type': 'desk_booking'
    }

    st.session_state.bookings[booking_key] = booking_data
    save_data()
    return True

def remove_booking(date, room, desk_num):
    """Remove existing desk booking"""
    booking_key = get_booking_key(date, room, desk_num)
    if booking_key in st.session_state.bookings:
        del st.session_state.bookings[booking_key]
        save_data()
        return True
    return False

def can_override_booking(current_booking, new_booking_type):
    """Check if current booking can be overridden by new booking type"""
    if not current_booking:
        return True

    current_type = current_booking.get('booking_type', '')

    # Maybe bookings can be overridden by any other type
    if current_type == 'maybe' and new_booking_type != 'maybe':
        return True

    # Half-day bookings can be combined
    if current_type == 'half_am' and new_booking_type == 'half_pm':
        return True
    if current_type == 'half_pm' and new_booking_type == 'half_am':
        return True

    return False

# ============================================================================
# 7. ROOM BLOCKER FUNCTIONS
# ============================================================================

def get_room_blocker_key(date, room):
    """Generate unique key for room blocker storage"""
    return f"{format_date_key(date)}_{room}_ROOM_BLOCKER"

def get_room_blocker(date, room):
    """Get current room blocker for specific date and room"""
    blocker_key = get_room_blocker_key(date, room)
    return st.session_state.bookings.get(blocker_key)

def create_room_blocker(date, room, user_id, blocker_type, custom_time_start=None, custom_time_end=None, reason=""):
    """Create new room blocker"""
    blocker_key = get_room_blocker_key(date, room)

    # Define time ranges for blocker types
    time_ranges = {
        'morning': ('09:00', '12:00'),
        'afternoon': ('13:00', '17:00'),
        'full_day': ('08:00', '18:00'),
        'custom': (custom_time_start, custom_time_end)
    }

    start_time, end_time = time_ranges[blocker_type]

    blocker_data = {
        'user_id': user_id,
        'blocker_type': blocker_type,
        'start_time': start_time,
        'end_time': end_time,
        'reason': reason[:20] if reason else "",
        'created_at': datetime.now().isoformat(),
        'date': format_date_key(date),
        'room': room,
        'entry_type': 'room_blocker'
    }

    st.session_state.bookings[blocker_key] = blocker_data
    save_data()
    return True

def remove_room_blocker(date, room):
    """Remove existing room blocker"""
    blocker_key = get_room_blocker_key(date, room)
    if blocker_key in st.session_state.bookings:
        del st.session_state.bookings[blocker_key]
        save_data()
        return True
    return False

def is_room_blocked(date, room):
    """Check if room is blocked on specific date"""
    return get_room_blocker(date, room) is not None

def get_room_block_message(date, room):
    """Get formatted room block message"""
    blocker = get_room_blocker(date, room)
    if not blocker:
        return None

    user_id = blocker.get('user_id')
    if user_id == 'DELETED_USER':
        username = blocker.get('archived_username', 'Deleted User')
    else:
        user_data = st.session_state.users.get(user_id, {})
        username = user_data.get('username', 'Unknown User')

    start_time = blocker.get('start_time', '')
    end_time = blocker.get('end_time', '')
    reason = blocker.get('reason', '')

    message = f"This room is blocked from {start_time} to {end_time} by {username}"
    if reason:
        message += f" ({reason})"

    return message

# ============================================================================
# 8. DIALOG DEFINITIONS
# ============================================================================

@st.dialog("Add New User")
def add_user_dialog():
    """Dialog for creating new users with avatar and color selection"""
    username = st.text_input("Username (Required)", placeholder="Enter username...")
    full_name = st.text_input("Full Name (Optional)", placeholder="Enter full name...")

    # Color selection with availability check
    available_colors = get_user_colors()
    used_colors = [user.get('color', '') for user in st.session_state.users.values()]
    free_colors = [color for color in available_colors if color not in used_colors]

    if free_colors:
        selected_color = st.selectbox("User Color", free_colors,
                                      format_func=lambda x: f"Color {available_colors.index(x) + 1}")
    else:
        selected_color = st.selectbox("User Color (all colors in use)", available_colors,
                                      format_func=lambda x: f"Color {available_colors.index(x) + 1}")

    # Color preview
    if selected_color:
        st.markdown(
            f'<div style="width: 60px; height: 60px; background-color: {selected_color}; '
            f'border-radius: 30px; border: 3px solid #66b446; margin: 10px auto;"></div>',
            unsafe_allow_html=True)

    # Avatar upload
    uploaded_avatar = st.file_uploader("Avatar Image", type=['png', 'jpg', 'jpeg'],
                                       help="Max 200x200px, will be resized")

    # Action buttons
    col1, col2 = st.columns(2)
    with col1:
        if st.button("✓ Create User", key="dialog_create_user", use_container_width=True):
            if username and username.strip():
                user_id = generate_user_id()
                avatar_path = None

                if uploaded_avatar:
                    avatar_path = save_avatar(uploaded_avatar, user_id)

                # Create user record
                st.session_state.users[user_id] = {
                    'username': username.strip(),
                    'full_name': full_name.strip() if full_name and full_name.strip() else username.strip(),
                    'color': selected_color,
                    'avatar_path': avatar_path,
                    'created_date': datetime.now().isoformat()
                }

                save_data()
                # FIXED: Use success message instead of balloons
                st.success(f"User '{username}' created successfully!")
                st.rerun()
            else:
                st.error("Username is required!")

    with col2:
        if st.button("✖ Cancel", key="dialog_cancel_user", use_container_width=True):
            st.rerun()


@st.dialog("Book Desk")
def book_desk_dialog(date, room, desk_num):
    """Dialog for creating desk bookings with FIXED user selection"""
    desk_display_name = get_desk_name(room, desk_num)

    # Display booking context
    st.markdown(f"**Location:** {room.replace('_', ' ').title()}")
    st.markdown(f"**Desk:** {desk_display_name}")
    st.markdown(f"**Date:** {date.strftime('%A, %d. %B %Y')}")

    # Check for room blocker and show warning
    room_blocker = get_room_blocker(date, room)
    if room_blocker:
        user_id = room_blocker.get('user_id')
        if user_id == 'DELETED_USER':
            blocker_username = room_blocker.get('archived_username', 'Deleted User')
        else:
            blocker_user_data = st.session_state.users.get(user_id, {})
            blocker_username = blocker_user_data.get('username', 'Unknown User')

        start_time = room_blocker.get('start_time', '')
        end_time = room_blocker.get('end_time', '')
        reason = room_blocker.get('reason', '')

        warning_message = f"⚠️ **Please be aware, this room is blocked from {start_time} to {end_time} by {blocker_username}"
        if reason:
            warning_message += f" ({reason})"
        warning_message += " and this desk might not be available during that time.**"

        st.warning(warning_message)

    existing_booking = get_desk_status(date, room, desk_num)

    # FIXED: User selection with mandatory selection
    if st.session_state.users:
        user_options = {f"{data['username']}": user_id
                        for user_id, data in st.session_state.users.items()}

        # CRITICAL FIX: Empty default + placeholder with SESSION PRE-SELECTION
        if st.session_state.get('selected_user_for_session'):
            # Pre-select the session user
            session_username = st.session_state.users[st.session_state.selected_user_for_session]['username']
            try:
                default_index = list(user_options.keys()).index(session_username)
            except ValueError:
                default_index = None
        else:
            default_index = None

        selected_username = st.selectbox(
            "Select User",
            options=list(user_options.keys()),
            index=default_index,
            placeholder="Choose a user..." if default_index is None else None,
            key="book_desk_user_select"
        )

        # VALIDATION: User must be selected
        if not selected_username:
            st.warning("⚠️ Please select a user first.")
            selected_user_id = None
        else:
            selected_user_id = user_options[selected_username]
    else:
        st.error("No users available. Please create users first.")
        selected_user_id = None

    # Booking type selection
    if selected_user_id:
        booking_options = {
            'Full Day': 'full_day',
            'Morning (AM)': 'half_am',
            'Afternoon (PM)': 'half_pm',
            'Maybe (Tentative)': 'maybe'
        }

        booking_type_display = st.selectbox("Booking Type", options=list(booking_options.keys()))
        booking_type = booking_options[booking_type_display]

        # User preview
        user_data = st.session_state.users[selected_user_id]
        st.markdown("**User Preview:**")
        color_box = f'<div style="display: inline-block; width: 40px; height: 40px; background-color: {user_data["color"]}; border-radius: 20px; margin-right: 10px; vertical-align: middle; border: 2px solid #66b446;"></div>'
        st.markdown(f'{color_box} {user_data["username"]}', unsafe_allow_html=True)

        if user_data.get('avatar_path') and os.path.exists(user_data['avatar_path']):
            st.image(user_data['avatar_path'], width=80)
    else:
        booking_type = None

    # Action buttons
    col1, col2 = st.columns(2)

    with col1:
        if st.button("✓ Confirm Booking", key="dialog_confirm_booking", use_container_width=True):
            if selected_user_id and booking_type:
                if not existing_booking or can_override_booking(existing_booking, booking_type):
                    success = create_booking(date, room, desk_num, selected_user_id, booking_type)
                    if success:
                        # FIXED: Use success message instead of balloons
                        st.success("Booking created successfully!")
                        st.rerun()
                    else:
                        st.error("Failed to create booking")
                else:
                    st.error("Cannot override existing booking")
            else:
                st.error("Please select a user and booking type")

    with col2:
        if st.button("✖ Cancel", key="dialog_cancel_booking", use_container_width=True):
            st.rerun()


@st.dialog("Block Room")
def block_room_dialog(date, room):
    """Dialog for creating room blockers with FIXED user selection"""
    st.markdown(f"### Block {room.replace('_', ' ').title()}")
    st.markdown(f"**Date:** {date.strftime('%A, %d. %B %Y')}")

    # Check if room is already blocked
    existing_blocker = get_room_blocker(date, room)
    if existing_blocker:
        user_id = existing_blocker.get('user_id')
        if user_id == 'DELETED_USER':
            blocker_username = existing_blocker.get('archived_username', 'Deleted User')
        else:
            blocker_user_data = st.session_state.users.get(user_id, {})
            blocker_username = blocker_user_data.get('username', 'Unknown User')

        st.warning(
            f"Room is already blocked by {blocker_username} from {existing_blocker.get('start_time')} to {existing_blocker.get('end_time')}")

        # Option to remove existing blocker
        if st.button("🗑️ Remove Existing Block", key="dialog_remove_blocker", use_container_width=True):
            remove_room_blocker(date, room)
            st.success("Room blocker removed!")
            st.rerun()

        if st.button("✖ Cancel", key="dialog_cancel_block_existing", use_container_width=True):
            st.rerun()
        return

    # FIXED: User selection with SESSION PRE-SELECTION
    if st.session_state.users:
        user_options = {f"{data['username']}": user_id
                        for user_id, data in st.session_state.users.items()}

        # Pre-select session user if available
        if st.session_state.get('selected_user_for_session'):
            session_username = st.session_state.users[st.session_state.selected_user_for_session]['username']
            try:
                default_index = list(user_options.keys()).index(session_username)
            except ValueError:
                default_index = None
        else:
            default_index = None

        selected_username = st.selectbox(
            "Select User",
            options=list(user_options.keys()),
            index=default_index,
            placeholder="Choose a user..." if default_index is None else None,
            key="block_room_user_select"
        )

        # VALIDATION: User must be selected
        if not selected_username:
            st.warning("⚠️ Please select a user first.")
            selected_user_id = None
        else:
            selected_user_id = user_options[selected_username]
    else:
        st.error("No users available. Please create users first.")
        selected_user_id = None

    # Rest of blocking logic only if user selected
    if selected_user_id:
        # Blocker type selection
        blocker_options = {
            'Morning': 'morning',
            'Afternoon': 'afternoon',
            'Full Day': 'full_day',
            'Custom Time': 'custom'
        }

        blocker_type_display = st.selectbox("Block Type", options=list(blocker_options.keys()))
        blocker_type = blocker_options[blocker_type_display]

        # Custom time inputs
        custom_start = None
        custom_end = None
        if blocker_type == 'custom':
            col1, col2 = st.columns(2)
            with col1:
                custom_start = st.time_input("Start Time", value=datetime.strptime("09:00", "%H:%M").time())
            with col2:
                custom_end = st.time_input("End Time", value=datetime.strptime("17:00", "%H:%M").time())

            custom_start = custom_start.strftime("%H:%M")
            custom_end = custom_end.strftime("%H:%M")

        # Reason input
        reason = st.text_input("Reason (Optional, max 20 chars)", max_chars=20,
                               placeholder="Meeting, maintenance, etc.")

        # Preview
        if blocker_type != 'custom':
            time_ranges = {
                'morning': ('09:00', '12:00'),
                'afternoon': ('13:00', '17:00'),
                'full_day': ('08:00', '18:00')
            }
            start_time, end_time = time_ranges[blocker_type]
        else:
            start_time, end_time = custom_start, custom_end

        st.markdown("**Preview:**")
        preview_text = f"Room will be blocked from {start_time} to {end_time}"
        if reason:
            preview_text += f" ({reason})"
        st.info(preview_text)
    else:
        blocker_type = None

    # Action buttons
    col1, col2 = st.columns(2)

    with col1:
        if st.button("🚫 Block Room", key="dialog_confirm_block", use_container_width=True):
            if selected_user_id and blocker_type:
                success = create_room_blocker(date, room, selected_user_id, blocker_type, custom_start, custom_end,
                                              reason)
                if success:
                    # FIXED: Use success message instead of balloons
                    st.success("Room blocked successfully!")
                    st.rerun()
                else:
                    st.error("Failed to block room")
            else:
                st.error("Please select a user and block type")

    with col2:
        if st.button("✖ Cancel", key="dialog_cancel_block", use_container_width=True):
            st.rerun()

@st.dialog("Change Desk Names")
def desk_naming_dialog():
    """Dialog for customizing desk names"""
    st.markdown("### 🏷️ Customize Desk Names")
    st.markdown("Give your desks personal names (max 20 characters each)")

    # Büro Klein section
    st.markdown("#### 🚪 Büro Klein")
    klein_col1, klein_col2 = st.columns(2)

    with klein_col1:
        st.markdown("**Left Position**")
        current_name_k1 = get_desk_name("klein", 1)
        new_name_k1 = st.text_input(
            "Desk Name",
            value=current_name_k1 if current_name_k1 != "Desk 1" else "",
            max_chars=20,
            key="klein_1_name",
            placeholder="Enter custom name..."
        )
        if st.button("💾 Update", key="save_klein_1", use_container_width=True):
            set_desk_name("klein", 1, new_name_k1)
            st.success(f"Updated Klein Desk 1!")
            st.rerun()

    with klein_col2:
        st.markdown("**Right Position**")
        current_name_k2 = get_desk_name("klein", 2)
        new_name_k2 = st.text_input(
            "Desk Name",
            value=current_name_k2 if current_name_k2 != "Desk 2" else "",
            max_chars=20,
            key="klein_2_name",
            placeholder="Enter custom name..."
        )
        if st.button("💾 Update", key="save_klein_2", use_container_width=True):
            set_desk_name("klein", 2, new_name_k2)
            st.success(f"Updated Klein Desk 2!")
            st.rerun()

    st.markdown("---")

    # Büro Gross section
    st.markdown("#### 🏢 Büro Gross")
    gross_cols = st.columns(5)

    for i in range(1, 6):
        with gross_cols[i - 1]:
            st.markdown(f"**Position {i}**")
            current_name = get_desk_name("gross", i)
            new_name = st.text_input(
                "Desk Name",
                value=current_name if current_name != f"Desk {i}" else "",
                max_chars=20,
                key=f"gross_{i}_name",
                placeholder="Enter name..."
            )
            if st.button("💾", key=f"save_gross_{i}", use_container_width=True):
                set_desk_name("gross", i, new_name)
                st.success(f"Updated Gross Desk {i}!")
                st.rerun()

    st.markdown("---")

    # Management actions
    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("🔄 Reset All Names", key="dialog_reset_desk_names", use_container_width=True):
            st.session_state.desk_names = {}
            save_data()
            st.success("All desk names reset to default!")
            st.rerun()

    with col2:
        if st.button("💾 Save All Changes", key="dialog_save_desk_names", use_container_width=True):
            save_data()
            st.success("All changes saved!")
            st.rerun()

    with col3:
        if st.button("✖ Close", key="dialog_close_desk_names", use_container_width=True):
            st.rerun()

@st.dialog("Team News Settings")
def settings_dialog():
    """Dialog for managing team news settings"""
    st.markdown("### 📢 Team News Settings")
    st.markdown("Configure the team news message displayed on the main page")

    # Current news display
    if st.session_state.team_news:
        st.markdown("**Current News:**")
        st.info(st.session_state.team_news)
    else:
        st.info("No team news currently set")

    # Edit news
    new_news = st.text_area(
        "Team News Message",
        value=st.session_state.team_news,
        height=100,
        max_chars=200,
        help="Maximum 200 characters"
    )

    # Action buttons
    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("💾 Save News", key="dialog_save_news", use_container_width=True):
            st.session_state.team_news = new_news
            save_data()
            st.success("Team news updated!")
            st.rerun()

    with col2:
        if st.button("🗑️ Clear News", key="dialog_clear_news", use_container_width=True):
            st.session_state.team_news = ""
            save_data()
            st.success("Team news cleared!")
            st.rerun()

    with col3:
        if st.button("✖ Close", key="dialog_close_settings", use_container_width=True):
            st.rerun()

def render_desk(date, room, desk_num):
    """Render individual desk component with booking status and controls"""
    booking = get_desk_status(date, room, desk_num)
    desk_key = f"{room}_{desk_num}_{format_date_key(date)}"
    desk_display_name = get_desk_name(room, desk_num)

    # Determine desk status and display properties
    if booking:
        user_id = booking.get('user_id')

        # Handle archived bookings (deleted users)
        if user_id == 'DELETED_USER':
            username = booking.get('archived_username', 'Deleted User')
            username_display = f"{username} 📋"  # Archive indicator
        else:
            user_data = st.session_state.users.get(user_id, {})
            username = user_data.get('username', 'Unknown User')
            username_display = username

        booking_type = booking.get('booking_type', 'full_day')

        # Determine desk styling based on booking type
        if booking_type == 'full_day':
            desk_class = "desk-booked"
            status_text = username_display
        elif booking_type == 'half_am':
            desk_class = "desk-half-am"
            status_text = f"{username_display} (AM)"
        elif booking_type == 'half_pm':
            desk_class = "desk-half-pm"
            status_text = f"{username_display} (PM)"
        elif booking_type == 'maybe':
            desk_class = "desk-maybe"
            status_text = f"{username_display} (?)"
    else:
        # Free desk styling
        desk_class = "desk-free"
        status_text = 'Free'

    # Debug mode: show file system information
    if st.session_state.debug_mode:
        in_use_exists = os.path.exists("media/images/in_use.png")
        not_used_exists = os.path.exists("media/images/not_used.png")

        st.error(f"🐛 DEBUG - Desk {desk_display_name}:")
        st.error(f"🐛 in_use.png exists: {in_use_exists}")
        st.error(f"🐛 not_used.png exists: {not_used_exists}")

        try:
            import glob
            all_images = glob.glob("media/images/*")
            st.error(f"🐛 All files in media/images/: {all_images}")
        except Exception as e:
            st.error(f"🐛 Could not list files: {e}")

    # Determine icon for embedded display
    if booking:
        icon_path = "media/images/in_use.png" if os.path.exists("media/images/in_use.png") else None
        fallback_emoji = "🔴"
    else:
        icon_path = "media/images/not_used.png" if os.path.exists("media/images/not_used.png") else None
        fallback_emoji = "🟢"

    # Create icon HTML
    if icon_path:
        try:
            with open(icon_path, 'rb') as f:
                import base64
                icon_base64 = base64.b64encode(f.read()).decode()
            icon_html = f'<img src="data:image/png;base64,{icon_base64}" class="desk-status-icon-overlay">'
        except:
            icon_html = f'<span class="desk-status-icon-overlay">{fallback_emoji}</span>'
    else:
        icon_html = f'<span class="desk-status-icon-overlay">{fallback_emoji}</span>'

    # Render desk container with embedded icon
    st.markdown(f'''
    <div class="desk-container {desk_class}">
        <div class="desk-header">
            <span class="desk-number">{desk_display_name}</span>
        </div>
        <div class="desk-status">{status_text}</div>
        {icon_html}
    </div>
    ''', unsafe_allow_html=True)

    # Render action buttons based on desk status
    if booking:
        if user_id == 'DELETED_USER':
            # Archived booking: show clear archive option
            if st.button("Clear Archive", key=f"clear_{desk_key}",
                        help=f"Remove archived booking for {desk_display_name}"):
                st.session_state[f'confirm_clear_{desk_key}'] = True

            # Confirmation dialog for clearing archive
            if st.session_state.get(f'confirm_clear_{desk_key}', False):
                st.warning(f"Clear archived booking for {desk_display_name}?")

                # Simple buttons without columns
                if st.button("No", key=f"no_clear_{desk_key}"):
                    st.session_state[f'confirm_clear_{desk_key}'] = False
                    st.rerun()
                if st.button("Yes", key=f"yes_clear_{desk_key}"):
                    remove_booking(date, room, desk_num)
                    st.session_state[f'confirm_clear_{desk_key}'] = False
                    st.rerun()
        else:
            # Active booking: show cancel option
            if st.button("Cancel", key=f"cancel_{desk_key}",
                         help=f"Cancel booking for {desk_display_name}"):
                st.session_state[f'confirm_remove_{desk_key}'] = True

            # Confirmation dialog for removing booking
            if st.session_state.get(f'confirm_remove_{desk_key}', False):
                st.warning(f"Cancel booking for {desk_display_name}?")

                # Simple buttons without columns
                if st.button("❌ No", key=f"no_{desk_key}"):
                    st.session_state[f'confirm_remove_{desk_key}'] = False
                    st.rerun()
                if st.button("✅ Yes", key=f"yes_{desk_key}"):
                    remove_booking(date, room, desk_num)
                    st.session_state[f'confirm_remove_{desk_key}'] = False
                    st.rerun()
    else:
        # Free desk: show booking option
        if st.button("Book", key=f"book_{desk_key}",
                    help=f"Book {desk_display_name}"):
            st.session_state.booking_desk = (date, room, desk_num)
            st.rerun()

# Load data on startup
load_data()

# ============================================================================
# 9. MAIN APPLICATION RENDERING
# ============================================================================

# ============================================================================
# LOADING SCREEN FUNCTIONALITY
# ============================================================================

def show_loading_screen():
    """Display loading screen with logo and title"""
    logo_base64 = get_logo_base64()

    loading_html = f"""
    <div style="
        position: fixed;
        top: 0;
        left: 0;
        width: 100vw;
        height: 100vh;
        background: linear-gradient(135deg, #5a5a5a, #3a3a3a);
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        z-index: 9999;
        animation: fadeOut 1s ease-out 2s forwards;
    ">
        <div style="
            text-align: center;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
        ">
            {'<img src="data:image/png;base64,' + logo_base64 + '" style="width: 150px; height: 150px; margin-bottom: 2rem; animation: pulse 2s infinite;">' if logo_base64 else ''}
            <h1 style="
                font-size: 3rem;
                background: linear-gradient(135deg, #4c80c1, #66b446);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                font-weight: 900;
                letter-spacing: 2px;
                margin: 0 0 2rem 0;
                text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
                animation: slideIn 1s ease-out;
                text-align: center;
            ">BIIS Desk Booking System</h1>
            <div style="
                width: 60px;
                height: 60px;
                border: 4px solid #66b446;
                border-top: 4px solid transparent;
                border-radius: 50%;
                animation: spin 1s linear infinite;
                margin: 0 auto;
                display: block;
            "></div>
        </div>
    </div>

    <style>
        @keyframes fadeOut {{
            to {{ opacity: 0; pointer-events: none; }}
        }}
        @keyframes pulse {{
            0%, 100% {{ transform: scale(1); }}
            50% {{ transform: scale(1.1); }}
        }}
        @keyframes slideIn {{
            from {{ transform: translateY(50px); opacity: 0; }}
            to {{ transform: translateY(0); opacity: 1; }}
        }}
        @keyframes spin {{
            0% {{ transform: rotate(0deg); }}
            100% {{ transform: rotate(360deg); }}
        }}
    </style>
    """

    st.markdown(loading_html, unsafe_allow_html=True)


# Show loading screen only on first load
if 'app_loaded' not in st.session_state:
    show_loading_screen()
    st.session_state.app_loaded = True

# Check for modal triggers and display dialogs
if st.session_state.get('show_add_user', False):
    st.session_state.show_add_user = False
    add_user_dialog()

if st.session_state.get('show_manage_users', False):
    st.session_state.show_manage_users = False
    # Import and call manage users dialog from sidebar module
    from sidebar_settings import manage_users_dialog
    manage_users_dialog()

if st.session_state.get('show_all_users', False):
    st.session_state.show_all_users = False
    # Import and call all users dialog from sidebar module
    from sidebar_settings import all_users_dialog
    all_users_dialog()

if st.session_state.get('show_holidays', False):
    st.session_state.show_holidays = False
    from sidebar_settings import holidays_dialog
    holidays_dialog()

# WORKING: Template management dialog trigger with proper state handling
if st.session_state.get('show_template_management', False):
    st.session_state.show_template_management = False
    # WORKING FIX: Always reset to main view when opening dialog
    st.session_state.template_dialog_fresh_start = True
    from template_management import show_template_dialog
    show_template_dialog()

if st.session_state.get('booking_desk'):
    date, room, desk_num = st.session_state.booking_desk
    st.session_state.booking_desk = None
    book_desk_dialog(date, room, desk_num)

if st.session_state.get('show_settings', False):
    st.session_state.show_settings = False
    settings_dialog()

if st.session_state.get('show_desk_naming', False):
    st.session_state.show_desk_naming = False
    desk_naming_dialog()

# Room blocker dialog trigger
if st.session_state.get('show_room_blocker', False):
    st.session_state.show_room_blocker = False
    if st.session_state.blocking_room:
        date, room = st.session_state.blocking_room
        st.session_state.blocking_room = None
        block_room_dialog(date, room)

# Create sidebar using modular approach
create_sidebar()

# Header with logo and title - OPTIMIZED
header_container = st.container()
with header_container:
    col1, col2, col3 = st.columns([2, 6, 2])  # Center column for content

    with col2:
        # Get cached logo
        logo_base64 = get_logo_base64()

        if logo_base64:
            st.markdown(f'''
            <div class="header-container">
                <div class="logo-container">
                    <img src="data:image/png;base64,{logo_base64}" width="90" height="90">
                </div>
                <h1 class="main-title">BIIS Desk Booking System</h1>
            </div>
            ''', unsafe_allow_html=True)
        else:
            # No logo file found
            st.markdown('''
            <div class="header-container">
                <h1 class="main-title">BIIS Desk Booking System</h1>
            </div>
            ''', unsafe_allow_html=True)

# Team news section
if st.session_state.team_news:
    st.markdown(f'''
    <div class="team-news-container">
        <div class="team-news-header">📢 TEAM NEWS</div>
        <div class="team-news-content">{st.session_state.team_news}</div>
    </div>
    ''', unsafe_allow_html=True)

st.markdown("---")

# Week navigation controls
# Smart week switching for Friday afternoon
today = datetime.now()
if today.weekday() == 4 and today.hour >= 14:  # Friday after 2pm
    current_monday = today - timedelta(days=today.weekday())
    if st.session_state.current_week_start == current_monday.date():
        st.session_state.current_week_start = (today + timedelta(days=3)).date()
        st.session_state.current_tab = 0

# Week navigation buttons
col1, col2, col3 = st.columns([1, 2, 1])

with col1:
    if st.button("← Previous Week", use_container_width=True):
        st.session_state.current_week_start -= timedelta(days=7)
        st.session_state.current_tab = 0
        st.rerun()

with col2:
    week_dates = get_week_dates(st.session_state.current_week_start)
    week_end = week_dates[-1]

    # Determine if viewing current week
    today = datetime.now().date()
    current_monday = today - timedelta(days=today.weekday())

    # Handle Friday afternoon / weekend logic
    if (today.weekday() == 4 and datetime.now().hour >= 14) or today.weekday() >= 5:
        days_until_monday = (7 - today.weekday()) % 7
        if days_until_monday == 0:
            days_until_monday = 7
        next_monday = today + timedelta(days=days_until_monday)
        effective_current_week = next_monday
        is_current_week = st.session_state.current_week_start == next_monday
    else:
        effective_current_week = current_monday
        is_current_week = st.session_state.current_week_start == current_monday

    # Display current week range (Swiss format)
    week_display = f"{st.session_state.current_week_start.strftime('%d.%m')} - {week_end.strftime('%d.%m.%Y')}"
    st.markdown(f"<h3 style='text-align: center;'>{week_display}</h3>", unsafe_allow_html=True)

    # Return to current week button
    if not is_current_week:
        st.markdown('<div style="display: flex; justify-content: center; margin-top: 10px;">', unsafe_allow_html=True)
        if st.button("↩ Return to Current Week", key="return_current", use_container_width=False):
            st.session_state.current_week_start = effective_current_week
            if today.weekday() < 5:
                st.session_state.current_tab = today.weekday()
            else:
                st.session_state.current_tab = 0
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

with col3:
    if st.button("Next Week →", use_container_width=True):
        st.session_state.current_week_start += timedelta(days=7)
        st.session_state.current_tab = 0
        st.rerun()

# Office layout rendering
week_dates = get_week_dates(st.session_state.current_week_start)
weekdays = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']

# Find today's tab for highlighting
today = datetime.now().date()
today_tab_index = None
for i, date in enumerate(week_dates):
    if date == today:
        today_tab_index = i
        break

# Create day tabs with Swiss date formatting
tab_container = st.container()
with tab_container:
    st.markdown('<div class="centered-tabs">', unsafe_allow_html=True)

    # Generate tab names with today indicator and holiday icons
    tab_names = []
    for i, (day, date) in enumerate(zip(weekdays, week_dates)):
        date_key = format_date_key(date)
        is_holiday = date_key in st.session_state.holidays

        if date == today:
            tab_name = f"📍 {day[:3]} {date.strftime('%d.%m')}"
        else:
            tab_name = f"{day[:3]} {date.strftime('%d.%m')}"

        if is_holiday:
            tab_name += " 🎉"

        tab_names.append(tab_name)

    # Initialize current tab - FIXED: Auto-land on today's tab
    if st.session_state.current_tab is None:
        if today_tab_index is not None:
            st.session_state.current_tab = today_tab_index
        else:
            st.session_state.current_tab = 0

    tabs = st.tabs(tab_names)
    st.markdown('</div>', unsafe_allow_html=True)

# Render each day's office layout
for tab_idx, (tab, date, weekday) in enumerate(zip(tabs, week_dates, weekdays)):
    with tab:
        is_today = date == today
        date_key = format_date_key(date)
        is_holiday = date_key in st.session_state.holidays

        # Create header row with date on left and user selection on right
        header_col1, header_col2, header_col3 = st.columns([2, 3, 2])

        with header_col1:
            # Day header with holiday indication
            if is_today:
                header_text = f"### 📍 TODAY - {weekday}, {date.strftime('%d. %B %Y')}"
            else:
                header_text = f"### {weekday}, {date.strftime('%d. %B %Y')}"

            if is_holiday:
                header_text += " 🎉"
                st.markdown(header_text)
                st.warning("⚠️ **Caution: This is a holiday**")
            else:
                st.markdown(header_text)

        with header_col3:
            # ============================================================================
            # USER SELECTION - SIMPLE AND CLEAN
            # ============================================================================
            if st.session_state.users:
                # Move everything up
                st.markdown('<div style="margin-top: -2rem;">', unsafe_allow_html=True)

                # Simple title with icon - BIGGER and WHITE icon
                user_icon_path = "media/images/user.png"
                if os.path.exists(user_icon_path):
                    try:
                        with open(user_icon_path, 'rb') as f:
                            import base64
                            user_icon_base64 = base64.b64encode(f.read()).decode()
                        st.markdown(f'''
                        <p style="text-align: center; margin: 0 0 0.3rem 0; font-size: 0.85rem; color: #4c80c1; font-weight: 700;">
                            <img src="data:image/png;base64,{user_icon_base64}" 
                                 style="width: 16px; height: 16px; vertical-align: middle; margin-right: 3px; filter: brightness(0) invert(1);">
                            Select User
                        </p>
                        ''', unsafe_allow_html=True)
                    except:
                        st.markdown('<p style="text-align: center; margin: 0 0 0.3rem 0; font-size: 0.85rem; color: #4c80c1; font-weight: 700;">👤 Select User</p>', unsafe_allow_html=True)
                else:
                    st.markdown('<p style="text-align: center; margin: 0 0 0.3rem 0; font-size: 0.85rem; color: #4c80c1; font-weight: 700;">👤 Select User</p>', unsafe_allow_html=True)

                # Add CSS to make dropdown narrower
                st.markdown('''
                <style>
                /* Make this specific dropdown narrower */
                div[data-testid="column"]:nth-of-type(3) .stSelectbox > div > div {
                    max-width: 120px !important;
                    margin: 0 auto !important;
                }
                </style>
                ''', unsafe_allow_html=True)

                # User options for dropdown
                user_options = {"": "Choose..."} | {
                    data['username']: user_id
                    for user_id, data in st.session_state.users.items()
                }

                # Get current selection for persistence
                current_selection = ""
                if st.session_state.get('selected_user_for_session'):
                    user_data = st.session_state.users.get(st.session_state.selected_user_for_session, {})
                    current_selection = user_data.get('username', '')

                # Simple dropdown WITHOUT on_change to prevent rerun
                selected_username = st.selectbox(
                    "User Selection",
                    options=list(user_options.keys()),
                    index=list(user_options.keys()).index(current_selection) if current_selection in user_options else 0,
                    key=f"user_dropdown_{tab_idx}",
                    label_visibility="collapsed",
                    help="Select your user for this session"
                )

                # Update session state directly without callback
                if selected_username and selected_username != "":
                    st.session_state.selected_user_for_session = user_options[selected_username]
                else:
                    st.session_state.selected_user_for_session = None

                st.markdown('</div>', unsafe_allow_html=True)

        # Office layout rendering
        room_col1, spacer, room_col2 = st.columns([5, 1, 9])

        with room_col1:
            # Büro Klein container
            klein_container = st.container()
            with klein_container:
                # Just the room title - NO BLOCK BUTTON
                st.markdown('<div class="room-title klein-title">Büro Klein</div>', unsafe_allow_html=True)

                # Show room block message if exists
                klein_block_message = get_room_block_message(date, "klein")
                if klein_block_message:
                    st.markdown(f'<div class="room-block-message">{klein_block_message}</div>', unsafe_allow_html=True)

                desk_col1, desk_col2 = st.columns(2)
                with desk_col1:
                    render_desk(date, "klein", 1)
                with desk_col2:
                    render_desk(date, "klein", 2)

        with room_col2:
            # Büro Gross container
            gross_container = st.container()
            with gross_container:
                # Just the room title - NO BLOCK BUTTON
                st.markdown('<div class="room-title gross-title">Büro Gross</div>', unsafe_allow_html=True)

                # Show room block message if exists
                gross_block_message = get_room_block_message(date, "gross")
                if gross_block_message:
                    st.markdown(f'<div class="room-block-message">{gross_block_message}</div>', unsafe_allow_html=True)

                desk_cols = st.columns(5)
                for i, col in enumerate(desk_cols):
                    with col:
                        render_desk(date, "gross", i + 1)

        # Daily bookings summary
        st.markdown("---")
        daily_bookings = [booking for key, booking in st.session_state.bookings.items()
                          if booking['date'] == format_date_key(date) and booking.get('entry_type') == 'desk_booking']

        if daily_bookings:
            st.markdown("**📋 Today's Bookings:**")
            for booking in daily_bookings:
                user_id = booking.get('user_id')

                # Handle archived vs active bookings
                if user_id == 'DELETED_USER':
                    username = booking.get('archived_username', 'Deleted User')
                    user_color = '#666666'
                    username_display = f"{username} 📋"
                else:
                    user_data = st.session_state.users.get(user_id, {})
                    username = user_data.get('username', 'Unknown')
                    user_color = user_data.get('color', '#666666')
                    username_display = username

                # Format booking display
                room_name = "Büro Klein" if booking['room'] == 'klein' else "Büro Gross"
                desk_display_name = get_desk_name(booking['room'], booking['desk_num'])
                booking_type_display = {
                    'full_day': 'Full Day',
                    'half_am': 'Morning (AM)',
                    'half_pm': 'Afternoon (PM)',
                    'maybe': 'Maybe'
                }.get(booking['booking_type'], booking['booking_type'])

                # Render booking entry
                st.markdown(
                    f'<div style="display: inline-flex; align-items: center; margin: 5px 0;">'
                    f'<div style="width: 20px; height: 20px; background-color: {user_color}; '
                    f'border-radius: 50%; margin-right: 10px;"></div>'
                    f'<span>{username_display} - {room_name} {desk_display_name} ({booking_type_display})</span>'
                    f'</div>',
                    unsafe_allow_html=True)
        else:
            st.info("No bookings for this day yet.")

# ============================================================================
# 10. FOOTER
# ============================================================================

st.markdown("---")
st.markdown('''
<div class="footer">
    <p>Built with ❤️ by <strong>Mathias Bäumli</strong> for the needs of the <strong>Testex Group BIIS Team</strong></p>
    <p class="footer-subtitle">© 2024 - Making office life easier, one desk at a time</p>
</div>
''', unsafe_allow_html=True)