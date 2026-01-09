import os
import time
import json
import datetime
import sys
import termios
import tty
import select
# Suppress pygame welcome message
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"
import pygame
from rich.console import Console
from rich.table import Table
from rich.live import Live
from rich.progress import Progress, BarColumn, TextColumn, TimeRemainingColumn
from rich.panel import Panel
from rich import box
from rich.layout import Layout
from rich.align import Align
from rich.text import Text
from audio_manager import AudioManager

class StatsManager:
    def __init__(self, filename="stats.json"):
        self.filename = filename
        self.stats = self.load_stats()

    def load_stats(self):
        default = {
            "total_seconds": 0.0,
            "last_session_date": None,
            "current_streak": 0
        }
        if not os.path.exists(self.filename):
            return default
        
        try:
            with open(self.filename, 'r') as f:
                data = json.load(f)
                return {**default, **data} # Merge with default to ensure keys exist
        except:
            return default

    def save_stats(self):
        with open(self.filename, 'w') as f:
            json.dump(self.stats, f, indent=2)

    def update_time(self, seconds):
        if seconds <= 0:
            return
            
        today = str(datetime.date.today())
        last_date = self.stats["last_session_date"]
        
        # Streak Logic
        if last_date != today:
            if last_date:
                # Check if consecutive day
                last_dt = datetime.datetime.strptime(last_date, "%Y-%m-%d").date()
                curr_dt = datetime.date.today()
                delta = (curr_dt - last_dt).days
                
                if delta == 1:
                    self.stats["current_streak"] += 1
                elif delta > 1:
                    self.stats["current_streak"] = 1
                # If delta < 1 (same day), do nothing
            else:
                self.stats["current_streak"] = 1
                
            self.stats["last_session_date"] = today
        
        self.stats["total_seconds"] += seconds
        self.save_stats()

    def get_display_stats(self):
        total_sec = int(self.stats["total_seconds"])
        hours = total_sec // 3600
        mins = (total_sec % 3600) // 60
        time_str = f"{hours}h {mins}m"
        
        streak = self.stats["current_streak"]
        streak_str = f"{streak} Day{'s' if streak != 1 else ''}"
        
        return time_str, streak_str

class SettingsManager:
    def __init__(self, filename="settings.json"):
        self.filename = filename
        self.settings = self.load_settings()

    def load_settings(self):
        default = {
            "volume": 100,
            "timer_duration": 25,
            "show_timer": True
        }
        if not os.path.exists(self.filename):
            return default
        try:
            with open(self.filename, 'r') as f:
                data = json.load(f)
                return {**default, **data}
        except:
            return default

    def save_settings(self):
        with open(self.filename, 'w') as f:
            json.dump(self.settings, f, indent=2)

    def get(self, key):
        return self.settings.get(key)

    def set(self, key, value):
        self.settings[key] = value
        self.save_settings()

class FocusApp:
    def __init__(self):
        self.console = Console()
        self.audio = AudioManager()
        self.stats = StatsManager()
        self.settings = SettingsManager()
        
    def show_menu(self):
        self.console.clear()
        self.console.print("[bold cyan]Focus Noise Player[/bold cyan] 🎧", justify="center")
        self.console.print()
        
        # Stats Panel
        time_str, streak_str = self.stats.get_display_stats()
        stats_text = f"[bold green]Total Focus:[/bold green] {time_str}  |  [bold yellow]Current Streak:[/bold yellow] {streak_str} 🔥"
        self.console.print(Panel(Align.center(stats_text), box=box.ROUNDED, style="blue"), justify="center")
        self.console.print()

        table = Table(title="Available Sounds", show_header=True, header_style="bold magenta", box=box.ROUNDED, padding=(0, 2))
        table.add_column("ID", style="dim", width=4, justify="center")
        table.add_column("Name", style="green")

        # Sort sounds for consistent ID
        sound_files = sorted(list(self.audio.sounds.keys()))
        self.sound_map = {str(i+1): f for i, f in enumerate(sound_files)}

        for i, f in enumerate(sound_files):
            idx = str(i+1)
            # Generic clean name: remove extension, replace separators
            base = os.path.splitext(f)[0]
            headers = base.replace("_", " ").replace("-", " ").title()
            table.add_row(idx, headers)

        self.console.print(table, justify="center")
        self.console.print(Panel("[bold yellow]S[/bold yellow] - Settings", box=box.SIMPLE), justify="center")
        self.console.print()

    def settings_menu(self):
        while True:
            self.console.clear()
            self.console.print("[bold cyan]Settings[/bold cyan] ⚙️", justify="center")
            self.console.print()
            
            table = Table(box=box.ROUNDED, show_header=True, header_style="bold magenta")
            table.add_column("Option", style="yellow")
            table.add_column("Value", style="green")
            
            # Helper to format boolean
            def fmt_bool(val): return "ON" if val else "OFF"
            
            table.add_row("1. Default Volume", f"{self.settings.get('volume')}%")
            table.add_row("2. Default Duration", f"{self.settings.get('timer_duration')} min")
            table.add_row("3. Show Timer", fmt_bool(self.settings.get('show_timer')))
            
            self.console.print(table, justify="center")
            self.console.print()
            self.console.print("[dim]Enter number to change, or 'b' to back[/dim]", justify="center")
            
            choice = input("\nSelect: ").strip().lower()
            
            if choice == 'b':
                break
            elif choice == '1':
                try:
                    val = int(input("Enter default volume (0-100): "))
                    if 0 <= val <= 100:
                        self.settings.set('volume', val)
                except ValueError:
                    pass
            elif choice == '2':
                try:
                    val = int(input("Enter default duration (min): "))
                    if val > 0:
                        self.settings.set('timer_duration', val)
                except ValueError:
                    pass
            elif choice == '3':
                current = self.settings.get('show_timer')
                self.settings.set('show_timer', not current)

    def phase_one_selection(self):
        while True:
            self.show_menu()
            
            # Selection
            self.console.print("[bold yellow]Select Sound IDs (comma separated) or 'S' for Settings:[/bold yellow] ", end="")
            selection_str = input().strip()
            
            if selection_str.lower() == 's':
                self.settings_menu()
                continue
            
            # Parse selection
            selected_ids = [s.strip() for s in selection_str.split(",")]
            selected_files = []
            valid_selection = False
            
            for sid in selected_ids:
                if sid in self.sound_map:
                    selected_files.append(self.sound_map[sid])
                    valid_selection = True
            
            if not valid_selection:
                if not selection_str: # Allow simple enter to refresh or nothing
                     self.console.print("[red]No valid sounds selected.[/red]")
                     time.sleep(1)
                     continue
                
                self.console.print("[red]No valid sounds selected. Exiting.[/red]")
                return None, None, []
                
            break
        
        # Duration
        default_duration = self.settings.get("timer_duration")
        self.console.print(f"[bold yellow]Session Duration (minutes) [{default_duration}]:[/bold yellow] ", end="")
        try:
            dur_input = input().strip()
            if not dur_input:
                minutes = float(default_duration)
            else:
                minutes = float(dur_input)
            seconds = int(minutes * 60)
        except ValueError:
            self.console.print(f"[red]Invalid duration. Defaulting to {default_duration} minutes.[/red]")
            seconds = int(default_duration * 60)
            
        # Initial Volume
        default_vol = self.settings.get("volume")
        self.console.print(f"[bold yellow]Initial Volume (0-100%) [{default_vol}]:[/bold yellow] ", end="")
        try:
            vol_input = input().strip()
            if not vol_input:
                vol_percent = float(default_vol)
            else:
                vol_percent = float(vol_input)
            self.audio.set_master_volume(vol_percent / 100.0)
        except ValueError:
            self.console.print(f"[red]Invalid volume. Using default {default_vol}%.[/red]")
            self.audio.set_master_volume(default_vol / 100.0)

        # Task Intents
        tasks = []
        self.console.print()
        self.console.print("[bold magenta]Optional: Enter up to 3 tasks for this session (press Enter to skip)[/bold magenta]")
        for i in range(3):
            self.console.print(f"[bold yellow]Task #{i+1}:[/bold yellow] ", end="")
            t = input().strip()
            if not t:
                break
            tasks.append(t)
            
        return selected_files, seconds, tasks

    def check_input(self):
        if select.select([sys.stdin], [], [], 0) == ([sys.stdin], [], []):
            return sys.stdin.read(1)
        return None

    def run(self):
        files, duration, tasks = self.phase_one_selection()
        if not files:
            return


        # Start Audio
        for f in files:
            self.audio.play_sound(f, fade_ms=2000)

        self.console.clear()
        self.console.print("[dim]controls: +/- to adjust volume, ctrl+c to quit[/dim]")
        
        # Prepare valid emojis for footer
        playing_emojis = []
        for f in files:
            base = os.path.splitext(f)[0]
            name = base.replace("_", " ").replace("-", " ").title()
            emoji = self.audio.get_emoji(f)
            playing_emojis.append(f"{emoji} {name}")
        
        base_footer = "Playing: " + " + ".join(playing_emojis)
        def get_footer():
            return f"{base_footer} | Volume: {int(self.audio.master_volume * 100)}%"

        # Progress bar configuration
        # Check settings for timer visibility
        show_timer = self.settings.get("show_timer")
        
        columns = [
            TextColumn("[bold blue]{task.description}"),
            BarColumn(bar_width=None),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        ]
        
        if show_timer:
            columns.append(TimeRemainingColumn())
            
        columns.append(TextColumn("{task.fields[timer_str] if 'timer_str' in task.fields else ''}"))
            
        progress = Progress(*columns, expand=True)
        
        task_id = progress.add_task("Focus Session", total=duration)
        
        # Layout
        layout = Layout()
        layout.split_column(
            Layout(name="upper", size=3),
            Layout(name="center"),
            Layout(name="lower", size=3)
        )
        
        # Configure center layout based on tasks
        if tasks:
            layout["center"].split_column(
                Layout(name="timer"),
                Layout(name="tasks", size=len(tasks) + 4)
            )
            timer_layout = layout["center"]["timer"]
            tasks_layout = layout["center"]["tasks"]
        else:
            timer_layout = layout["center"]
        
        # Initial View
        old_settings = termios.tcgetattr(sys.stdin)
        try:
            tty.setcbreak(sys.stdin.fileno())
            with Live(layout, refresh_per_second=4, screen=True) as live:
                start_time = time.time()
                while True:
                    elapsed = time.time() - start_time
                    remaining = duration - elapsed
                    
                    if remaining <= 0:
                        break
                    
                    # Periodic Dynamic Weather Update
                    self.audio.update_textures()
                    
                    # Input Handling
                    key = self.check_input()
                    if key:
                        if key in ('+', 'w', '='): # = is unshifted +
                            self.audio.set_master_volume(self.audio.master_volume + 0.05)
                        elif key in ('-', 's'):
                            self.audio.set_master_volume(self.audio.master_volume - 0.05)

                    # Update Progress
                    progress.update(task_id, completed=elapsed)
                    
                    # Update Layout details
                    layout["upper"].update(Align.center(Text("Focus Noise Player", style="bold cyan")))
                    
                    # We render progress into a panel for the center
                    timer_layout.update(
                        Panel(progress, title="Time Remaining", border_style="green")
                    )
                    
                    if tasks:
                        task_table = Table.grid(padding=(0, 1))
                        task_table.add_column(style="bold yellow", justify="right")
                        task_table.add_column(style="white")
                        for i, t in enumerate(tasks):
                            task_table.add_row(f"{i+1}.", t)
                        
                        tasks_layout.update(
                            Panel(Align.center(task_table), title="Current Tasks", border_style="magenta")
                        )
                    
                    layout["lower"].update(
                        Panel(Align.center(Text(get_footer(), style="dim")))
                    )
                    
                    time.sleep(0.1) # Faster poll for input responsiveness
            
            # Save stats
            elapsed_total = time.time() - start_time
            self.stats.update_time(elapsed_total)
            
            self.console.print("[dim]Fading out...[/dim]")
            self.audio.stop_all(fade_ms=2000)
            time.sleep(2.0)
            
            # Play Gong
            self.audio.play_gong()
            time.sleep(4.0) # Wait for gong to ring out
            
            self.console.print("[bold green]Session Complete![/bold green] 🎉")
            self.console.print(f"[dim]Stats Saved: +{int(elapsed_total/60)}m focus time[/dim]")
            
        except KeyboardInterrupt:
            # Save stats on interrupt too
            elapsed_total = time.time() - start_time
            self.stats.update_time(elapsed_total)
            
            self.console.print("\n[dim]Fading out...[/dim]")
            self.audio.stop_all(fade_ms=2000)
            time.sleep(2.0)
            self.console.print("\n[bold red]Session Stopped.[/bold red] 👋")
            self.console.print(f"[dim]Stats Saved: +{int(elapsed_total/60)}m focus time[/dim]")
        finally:
            termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)

if __name__ == "__main__":
    app = FocusApp()
    app.run()
