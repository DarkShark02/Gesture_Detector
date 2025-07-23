import numpy as np
from scipy.io.wavfile import write as write_wav
import os

# --- Configurazione dei Suoni ---
SAMPLE_RATE = 44100  # Frequenza di campionamento (Hz), standard CD quality
DURATION = 0.3     # Durata di ogni suono in secondi

# Frequenze per diversi toni (puoi modificarle)
FREQ_HIGH = 880    # La più alta (per LIKE, VITTORIA)
FREQ_MEDIUM = 440  # Media (per ROCK, CHIAMAMI)
FREQ_LOW = 220     # La più bassa (per DISLIKE, DITO_MEDIO)
FREQ_IMPACT = 660  # Per BANG_BANG (simile a sparo)

# --- Funzioni per Generare i Suoni ---

def generate_tone(frequency, duration, sample_rate, amplitude=0.5):
    """Genera un tono sinusoidale."""
    t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
    waveform = amplitude * np.sin(2 * np.pi * frequency * t)
    return waveform

def generate_click(duration, sample_rate, amplitude=0.7):
    """Genera un suono simile a un click."""
    num_samples = int(sample_rate * duration)
    waveform = np.zeros(num_samples)
    waveform[0:int(num_samples * 0.1)] = amplitude # Breve impulso iniziale
    waveform = np.convolve(waveform, np.array([1, 0.5, 0.25]), mode='same') # Smussa un po'
    return waveform

def generate_noise_burst(duration, sample_rate, amplitude=0.3):
    """Genera un breve rumore bianco."""
    num_samples = int(sample_rate * duration)
    waveform = (np.random.rand(num_samples) * 2 - 1) * amplitude
    return waveform

# --- Mappa delle Gesture ai Suoni Desiderati ---
# Puoi personalizzare quale funzione di suono e quali parametri usare per ogni gesture.
GESTURE_SOUND_CONFIGS = {
    "like.wav": {"type": "tone", "freq": FREQ_HIGH, "duration": DURATION},
    "dislike.wav": {"type": "tone", "freq": FREQ_LOW, "duration": DURATION},
    "vittoria.wav": {"type": "tone", "freq": FREQ_HIGH, "duration": DURATION + 0.1}, # Più lungo
    "dito_medio.wav": {"type": "noise_burst", "duration": DURATION * 0.8, "amplitude": 0.5},
    "rock.wav": {"type": "tone", "freq": FREQ_MEDIUM, "duration": DURATION},
    "chiamami.wav": {"type": "tone", "freq": FREQ_MEDIUM + 100, "duration": DURATION},
    "bang_bang.wav": {"type": "click", "duration": DURATION * 0.5, "amplitude": 1.0},
}

# --- Creazione della Cartella dei Suoni ---
SOUND_DIR = "suoni"
if not os.path.exists(SOUND_DIR):
    os.makedirs(SOUND_DIR)
    print(f"Creata la cartella: {SOUND_DIR}")

# --- Genera e Salva i File WAV ---
print("Generazione dei file WAV in corso...")
for filename, config in GESTURE_SOUND_CONFIGS.items():
    filepath = os.path.join(SOUND_DIR, filename)
    waveform = None

    if config["type"] == "tone":
        waveform = generate_tone(config["freq"], config["duration"], SAMPLE_RATE)
    elif config["type"] == "click":
        waveform = generate_click(config["duration"], SAMPLE_RATE, config.get("amplitude", 0.7))
    elif config["type"] == "noise_burst":
        waveform = generate_noise_burst(config["duration"], SAMPLE_RATE, config.get("amplitude", 0.3))
    
    if waveform is not None:
        # Normalizza a 16-bit intero per il formato WAV comune
        scaled_waveform = np.int16(waveform / np.max(np.abs(waveform)) * 32767)
        write_wav(filepath, SAMPLE_RATE, scaled_waveform)
        print(f"Generato: {filepath}")
    else:
        print(f"Errore: Tipo di suono non riconosciuto per {filename}")

print("Generazione completata!")