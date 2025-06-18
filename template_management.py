"""
BIIS Desk Booking System - Template Management Module (FIXED)
Author: [Your Name]
Date: [Date]
Description: FIXED template system with Next/Back buttons under textfield

FIXES APPLIED:
1. Back button moved under textfield instead of above
2. Next button appears when 3+ characters entered
3. Navigation buttons side-by-side (Back left, Next right)
4. Proper button coloring for navigation vs actions
5. USER PRESELECTION from session state

"""

# ============================================================================
# 1. IMPORTS & TYPE HINTS
# ============================================================================

import streamlit as st
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple

# Import shared utilities
from shared_functions import save_data_utility


# ============================================================================
# 2. TEMPLATE DATA MANAGEMENT
# ============================================================================

def get_user_templates(user_id: str) -> Dict[str, Any]:
    """Get all templates for a specific user"""
    if user_id not in st.session_state.users:
        return {}

    user_data = st.session_state.users[user_id]
    templates = user_data.get('templates', {})

    # DEBUG mode verification
    if st.session_state.get('debug_mode', False):
        st.error(f"🐛 DEBUG - Templates for {user_id}: {len(templates)} found")

    return templates


def save_user_template(user_id: str, template_name: str, schedule: Dict[str, str]) -> bool:
    """Save template with verification"""
    try:
        if user_id not in st.session_state.users:
            st.error(f"❌ User {user_id} not found!")
            return False

        # Ensure nested structure exists
        if 'templates' not in st.session_state.users[user_id]:
            st.session_state.users[user_id]['templates'] = {}

        templates = st.session_state.users[user_id]['templates']

        # Check 5-template limit
        if len(templates) >= 5 and template_name not in templates:
            st.error("❌ Maximum 5 templates per user allowed!")
            return False

        # Validate schedule
        if not schedule:
            st.error("❌ Template must have at least one weekday selected!")
            return False

        # Create template data
        template_data = {
            'name': template_name,
            'schedule': schedule,
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat(),
            'version': 1
        }

        # Update session state
        st.session_state.users[user_id]['templates'][template_name] = template_data

        # Save to disk with force reload
        success = save_data_utility(
            st.session_state.users,
            st.session_state.bookings,
            st.session_state.team_news,
            st.session_state.desk_names,
            st.session_state.holidays
        )

        # CRITICAL: Force reload data after save
        if success:
            try:
                from app import force_reload_data
                force_reload_data()
            except:
                # Fallback: clear cache
                st.cache_data.clear()

        return success

    except Exception as e:
        st.error(f"❌ Template save error: {e}")
        return False


def delete_user_template(user_id: str, template_name: str) -> bool:
    """Delete template - FORCE SAVE + CLEAR CACHE"""
    try:
        if user_id not in st.session_state.users:
            return False

        templates = st.session_state.users[user_id].get('templates', {})
        if template_name not in templates:
            return False

        # Remove from session state
        del st.session_state.users[user_id]['templates'][template_name]

        # FORCE SAVE: Write JSON immediately
        import json
        import os

        # Ensure data directory exists
        os.makedirs('data', exist_ok=True)

        # Write users.json directly
        with open('data/users.json', 'w', encoding='utf-8') as f:
            json.dump(st.session_state.users, f, ensure_ascii=False, indent=2)

        # Also write complete settings
        settings_data = {
            'team_news': st.session_state.get('team_news', ''),
            'desk_names': st.session_state.get('desk_names', {}),
            'holidays': st.session_state.get('holidays', {}),
            'updated': datetime.now().isoformat()
        }

        with open('data/settings.json', 'w', encoding='utf-8') as f:
            json.dump(settings_data, f, ensure_ascii=False, indent=2)

        # CRITICAL: Clear the data cache so templates reload immediately
        try:
            from app import force_reload_data
            force_reload_data()
        except:
            # If import fails, clear all caches
            st.cache_data.clear()

        return True

    except Exception as e:
        st.error(f"❌ Template deletion error: {e}")
        return False


# ============================================================================
# 3. TEMPLATE VALIDATION & LOGIC
# ============================================================================

def get_future_weeks(max_weeks: int = 5) -> List[Tuple[datetime, str]]:
    """Get list of future weeks"""
    weeks = []
    today = datetime.now().date()

    # Start from next Monday
    days_until_monday = (7 - today.weekday()) % 7
    if days_until_monday == 0:
        days_until_monday = 7

    next_monday = today + timedelta(days=days_until_monday)

    for i in range(max_weeks):
        week_start = next_monday + timedelta(weeks=i)
        week_end = week_start + timedelta(days=4)  # Friday

        if i == 0:
            week_label = f"Next Week ({week_start.strftime('%d.%m')} - {week_end.strftime('%d.%m')})"
        else:
            week_label = f"In {i + 1} Weeks ({week_start.strftime('%d.%m')} - {week_end.strftime('%d.%m')})"

        weeks.append((week_start, week_label))

    return weeks


def get_desk_name(room: str, desk_num: int) -> str:
    """Get custom desk name or fallback to default"""
    desk_key = f"{room}_{desk_num}"
    return st.session_state.desk_names.get(desk_key, f"Desk {desk_num}")


def check_desk_availability(date: datetime, room: str) -> List[int]:
    """Check which desks are available"""
    date_key = date.strftime('%Y-%m-%d')
    desk_count = 2 if room == "klein" else 5
    available_desks = []

    # Check if room is blocked
    room_blocker_key = f"{date_key}_{room}_ROOM_BLOCKER"
    if room_blocker_key in st.session_state.bookings:
        return []

    # Check individual desks
    for desk_num in range(1, desk_count + 1):
        booking_key = f"{date_key}_{room}_{desk_num}"
        if booking_key not in st.session_state.bookings:
            available_desks.append(desk_num)

    return available_desks


def validate_template_application(user_id: str, week_start: datetime, schedule: Dict[str, str]) -> Dict[str, Any]:
    """Validate template application"""
    validation_result = {
        'valid_days': {},
        'blocked_days': {},
        'past_days': {}
    }

    today = datetime.now().date()
    weekdays = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday']

    for i, weekday in enumerate(weekdays):
        if weekday not in schedule:
            continue

        current_date = week_start + timedelta(days=i)

        if current_date < today:
            validation_result['past_days'][weekday] = {
                'date': current_date,
                'reason': 'Past date'
            }
            continue

        # Check availability for both rooms
        day_availability = {}
        for room in ['klein', 'gross']:
            available_desks = check_desk_availability(current_date, room)
            day_availability[room] = {
                'available_desks': available_desks,
                'total_desks': 2 if room == "klein" else 5
            }

        # Check if any desks available
        has_available_desks = any(
            day_availability[room]['available_desks']
            for room in ['klein', 'gross']
        )

        if has_available_desks:
            validation_result['valid_days'][weekday] = {
                'date': current_date,
                'availability': day_availability,
                'booking_type': schedule[weekday]
            }
        else:
            validation_result['blocked_days'][weekday] = {
                'date': current_date,
                'reason': 'No available desks'
            }

    return validation_result


# ============================================================================
# 4. SESSION STATE MANAGEMENT
# ============================================================================

def initialize_template_dialog_state():
    """Initialize template dialog state with timer"""
    current_time = datetime.now()

    st.session_state.template_dialog_state = {
        'current_view': 'main',
        'selected_user_id': None,
        'selected_template_name': None,
        'last_activity': current_time.isoformat(),
        'session_active': True,
        'dialog_step': 'main',
        'save_step': 'form'
    }


def get_template_dialog_state() -> Dict[str, Any]:
    """Get current template dialog state with timer check"""
    current_time = datetime.now()

    # Check if state exists
    if 'template_dialog_state' not in st.session_state:
        initialize_template_dialog_state()
        return st.session_state.template_dialog_state

    state = st.session_state.template_dialog_state

    # Update last activity
    state['last_activity'] = current_time.isoformat()
    return state


def set_template_view(view: str, user_id: str = None, template_name: str = None):
    """Set template view with activity tracking"""
    state = get_template_dialog_state()
    state['current_view'] = view
    state['last_activity'] = datetime.now().isoformat()

    if user_id:
        state['selected_user_id'] = user_id
    if template_name:
        state['selected_template_name'] = template_name

    # Reset dialog step when changing views
    if view != 'create' and view != 'edit':
        state['save_step'] = 'form'


def reset_template_dialog_state():
    """Reset template dialog state when dialog is closed"""
    # Clear ALL template-related session state
    keys_to_clear = [
        'template_dialog_state',
        'template_just_saved',
        'saved_template_name',
        'template_dialog_fresh_start',
        'pending_template_deletes'
    ]
    for key in keys_to_clear:
        if key in st.session_state:
            del st.session_state[key]


# ============================================================================
# 5. TEMPLATE DIALOGS & UI
# ============================================================================

def template_main_view():
    """Main template management view with USER PRESELECTION"""
    st.markdown("### 📋 Template Management")
    st.markdown("Create and manage booking templates for automated scheduling")

    state = get_template_dialog_state()

    if not st.session_state.users:
        st.error("❌ No users available. Please create users first.")
        if st.button("Close", key="template_close_no_users", use_container_width=True):
            reset_template_dialog_state()
            st.rerun()
        return

    # User selection with PRESELECTION from session
    user_options = {
        f"{data['username']}": user_id
        for user_id, data in st.session_state.users.items()
    }

    # FIXED: Check for preselected user from session
    default_index = None
    if st.session_state.get('selected_user_for_session'):
        # User is preselected from main app
        preselected_user_id = st.session_state.selected_user_for_session
        if preselected_user_id in st.session_state.users:
            preselected_username = st.session_state.users[preselected_user_id]['username']
            try:
                default_index = list(user_options.keys()).index(preselected_username)
                # Also update dialog state to use preselected user
                state['selected_user_id'] = preselected_user_id
            except ValueError:
                pass
    elif state.get('selected_user_id'):
        # Use previously selected user in dialog
        current_user_id = state.get('selected_user_id')
        if current_user_id in st.session_state.users:
            username = st.session_state.users[current_user_id]['username']
            try:
                default_index = list(user_options.keys()).index(username)
            except ValueError:
                default_index = None

    selected_username = st.selectbox(
        "Select User",
        options=list(user_options.keys()),
        index=default_index,
        placeholder="Choose a user..." if default_index is None else None,
        key="template_user_select"
    )

    if not selected_username:
        st.warning("⚠️ Please select a user first to manage templates.")
        return

    selected_user_id = user_options[selected_username]
    state['selected_user_id'] = selected_user_id

    st.markdown("---")

    # CALLBACK-BASED: Navigation buttons with on_click callbacks
    st.markdown("### What do you want to do?")
    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("Create Template", key="template_create", use_container_width=True,
                     on_click=lambda: st.session_state.update({'template_dialog_state': {**get_template_dialog_state(), 'current_view': 'create'}})):
            pass

    with col2:
        if st.button("Edit Template", key="template_edit", use_container_width=True,
                     on_click=lambda: st.session_state.update({'template_dialog_state': {**get_template_dialog_state(), 'current_view': 'edit'}})):
            pass

    with col3:
        if st.button("Apply Template", key="template_apply", use_container_width=True,
                     on_click=lambda: st.session_state.update({'template_dialog_state': {**get_template_dialog_state(), 'current_view': 'apply'}})):
            pass

    # Show existing templates with CALLBACK-BASED delete pattern
    templates = get_user_templates(selected_user_id)
    if templates:
        st.markdown("---")
        st.markdown("### 📚 Existing Templates")

        # Process templates safely
        templates_copy = dict(templates)
        for template_name, template_data in templates_copy.items():
            col_info, col_actions = st.columns([3, 1])

            with col_info:
                schedule = template_data.get('schedule', {})
                active_days = list(schedule.keys())
                days_display = ', '.join([day.title() for day in active_days])
                st.markdown(f"**{template_name}**")
                st.markdown(f"*Days: {days_display}* ({len(active_days)} days)")

            with col_actions:
                # Delete with session state flag pattern + proper spacing
                delete_key = f"confirm_delete_{template_name}"

                if st.session_state.get(delete_key, False):
                    # Show confirmation with proper spacing
                    st.markdown("**⚠️ Delete?**")

                    # Properly spaced Yes/No buttons with more distance
                    confirm_col1, spacer_col, confirm_col2 = st.columns([1, 0.2, 1])

                    with confirm_col1:
                        def immediate_delete_callback(user_id, template_name):
                            """IMMEDIATE delete - no pending arrays"""
                            success = delete_user_template(user_id, template_name)
                            if success:
                                st.session_state[f'delete_success_{template_name}'] = True
                            st.session_state[f'confirm_delete_{template_name}'] = False

                        if st.button("Yes", key=f"yes_delete_{template_name}", use_container_width=True,
                                     on_click=immediate_delete_callback, args=(selected_user_id, template_name)):
                            pass

                    with confirm_col2:
                        if st.button("No", key=f"no_delete_{template_name}", use_container_width=True,
                                     on_click=lambda tn=template_name: st.session_state.update({f'confirm_delete_{tn}': False})):
                            pass
                else:
                    # Delete button with on_click callback
                    if st.button("🗑️", key=f"delete_template_{template_name}",
                                 help=f"Delete {template_name}", use_container_width=True,
                                 on_click=lambda tn=template_name: st.session_state.update({f'confirm_delete_{tn}': True})):
                        pass

    # Close button
    st.markdown("---")
    if st.button("Close", key="template_close", use_container_width=True):
        reset_template_dialog_state()
        st.rerun()


def template_create_edit_view():
    """Template creation/editing view with FIXED Next/Back buttons under textfield"""
    state = get_template_dialog_state()
    user_id = state.get('selected_user_id')
    is_editing = state['current_view'] == 'edit'
    save_step = state.get('save_step', 'form')

    if not user_id or user_id not in st.session_state.users:
        st.error("❌ Invalid user session")
        set_template_view('main')
        return

    user_data = st.session_state.users[user_id]
    username = user_data.get('username', 'Unknown User')

    st.markdown(f"### {'✏️ Edit' if is_editing else '📝 Create'} Template for {username}")

    # MULTI-STEP DIALOG: Success state
    if save_step == 'success':
        saved_template_name = st.session_state.get('saved_template_name', 'Template')

        st.success(f"🎉 SUCCESS! Template '{saved_template_name}' saved successfully!")
        st.info("💡 Your template is now available in the template list and can be applied to future weeks.")

        # Success navigation buttons
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Ok! Back to Main Menu", key="template_success_back",
                         type="primary", use_container_width=True,
                         on_click=lambda: st.session_state.update({
                             'template_dialog_state': {**get_template_dialog_state(), 'current_view': 'main', 'save_step': 'form'}
                         })):
                # Clear success state
                if 'saved_template_name' in st.session_state:
                    del st.session_state.saved_template_name

        with col2:
            if st.button("Create Another", key="template_success_another",
                         use_container_width=True,
                         on_click=lambda: st.session_state.update({
                             'template_dialog_state': {**get_template_dialog_state(), 'save_step': 'form'}
                         })):
                # Clear success state and stay in create view
                if 'saved_template_name' in st.session_state:
                    del st.session_state.saved_template_name

        return  # Don't show form when in success state

    # Template selection for editing
    template_to_edit = None
    template_name = ""

    if is_editing:
        templates = get_user_templates(user_id)
        if not templates:
            st.error("❌ No templates found for this user.")
            st.info("💡 Create templates first using 'Create Template' option.")
            return

        template_names = list(templates.keys())
        template_name = st.selectbox(
            "Select Template to Edit",
            options=template_names,
            key="template_edit_select"
        )

        if template_name:
            template_to_edit = templates[template_name]
            st.markdown("---")

    else:
        # Creating new template - FIXED: Template name input
        template_name = st.text_input(
            "Template Name",
            placeholder="e.g., 'Standard Week', 'Morning Schedule'",
            max_chars=30,
            key="template_name_input"
        )

    # FIXED: Navigation buttons under textfield - ALWAYS VISIBLE
    if not is_editing:
        col_back, col_next = st.columns(2)

        with col_back:
            if st.button("Back", key="template_back_main", use_container_width=True,
                         on_click=lambda: st.session_state.update({'template_dialog_state': {**get_template_dialog_state(), 'current_view': 'main'}})):
                return

        with col_next:
            if st.button("Next", key="template_next_step", use_container_width=True, type="primary"):
                # Validation: Check if at least 3 characters
                if not template_name or len(template_name.strip()) < 3:
                    st.error("⚠️ Please enter at least 3 characters for the template name.")
                    return
                # Continue to schedule configuration if validation passes

    # Only continue if we have a valid template name (for create) or selected template (for edit)
    if not is_editing and (not template_name or len(template_name.strip()) < 3):
        return
    elif is_editing and not template_name:
        return

    # For editing, show Back button under dropdown
    if is_editing:
        if st.button("Back", key="template_edit_back_main", use_container_width=True,
                     on_click=lambda: st.session_state.update({'template_dialog_state': {**get_template_dialog_state(), 'current_view': 'main'}})):
            return

    st.markdown("### 📅 Weekly Schedule")
    st.markdown("Select weekdays and booking types:")

    # Weekday configuration using containers
    weekdays = [
        ('monday', 'Monday'),
        ('tuesday', 'Tuesday'),
        ('wednesday', 'Wednesday'),
        ('thursday', 'Thursday'),
        ('friday', 'Friday')
    ]

    booking_options = ['Full Day', 'Morning (AM)', 'Afternoon (PM)']
    booking_values = ['full_day', 'half_am', 'half_pm']

    schedule = {}
    existing_schedule = template_to_edit['schedule'] if template_to_edit else {}

    # Use containers with visible labels
    for day_key, day_name in weekdays:
        weekday_container = st.container()
        with weekday_container:
            col_label, col_check, col_dropdown = st.columns([1, 0.5, 2])

            with col_label:
                st.markdown(f"**{day_name}**")

            with col_check:
                day_enabled = st.checkbox(
                    "Enable",
                    value=day_key in existing_schedule,
                    key=f"template_day_{day_key}",
                    label_visibility="collapsed"
                )

            with col_dropdown:
                if day_enabled:
                    existing_type = existing_schedule.get(day_key, 'full_day')
                    try:
                        default_index = booking_values.index(existing_type)
                    except ValueError:
                        default_index = 0

                    selected_type = st.selectbox(
                        f"Booking Type for {day_name}",
                        options=booking_options,
                        index=default_index,
                        key=f"template_type_{day_key}",
                        label_visibility="collapsed"
                    )

                    schedule[day_key] = booking_values[booking_options.index(selected_type)]

    if not schedule:
        st.warning("⚠️ Please select at least one weekday.")
        return

    # Preview schedule
    st.markdown("### 📋 Preview")
    for day_key, booking_type in schedule.items():
        day_name = next(name for key, name in weekdays if key == day_key)
        booking_display = next(opt for opt, val in zip(booking_options, booking_values) if val == booking_type)
        st.markdown(f"• **{day_name}**: {booking_display}")

    # Save/Close buttons (only show in form step)
    st.markdown("---")
    col1, col2 = st.columns(2)

    with col1:
        if st.button("Save Template", key="template_save", use_container_width=True):
            if save_user_template(user_id, template_name.strip(), schedule):
                state['save_step'] = 'success'
                st.session_state.saved_template_name = template_name.strip()
                st.rerun()

    with col2:
        if st.button("Close", key="template_editor_close", use_container_width=True):
            reset_template_dialog_state()
            st.rerun()


def template_apply_view():
    """Template application view with BACK BUTTON"""
    state = get_template_dialog_state()
    user_id = state.get('selected_user_id')

    if not user_id or user_id not in st.session_state.users:
        st.error("❌ Invalid user session")
        set_template_view('main')
        return

    user_data = st.session_state.users[user_id]
    username = user_data.get('username', 'Unknown User')

    st.markdown(f"### 🚀 Apply Template for {username}")

    # BACK BUTTON - Navigate back to main view
    if st.button("Back", key="template_apply_back_main", use_container_width=True,
                 on_click=lambda: st.session_state.update({'template_dialog_state': {**get_template_dialog_state(), 'current_view': 'main'}})):
        return

    # Template selection
    templates = get_user_templates(user_id)
    if not templates:
        st.error("❌ No templates found for this user.")
        st.info("💡 Create templates first using 'Create Template' option.")
        return

    template_names = list(templates.keys())
    template_name = st.selectbox(
        "Select Template",
        options=template_names,
        key="template_apply_select"
    )

    if not template_name:
        return

    template = templates[template_name]
    schedule = template['schedule']

    # Week selection
    st.markdown("### 📅 Select Week")
    future_weeks = get_future_weeks(5)

    week_options = {label: week_start for week_start, label in future_weeks}
    selected_week_label = st.selectbox(
        "Target Week",
        options=list(week_options.keys()),
        key="template_week_select"
    )

    if not selected_week_label:
        return

    selected_week_start = week_options[selected_week_label]

    # Validate template application
    validation = validate_template_application(user_id, selected_week_start, schedule)

    st.markdown("---")
    st.markdown("### 📋 Template Validation")

    # Show validation results
    if validation['past_days']:
        st.error("**Past Days (Skipped):**")
        for day, info in validation['past_days'].items():
            st.error(f"• {day.title()}: {info['reason']}")

    if validation['blocked_days']:
        st.error("**Blocked Days (No Available Desks):**")
        for day, info in validation['blocked_days'].items():
            st.error(f"• {day.title()}: {info['reason']}")

    if validation['valid_days']:
        st.success("**Available Days:**")

        # Desk selection
        desk_selections = {}

        for day, info in validation['valid_days'].items():
            st.markdown(f"#### {day.title()} ({info['date'].strftime('%d.%m.%Y')})")
            st.markdown(f"*Booking Type: {info['booking_type'].replace('_', ' ').title()}*")

            # Room options
            room_options = []
            room_info = {}

            for room in ['klein', 'gross']:
                room_data = info['availability'][room]
                available_desks = room_data['available_desks']

                if available_desks:
                    room_display = "Büro Klein" if room == "klein" else "Büro Gross"
                    room_options.append(room)
                    room_info[room] = {
                        'display_name': room_display,
                        'available_desks': available_desks
                    }

            if room_options:
                all_options = room_options + ["skip"]

                selected_option = st.radio(
                    f"Choose option for {day.title()}:",
                    options=all_options,
                    format_func=lambda x: room_info[x]['display_name'] if x in room_info else "⏭️ Skip this day",
                    key=f"room_select_{day}",
                    horizontal=True
                )

                if selected_option != "skip" and selected_option in room_info:
                    selected_room = selected_option
                    available_desks = room_info[selected_room]['available_desks']

                    # Desk selection
                    desk_options = []
                    for desk_num in available_desks:
                        desk_display_name = get_desk_name(selected_room, desk_num)
                        desk_options.append((desk_num, desk_display_name))

                    if len(desk_options) == 1:
                        selected_desk_num, selected_desk_name = desk_options[0]
                        st.info(f"✅ Auto-selected: {selected_desk_name}")
                    else:
                        selected_desk_option = st.radio(
                            f"Choose desk:",
                            options=desk_options,
                            format_func=lambda x: x[1],
                            key=f"desk_select_{day}_{selected_room}",
                            horizontal=True
                        )
                        selected_desk_num, selected_desk_name = selected_desk_option

                    # Store selection
                    desk_selections[f"{day}_{selected_room}_{selected_desk_num}"] = {
                        'day': day,
                        'room': selected_room,
                        'desk': selected_desk_num,
                        'date': info['date'],
                        'booking_type': info['booking_type']
                    }

            st.markdown("---")

    # Apply button
    st.markdown("---")
    col1, col2 = st.columns(2)

    with col1:
        if validation['valid_days'] and desk_selections:
            if st.button("Apply Template", key="template_apply_confirm",
                        type="primary", use_container_width=True):
                success_count = apply_template_bookings(user_id, desk_selections)

                if success_count > 0:
                    st.success(f"Template applied successfully! {success_count} booking(s) created.")
                    set_template_view('main', user_id)
                    st.rerun()
                else:
                    st.error("No bookings were created. Please check desk availability.")

    with col2:
        if st.button("Close", key="template_apply_close", use_container_width=True):
            reset_template_dialog_state()
            st.rerun()


# ============================================================================
# 6. TEMPLATE APPLICATION ENGINE
# ============================================================================

def apply_template_bookings(user_id: str, desk_selections: Dict[str, Any]) -> int:
    """Apply template bookings"""
    success_count = 0

    for selection_key, selection_data in desk_selections.items():
        try:
            date = selection_data['date']
            room = selection_data['room']
            desk_num = selection_data['desk']
            booking_type = selection_data['booking_type']

            # Create booking key
            date_key = date.strftime('%Y-%m-%d')
            booking_key = f"{date_key}_{room}_{desk_num}"

            # Check availability
            if booking_key in st.session_state.bookings:
                continue

            # Create booking data
            booking_data = {
                'user_id': user_id,
                'booking_type': booking_type,
                'created_at': datetime.now().isoformat(),
                'date': date_key,
                'room': room,
                'desk_num': desk_num,
                'entry_type': 'desk_booking',
                'created_via': 'template'
            }

            # Save booking
            st.session_state.bookings[booking_key] = booking_data
            success_count += 1

        except Exception:
            continue

    # Save to disk
    if success_count > 0:
        save_data_utility(
            st.session_state.users,
            st.session_state.bookings,
            st.session_state.team_news,
            st.session_state.desk_names,
            st.session_state.holidays
        )

        # Force reload data after booking creation
        try:
            from app import force_reload_data
            force_reload_data()
        except:
            st.cache_data.clear()

    return success_count


# ============================================================================
# 7. MAIN DIALOG FUNCTION
# ============================================================================

@st.dialog("Template Management")
def show_template_dialog():
    """Main template dialog with WORKING timer reset solution"""
    current_time = datetime.now()

    # FORCE reset every time from sidebar
    if ('template_dialog_state' not in st.session_state or
        st.session_state.get('template_dialog_fresh_start', False)):
        st.session_state.template_dialog_state = {
            'current_view': 'main',
            'selected_user_id': None,
            'selected_template_name': None,
            'last_activity': current_time.isoformat(),
            'session_active': True,
            'dialog_step': 'main',
            'save_step': 'form'
        }
        # Clear fresh start flag
        if 'template_dialog_fresh_start' in st.session_state:
            del st.session_state.template_dialog_fresh_start

    # Get current state
    state = st.session_state.template_dialog_state
    current_view = state.get('current_view', 'main')

    # Route to appropriate view
    if current_view == 'create':
        template_create_edit_view()
    elif current_view == 'edit':
        template_create_edit_view()
    elif current_view == 'apply':
        template_apply_view()
    else:
        template_main_view()


def initialize_template_management():
    """Initialize template management system"""
    if 'show_template_management' not in st.session_state:
        st.session_state.show_template_management = False