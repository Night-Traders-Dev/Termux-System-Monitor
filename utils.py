# utils.py - Enhanced version with sparkline support
import shutil
import time
from collections import deque

def get_terminal_size():
    """Get current terminal dimensions."""
    try:
        size = shutil.get_terminal_size()
        return size.columns, size.lines
    except:
        return 80, 24

def truncate_text(text, max_len):
    """Truncate text with ellipsis if too long."""
    if len(text) <= max_len:
        return text
    if max_len < 3:
        return text[:max_len]
    return text[:max_len-3] + "..."

def create_bar(percent, width=20, filled_char="█", empty_char="░"):
    """Create a dynamic progress bar."""
    filled = int(percent / 100 * width)
    filled = max(0, min(width, filled))  # Clamp to valid range
    return filled_char * filled + empty_char * (width - filled)

def format_bytes(bytes_val):
    """Format bytes to human readable format."""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes_val < 1024.0:
            return f"{bytes_val:.1f} {unit}"
        bytes_val /= 1024.0
    return f"{bytes_val:.1f} PB"

def get_color_for_percent(percent, low=40, high=80):
    """Get color based on percentage thresholds."""
    if percent < low:
        return "green"
    elif percent < high:
        return "yellow"
    else:
        return "red"

def format_sparkline(data_points, chars="▁▂▃▄▅▆▇█"):
    """
    Create a sparkline from a list of data points.
    
    Args:
        data_points: List of numeric values
        chars: Characters to use for sparkline (lowest to highest)
    
    Returns:
        String representation of sparkline
    """
    if not data_points or len(data_points) == 0:
        return ""
    
    # Handle all zeros
    if all(x == 0 for x in data_points):
        return chars[0] * len(data_points)
    
    min_val = min(data_points)
    max_val = max(data_points)
    
    # Avoid division by zero
    if max_val == min_val:
        return chars[len(chars)//2] * len(data_points)
    
    # Normalize and map to character range
    sparkline = ""
    for point in data_points:
        normalized = (point - min_val) / (max_val - min_val)
        char_idx = int(normalized * (len(chars) - 1))
        sparkline += chars[char_idx]
    
    return sparkline

# Global state for various calculations
_state = {
    "net": {"rx": 0, "tx": 0, "time": time.time(), "rx_s": 0, "tx_s": 0},
    "cpu": {},
    "disk_io": {"read": 0, "write": 0, "time": time.time()},
    "history": {
        # Store recent history for sparklines (last 10 data points)
        "memory": deque(maxlen=10),
        "cpu0": deque(maxlen=10),
        "cpu1": deque(maxlen=10),
        "cpu2": deque(maxlen=10),
        "cpu3": deque(maxlen=10),
        "cpu4": deque(maxlen=10),
        "cpu5": deque(maxlen=10),
        "cpu6": deque(maxlen=10),
        "cpu7": deque(maxlen=10),
    }
}

def get_state():
    """Get global state object."""
    return _state

def update_history(key, value):
    """Update historical data for sparklines."""
    history = _state.get("history", {})
    if key in history:
        history[key].append(value)
    else:
        history[key] = deque([value], maxlen=10)
