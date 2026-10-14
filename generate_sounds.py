import os

import numpy as np
from scipy.io.wavfile import write as write_wav

# --- Sound Configuration ---
SAMPLE_RATE = 44100  # Sampling rate (Hz), CD quality
DURATION = 0.3       # Duration of each sound in seconds

# Tone frequencies (feel free to change them)
FREQ_HIGH = 880    # Highest (LIKE, VICTORY)
FREQ_MEDIUM = 440  # Medium (ROCK, CALL_ME)
FREQ_LOW = 220     # Lowest (DISLIKE)

SOUND_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sounds")


# --- Sound Generators ---

def generate_tone(frequency, duration, sample_rate, amplitude=0.5):
    """Generates a sine wave tone."""
    t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
    return amplitude * np.sin(2 * np.pi * frequency * t)


def generate_click(duration, sample_rate, amplitude=0.7):
    """Generates a click-like sound."""
    num_samples = int(sample_rate * duration)
    waveform = np.zeros(num_samples)
    waveform[0:int(num_samples * 0.1)] = amplitude  # short initial pulse
    return np.convolve(waveform, np.array([1, 0.5, 0.25]), mode="same")  # smooth it a bit


def generate_noise_burst(duration, sample_rate, amplitude=0.3):
    """Generates a short burst of white noise."""
    num_samples = int(sample_rate * duration)
    return (np.random.rand(num_samples) * 2 - 1) * amplitude


# --- Gesture -> Sound Mapping ---
# Customize which generator and parameters are used for each gesture.
GESTURE_SOUND_CONFIGS = {
    "like.wav": {"type": "tone", "freq": FREQ_HIGH, "duration": DURATION},
    "dislike.wav": {"type": "tone", "freq": FREQ_LOW, "duration": DURATION},
    "victory.wav": {"type": "tone", "freq": FREQ_HIGH, "duration": DURATION + 0.1},  # longer
    "middle_finger.wav": {"type": "noise_burst", "duration": DURATION * 0.8, "amplitude": 0.5},
    "rock.wav": {"type": "tone", "freq": FREQ_MEDIUM, "duration": DURATION},
    "call_me.wav": {"type": "tone", "freq": FREQ_MEDIUM + 100, "duration": DURATION},
    "bang_bang.wav": {"type": "click", "duration": DURATION * 0.5, "amplitude": 1.0},
}


def main():
    os.makedirs(SOUND_DIR, exist_ok=True)

    print("Generating WAV files...")
    for filename, config in GESTURE_SOUND_CONFIGS.items():
        filepath = os.path.join(SOUND_DIR, filename)

        if config["type"] == "tone":
            waveform = generate_tone(config["freq"], config["duration"], SAMPLE_RATE)
        elif config["type"] == "click":
            waveform = generate_click(config["duration"], SAMPLE_RATE, config.get("amplitude", 0.7))
        elif config["type"] == "noise_burst":
            waveform = generate_noise_burst(config["duration"], SAMPLE_RATE, config.get("amplitude", 0.3))
        else:
            print(f"Error: unknown sound type for {filename}")
            continue

        # Normalize to 16-bit integers, the most common WAV format
        scaled_waveform = np.int16(waveform / np.max(np.abs(waveform)) * 32767)
        write_wav(filepath, SAMPLE_RATE, scaled_waveform)
        print(f"Generated: {filepath}")

    print("Done!")


if __name__ == "__main__":
    main()
