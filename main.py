import os
import time
import sys
# Suppress pygame welcome message
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"
import pygame
from rich.console import Console
from rich.table import Table
from rich.live import Live
from rich.progress import Progress, BarColumn, TextColumn, TimeRemainingColumn
from rich.panel import Panel
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
            self.channels[filename] = channel
            self.playing.append(filename)

    def set_volume(self, filename, level):
        # level 0.0 to 1.0
        if filename in self.sounds:
            self.sounds[filename].set_volume(level)

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

        table = Table(title="Available Sounds", show_header=True, header_style="bold magenta")
        table.add_column("ID", style="dim", width=4, justify="center")
        table.add_column("Emoji", width=6, justify="center")
        table.add_column("Name", style="green")

        # Sort sounds for consistent ID
        sound_files = sorted(list(self.audio.sounds.keys()))
        self.sound_map = {str(i+1): f for i, f in enumerate(sound_files)}

        for i, f in enumerate(sound_files):
            idx = str(i+1)
            emoji = self.audio.get_emoji(f)
            # Generic clean name: remove extension, replace separators
            base = os.path.splitext(f)[0]
            headers = base.replace("_", " ").replace("-", " ").title()
            table.add_row(idx, emoji, headers)

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
            
        return selected_files, seconds

    def run(self):
        files, duration = self.phase_one_selection()
        if not files:
            return

        # Start Audio
        for f in files:
            self.audio.play_sound(f)

        self.console.clear()
        
        # Prepare valid emojis for footer
        playing_emojis = []
        for f in files:
            base = os.path.splitext(f)[0]
            name = base.replace("_", " ").replace("-", " ").title()
            emoji = self.audio.get_emoji(f)
            playing_emojis.append(f"{emoji} {name}")
        
        footer_text = "Playing: " + " + ".join(playing_emojis)

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
        try:
            with Live(layout, refresh_per_second=4, screen=True) as live:
                start_time = time.time()
                while True:
                    elapsed = time.time() - start_time
                    remaining = duration - elapsed
                    
                    if remaining <= 0:
                        break
                    
                    # Update Progress
                    progress.update(task_id, completed=elapsed)
                    
                    # Update Layout details
                    layout["upper"].update(Align.center(Text("Focus Noise Player", style="bold cyan")))
                    
                    # We render progress into a panel for the center
                    layout["center"].update(
                        Panel(progress, title="Time Remaining", border_style="green")
                    )
                    
                    layout["lower"].update(
                        Panel(Align.center(Text(footer_text, style="dim")))
                    )
                    
                    time.sleep(0.5)
            
            self.audio.stop_all()
            self.console.print("[bold green]Session Complete![/bold green] 🎉")
            
        except KeyboardInterrupt:
            self.audio.stop_all()
            self.console.print("\n[bold red]Session Stopped.[/bold red] 👋")

if __name__ == "__main__":
    app = FocusApp()
    app.run()
