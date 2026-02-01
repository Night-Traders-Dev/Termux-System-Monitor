from rich.panel import Panel
from rich.text import Text
from rich.align import Align

from utils.ui import (
    get_omissions

)



def create_footer_panel(width, height, mode):
    """Create footer showing terminal size and omitted information."""
    omissions = get_omissions()

    size_text = f"Terminal: {width}x{height}"
    mode_text = f"Mode: {mode.upper()}"

    parts = [Text(size_text, style="bold cyan"), Text("  •  ", style="dim"), Text(mode_text, style="bold yellow")]

    if omissions:
        omit_str = ", ".join(omissions)
        # Leave some room for the rest of the footer text
        max_len = max(10, width - 45)
        if len(omit_str) > max_len:
            omit_str = omit_str[: max_len - 3] + "..."
        parts.extend(
            [
                Text("  •  ", style="dim"),
                Text("Omitted: ", style="bold red"),
                Text(omit_str, style="dim red"),
            ]
        )
    else:
        parts.extend([Text("  •  ", style="dim"), Text("All info displayed", style="green")])

    footer_text = Text.assemble(*parts)
    centered = Align.center(footer_text)
    return Panel(centered, title="", border_style="bright_black", padding=(0, 1))
