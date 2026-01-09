import os
import time
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

class AudioManager:
    def __init__(self, assets_dir="assets"):
        pygame.mixer.init()
        self.assets_dir = assets_dir
        self.sounds = {} # filename -> mixer.Sound
        self.channels = {} # filename -> mixer.Channel
        self.playing = [] # List of filenames currently playing
        self.master_volume = 1.0
        self.emojis = {
            'rain': '🌧️',
            'fire': '🔥',
            'cafe': '☕',
            'coffee': '☕',
            'brown': '🤎',
            'city': '🏙️',
            'water': '💧',
            'sea': '🌊',
            'lofi': '🎧',
            'omm': '🧘'
        }
        self.scan_assets()

    def scan_assets(self):
        if not os.path.exists(self.assets_dir):
            return
        
        valid_extensions = (".wav", ".mp3", ".ogg")
        for f in os.listdir(self.assets_dir):
            if f.lower().endswith(valid_extensions):
                path = os.path.join(self.assets_dir, f)
                try:
                    self.sounds[f] = pygame.mixer.Sound(path)
                except Exception as e:
                    print(f"Error loading {f}: {e}")

    def get_emoji(self, filename):
        # ID generic names from filename
        lower_name = filename.lower()
        for key, emoji in self.emojis.items():
            if key in lower_name:
                return emoji
        return '🎵'

    def play_sound(self, filename):
        if filename in self.sounds:
            # Play in loop
            channel = self.sounds[filename].play(loops=-1)
            channel.set_volume(self.master_volume)
            self.channels[filename] = channel
            self.playing.append(filename)

    def set_volume(self, filename, level):
        # level 0.0 to 1.0
        if filename in self.sounds:
            self.sounds[filename].set_volume(level)

    def set_master_volume(self, level):
        self.master_volume = max(0.0, min(1.0, level))
        for filename, channel in self.channels.items():
            if channel.get_busy():
                channel.set_volume(self.master_volume)

    def stop_all(self):
        for filename in self.playing:
            self.sounds[filename].stop()
        self.playing.clear()
        self.channels.clear()

class FocusApp:
    def __init__(self):
        self.console = Console()
        self.audio = AudioManager()
        
    def show_menu(self):
        self.console.clear()
        self.console.print("[bold cyan]Focus Noise Player[/bold cyan] 🎧", justify="center")
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
        self.console.print()

    def phase_one_selection(self):
        self.show_menu()
        
        # Selection
        self.console.print("[bold yellow]Select Sound IDs (comma separated):[/bold yellow] ", end="")
        selection_str = input()
        
        # Parse selection
        selected_ids = [s.strip() for s in selection_str.split(",")]
        selected_files = []
        for sid in selected_ids:
            if sid in self.sound_map:
                selected_files.append(self.sound_map[sid])
        
        if not selected_files:
            self.console.print("[red]No valid sounds selected. Exiting.[/red]")
            return None, None

        # Duration
        self.console.print("[bold yellow]Session Duration (minutes):[/bold yellow] ", end="")
        try:
            minutes = float(input())
            seconds = int(minutes * 60)
        except ValueError:
            self.console.print("[red]Invalid duration. Defaulting to 25 minutes.[/red]")
            seconds = 25 * 60
            
        # Initial Volume
        self.console.print("[bold yellow]Initial Volume (0-100%):[/bold yellow] ", end="")
        try:
            vol_input = input()
            if vol_input.strip():
                vol_percent = float(vol_input)
                self.audio.set_master_volume(vol_percent / 100.0)
        except ValueError:
            self.console.print("[red]Invalid volume. Defaulting to 100%.[/red]")
            
        return selected_files, seconds

    def check_input(self):
        if select.select([sys.stdin], [], [], 0) == ([sys.stdin], [], []):
            return sys.stdin.read(1)
        return None

    def run(self):
        files, duration = self.phase_one_selection()
        if not files:
            return


        # Start Audio
        for f in files:
            self.audio.play_sound(f)

        self.console.clear()
        self.console.print("[dim]controls: +/- to adjust volume, ctrl+c to quit[/dim]")
        
        # Prepare valid emojis for footer
        playing_emojis = []
        for f in files:
            base = os.path.splitext(f)[0]
            name = base.replace("_", " ").replace("-", " ").title()
            emoji = self.audio.get_emoji(f)
            playing_emojis.append(f"{emoji} {name}")
        
            playing_emojis.append(f"{emoji} {name}")
        
        base_footer = "Playing: " + " + ".join(playing_emojis)
        def get_footer():
            return f"{base_footer} | Volume: {int(self.audio.master_volume * 100)}%"

        # Progress bar configuration
        progress = Progress(
            TextColumn("[bold blue]{task.description}"),
            BarColumn(bar_width=None),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TimeRemainingColumn(),
            expand=True
        )
        
        task_id = progress.add_task("Focus Session", total=duration)
        
        # Layout
        layout = Layout()
        layout.split_column(
            Layout(name="upper", size=3),
            Layout(name="center"),
            Layout(name="lower", size=3)
        )
        
        # Initial View
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
                    layout["center"].update(
                        Panel(progress, title="Time Remaining", border_style="green")
                    )
                    
                    layout["lower"].update(
                        Panel(Align.center(Text(get_footer(), style="dim")))
                    )
                    
                    time.sleep(0.1) # Faster poll for input responsiveness
            
            self.audio.stop_all()
            self.console.print("[bold green]Session Complete![/bold green] 🎉")
            
        except KeyboardInterrupt:
            self.audio.stop_all()
            self.console.print("\n[bold red]Session Stopped.[/bold red] 👋")
        finally:
            termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)

if __name__ == "__main__":
    app = FocusApp()
    app.run()
