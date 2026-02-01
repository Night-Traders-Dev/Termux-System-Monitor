from rich.table import Table
from rich.panel import Panel

from utils.utils import (
    create_bar,
    get_color_for_percent,
    format_sparkline,
)


from hardware.hardware import (
    get_cpu_data
)

from utils.system_info import get_load_info

from utils.ui import (
    add_omission
)   

def _pad_row(ncols, values):
    vals = list(values)
    if len(vals) < ncols:
        vals.extend([""] * (ncols - len(vals)))
    return vals[:ncols]

def create_cpu_panel(width, mode, history=None):
    """Create adaptive CPU panel with optional sparkline history."""
    cpu_table = Table(
        expand=True,
        box=None,
        show_header=(mode != "minimal"),
        header_style="bold magenta",
        padding=(0, 1),
    )

    show_trend = bool(history)

    if mode == "minimal":
        cpu_table.add_column("C", style="bold magenta", width=4)
        cpu_table.add_column("Usage", ratio=1)
        bar_width = max(8, width // 4)
        ncols = 2
    elif mode == "compact":
        cpu_table.add_column("Core", style="bold magenta", width=6)
        cpu_table.add_column("Usage", ratio=1)
        if show_trend:
            cpu_table.add_column("Trend", width=10)
        bar_width = max(10, width // 4)
        ncols = 3 if show_trend else 2
    else:
        cpu_table.add_column("Core", style="bold magenta", width=8)
        cpu_table.add_column("Freq", justify="right", width=10)
        cpu_table.add_column("Usage", ratio=1)
        if show_trend:
            cpu_table.add_column("Trend", width=12)
        bar_width = max(15, min(30, width // 4))
        ncols = 4 if show_trend else 3

    cpu_cores = get_cpu_data()

    cores_to_show = cpu_cores[:4] if mode == "minimal" else cpu_cores
    if mode == "minimal" and len(cpu_cores) > 4:
        add_omission(f"{len(cpu_cores) - 4} CPU cores")

    for i, c in enumerate(cores_to_show):
        usage = float(c.get("usage", 0.0))
        color = get_color_for_percent(usage)
        bar = create_bar(usage, bar_width)

        # "~" means proxy (freq-based), not true busy%
        src = c.get("usage_src", "")
        suffix = "~" if src == "cpufreq" else ""

        if mode == "minimal":
            cpu_table.add_row(
                c.get("id", "?")[-1:],
                f"[{color}]{bar}[/] {usage:.0f}%{suffix}",
            )
        elif mode == "compact":
            row = [
                c.get("id", "?")[-4:],
                f"[{color}]{bar}[/] {usage:.0f}%{suffix}",
            ]
            if show_trend:
                spark = format_sparkline(history.get(f"cpu{i}", [])) if history else ""
                row.append(spark)
            cpu_table.add_row(*_pad_row(ncols, row))
        else:
            freq_str = f"{c.get('cur', 0)} MHz" if c.get("cur", 0) > 0 else "N/A"
            row = [
                c.get("id", "?"),
                freq_str,
                f"[{color}]{bar}[/] {usage:.1f}%{suffix}",
            ]
            if show_trend:
                spark = format_sparkline(history.get(f"cpu{i}", [])) if history else ""
                row.append(spark)
            cpu_table.add_row(*_pad_row(ncols, row))

    # Add load average (skip in minimal mode)
    if mode != "minimal":
        load = get_load_info()
        if load:
            cpu_table.add_row(*([""] * ncols))
            if mode == "full":
                cpu_table.add_row(
                    *_pad_row(
                        ncols,
                        [
                            "[bold]Load[/]",
                            f"{load['load1']:.2f}",
                            f"{load['load5']:.2f} / {load['load15']:.2f}",
                        ],
                    )
                )
                cpu_table.add_row(
                    *_pad_row(
                        ncols,
                        [
                            "[bold]Procs[/]",
                            f"{load['running']}",
                            f"total: {load['total']}",
                        ],
                    )
                )
            else:
                cpu_table.add_row(
                    *_pad_row(
                        ncols,
                        [
                            "[bold]Load[/]",
                            f"{load['load1']:.1f} {load['load5']:.1f} {load['load15']:.1f}",
                        ],
                    )
                )
        else:
            add_omission("Load avg")

    title = "💻" if mode == "minimal" else "💻 CPU"
    return Panel(cpu_table, title=title, border_style="green")
