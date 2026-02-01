# ui.py - Enhanced version with footer and omission tracking + CPU usage source suffix

from rich.table import Table
from rich.panel import Panel
from rich.layout import Layout
from rich.text import Text
from rich.align import Align

from utils.utils import (
    get_terminal_size,
    truncate_text,
    create_bar,
    get_color_for_percent,
    format_sparkline,
)

from utils.system_info import get_sys_info, get_load_info, get_top_processes

from hardware.hardware import (
    get_cpu_data,
    get_temps,
    get_battery,
    get_mem,
    get_storage,
    get_disk_io,
)

from utils.network import get_net_stats

from ui.panels.cpu import create_cpu_panel
from ui.panels.footer import create_footer_panel
from ui.panels.header import create_header_panel
from ui.panels.network import create_network_panel
from ui.panels.processes import create_processes_panel
from ui.panels.resources import create_resources_panel
from ui.panels.sensors import create_sensors_panel

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



def generate_layout(history=None):
    """Generate adaptive layout based on terminal size."""
    reset_omissions()

    width, height = get_terminal_size()
    mode = determine_layout_mode(width, height)
    info = get_sys_info()

    layout = Layout()

    header_size = 6 if mode == "minimal" else 5
    footer_size = 3

    if mode == "minimal":
        layout.split_column(
            Layout(name="header", size=header_size),
            Layout(name="cpu", size=8),
            Layout(name="resources", size=7),
            Layout(name="sensors", size=6),
            Layout(name="network", size=5),
            Layout(name="footer", size=footer_size),
        )
        layout["header"].update(create_header_panel(info, width, mode))
        layout["cpu"].update(create_cpu_panel(width, mode, history))
        layout["resources"].update(create_resources_panel(width, mode, history))
        layout["sensors"].update(create_sensors_panel(width, mode))
        layout["network"].update(create_network_panel(width, mode))
        layout["footer"].update(create_footer_panel(width, height, mode))
        return layout

    if mode == "compact":
        layout.split_column(
            Layout(name="header", size=header_size),
            Layout(name="cpu", ratio=3),
            Layout(name="resources", ratio=2),
            Layout(name="sensors", ratio=2),
            Layout(name="processes", ratio=2),
            Layout(name="network", size=5),
            Layout(name="footer", size=footer_size),
        )
        layout["header"].update(create_header_panel(info, width, mode))
        layout["cpu"].update(create_cpu_panel(width, mode, history))
        layout["resources"].update(create_resources_panel(width, mode, history))
        layout["sensors"].update(create_sensors_panel(width, mode))
        layout["network"].update(create_network_panel(width, mode))
        proc_panel = create_processes_panel(width, mode)
        if proc_panel:
            layout["processes"].update(proc_panel)
        layout["footer"].update(create_footer_panel(width, height, mode))
        return layout

    # full
    layout.split_column(
        Layout(name="header", size=header_size),
        Layout(name="body", ratio=1),
        Layout(name="network", size=6),
        Layout(name="footer", size=footer_size),
    )
    layout["body"].split_row(
        Layout(name="left_col", ratio=2),
        Layout(name="right_col", ratio=1),
    )
    layout["body"]["left_col"].split_column(
        Layout(name="cpu", ratio=2),
        Layout(name="processes", ratio=2),
    )
    layout["body"]["right_col"].split_column(
        Layout(name="resources", ratio=1),
        Layout(name="sensors", ratio=1),
    )

    layout["header"].update(create_header_panel(info, width, mode))
    layout["body"]["left_col"]["cpu"].update(create_cpu_panel(width, mode, history))
    layout["body"]["right_col"]["resources"].update(create_resources_panel(width, mode, history))
    layout["body"]["right_col"]["sensors"].update(create_sensors_panel(width, mode))
    layout["network"].update(create_network_panel(width, mode))

    proc_panel = create_processes_panel(width, mode)
    if proc_panel:
        layout["body"]["left_col"]["processes"].update(proc_panel)

    layout["footer"].update(create_footer_panel(width, height, mode))
    return layout
