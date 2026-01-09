import os
import numpy as np
import scipy.io.wavfile as wav

ASSETS_DIR = "assets"

def ensure_assets_dir():
    if not os.path.exists(ASSETS_DIR):
        os.makedirs(ASSETS_DIR)
        print(f"Created directory: {ASSETS_DIR}")

def save_wav(filename, data, rate=44100):
    # Normalize to 16-bit PCM range
    data = data / np.max(np.abs(data)) * 32767
    data = data.astype(np.int16)
    path = os.path.join(ASSETS_DIR, filename)
    wav.write(path, rate, data)
    print(f"Generated: {path}")

def generate_brown_noise(duration, rate=44100):
    # Brown noise is the integral of white noise
    k = duration * rate
    white = np.random.uniform(-1, 1, k)
    brown = np.cumsum(white)
    # Remove DC offset and normalize roughly here to avoid drift issues before final norm
    brown -= np.mean(brown)
    return brown

def generate_rain_noise(duration, rate=44100):
    # Rain is often modeled as white/pink noise. 
    # We will use simple white noise with a slight low-pass trend (simulated by averaging) 
    # to make it less harsh than pure static.
    k = duration * rate
    white = np.random.uniform(-1, 1, k)
    # Simple moving average to dampen highs slightly
    return np.convolve(white, np.ones(5)/5, mode='same')

def generate_cafe_noise(duration, rate=44100):
    # Simulating cafe chatter is complex. We will create "babble" noise.
    # We'll superposition many random snippets of filtered noise to simulate distinct "voices".
    k = duration * rate
    mix = np.zeros(k)
    
    # Create 20 "voices"
    for _ in range(20):
        # Each voice is a bursty signal
        # Carrier: Band-limited noise (speech range ~300Hz - 3400Hz)
        # We simulate this by generating white noise
        voice_len = np.random.randint(rate//2, rate*2) # 0.5s to 2s bursts
        start = np.random.randint(0, k - voice_len)
        
        # Primitive filtering (smoothing) to make it muddled
        voice = np.random.uniform(-1, 1, voice_len)
        voice = np.convolve(voice, np.ones(50)/50, mode='same') # Low-pass heavily
        
        # Modulation: Random amplitude envelope
        envelope = np.sin(np.linspace(0, np.pi, voice_len))
        
        mix[start:start+voice_len] += voice * envelope

    # Add some background "clatter" (high freq bursts)
    for _ in range(10):
        clatter_len = np.random.randint(1000, 5000)
        start = np.random.randint(0, k - clatter_len)
        clatter = np.random.uniform(-0.5, 0.5, clatter_len)
        mix[start:start+clatter_len] += clatter

    return mix

def main():
    ensure_assets_dir()
    duration = 5 # seconds
    
    print("Generating Brown Noise...")
    brown = generate_brown_noise(duration)
    save_wav("brown_noise.wav", brown)
    
    print("Generating Rain Noise...")
    rain = generate_rain_noise(duration)
    save_wav("rain.wav", rain)
    
    print("Generating Cafe Noise...")
    cafe = generate_cafe_noise(duration)
    save_wav("cafe.wav", cafe)
    
    print("All assets generated.")

if __name__ == "__main__":
    main()
