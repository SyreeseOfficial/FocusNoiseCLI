import os
import pygame
import shutil
import random
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# Texture mapping as requested
TEXTURE_MAP = {
    "Brown Noise": ["keyboard.mp3", "page-turn.mp3", "vinyl-crackle.mp3"],
    "City": ["distant-ambulance-siren.mp3", "distant-train.mp3", "bike-bell.mp3", "door-open-close-with-bell.mp3"],
    "Coffee Shop": ["espresso-steam.mp3", "pouring-coffee.mp3", "spoon-and-cup.mp3", "cup-and-saucer.mp3", "cash-register.mp3"],
    "Fire": ["page-turn.mp3", "vinyl-crackle.mp3", "crickets.mp3", "owl.mp3", "winter-wind.mp3"],
    "Flowing Water": ["frog.mp3", "wind-chimes.mp3", "distant-thunder.mp3"],
    "Gentle Rain": ["distant-thunder.mp3", "winter-wind.mp3", "wind-chimes.mp3"],
    "Lofi": ["vinyl-crackle.mp3", "keyboard.mp3", "page-turn.mp3", "big-bell.mp3"],
    "Omm": ["big-bell.mp3", "wind-chimes.mp3"],
    "Rain Sounds": ["distant-thunder.mp3", "winter-wind.mp3"],
    "Sea Wave": ["seagull.mp3", "distant-foghorn.mp3", "winter-wind.mp3"]
}

class AudioManager:
    def __init__(self, assets_dir: str = "assets") -> None:
        try:
            pygame.mixer.init()
        except Exception as e:
            print(f"Warning: Audio init failed ({e}). Sound will be disabled.")
        
        # Resolve Assets Directory
        if assets_dir == "assets":
            # Search order: Local -> Script Relative -> System
            candidates = [
                Path("assets"),
                Path(__file__).parent / "assets",
                Path("/usr/share/focusnoise-cli/assets"),
                Path("/usr/local/share/focusnoise-cli/assets")
            ]
            self.assets_dir = Path("assets") # Fallback
            for candidate in candidates:
                if candidate.exists() and candidate.is_dir():
                    self.assets_dir = candidate
                    break
        else:
            self.assets_dir = Path(assets_dir)

        self.sfx_dir = self.assets_dir / "sfx"
        self.textures_dir = self.assets_dir / "textures"
        
        # 1. Automatic File Setup (Only if we have write access)
        if os.access(self.assets_dir, os.W_OK):
            self.organize_textures()
        
        # Storage
        self.sounds: Dict[str, pygame.mixer.Sound] = {}   # filename -> mixer.Sound
        self.sfx: Dict[str, pygame.mixer.Sound] = {}      # filename -> mixer.Sound
        self.textures: Dict[str, pygame.mixer.Sound] = {} # filename -> mixer.Sound
        
        self.channels: Dict[str, pygame.mixer.Channel] = {} # filename -> mixer.Channel
        self.playing: List[str] = [] # List of filenames currently playing (loops)
        self.master_volume: float = 1.0
        
        # Dynamic Weather State
        self.last_texture_time = time.time()
        self.weather_freq_range: Tuple[int, int] = (30, 90) # Default Medium
        self.next_texture_interval = random.uniform(*self.weather_freq_range)
        
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
        
        # Scan all folders
        self._scan_folder(self.assets_dir, self.sounds)
        self._scan_folder(self.sfx_dir, self.sfx)
        self._scan_folder(self.textures_dir, self.textures)

    def organize_textures(self) -> None:
        """Checks for 'noises' folder and moves files to 'assets/textures'."""
        noises_path = Path("noises")
        if noises_path.exists():
            self.textures_dir.mkdir(parents=True, exist_ok=True)
            
            print(f"Moving files from {noises_path} to {self.textures_dir}...")
            count = 0
            for item in noises_path.iterdir():
                if item.is_file():
                    try:
                        shutil.move(str(item), str(self.textures_dir / item.name))
                        count += 1
                    except Exception as e:
                        print(f"Failed to move {item.name}: {e}")
            
            try:
                noises_path.rmdir()
            except OSError:
                print("Could not remove 'noises' directory (might not be empty).")
                
            print(f"Moved {count} texture files.")

    def _scan_folder(self, folder: Path, storage: Dict[str, pygame.mixer.Sound]) -> None:
        """Helper to scan a folder for audio files and load them."""
        if not folder.exists():
            return
        
        valid_extensions = {".wav", ".mp3", ".ogg"}
        for item in folder.iterdir():
            if item.is_file() and item.suffix.lower() in valid_extensions:
                try:
                    storage[item.name] = pygame.mixer.Sound(str(item))
                except Exception as e:
                    print(f"Error loading {item.name}: {e}")

    def scan_assets(self) -> None:
        """Public alias for rescanning main assets."""
        self._scan_folder(self.assets_dir, self.sounds)

    def play_gong(self) -> None:
        # Specific helper for the gong
        gong_file = "gong.mp3"
        if gong_file in self.sfx:
            try:
                self.sfx[gong_file].set_volume(self.master_volume)
                self.sfx[gong_file].play()
            except Exception:
                pass

    def get_emoji(self, filename: str) -> str:
        # ID generic names from filename
        lower_name = filename.lower()
        for key, emoji in self.emojis.items():
            if key in lower_name:
                return emoji
        return '🎵'

    def play_sound(self, filename: str, fade_ms: int = 2000) -> None:
        if filename in self.sounds:
            try:
                # Play in loop
                channel = self.sounds[filename].play(loops=-1, fade_ms=fade_ms)
                if channel:
                    channel.set_volume(self.master_volume)
                    self.channels[filename] = channel
                    if filename not in self.playing:
                        self.playing.append(filename)
            except Exception as e:
                print(f"Error playing {filename}: {e}")

    def set_volume(self, filename: str, level: float) -> None:
        # level 0.0 to 1.0
        if filename in self.sounds:
            self.sounds[filename].set_volume(level)

    def set_master_volume(self, level: float) -> None:
        self.master_volume = max(0.0, min(1.0, level))
        for _, channel in self.channels.items():
            if channel.get_busy():
                channel.set_volume(self.master_volume)

    def stop_all(self, fade_ms: int = 2000) -> None:
        for filename in self.playing:
            if filename in self.sounds:
                self.sounds[filename].fadeout(fade_ms)
        self.playing.clear()
        self.channels.clear()

    def update_textures(self) -> None:
        """Called periodically to play random texture sounds."""
        now = time.time()
        
        if now - self.last_texture_time > self.next_texture_interval:
            self.play_random_texture()
            self.last_texture_time = now
            # Set next interval based on current range
            self.next_texture_interval = random.uniform(*self.weather_freq_range)

    def set_weather_frequency(self, level: str) -> None:
        ranges = {
            "low": (60, 120),
            "medium": (30, 90),
            "high": (15, 45)
        }
        self.weather_freq_range = ranges.get(level.lower(), (30, 90))

    def play_random_texture(self) -> None:
        if not self.playing:
            return

        # 1. Identify valid textures based on playing loops
        valid_textures: List[str] = []
        
        for loop_file in self.playing:
            loop_name_clean = os.path.splitext(loop_file)[0].replace("_", " ").replace("-", " ").lower()
            
            for key, textures in TEXTURE_MAP.items():
                if key.lower() in loop_name_clean or loop_name_clean in key.lower():
                    valid_textures.extend(textures)
        
        if not valid_textures:
            return

        # 2. Pick one
        texture_file = random.choice(valid_textures)
        
        # 3. Play it
        if texture_file in self.textures:
            try:
                # Volume: subtle, 30-60% of master volume
                vol = self.master_volume * random.uniform(0.3, 0.6)
                self.textures[texture_file].set_volume(vol)
                self.textures[texture_file].play()
            except Exception:
                pass
