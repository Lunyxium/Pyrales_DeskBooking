"""
BIIS Desk Booking System - Shared Functions (OPTIMIZED)
Author: [Your Name]
Date: [Date]
Description: Optimized shared utility functions to avoid import loops

OPTIMIZATIONS APPLIED:
- Type hints added for better performance and documentation
- Error handling consolidated
- Import optimization
- Function signature improvements
- Better memory management for image processing

INDEX:
1. IMPORTS & TYPE HINTS
2. USER UTILITY FUNCTIONS
3. DATA MANAGEMENT FUNCTIONS
4. IMAGE PROCESSING FUNCTIONS
"""

# ============================================================================
# 1. IMPORTS & TYPE HINTS
# ============================================================================

import json
import os
from datetime import datetime
from typing import Dict, Any, Optional, Union
from PIL import Image


# ============================================================================
# 2. USER UTILITY FUNCTIONS
# ============================================================================

def get_user_colors() -> list[str]:
    """
    Return list of available user colors for the booking system.

    Returns:
        List of hex color codes for user identification
    """
    return [
        "#FF6B6B", "#4ECDC4", "#45B7D1", "#96CEB4",
        "#FECA57", "#FF9FF3", "#54A0FF", "#5F27CD",
        "#00D2D3", "#FF9F43", "#C44569", "#F8B500"
    ]


# ============================================================================
# 3. DATA MANAGEMENT FUNCTIONS
# ============================================================================

def save_data_utility(
    users: Dict[str, Any],
    bookings: Dict[str, Any],
    team_news: str,
    desk_names: Dict[str, str],
    holidays: Optional[Dict[str, Any]] = None
) -> bool:
    """
    Save all application data to JSON files with optimized error handling.

    Args:
        users: User data dictionary
        bookings: Booking data dictionary
        team_news: Team news string
        desk_names: Desk name mappings
        holidays: Holiday data dictionary (optional)

    Returns:
        True if successful, False otherwise
    """
    try:
        # Ensure data directory exists
        os.makedirs('data', exist_ok=True)

        # Prepare data for batch writing
        data_files = {
            'data/users.json': users,
            'data/bookings.json': bookings,
            'data/settings.json': {
                'team_news': team_news,
                'desk_names': desk_names,
                'holidays': holidays or {},
                'updated': datetime.now().isoformat()
            }
        }

        # Write all files with consistent encoding and formatting
        for filepath, data in data_files.items():
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

        return True

    except (OSError, IOError, json.JSONEncodeError) as e:
        # Import streamlit only when needed to avoid circular imports
        try:
            import streamlit as st
            st.error(f"Error saving data: {e}")
        except ImportError:
            print(f"Error saving data: {e}")
        return False


def delete_user_and_handle_bookings_utility(
    user_id: str,
    users: Dict[str, Any],
    bookings: Dict[str, Any]
) -> bool:
    """
    Delete user and handle associated bookings with optimized processing.

    Args:
        user_id: ID of user to delete
        users: Users dictionary to modify
        bookings: Bookings dictionary to modify

    Returns:
        True if successful, False otherwise
    """
    if user_id not in users:
        return False

    try:
        user_data = users[user_id]
        username = user_data.get('username', 'Deleted User')
        today = datetime.now().date()

        # Process bookings in batch for better performance
        user_bookings = [
            (booking_key, booking)
            for booking_key, booking in bookings.items()
            if booking.get('user_id') == user_id
        ]

        # Archive or delete bookings based on date
        archive_data = {
            'user_id': 'DELETED_USER',
            'archived_username': username,
            'archived_at': datetime.now().isoformat(),
            'original_user_id': user_id
        }

        for booking_key, booking in user_bookings:
            try:
                booking_date = datetime.strptime(booking['date'], '%Y-%m-%d').date()

                if booking_date >= today:
                    # Future/today bookings: delete completely
                    del bookings[booking_key]
                else:
                    # Past bookings: archive with preserved username
                    bookings[booking_key].update(archive_data)

            except (KeyError, ValueError) as e:
                # Skip invalid booking entries
                print(f"Warning: Invalid booking entry {booking_key}: {e}")
                continue

        # Clean up avatar file if it exists
        avatar_path = user_data.get('avatar_path')
        if avatar_path and os.path.exists(avatar_path):
            try:
                os.remove(avatar_path)
            except OSError:
                # File might be in use or already deleted
                pass

        # Delete user record
        del users[user_id]
        return True

    except Exception as e:
        print(f"Error deleting user {user_id}: {e}")
        return False


# ============================================================================
# 4. IMAGE PROCESSING FUNCTIONS
# ============================================================================

def save_avatar_utility(uploaded_file, user_id: str) -> Optional[str]:
    """
    Save and resize uploaded avatar file with optimized processing.

    Args:
        uploaded_file: Streamlit uploaded file object
        user_id: User ID for filename

    Returns:
        Path to saved avatar file or None if failed
    """
    try:
        # Ensure avatar directory exists
        avatar_dir = 'media/images/avatars'
        os.makedirs(avatar_dir, exist_ok=True)

        # Validate file extension
        filename = uploaded_file.name.lower()
        if not filename.endswith(('.png', '.jpg', '.jpeg')):
            raise ValueError("Invalid file format. Only PNG, JPG, JPEG allowed.")

        # Determine file extension and create path
        file_extension = filename.split('.')[-1]
        avatar_path = f'{avatar_dir}/{user_id}.{file_extension}'

        # Save uploaded file with optimized buffer handling
        with open(avatar_path, 'wb') as f:
            f.write(uploaded_file.getbuffer())

        # Resize image efficiently
        return _resize_avatar_image(avatar_path)

    except Exception as e:
        # Import streamlit only when needed
        try:
            import streamlit as st
            st.error(f"Error saving avatar: {e}")
        except ImportError:
            print(f"Error saving avatar: {e}")
        return None


def _resize_avatar_image(image_path: str, max_size: tuple[int, int] = (200, 200)) -> Optional[str]:
    """
    Resize avatar image to maximum dimensions with optimized processing.

    Args:
        image_path: Path to image file
        max_size: Maximum (width, height) dimensions

    Returns:
        Path to resized image or None if failed
    """
    try:
        with Image.open(image_path) as img:
            # Convert to RGB if necessary (for JPEG compatibility)
            if img.mode in ('RGBA', 'LA', 'P'):
                img = img.convert('RGB')

            # Only resize if image is larger than max_size
            if img.size[0] > max_size[0] or img.size[1] > max_size[1]:
                img.thumbnail(max_size, Image.Resampling.LANCZOS)

                # Save with optimized quality
                img.save(image_path, optimize=True, quality=85)

            return image_path

    except Exception as e:
        print(f"Error resizing image {image_path}: {e}")
        # Clean up corrupted file
        try:
            os.remove(image_path)
        except OSError:
            pass
        return None