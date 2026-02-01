from rich.table import Table
from rich.panel import Panel
from utils.ui import (
    add_omission
)

from utils.utils import (
    truncate_text,
    get_color_for_percent,
)


from hardware.hardware import (
    get_temps,
    get_battery,
)


def create_sensors_panel(width, mode):
    """Create adaptive temperature and battery panel."""
    extra_table = Table(
        expand=True,
        box=None,
        show_header=False,
        padding=(0, 1),
    )
    extra_table.add_column("Sensor", style="bold white")

    temps = get_temps()
    temp_name_width = max(8, width // 8) if mode == "full" else max(6, width // 10)

    temps_to_show = temps[:2] if mode == "minimal" else temps
    if mode == "minimal" and len(temps) > 2:
        add_omission(f"{len(temps) - 2} temp sensors")

    if temps_to_show:
        for t in temps_to_show:
            color = get_color_for_percent(t["temp"], 60, 80)
            name = truncate_text(t["name"], temp_name_width)
            extra_table.add_row(f"[{color}]{name}: {t['temp']:.1f}°C[/]")
    else:
        if mode != "minimal":
            extra_table.add_row("[dim]No sensors[/]")

    battery = get_battery()
    if battery:
        extra_table.add_row("")
        batt_color = get_color_for_percent(100 - battery["level"], 50, 80)  # inverted
        if mode == "minimal":
            extra_table.add_row("[bold cyan]Batt[/]")
            extra_table.add_row(f"[{batt_color}]{battery['level']}%[/]")
        else:
            extra_table.add_row("[bold cyan]Battery[/]")
            status = truncate_text(battery.get("status", "Unknown"), 10)
            extra_table.add_row(f"[{batt_color}]{battery['level']}%[/] {status}")

            if battery.get("temp", 0) > 0 and mode == "full":
                temp_color = get_color_for_percent(battery["temp"], 40, 45)
                extra_table.add_row(f"[{temp_color}]{battery['temp']:.1f}°C[/]")

            if battery.get("health") and mode == "full":
                extra_table.add_row(f"[dim]{battery['health']}[/]")
            elif battery.get("health") and mode != "full":
                add_omission("Battery health")
    else:
        if mode == "full":
            extra_table.add_row("")
            extra_table.add_row("[dim]No battery[/]")

    title = "🌡" if mode == "minimal" else "🌡 Sensors"
    return Panel(extra_table, title=title, border_style="magenta")
