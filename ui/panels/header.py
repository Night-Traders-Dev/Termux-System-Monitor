def create_header_panel(info, width, mode):
    """Create adaptive header panel."""
    kernel_display = truncate_text(info["kernel"], max(15, width // 5))
    os_display = truncate_text(info["os"], max(12, width // 6))

    if mode == "minimal":
        header_text = Text.assemble(
            ("OS: ", "bold cyan"),
            (f"{os_display}", "white"),
            ("Kernel: ", "bold cyan"),
            (f"{kernel_display}", "white"),
            (f"{info['arch']} | Up: {info['uptime']}", "white"),
        )
    elif mode == "compact":
        header_text = Text.assemble(
            ("OS: ", "bold cyan"),
            (f"{os_display}", "white"),
            ("Kernel: ", "bold cyan"),
            (f"{kernel_display} ", "white"),
            ("Arch: ", "bold cyan"),
            (f"{info['arch']}", "white"),
            ("Uptime: ", "bold cyan"),
            (f"{info['uptime']}", "white"),
        )
    else:
        header_text = Text.assemble(
            ("OS: ", "bold cyan"),
            (f"{os_display} ", "white"),
            ("Kernel: ", "bold cyan"),
            (f"{kernel_display} ", "white"),
            ("Arch: ", "bold cyan"),
            (f"{info['arch']} ", "white"),
            ("Uptime: ", "bold cyan"),
            (f"{info['uptime']}", "white"),
        )

    title = "⚙ Sys" if mode == "minimal" else "⚙ System Info"
    return Panel(header_text, title=title, border_style="bright_blue")
