#!/usr/bin/env python3
# main.py - Enhanced version with history tracking
import time
from rich.live import Live
from rich.console import Console
from utils.system_info import check_dependencies
from ui.ui import generate_layout
from utils.utils import get_state, update_history
from hardware.hardware import get_cpu_data, get_mem

console = Console()

def update_sparkline_history():
    """Update historical data for sparklines."""
    # Update memory history
    mem = get_mem()
    update_history('memory', mem['percent'])
    
    # Update CPU history for each core
    cpus = get_cpu_data()
    for i, cpu in enumerate(cpus):
        update_history(f'cpu{i}', cpu['usage'])

def main():
    """Main entry point for the system monitor."""
    # Check dependencies on startup
    warnings = check_dependencies()
    if warnings:
        console.print("\n[yellow]⚠ Warnings:[/yellow]")
        for w in warnings:
            console.print(f"  • {w}")
        console.print("\n[dim]Starting in 2 seconds...[/dim]\n")
        time.sleep(2)
    
    try:
        # Initialize history
        state = get_state()
        history = state.get("history", {})
        
        with Live(generate_layout(history), refresh_per_second=2, screen=True) as live:
            while True:
                time.sleep(0.5)
                
                # Update sparkline history
                update_sparkline_history()
                
                # Regenerate layout with updated history
                live.update(generate_layout(history))
    
    except KeyboardInterrupt:
        console.print("\n[green]✓[/green] Exiting gracefully...")
    except Exception as e:
        console.print(f"\n[red]✗[/red] Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
