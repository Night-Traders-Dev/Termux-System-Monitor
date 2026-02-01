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
        padding=(0, 1),
    )

    if mode == "compact":
        proc_table.add_column("PID", width=7, style="dim")
        proc_table.add_column("Name", ratio=1)
        proc_table.add_column("CPU", justify="right", width=6)
        for p in procs:
            name = truncate_text(p.get("name", "?"), 20)
            cpu = float(p.get("cpu", 0.0))
            cpu_color = get_color_for_percent(cpu, 30, 70)
            proc_table.add_row(str(p.get("pid", "")), name, f"[{cpu_color}]{cpu:.1f}%[/]")
        title = "🔥 Top Procs"
    else:
        proc_table.add_column("PID", width=8, style="dim")
        proc_table.add_column("Name", ratio=2)
        proc_table.add_column("CPU", justify="right", width=7)
        proc_table.add_column("MEM", justify="right", width=7)
        for p in procs:
            name = truncate_text(p.get("name", "?"), 30)
            cpu = float(p.get("cpu", 0.0))
            mem = float(p.get("mem", 0.0))
            cpu_color = get_color_for_percent(cpu, 30, 70)
            mem_color = get_color_for_percent(mem, 5, 15)
            proc_table.add_row(
                str(p.get("pid", "")),
                name,
                f"[{cpu_color}]{cpu:.1f}%[/]",
                f"[{mem_color}]{mem:.1f}%[/]",
            )
        title = "🔥 Top Processes"

    return Panel(proc_table, title=title, border_style="red")
