import platform
import json
import datetime
import shutil
from pathlib import Path
from typing import Dict, Any, Tuple, Optional, Union

# Shared Constants
RANK_DATA = [
    ("Noob", 0),
    ("Novice", 1),
    ("Terminal Tourist", 5),
    ("Flow Apprentice", 10),
    ("Deep Work Specialist", 25),
    ("Cyber Monk", 50),
    ("Neural Architect", 75),
    ("Time Lord", 100)
]

def get_config_dir() -> Path:
    """Returns the OS-specific configuration directory with fallback."""
    try:
        system = platform.system()
        home = Path.home()
        
        if system == "Windows":
            path = home / "AppData" / "Local" / "focus-cli"
        elif system == "Darwin": # MacOS
            path = home / "Library" / "Application Support" / "focus-cli"
        else: # Linux/Unix
            path = home / ".config" / "focus-cli"
            
        path.mkdir(parents=True, exist_ok=True)
        return path
    except Exception as e:
        print(f"Warning: Could not create config dir ({e}). Using temporary mode.")
        return Path("/tmp/focus-cli" if platform.system() != "Windows" else "C:\\Temp\\focus-cli")

class StatsManager:
    def __init__(self) -> None:
        self.config_dir = get_config_dir()
        self.filename = self.config_dir / "stats.json"
        self._migrate_old_file()
        self.stats = self.load_stats()

    def _migrate_old_file(self) -> None:
        """Migrates local stats.json to config dir if needed."""
        local_file = Path("stats.json")
        if local_file.exists() and not self.filename.exists():
            try:
                shutil.move(str(local_file), str(self.filename))
                # print(f"Migrated stats to {self.filename}") # Silence migration logs for cleanness
            except Exception:
                pass

    def load_stats(self) -> Dict[str, Any]:
        default = {
            "total_seconds": 0.0,
            "last_session_date": None,
            "current_streak": 0
        }
        if not self.filename.exists():
            return default
        
        try:
            with open(self.filename, 'r') as f:
                data = json.load(f)
                return {**default, **data}
        except Exception:
            return default

    def save_stats(self) -> None:
        try:
            if not self.config_dir.exists():
                 self.config_dir.mkdir(parents=True, exist_ok=True)
            with open(self.filename, 'w') as f:
                json.dump(self.stats, f, indent=2)
        except Exception:
            pass # Fail silently if we can't write stats

    def update_time(self, seconds: float) -> None:
        if seconds <= 0:
            return
            
        today = str(datetime.date.today())
        last_date = self.stats.get("last_session_date")
        
        # Streak Logic
        if last_date != today:
            if last_date:
                try:
                    last_dt = datetime.datetime.strptime(last_date, "%Y-%m-%d").date()
                    curr_dt = datetime.date.today()
                    delta = (curr_dt - last_dt).days
                    
                    if delta == 1:
                        self.stats["current_streak"] += 1
                    elif delta > 1:
                        self.stats["current_streak"] = 1
                except ValueError:
                    self.stats["current_streak"] = 1
            else:
                self.stats["current_streak"] = 1
                
            self.stats["last_session_date"] = today
        
        self.stats["total_seconds"] += seconds
        self.save_stats()

    def get_rank_title(self) -> str:
        total_hours = self.stats["total_seconds"] / 3600.0
        
        # Iterate backwards to find the highest rank achieved
        current_title = RANK_DATA[0][0]
        for title, hours in RANK_DATA:
            if total_hours >= hours:
                current_title = title
            else:
                break
        return current_title

    def get_display_stats(self) -> Tuple[str, str, str]:
        total_sec = int(self.stats["total_seconds"])
        hours = total_sec // 3600
        mins = (total_sec % 3600) // 60
        time_str = f"{hours}h {mins}m"
        
        streak = self.stats["current_streak"]
        streak_str = f"{streak} Day{'s' if streak != 1 else ''}"
        
        rank = self.get_rank_title()
        
        return time_str, streak_str, rank

    def reset_stats(self) -> None:
        self.stats = {
            "total_seconds": 0.0,
            "last_session_date": None,
            "current_streak": 0
        }
        self.save_stats()

class SettingsManager:
    def __init__(self) -> None:
        self.config_dir = get_config_dir()
        self.filename = self.config_dir / "settings.json"
        self._migrate_old_file()
        self.settings = self.load_settings()

    def _migrate_old_file(self) -> None:
        local_file = Path("settings.json")
        if local_file.exists() and not self.filename.exists():
            try:
                shutil.move(str(local_file), str(self.filename))
            except Exception:
                pass

    def load_settings(self) -> Dict[str, Any]:
        default = {
            "volume": 100,
            "timer_duration": 25,
            "show_timer": True,
            "play_gong": True,
            "dynamic_weather": True,
            "theme_color": "cyan",
            "volume_step": 5,
            "auto_start": False,
            "weather_freq": "medium",
            "fade_duration": 2.0,
            "confirm_exit": False,
            "show_system_log": True,
            "enable_ghosts": True,
            "ghost_chance": "rare"
        }
        if not self.filename.exists():
            return default
        try:
            with open(self.filename, 'r') as f:
                data = json.load(f)
                return {**default, **data}
        except Exception:
            return default

    def save_settings(self) -> None:
        try:
            if not self.config_dir.exists():
                 self.config_dir.mkdir(parents=True, exist_ok=True)
            with open(self.filename, 'w') as f:
                json.dump(self.settings, f, indent=2)
        except Exception:
            pass

    def get(self, key: str, default: Any = None) -> Any:
        return self.settings.get(key, default)

    def set(self, key: str, value: Any) -> None:
        self.settings[key] = value
        self.save_settings()
