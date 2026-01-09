import os
import numpy as np
from scipy.io import wavfile

ASSETS_DIR = "assets"

def generate_noise(duration_sec=5, sample_rate=44100, noise_type="white"):
    """
    Generates placeholder noise.
    """
    t = np.linspace(0, duration_sec, int(sample_rate * duration_sec), endpoint=False)
    
    if noise_type == "brown":
        # Brown noise: integrated white noise
        white = np.random.standard_normal(size=t.shape)
        brown = np.cumsum(white)
        # Normalize
        brown /= np.max(np.abs(brown))
        return brown
    
    elif noise_type == "pink":
        # Simple approximation for pinkish noise (placeholder for rain)
        white = np.random.standard_normal(size=t.shape)
        # Apply a simple low-pass filter-like effect via accumulation with decay? 
        # Or just use the 1/f generally.
        # For a placeholder, lets just smooth white noise a bit
        b = np.array([0.049922035, -0.095993537, 0.050612699, -0.004408786])
        a = np.array([1.0, -2.494956002, 2.017265875, -0.522189400])
        # Implementing a full filter might be overkill for a placeholder script 
        # without importing scipy.signal.
        # Let's stick to a simpler "rain" approximation: deeply smoothed white noise
        # or just random walk (brown) but higher pitch?
        # Actually proper pink noise generation is complex in pure numpy without FFT.
        # Let's use FFT for pink noise.
        req_shape = t.shape[0]
        f = np.fft.rfft(np.random.randn(req_shape))
        # 1/f magnitude
        f[1:] /= np.sqrt(np.arange(1, len(f)))
        pink = np.fft.irfft(f)
        pink /= np.max(np.abs(pink))
        return pink

    else: # cafe / white
        # White noise
        white = np.random.uniform(-1, 1, size=t.shape)
        return white

def save_wav(filename, data, sample_rate=44100):
    # Convert to 16-bit PCM
    data_int16 = np.int16(data * 32767)
    wavfile.write(filename, sample_rate, data_int16)
    print(f"Generated {filename}")

def main():
    if not os.path.exists(ASSETS_DIR):
        os.makedirs(ASSETS_DIR)

    # Check if assets folder is empty (ignoring hidden files)
    files = [f for f in os.listdir(ASSETS_DIR) if not f.startswith('.')]
    if files:
        print(f"Assets directory '{ASSETS_DIR}' is not empty. Skipping generation.")
        return

    print("Generating placeholder audio assets...")
    
    # Generate Brown Noise
    brown_data = generate_noise(noise_type="brown")
    save_wav(os.path.join(ASSETS_DIR, "brown_noise.wav"), brown_data)

    # Generate Rain (Pink Noise approximation)
    rain_data = generate_noise(noise_type="pink")
    save_wav(os.path.join(ASSETS_DIR, "rain.wav"), rain_data)

    # Generate Cafe (White Noise placeholder - real cafe sound is hard to synthesize)
    # We'll just generate white noise but maybe pulse it or something? 
    # Let's just stick to plain white noise for 'cafe' placeholder as requested.
    cafe_data = generate_noise(noise_type="white")
    save_wav(os.path.join(ASSETS_DIR, "cafe.wav"), cafe_data)

    print("Done.")

if __name__ == "__main__":
    main()
