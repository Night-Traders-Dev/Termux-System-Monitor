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
        padding=(0, 1),
    )
    sys_table.add_column("Info", style="bold white")

    bar_width = max(8, min(20, width // 5)) if mode != "minimal" else max(6, width // 6)

    # Memory
    mem_bar = create_bar(mem["percent"], bar_width)
    mem_color = get_color_for_percent(mem["percent"], 60, 85)

    if mode == "minimal":
        sys_table.add_row(
            f"[bold cyan]RAM:[/] {mem['used']/1024:.1f}/{mem['total']/1024:.1f}G"
        )
        sys_table.add_row(f"[{mem_color}]{mem_bar}[/] {mem['percent']:.0f}%")
    else:
        sys_table.add_row(
            f"[bold cyan]RAM:[/] {mem['used']/1024:.1f}/{mem['total']/1024:.1f} GB"
        )
        sys_table.add_row(f"[{mem_color}]{mem_bar}[/] {mem['percent']:.1f}%")
        if history and "memory" in history:
            spark = format_sparkline(history["memory"])
            sys_table.add_row(f"[dim]Trend: {spark}[/]")
        if mode == "full":
            sys_table.add_row(f"[dim]Cached: {mem['cached']/1024:.1f} GB[/]")

    # Swap (show only if available, and not in minimal to save space)
    if mem.get("swap_total", 0) > 0:
        if mode != "minimal":
            swap_percent = (mem["swap_used"] / mem["swap_total"]) * 100 if mem["swap_total"] > 0 else 0
            sys_table.add_row(
                f"[dim]Swap: {mem['swap_used']/1024:.1f}/{mem['swap_total']/1024:.1f} GB ({swap_percent:.1f}%)[/]"
            )
        else:
            add_omission("Swap")

    sys_table.add_row("")

    # Storage
    stor_bar = create_bar(storage["percent"], bar_width)
    stor_color = get_color_for_percent(storage["percent"], 60, 85)

    if mode == "minimal":
        sys_table.add_row(
            f"[bold cyan]Disk:[/] {storage['used']:.1f}/{storage['total']:.1f}G"
        )
        sys_table.add_row(f"[{stor_color}]{stor_bar}[/] {storage['percent']:.0f}%")
    else:
        sys_table.add_row(
            f"[bold cyan]Disk:[/] {storage['used']:.1f}/{storage['total']:.1f} GB"
        )
        sys_table.add_row(f"[{stor_color}]{stor_bar}[/] {storage['percent']:.1f}%")

    # Disk I/O (full mode only)
    if disk_io and mode == "full":
        sys_table.add_row(f"[dim]Read: {disk_io['read_speed']:.1f} MB/s[/]")
        sys_table.add_row(f"[dim]Write: {disk_io['write_speed']:.1f} MB/s[/]")
    elif disk_io and mode != "full":
        add_omission("Disk IO stats")

    title = "💾" if mode == "minimal" else "💾 Resources"
    return Panel(sys_table, title=title, border_style="yellow")
