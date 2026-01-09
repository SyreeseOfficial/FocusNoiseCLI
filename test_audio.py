import time
from audio_engine import AudioManager

def main():
    print("Initializing Audio Manager...")
    audio = AudioManager()
    
    available_sounds = list(audio.sounds.keys())
    print(f"Available sounds: {available_sounds}")
    
    if not available_sounds:
        print("No sounds found to test.")
        return

    # Test playing the first sound found
    test_sound = available_sounds[0]
    print(f"\nTesting '{test_sound}' for 3 seconds...")
    
    audio.play_sound(test_sound)
    time.sleep(3)
    
    print(f"Stopping '{test_sound}'...")
    audio.stop_sound(test_sound)

    # Test Volume
    print(f"\nTesting Volume (50%) on '{test_sound}' for 2 seconds...")
    audio.set_volume(test_sound, 0.5)
    audio.play_sound(test_sound)
    time.sleep(2)
    audio.stop_sound(test_sound)
    
    print("\nTest Complete.")

if __name__ == "__main__":
    main()
