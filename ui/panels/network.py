def create_network_panel(width, mode):
    """Create adaptive network panel."""
    net = get_net_stats()

    net_table = Table(
        expand=True,
        box=None,
        show_header=(mode != "minimal"),
        header_style="bold cyan",
        padding=(0, 1),
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

    rx_color = get_color_for_percent(net["rx_speed"] / 10, 10, 100)  # KB/s scaled
    tx_color = get_color_for_percent(net["tx_speed"] / 10, 10, 100)

    if mode == "minimal":
        net_table.add_row("↓", f"{net['rx_total']:.1f}M", f"[{rx_color}]{net['rx_speed']:.0f}K[/]")
        net_table.add_row("↑", f"{net['tx_total']:.1f}M", f"[{tx_color}]{net['tx_speed']:.0f}K[/]")
    elif mode == "compact":
        net_table.add_row("📥", f"{net['rx_total']:.1f}M", f"[{rx_color}]{net['rx_speed']:.0f}K/s[/]")
        net_table.add_row("📤", f"{net['tx_total']:.1f}M", f"[{tx_color}]{net['tx_speed']:.0f}K/s[/]")
    else:
        net_table.add_row("📥 DOWN", f"{net['rx_total']:.1f} MB", f"[{rx_color}]{net['rx_speed']:.1f} KB/s[/]")
        net_table.add_row("📤 UP", f"{net['tx_total']:.1f} MB", f"[{tx_color}]{net['tx_speed']:.1f} KB/s[/]")

    interfaces = net.get("interfaces") or {}
    if interfaces and mode == "full":
        net_table.add_row("", "", "")
        net_table.add_row("[bold]Interfaces[/]", "", "")
        items = list(interfaces.items())
        for iface, data in items[:3]:
            iface_display = truncate_text(iface, 10)
            net_table.add_row(
                f"[dim]{iface_display}[/]",
                f"{data['rx']/(1024**2):.1f} MB",
                f"{data['tx']/(1024**2):.1f} MB",
            )
        if len(items) > 3:
            add_omission(f"{len(items) - 3} network interfaces")
    elif interfaces and mode != "full":
        add_omission("Network interfaces")

    title = "🌐" if mode == "minimal" else ("🌐 Net" if mode == "compact" else "🌐 Network")
    return Panel(net_table, title=title, border_style="cyan")
