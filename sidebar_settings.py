"""
BIIS Desk Booking System - Sidebar Settings Module (GORGEOUS USER SELECTION EDITION)
Author: [Your Name]
Date: [Date]
Description: Optimized modular sidebar with GORGEOUS compact user selection at top

GORGEOUS FEATURES ADDED:
- Compact user selection at top of sidebar
- Platzsparend and stylish design
- No search field (as requested)
- Dezent but visible styling
- Maintains all existing functionality

INDEX:
1. IMPORTS & TYPE HINTS
2. USER MANAGEMENT DIALOGS
3. OPTIMIZED TOGGLE FUNCTIONS
4. GORGEOUS SIDEBAR USER SELECTION (NEW!)
5. SIDEBAR CREATION FUNCTION
"""

# ============================================================================
# 1. IMPORTS & TYPE HINTS
# ============================================================================

import streamlit as st
import os
from datetime import datetime
from typing import Dict, Any, Optional

# Import shared utilities to avoid import loops
from shared_functions import (
    get_user_colors,
    save_data_utility,
    delete_user_and_handle_bookings_utility,
    save_avatar_utility
)

# ============================================================================
# 2. USER MANAGEMENT DIALOGS
# ============================================================================

@st.dialog("Manage Users")
def manage_users_dialog():
    """Dialog for comprehensive user management with FIXED user selection"""
    st.markdown("### User Management")

    if not st.session_state.users:
        st.info("No users created yet. Use 'Add User' to create the first user.")
        if st.button("✖ Close", key="dialog_close_empty", use_container_width=True):
            st.rerun()
        return

    # Lazy import pandas only when needed
    try:
        import pandas as pd

        # Create users dataframe efficiently
        users_data = [
            {
                'Username': user_data['username'],
                'Full Name': user_data.get('full_name', ''),
                'Color': user_data['color'],
                'ID': user_id
            }
            for user_id, user_data in st.session_state.users.items()
        ]

        df = pd.DataFrame(users_data)
        st.dataframe(df, use_container_width=True, hide_index=True)

    except ImportError:
        # Fallback display without pandas
        st.markdown("**Current Users:**")
        for user_id, user_data in st.session_state.users.items():
            st.markdown(f"• **{user_data['username']}** ({user_data.get('full_name', 'N/A')}) - ID: {user_id}")

    # FIXED: User selection for editing with mandatory selection
    st.markdown("---")
    user_options = {
        f"{data['username']}": user_id
        for user_id, data in st.session_state.users.items()
    }

    # CRITICAL FIX: Empty default + placeholder
    selected_username = st.selectbox(
        "Select user to edit:",
        options=list(user_options.keys()),
        index=None,  # CRITICAL: Empty default
        placeholder="Choose a user to edit...",  # CRITICAL: Placeholder
        key="manage_user_select"
    )

    # VALIDATION: User must be selected
    if not selected_username:
        st.warning("⚠️ Please select a user to edit.")
        return

    selected_user_id = user_options[selected_username]
    user_data = st.session_state.users[selected_user_id]

    st.markdown("### Edit User")

    # Basic user information editing
    new_username = st.text_input("Username", value=user_data['username'])
    new_full_name = st.text_input("Full Name", value=user_data.get('full_name', ''))

    # Optimized color selection
    available_colors = get_user_colors()
    try:
        current_color_index = available_colors.index(user_data['color'])
    except ValueError:
        current_color_index = 0

    new_color = st.selectbox(
        "User Color",
        available_colors,
        index=current_color_index,
        format_func=lambda x: f"Color {available_colors.index(x) + 1}"
    )

    # Color preview
    st.markdown(
        f'<div style="width: 60px; height: 60px; background-color: {new_color}; '
        f'border-radius: 30px; border: 3px solid #66b446; margin: 10px 0;"></div>',
        unsafe_allow_html=True
    )

    # Avatar management
    _handle_avatar_management(user_data, selected_user_id)

    # New avatar upload
    new_avatar = st.file_uploader(
        "Upload new avatar",
        type=['png', 'jpg', 'jpeg'],
        key="edit_avatar"
    )

    # Action buttons
    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("💾 Update", key="dialog_update_user", type="primary", use_container_width=True):
            _update_user(selected_user_id, new_username, new_full_name, new_color, new_avatar, user_data)

    with col2:
        if st.button("🗑️ Delete", key="dialog_delete_user", type="secondary", use_container_width=True):
            st.session_state[f'confirm_delete_{selected_user_id}'] = True

        _handle_user_deletion(selected_user_id)

    with col3:
        if st.button("✖ Close", key="dialog_close_manage", use_container_width=True):
            st.rerun()


def _handle_avatar_management(user_data: Dict[str, Any], user_id: str) -> None:
    """Handle existing avatar display and removal"""
    avatar_path = user_data.get('avatar_path')
    if avatar_path and os.path.exists(avatar_path):
        st.image(avatar_path, width=100)
        if st.button("🗑️ Remove Avatar", key="dialog_remove_avatar", use_container_width=True):
            try:
                os.remove(avatar_path)
                user_data['avatar_path'] = None
                save_data_utility(
                    st.session_state.users,
                    st.session_state.bookings,
                    st.session_state.team_news,
                    st.session_state.desk_names,
                    st.session_state.holidays
                )
                st.success("Avatar removed!")
                st.rerun()
            except OSError as e:
                st.error(f"Failed to remove avatar: {e}")


def _update_user(user_id: str, username: str, full_name: str, color: str, new_avatar, user_data: Dict[str, Any]) -> None:
    """Update user data with validation"""
    if not username or not username.strip():
        st.error("Username cannot be empty!")
        return

    try:
        # Update user data
        user_data.update({
            'username': username.strip(),
            'full_name': full_name.strip(),
            'color': color
        })

        # Handle new avatar
        if new_avatar:
            # Remove old avatar if exists
            old_avatar = user_data.get('avatar_path')
            if old_avatar and os.path.exists(old_avatar):
                try:
                    os.remove(old_avatar)
                except OSError:
                    pass  # Continue even if old avatar can't be removed

            user_data['avatar_path'] = save_avatar_utility(new_avatar, user_id)

        save_data_utility(
            st.session_state.users,
            st.session_state.bookings,
            st.session_state.team_news,
            st.session_state.desk_names,
            st.session_state.holidays
        )
        st.success(f"User '{username}' updated!")
        st.rerun()

    except Exception as e:
        st.error(f"Failed to update user: {e}")


def _handle_user_deletion(user_id: str) -> None:
    """Handle user deletion with multi-step confirmation"""
    if not st.session_state.get(f'confirm_delete_{user_id}', False):
        return

    st.error("⚠️ This will delete the user and remove all future bookings!")
    st.warning("Past bookings will be archived with the username preserved.")

    if st.checkbox("✓ I understand - Delete this user", key="final_confirm_delete"):
        if st.button("🗑️ CONFIRM DELETE", key="final_delete_user", type="secondary"):
            _execute_user_deletion(user_id)

    if st.button("↩️ Cancel", key="cancel_delete_user"):
        st.session_state[f'confirm_delete_{user_id}'] = False
        st.rerun()


def _execute_user_deletion(user_id: str) -> None:
    """Execute the actual user deletion with booking analysis"""
    try:
        # Count affected bookings for user feedback
        today = datetime.now().date()
        future_bookings = 0
        past_bookings = 0

        for booking in st.session_state.bookings.values():
            if booking.get('user_id') == user_id:
                try:
                    booking_date = datetime.strptime(booking['date'], '%Y-%m-%d').date()
                    if booking_date >= today:
                        future_bookings += 1
                    else:
                        past_bookings += 1
                except (KeyError, ValueError):
                    continue

        # Perform deletion
        username = st.session_state.users[user_id]['username']
        success = delete_user_and_handle_bookings_utility(
            user_id, st.session_state.users, st.session_state.bookings
        )

        if success:
            save_data_utility(
                st.session_state.users,
                st.session_state.bookings,
                st.session_state.team_news,
                st.session_state.desk_names,
                st.session_state.holidays
            )
            st.success(f"✅ User '{username}' deleted successfully!")
            if future_bookings > 0:
                st.info(f"🗑️ Removed {future_bookings} future booking(s)")
            if past_bookings > 0:
                st.info(f"📋 Archived {past_bookings} past booking(s)")

            # Clear confirmation state
            st.session_state[f'confirm_delete_{user_id}'] = False
            st.balloons()
            st.rerun()
        else:
            st.error("❌ Failed to delete user")

    except Exception as e:
        st.error(f"Error during deletion: {e}")


@st.dialog("All Users")
def all_users_dialog():
    """Dialog showing simple list of all users"""
    st.markdown("### User Overview")

    if st.session_state.users:
        st.markdown("**Current Users:**")

        # Create neat list with dots
        for user_id, user_data in st.session_state.users.items():
            username = user_data.get('username', 'Unknown')
            full_name = user_data.get('full_name', username)
            st.markdown(f"• **{username}** - {full_name}")

        st.markdown(f"\n**Total:** {len(st.session_state.users)} users")
    else:
        st.info("No users created yet.")

    # Close button
    if st.button("✖ Close", key="dialog_close_all_users", use_container_width=True):
        st.rerun()


@st.dialog("Holiday Settings")
def holidays_dialog():
    """Dialog for managing company holidays"""
    st.markdown("### 🎉 Holiday Management")
    st.markdown("Manage company holidays and non-working days")

    # Initialize holidays in session state if not exists
    if 'holidays' not in st.session_state:
        st.session_state.holidays = {}

    # Add new holiday section
    st.markdown("#### Add New Holiday")
    st.markdown("**Date Format:** DD.MM.YYYY (e.g., 25.12.2025 for Christmas)")

    col1, col2 = st.columns([3, 1])
    with col1:
        holiday_input = st.text_input(
            "Holiday Date",
            placeholder="25.12.2025",
            help="Use Swiss format: DD.MM.YYYY"
        )
    with col2:
        if st.button("➕ Add", key="dialog_add_holiday", use_container_width=True):
            _add_holiday(holiday_input)

    # Show existing holidays
    _display_existing_holidays()

    # Close button
    st.markdown("---")
    if st.button("✖ Close", key="dialog_close_holidays", use_container_width=True):
        st.rerun()


def _add_holiday(holiday_input: str) -> None:
    """Add a new holiday with validation"""
    if not holiday_input:
        st.error("Please enter a date!")
        return

    try:
        holiday_date = datetime.strptime(holiday_input, "%d.%m.%Y")
        holiday_key = holiday_date.strftime("%Y-%m-%d")

        st.session_state.holidays[holiday_key] = {
            'date': holiday_key,
            'display_date': holiday_input,
            'added_date': datetime.now().isoformat()
        }

        save_data_utility(
            st.session_state.users,
            st.session_state.bookings,
            st.session_state.team_news,
            st.session_state.desk_names,
            st.session_state.holidays
        )

        st.success(f"Holiday {holiday_input} added!")
        st.rerun()

    except ValueError:
        st.error("Invalid date format! Use DD.MM.YYYY (e.g., 25.12.2025)")


def _display_existing_holidays() -> None:
    """Display existing holidays with delete functionality"""
    if not st.session_state.holidays:
        st.info("No holidays set yet.")
        return

    st.markdown("---")
    st.markdown("#### Current Holidays")

    for holiday_key, holiday_data in sorted(st.session_state.holidays.items()):
        col_date, col_delete = st.columns([4, 1])

        with col_date:
            display_date = holiday_data.get('display_date', holiday_key)
            st.markdown(f"🎉 **{display_date}**")

        with col_delete:
            if st.button("🗑️", key=f"delete_holiday_{holiday_key}",
                       help=f"Delete holiday {display_date}"):
                del st.session_state.holidays[holiday_key]
                save_data_utility(
                    st.session_state.users,
                    st.session_state.bookings,
                    st.session_state.team_news,
                    st.session_state.desk_names,
                    st.session_state.holidays
                )
                st.success(f"Holiday {display_date} deleted!")
                st.rerun()

# ============================================================================
# 3. OPTIMIZED TOGGLE FUNCTIONS
# ============================================================================

def render_toggle_switch(label: str, status_text: str, toggle_key: str, toggle_value: bool) -> bool:
    """Render an optimized toggle switch with label and status"""
    col1, col2 = st.columns([4, 1])

    with col1:
        st.markdown(f"""
        <div class="toggle-container">
            <span class="toggle-label">{label}</span>
            <span class="toggle-status">{status_text}</span>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        return st.checkbox(
            f"{label} Toggle",
            value=toggle_value,
            key=toggle_key,
            label_visibility="hidden"
        )


def handle_interface_toggles() -> None:
    """Handle interface toggle switches with optimized state management"""
    # Streamlit header toggle
    header_status = "🟢 Visible" if st.session_state.show_streamlit_header else "🔴 Hidden"
    header_toggle = render_toggle_switch(
        "Streamlit Header",
        header_status,
        "header_toggle",
        st.session_state.show_streamlit_header
    )

    # Check for state change - NO CSS reload trigger needed
    if header_toggle != st.session_state.show_streamlit_header:
        st.session_state.show_streamlit_header = header_toggle
        st.rerun()

    # Debug mode toggle
    debug_status = "🟢 Enabled" if st.session_state.debug_mode else "🔴 Disabled"
    debug_toggle = render_toggle_switch(
        "Debug Mode",
        debug_status,
        "debug_toggle",
        st.session_state.debug_mode
    )

    # Check for state change
    if debug_toggle != st.session_state.debug_mode:
        st.session_state.debug_mode = debug_toggle
        st.rerun()


def display_interface_info() -> None:
    """Display optimized informational messages about current interface state"""
    st.markdown("---")

    # Use more efficient conditional display
    if st.session_state.show_streamlit_header:
        st.info("💡 Deploy button and settings visible")
    else:
        st.info("💡 Clean interface active")

    if st.session_state.debug_mode:
        st.warning("🐛 Debug info enabled")
    else:
        st.success("✨ Clean display active")

# ============================================================================
# 4. GORGEOUS SIDEBAR USER SELECTION - FIXED WITHOUT RERUN
# ============================================================================

def render_gorgeous_sidebar_user_selection():
    """Render gorgeous compact user selection at top of sidebar"""
    if not st.session_state.users:
        return  # Don't show if no users exist

    # Create gorgeous container with integrated dropdown
    st.markdown('''
    <div class="sidebar-user-selection">
        <div class="sidebar-user-title">Quick User Select</div>
    ''', unsafe_allow_html=True)

    # Compact dropdown INSIDE the container
    user_options = {"": "👤 Choose user..."} | {
        data['username']: user_id
        for user_id, data in st.session_state.users.items()
    }

    # Get current selection for persistence
    current_selection = ""
    if st.session_state.get('selected_user_for_session'):
        user_data = st.session_state.users.get(st.session_state.selected_user_for_session, {})
        current_selection = user_data.get('username', '')

    # Dropdown WITHOUT callback to prevent rerun
    selected_username = st.selectbox(
        "sidebar_user",
        options=list(user_options.keys()),
        index=list(user_options.keys()).index(current_selection) if current_selection in user_options else 0,
        key="sidebar_user_dropdown",
        label_visibility="collapsed"
    )

    # Update session state directly - no callback, no rerun!
    if selected_username and selected_username != "" and selected_username != "👤 Choose user...":
        st.session_state.selected_user_for_session = user_options[selected_username]
    else:
        st.session_state.selected_user_for_session = None

    # Close the container
    st.markdown('</div>', unsafe_allow_html=True)


# ============================================================================
# 5. SIDEBAR CREATION FUNCTION
# ============================================================================

def create_sidebar() -> None:
    """Create the complete sidebar with gorgeous compact user selection at top"""
    with st.sidebar:
        st.markdown("## Booking System Settings")

        # GORGEOUS USER SELECTION AT TOP - Compact and platzsparend
        render_gorgeous_sidebar_user_selection()

        st.markdown("---")

        # User management section
        _render_user_management_section()

        # Room management section
        _render_room_management_section()

        # Settings section
        _render_settings_section()

        # Quick actions section
        _render_quick_actions_section()

        # Interface controls section
        _render_interface_section()


def _render_user_management_section() -> None:
    """Render user management section of sidebar"""
    st.markdown("### Users")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Add User", use_container_width=True, type="primary"):
            st.session_state.show_add_user = True
            st.rerun()

    with col2:
        if st.button("Manage", use_container_width=True):
            st.session_state.show_manage_users = True
            st.rerun()

    # Templates and All Users buttons
    col3, col4 = st.columns(2)
    with col3:
        if st.button("Templates", use_container_width=True):
            st.session_state.show_template_management = True
            st.rerun()

    with col4:
        if st.button("All Users", use_container_width=True):
            st.session_state.show_all_users = True
            st.rerun()

    # Display user count efficiently
    user_count = len(st.session_state.users)
    st.markdown(f"**Total Users:** {user_count}")


def _render_room_management_section() -> None:
    """Render room management section of sidebar"""
    st.markdown("---")
    st.markdown("### Room Management")

    # Room blocking buttons in grid
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Block Klein", use_container_width=True):
            # Get current selected date from main app
            from datetime import datetime, timedelta

            # Use current tab date or today
            today = datetime.now().date()
            if hasattr(st.session_state, 'current_week_start') and hasattr(st.session_state, 'current_tab'):
                if st.session_state.current_tab is not None:
                    selected_date = st.session_state.current_week_start + timedelta(days=st.session_state.current_tab)
                else:
                    selected_date = today
            else:
                selected_date = today

            st.session_state.show_room_blocker = True
            st.session_state.blocking_room = (selected_date, "klein")
            st.rerun()

    with col2:
        if st.button("Block Gross", use_container_width=True):
            # Get current selected date from main app
            from datetime import datetime, timedelta

            # Use current tab date or today
            today = datetime.now().date()
            if hasattr(st.session_state, 'current_week_start') and hasattr(st.session_state, 'current_tab'):
                if st.session_state.current_tab is not None:
                    selected_date = st.session_state.current_week_start + timedelta(days=st.session_state.current_tab)
                else:
                    selected_date = today
            else:
                selected_date = today

            st.session_state.show_room_blocker = True
            st.session_state.blocking_room = (selected_date, "gross")
            st.rerun()

    # Room/Desk naming buttons
    col3, col4 = st.columns(2)
    with col3:
        if st.button("Desk Names", use_container_width=True):
            st.session_state.show_desk_naming = True
            st.rerun()

    with col4:
        if st.button("Room Names", use_container_width=True):
            # Dummy button for future room naming functionality
            st.info("🚧 Room naming feature coming soon!")


def _render_settings_section() -> None:
    """Render settings section of sidebar"""
    st.markdown("---")
    st.markdown("### Settings")

    # Settings buttons - Team News and Holidays only
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Team News", use_container_width=True):
            st.session_state.show_settings = True
            st.rerun()

    with col2:
        if st.button("Holidays", use_container_width=True):
            st.session_state.show_holidays = True
            st.rerun()


def _render_quick_actions_section() -> None:
    """Render quick actions section of sidebar"""
    st.markdown("---")
    st.markdown("### Quick Actions")

    if st.button("Refresh", use_container_width=True):
        _refresh_application_data()


def _render_interface_section() -> None:
    """Render interface controls section with toggle visibility"""
    st.markdown("---")
    st.markdown("### Interface")

    # Interface visibility toggle
    show_interface_status = "🟢 Visible" if st.session_state.get('show_interface_controls', False) else "🔴 Hidden"
    show_interface_toggle = render_toggle_switch(
        "Show Controls",
        show_interface_status,
        "interface_visibility_toggle",
        st.session_state.get('show_interface_controls', False)
    )

    # Update interface visibility state
    if show_interface_toggle != st.session_state.get('show_interface_controls', False):
        st.session_state.show_interface_controls = show_interface_toggle
        st.rerun()

    # Only show interface controls if toggle is enabled
    if st.session_state.get('show_interface_controls', False):
        st.markdown("---")

        # Render toggle switches
        handle_interface_toggles()

        # Display status information
        display_interface_info()
    else:
        # Show info about hidden controls
        st.markdown("*Interface controls are hidden for safety*")


def _refresh_application_data() -> None:
    """Refresh application data with optimized loading"""
    try:
        import json

        # Load data files in batch for better performance
        data_files = {
            'users': 'data/users.json',
            'bookings': 'data/bookings.json',
            'settings': 'data/settings.json'
        }

        for data_type, filepath in data_files.items():
            if os.path.exists(filepath):
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        data = json.load(f)

                    if data_type == 'users':
                        st.session_state.users = data
                    elif data_type == 'bookings':
                        st.session_state.bookings = data
                    elif data_type == 'settings':
                        st.session_state.team_news = data.get('team_news', '')
                        st.session_state.desk_names = data.get('desk_names', {})
                        st.session_state.holidays = data.get('holidays', {})

                except (json.JSONDecodeError, KeyError) as e:
                    st.warning(f"Could not load {data_type}: {e}")

        st.success("Data refreshed!")

    except Exception as e:
        st.error(f"Error refreshing data: {e}")


# Main function to be called from app.py
def initialize_sidebar() -> None:
    """Initialize and render the sidebar - main entry point"""
    create_sidebar()