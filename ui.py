# ui.py - Enhanced version with footer and omission tracking
from rich.table import Table
from rich.panel import Panel
from rich.layout import Layout
from rich.text import Text
from rich.align import Align
from utils import (
    get_terminal_size, truncate_text, create_bar,
    get_color_for_percent, format_sparkline
)
from system_info import get_sys_info, get_load_info, get_top_processes
from hardware import (
    get_cpu_data, get_temps, get_battery,
    get_mem, get_storage, get_disk_io
)
from network import get_net_stats

# Track what information is omitted for footer display
_omissions = []

def reset_omissions():
    """Clear omission tracking for new render cycle."""
    global _omissions
    _omissions = []

def add_omission(item):
    """Track an omitted piece of information."""
    global _omissions
    if item not in _omissions:
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

def create_header_panel(info, width, mode):
    """Create adaptive header panel."""
    kernel_display = truncate_text(info['kernel'], max(15, width // 5))
    os_display = truncate_text(info['os'], max(12, width // 6))
    
    if mode == "minimal":
        header_text = Text.assemble(
            ("OS: ", "bold cyan"), (f"{os_display}\n", "white"),
            ("Kernel: ", "bold cyan"), (f"{kernel_display}\n", "white"),
            (f"{info['arch']} | Up: {info['uptime']}", "white")
        )
    elif mode == "compact":
        header_text = Text.assemble(
            ("OS: ", "bold cyan"), (f"{os_display}\n", "white"),
            ("Kernel: ", "bold cyan"), (f"{kernel_display} ", "white"),
            ("Arch: ", "bold cyan"), (f"{info['arch']}\n", "white"),
            ("Uptime: ", "bold cyan"), (f"{info['uptime']}", "white")
        )
    else:
        header_text = Text.assemble(
            ("OS: ", "bold cyan"), (f"{os_display} ", "white"),
            ("Kernel: ", "bold cyan"), (f"{kernel_display} ", "white"),
            ("Arch: ", "bold cyan"), (f"{info['arch']} ", "white"),
            ("Uptime: ", "bold cyan"), (f"{info['uptime']}", "white")
        )
    
    title = "⚙ Sys" if mode == "minimal" else "⚙ System Info"
    return Panel(header_text, title=title, border_style="bright_blue")

def create_cpu_panel(width, mode, history=None):
    """Create adaptive CPU panel with optional sparkline history."""
    cpu_table = Table(
        expand=True,
        box=None,
        show_header=(mode != "minimal"),
        header_style="bold magenta",
        padding=(0, 1)
    )
    
    # Adaptive column configuration
    if mode == "minimal":
        cpu_table.add_column("C", style="bold magenta", width=4)
        cpu_table.add_column("Usage", ratio=1)
        bar_width = max(8, width // 4)
    elif mode == "compact":
        cpu_table.add_column("Core", style="bold magenta", width=6)
        cpu_table.add_column("Usage", ratio=1)
        if history:
            cpu_table.add_column("Trend", width=10)
        bar_width = max(10, width // 4)
    else:
        cpu_table.add_column("Core", style="bold magenta", width=8)
        cpu_table.add_column("Freq", justify="right", width=10)
        cpu_table.add_column("Usage", ratio=1)
        if history:
            cpu_table.add_column("Trend", width=12)
        bar_width = max(15, min(30, width // 4))
    
    cpu_cores = get_cpu_data()
    
    # Limit cores shown in minimal mode
    cores_to_show = cpu_cores[:4] if mode == "minimal" else cpu_cores
    
    if mode == "minimal" and len(cpu_cores) > 4:
        add_omission(f"{len(cpu_cores) - 4} CPU cores")
    
    for i, c in enumerate(cores_to_show):
        color = get_color_for_percent(c['usage'])
        bar = create_bar(c['usage'], bar_width)
        
        if mode == "minimal":
            cpu_table.add_row(
                c['id'][-1],  # Just the number
                f"[{color}]{bar}[/] {c['usage']:.0f}%"
            )
        elif mode == "compact":
            row_data = [
                c['id'][-4:],
                f"[{color}]{bar}[/] {c['usage']:.0f}%"
            ]
            if history and f"cpu{i}" in history:
                sparkline = format_sparkline(history[f"cpu{i}"])
                row_data.append(sparkline)
            cpu_table.add_row(*row_data)
        else:
            freq_str = f"{c['cur']} MHz" if c['cur'] > 0 else "N/A"
            row_data = [
                c['id'],
                freq_str,
                f"[{color}]{bar}[/] {c['usage']:.1f}%"
            ]
            if history and f"cpu{i}" in history:
                sparkline = format_sparkline(history[f"cpu{i}"])
                row_data.append(sparkline)
            cpu_table.add_row(*row_data)
    
    # Add load average (skip in minimal mode)
    if mode != "minimal":
        load = get_load_info()
        if load:
            cpu_table.add_row(*[""] * (4 if history and mode != "minimal" else 3 if mode == "full" else 2))
            if mode == "full":
                cpu_table.add_row(
                    "[bold]Load[/]",
                    f"{load['load1']:.2f}",
                    f"{load['load5']:.2f} / {load['load15']:.2f}",
                    "" if history else None
                )
                cpu_table.add_row(
                    "[bold]Procs[/]",
                    f"{load['running']}",
                    f"total: {load['total']}",
                    "" if history else None
                )
            else:
                cpu_table.add_row(
                    "[bold]Load[/]",
                    f"{load['load1']:.1f} {load['load5']:.1f} {load['load15']:.1f}",
                    "" if history else None
                )
    else:
        add_omission("Load avg")
    
    title = "💻" if mode == "minimal" else "💻 CPU"
    return Panel(cpu_table, title=title, border_style="green")

def create_resources_panel(width, mode, history=None):
    """Create adaptive memory and storage panel."""
    mem = get_mem()
    storage = get_storage()
    disk_io = get_disk_io()
    
    sys_table = Table(
        expand=True,
        box=None,
        show_header=False,
        pad_edge=False,
        padding=(0, 1)
    )
    
    sys_table.add_column("Info", style="bold white")
    
    # Adaptive bar width
    bar_width = max(8, min(20, width // 5)) if mode != "minimal" else max(6, width // 6)
    
    # Memory section
    mem_bar = create_bar(mem['percent'], bar_width)
    mem_color = get_color_for_percent(mem['percent'], 60, 85)
    
    if mode == "minimal":
        sys_table.add_row(f"[bold cyan]RAM:[/] {mem['used']/1024:.1f}/{mem['total']/1024:.1f}G")
        sys_table.add_row(f"[{mem_color}]{mem_bar}[/] {mem['percent']:.0f}%")
    else:
        sys_table.add_row(f"[bold cyan]RAM:[/] {mem['used']/1024:.1f}/{mem['total']/1024:.1f} GB")
        sys_table.add_row(f"[{mem_color}]{mem_bar}[/] {mem['percent']:.1f}%")
        if history and 'memory' in history:
            sparkline = format_sparkline(history['memory'])
            sys_table.add_row(f"[dim]Trend: {sparkline}[/]")
    
    if mode == "full":
        sys_table.add_row(f"[dim]Cached: {mem['cached']/1024:.1f} GB[/]")
        # Show swap if available
        if mem.get('swap_total', 0) > 0:
            swap_percent = (mem['swap_used'] / mem['swap_total']) * 100
            sys_table.add_row(f"[dim]Swap: {mem['swap_used']/1024:.1f}/{mem['swap_total']/1024:.1f} GB ({swap_percent:.1f}%)[/]")
    else:
        if mem.get('swap_total', 0) > 0:
            add_omission("Swap memory")
    
    sys_table.add_row("")
    
    # Storage section
    stor_bar = create_bar(storage['percent'], bar_width)
    stor_color = get_color_for_percent(storage['percent'], 60, 85)
    
    if mode == "minimal":
        sys_table.add_row(f"[bold cyan]Disk:[/] {storage['used']:.1f}/{storage['total']:.1f}G")
        sys_table.add_row(f"[{stor_color}]{stor_bar}[/] {storage['percent']:.0f}%")
    else:
        sys_table.add_row(f"[bold cyan]Disk:[/] {storage['used']:.1f}/{storage['total']:.1f} GB")
        sys_table.add_row(f"[{stor_color}]{stor_bar}[/] {storage['percent']:.1f}%")
    
    # Disk I/O (only in full mode)
    if mode == "full" and disk_io:
        sys_table.add_row(f"[dim]Read: {disk_io['read_speed']:.1f} MB/s[/]")
        sys_table.add_row(f"[dim]Write: {disk_io['write_speed']:.1f} MB/s[/]")
    elif disk_io:
        add_omission("Disk I/O stats")
    
    title = "💾" if mode == "minimal" else "💾 Resources"
    return Panel(sys_table, title=title, border_style="yellow")

def create_sensors_panel(width, mode):
    """Create adaptive temperature and battery panel."""
    extra_table = Table(
        expand=True,
        box=None,
        show_header=False,
        padding=(0, 1)
    )
    
    extra_table.add_column("Sensor", style="bold white")
    
    temps = get_temps()
    temp_name_width = max(8, width // 8) if mode == "full" else max(6, width // 10)
    
    # Limit temps shown in minimal mode
    temps_to_show = temps[:2] if mode == "minimal" else temps
    
    if mode == "minimal" and len(temps) > 2:
        add_omission(f"{len(temps) - 2} temp sensors")
    
    if temps_to_show:
        for t in temps_to_show:
            color = get_color_for_percent(t['temp'], 60, 80)
            name = truncate_text(t['name'], temp_name_width)
            extra_table.add_row(f"[{color}]{name}: {t['temp']:.1f}°C[/]")
    else:
        if mode != "minimal":
            extra_table.add_row("[dim]No sensors[/]")
    
    battery = get_battery()
    if battery:
        extra_table.add_row("")
        batt_color = get_color_for_percent(100 - battery['level'], 50, 80)  # Inverted
        if mode == "minimal":
            extra_table.add_row(f"[bold cyan]Batt[/]")
            extra_table.add_row(f"[{batt_color}]{battery['level']}%[/]")
        else:
            extra_table.add_row(f"[bold cyan]Battery[/]")
            status = truncate_text(battery['status'], 10)
            extra_table.add_row(f"[{batt_color}]{battery['level']}%[/] {status}")
            if battery['temp'] > 0 and mode == "full":
                temp_color = get_color_for_percent(battery['temp'], 40, 45)
                extra_table.add_row(f"[{temp_color}]{battery['temp']:.1f}°C[/]")
            if mode == "full" and battery.get('health'):
                extra_table.add_row(f"[dim]{battery['health']}[/]")
            elif battery.get('health'):
                add_omission("Battery health")
    else:
        if mode == "full":
            extra_table.add_row("")
            extra_table.add_row("[dim]No battery[/]")
    
    title = "🌡" if mode == "minimal" else "🌡 Sensors"
    return Panel(extra_table, title=title, border_style="magenta")

def create_network_panel(width, mode):
    """Create adaptive network panel."""
    net = get_net_stats()
    
    net_table = Table(
        expand=True,
        box=None,
        show_header=(mode != "minimal"),
        header_style="bold cyan",
        padding=(0, 1)
    )
    
    if mode == "minimal":
        net_table.add_column("", style="bold", width=2)
        net_table.add_column("Tot", justify="center", width=8)
        net_table.add_column("Spd", justify="right")
    elif mode == "compact":
        net_table.add_column("Dir", style="bold", width=4)
        net_table.add_column("Total", justify="center", width=10)
        net_table.add_column("Speed", justify="right")
    else:
        net_table.add_column("Direction", style="bold", width=8)
        net_table.add_column("Total", justify="center", width=12)
        net_table.add_column("Speed", justify="right", width=15)
    
    # Speed color coding
    rx_color = get_color_for_percent(net['rx_speed'] / 10, 10, 100)
    tx_color = get_color_for_percent(net['tx_speed'] / 10, 10, 100)
    
    if mode == "minimal":
        net_table.add_row(
            "↓",
            f"{net['rx_total']:.1f}M",
            f"[{rx_color}]{net['rx_speed']:.0f}K[/]"
        )
        net_table.add_row(
            "↑",
            f"{net['tx_total']:.1f}M",
            f"[{tx_color}]{net['tx_speed']:.0f}K[/]"
        )
    elif mode == "compact":
        net_table.add_row(
            "📥",
            f"{net['rx_total']:.1f}M",
            f"[{rx_color}]{net['rx_speed']:.0f}K/s[/]"
        )
        net_table.add_row(
            "📤",
            f"{net['tx_total']:.1f}M",
            f"[{tx_color}]{net['tx_speed']:.0f}K/s[/]"
        )
    else:
        net_table.add_row(
            "📥 DOWN",
            f"{net['rx_total']:.1f} MB",
            f"[{rx_color}]{net['rx_speed']:.1f} KB/s[/]"
        )
        net_table.add_row(
            "📤 UP",
            f"{net['tx_total']:.1f} MB",
            f"[{tx_color}]{net['tx_speed']:.1f} KB/s[/]"
        )
    
    # Show active interfaces (only in full mode)
    if net['interfaces'] and mode == "full":
        net_table.add_row("", "", "")
        net_table.add_row("[bold]Interfaces[/]", "", "")
        for iface, data in list(net['interfaces'].items())[:3]:
            iface_display = truncate_text(iface, 10)
            net_table.add_row(
                f"[dim]{iface_display}[/]",
                f"{data['rx']/(1024**2):.1f} MB",
                f"{data['tx']/(1024**2):.1f} MB"
            )
        if len(net['interfaces']) > 3:
            add_omission(f"{len(net['interfaces']) - 3} network interfaces")
    elif net['interfaces']:
        add_omission("Network interfaces")
    
    title = "🌐" if mode == "minimal" else "🌐 Net" if mode == "compact" else "🌐 Network"
    return Panel(net_table, title=title, border_style="cyan")

def create_processes_panel(width, mode):
    """Create top processes panel (compact and full modes only)."""
    if mode == "minimal":
        add_omission("Top processes")
        return None
    
    procs = get_top_processes(limit=5 if mode == "compact" else 8)
    
    proc_table = Table(
        expand=True,
        box=None,
        show_header=True,
        header_style="bold red",
        padding=(0, 1)
    )
    
    if mode == "compact":
        proc_table.add_column("PID", width=7, style="dim")
        proc_table.add_column("Name", ratio=1)
        proc_table.add_column("CPU%", justify="right", width=6)
    else:
        proc_table.add_column("PID", width=8, style="dim")
        proc_table.add_column("Name", ratio=2)
        proc_table.add_column("CPU%", justify="right", width=7)
        proc_table.add_column("MEM%", justify="right", width=7)
    
    for p in procs:
        name = truncate_text(p['name'], 20 if mode == "compact" else 30)
        cpu_color = get_color_for_percent(p['cpu'], 30, 70)
        
        if mode == "compact":
            proc_table.add_row(
                str(p['pid']),
                name,
                f"[{cpu_color}]{p['cpu']:.1f}[/]"
            )
        else:
            mem_color = get_color_for_percent(p['mem'], 5, 15)
            proc_table.add_row(
                str(p['pid']),
                name,
                f"[{cpu_color}]{p['cpu']:.1f}[/]",
                f"[{mem_color}]{p['mem']:.1f}[/]"
            )
    
    title = "⚡ Top Procs" if mode == "compact" else "⚡ Top Processes"
    return Panel(proc_table, title=title, border_style="red")

def create_footer_panel(width, height, mode):
    """Create footer showing terminal size and omitted information."""
    omissions = get_omissions()
    
    # Build footer text
    size_text = f"Terminal: {width}×{height}"
    mode_text = f"Mode: {mode.upper()}"
    
    footer_parts = [
        Text(size_text, style="bold cyan"),
        Text(" │ ", style="dim"),
        Text(mode_text, style="bold yellow")
    ]
    
    if omissions:
        omit_str = ", ".join(omissions)
        if len(omit_str) > width - 50:  # Truncate if too long
            omit_str = omit_str[:width-53] + "..."
        footer_parts.extend([
            Text(" │ ", style="dim"),
            Text("Omitted: ", style="bold red"),
            Text(omit_str, style="dim red")
        ])
    else:
        footer_parts.extend([
            Text(" │ ", style="dim"),
            Text("All info displayed", style="green")
        ])
    
    footer_text = Text.assemble(*footer_parts)
    
    # Center the footer
    centered_footer = Align.center(footer_text)
    
    return Panel(
        centered_footer,
        title="",
        border_style="bright_black",
        padding=(0, 1)
    )

def generate_layout(history=None):
    """Generate adaptive layout based on terminal size."""
    reset_omissions()
    
    width, height = get_terminal_size()
    mode = determine_layout_mode(width, height)
    
    info = get_sys_info()
    
    layout = Layout()
    
    # Determine sizes based on mode
    if mode == "minimal":
        header_size = 6
        footer_size = 3
    elif mode == "compact":
        header_size = 5
        footer_size = 3
    else:
        header_size = 5
        footer_size = 3
    
    # Create layout structure based on mode
    if mode == "minimal":
        # Ultra compact: stack everything vertically
        layout.split_column(
            Layout(name="header", size=header_size),
            Layout(name="cpu", size=8),
            Layout(name="resources", size=7),
            Layout(name="sensors", size=6),
            Layout(name="network", size=5),
            Layout(name="footer", size=footer_size)
        )
    elif mode == "compact":
        # Compact: single column with processes
        layout.split_column(
            Layout(name="header", size=header_size),
            Layout(name="cpu", ratio=3),
            Layout(name="resources", ratio=2),
            Layout(name="sensors", ratio=2),
            Layout(name="processes", ratio=2),
            Layout(name="network", size=5),
            Layout(name="footer", size=footer_size)
        )
    else:
        # Full: multi-column layout
        layout.split_column(
            Layout(name="header", size=header_size),
            Layout(name="body", ratio=1),
            Layout(name="network", size=6),
            Layout(name="footer", size=footer_size)
        )
        
        layout["body"].split_row(
            Layout(name="left_col", ratio=2),
            Layout(name="right_col", ratio=1)
        )
        
        layout["body"]["left_col"].split_column(
            Layout(name="cpu", ratio=2),
            Layout(name="processes", ratio=2)
        )
        
        layout["body"]["right_col"].split_column(
            Layout(name="resources", ratio=1),
            Layout(name="sensors", ratio=1)
        )
    
    # Populate panels
    layout["header"].update(create_header_panel(info, width, mode))
    
    if mode in ["minimal", "compact"]:
        layout["cpu"].update(create_cpu_panel(width, mode, history))
        layout["resources"].update(create_resources_panel(width, mode, history))
        layout["sensors"].update(create_sensors_panel(width, mode))
        layout["network"].update(create_network_panel(width, mode))
        
        if mode == "compact":
            proc_panel = create_processes_panel(width, mode)
            if proc_panel:
                layout["processes"].update(proc_panel)
    else:
        layout["body"]["left_col"]["cpu"].update(create_cpu_panel(width, mode, history))
        layout["body"]["right_col"]["resources"].update(create_resources_panel(width, mode, history))
        layout["body"]["right_col"]["sensors"].update(create_sensors_panel(width, mode))
        layout["network"].update(create_network_panel(width, mode))
        
        proc_panel = create_processes_panel(width, mode)
        if proc_panel:
            layout["body"]["left_col"]["processes"].update(proc_panel)
    
    # Always add footer
    layout["footer"].update(create_footer_panel(width, height, mode))
    
    return layout
