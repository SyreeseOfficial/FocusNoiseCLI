import os
import pygame

class AudioManager:
    def __init__(self, assets_dir="assets"):
        """
        Initializes the AudioManager.
        """
        # Initialize pygame mixer
        pygame.mixer.init()
        
        self.assets_dir = assets_dir
        self.sounds = {} # Dictionary to store filename -> Sound object
        
        self._load_sounds()

    def _load_sounds(self):
        """
        Scans the assets directory and loads all .wav files.
        """
        if not os.path.exists(self.assets_dir):
            print(f"Warning: Assets directory '{self.assets_dir}' does not exist.")
            return

        # Find all .wav files
        wav_files = [f for f in os.listdir(self.assets_dir) if f.lower().endswith('.wav')]
        
        if not wav_files:
            print("No .wav files found in assets directory.")
            return

        # Ensure we have enough channels
        current_channels = pygame.mixer.get_num_channels()
        if len(wav_files) > current_channels:
            pygame.mixer.set_num_channels(len(wav_files) + 4) # Add some buffer

        print(f"Found {len(wav_files)} audio files.")
        
        for filename in wav_files:
            file_path = os.path.join(self.assets_dir, filename)
            try:
                sound = pygame.mixer.Sound(file_path)
                self.sounds[filename] = sound
                print(f"Loaded: {filename}")
            except Exception as e:
                print(f"Error loading {filename}: {e}")

    def play_sound(self, filename):
        """
        Starts playing the sound in a loop.
        """
        if filename in self.sounds:
            # loops=-1 means loop indefinitely
            self.sounds[filename].play(loops=-1)
            print(f"Playing {filename}...")
        else:
            print(f"Sound '{filename}' not found.")

    def set_volume(self, filename, volume_level):
        """
        Sets the volume for a specific sound.
        volume_level: float between 0.0 and 1.0
        """
        if filename in self.sounds:
            # Clamp volume between 0.0 and 1.0
            volume_level = max(0.0, min(1.0, volume_level))
            self.sounds[filename].set_volume(volume_level)
            # print(f"Set volume for {filename} to {volume_level}")
        else:
            print(f"Sound '{filename}' not found.")

    def stop_sound(self, filename):
        """
        Stops a specific sound.
        """
        if filename in self.sounds:
            self.sounds[filename].stop()
        else:
            print(f"Sound '{filename}' not found.")

    def stop_all(self):
        """
        Stops all sounds.
        """
        pygame.mixer.stop()
