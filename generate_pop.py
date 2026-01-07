
import numpy as np
import os
from scipy.io.wavfile import write
import moviepy.editor as mp

def generate_pop():
    # Parameters
    sample_rate = 44100
    duration = 0.1  # Seconds
    frequency = 600.0  # Hz
    
    # Generate time array
    t = np.linspace(0, duration, int(sample_rate * duration))
    
    # Generate sine wave with exponential decay to sound like a "pop" or "pluck"
    envelope = np.exp(-t * 30)
    waveform = np.sin(2 * np.pi * frequency * t) * envelope
    
    # Normalize to 16-bit integer
    waveform = (waveform * 32767).astype(np.int16)
    
    # Save as WAV first
    os.makedirs("assets/sfx", exist_ok=True)
    wav_path = "assets/sfx/pop.wav"
    write(wav_path, sample_rate, waveform)
    
    # Convert to MP3
    mp3_path = "assets/sfx/pop.mp3"
    # Using moviepy or ffmpeg
    # MoviePy audio clip
    from moviepy.audio.io.AudioFileClip import AudioFileClip
    clip = AudioFileClip(wav_path)
    clip.write_audiofile(mp3_path)
    clip.close()
    
    # Clean up wav
    os.remove(wav_path)
    print(f"Generated {mp3_path}")

if __name__ == "__main__":
    generate_pop()
