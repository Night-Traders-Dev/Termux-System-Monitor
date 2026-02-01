# Track what information is omitted for footer display
_omissions = []


def reset_omissions():
    """Clear omission tracking for new render cycle."""
    global _omissions
    _omissions = []


def add_omission(item):
    """Track an omitted piece of information."""
    global _omissions
    if item and item not in _omissions:
        _omissions.append(item)


def get_omissions():
    """Get list of currently omitted information."""
    return _omissions


def determine_layout_mode(width, height):
    """Determine which layout mode to use based on terminal size."""
    if width < 60 or height < 15:
        return "minimal"  # Very compact, stack everything
    elif width < 90 or height < 20:
        return "compact"  # Single column
    else:
        return "full"  # Multi-column


def _pad_row(ncols, values):
    vals = list(values)
    if len(vals) < ncols:
        vals.extend([""] * (ncols - len(vals)))
    return vals[:ncols]