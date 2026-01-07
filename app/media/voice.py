import edge_tts
import asyncio
import os
import re
import subprocess
from app.config import ASSETS_DIR

# Voice Profiles
VOICE_PROFILES = {
    "long": "en-US-GuyNeural", # Friendly, Happy, Energetic (User Choice)
    "shorts": "en-US-GuyNeural", # Same consistent voice
    "brand": "en-US-GuyNeural"
}

from moviepy.editor import concatenate_audioclips, AudioFileClip
from moviepy.audio.AudioClip import AudioArrayClip
import numpy as np

def clean_text(text):
    """
    Cleans text of regex artifacts but keeps [pause] tokens for splitting.
    """
    # Remove prefixes like "Voiceover:", "Narrator:"
    text = re.sub(r'^(Voiceover|Narrator|Host):\s*', '', text, flags=re.IGNORECASE)
    # Remove text in parentheses
    text = re.sub(r'\(.*?\)', '', text)
    # Remove remaining square brackets EXCEPT [pause] keys
    # We want to preserve [pause], [short pause], [long pause]
    # Strat: Replace known pauses with temp placeholders, kill brackets, restore placeholders?
    # Or just simpler regex: Remove brackets that are NOT pause?
    
    # Let's simplify: Just kill generic visual cues usually in [Visual: ...]
    text = re.sub(r'\[Visual:.*?\]', '', text, flags=re.IGNORECASE)
    
    # Remove asterisks
    text = text.replace('*', '')
    # Clean spaces
    text = re.sub(r'\s+', ' ', text).strip()
    return text

async def generate_segment(text, voice, out_path):
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(out_path)
    return out_path

async def generate_voiceover(text, output_file, script_type="long"):
    """
    Generates mp3 by chunking text at [pause] markers.
    """
    text = clean_text(text)
    voice = VOICE_PROFILES.get(script_type, VOICE_PROFILES["long"])
    
    # Define pauses
    pause_map = {
        "[pause]": 0.6,
        "[short pause]": 0.3,
        "[long pause]": 1.2
    }
    
    # Split text logic
    # Regex split keeping delimiters?
    # pattern = r'(\[pause\]|\[short pause\]|\[long pause\])'
    pattern = re.compile(r'(\[.*?pause\])')
    parts = pattern.split(text)
    
    audio_clips = []
    temp_files = []
    
    base_name = output_file.replace(".mp3", "")
    
    import numpy as np
    
    current_time_offset = 0.0
    all_word_timestamps = []
    
    for i, part in enumerate(parts):
        part = part.strip()
        if not part: continue
        
        if part in pause_map:
            # It's a pause
            duration = pause_map[part]
            # Create silence
            # AudioArrayClip needs numpy array
            # silence = AudioArrayClip(np.zeros((int(44100 * duration), 2)), fps=44100)
            # Actually simpler: make a silent clip using a function?
            # Or just use AudioClip(lambda t: [0,0], duration=duration)
            from moviepy.audio.AudioClip import AudioClip
            silence = AudioClip(lambda t: [0,0], duration=duration, fps=44100)
            audio_clips.append(silence)
            current_time_offset += duration
        else:
            # It's text
            # Generate audio
            seg_path = f"{base_name}_part{i}.mp3"
            await generate_segment(part, voice, seg_path)
            temp_files.append(seg_path)
            
            if os.path.exists(seg_path):
                clip = AudioFileClip(seg_path)
                audio_clips.append(clip)
                
                # We need word timestamps for this segment?
                # edge_tts word boundary extraction is hard if we just saved to file.
                # To get timestamps, we need to stream it.
                # Redo generate_segment logic to parse stream?
                # Yes.
                
                # Re-run communicate to get timings? Or do it in one pass?
                # Doing it in one pass is better.
                # Let's refactor loop to use stream for text parts.
                
                # BUT wait, we need to save the file to load into MoviePy?
                # Yes.
                
                # Refined loop block for text:
                seg_timestamps = []
                communicate = edge_tts.Communicate(part, voice)
                with open(seg_path, "wb") as f:
                    async for chunk in communicate.stream():
                        if chunk["type"] == "audio":
                            f.write(chunk["data"])
                        elif chunk["type"] == "WordBoundary":
                            start = chunk["offset"] / 10_000_000
                            duration = chunk["duration"] / 10_000_000
                            seg_timestamps.append({
                                "word": chunk["text"],
                                "start": start + current_time_offset,
                                "end": start + duration + current_time_offset
                            })
                
                # Fallback: If no timestamps found (e.g. WordBoundary missing), use estimation
                if not seg_timestamps:
                    words = part.split()
                    if words:
                        # Use actual clip duration from file
                        # Reload clip to get accurate audio duration (ffmpeg/moviepy)
                        # We already loaded 'clip' above but didn't use it yet for duration in this scope
                        # Wait, we loaded 'clip' at line 100.
                        seg_duration = clip.duration
                        time_per_word = seg_duration / len(words)
                        for w_idx, w in enumerate(words):
                            s = current_time_offset + (w_idx * time_per_word)
                            e = s + time_per_word
                            seg_timestamps.append({
                                "word": w,
                                "start": s,
                                "end": e
                            })
                
                all_word_timestamps.extend(seg_timestamps)
                
                # clip duration
                # Reload clip to be sure of duration (already loaded as 'clip')
                # Use clip.duration for offset correctness
                current_time_offset += clip.duration
    
    # Concatenate
    if audio_clips:
        final_clip = concatenate_audioclips(audio_clips)
        final_clip.write_audiofile(output_file, logger=None)
        final_clip.close()
        for c in audio_clips:
            c.close() 
    else:
        # Create empty file?
        pass

    # Cleanup temp
    for f in temp_files:
        try:
            os.remove(f)
        except:
            pass

    # Post Processing
    polish_audio(output_file)
    
    return output_file, all_word_timestamps

def polish_audio(input_path):
    """
    Applies EQ and Compression using FFMPEG.
    Overwrites input file or creates temp? Let's overwrite safely.
    """
    temp_path = input_path.replace(".mp3", "_polished.mp3")
    
    # Complex filter: 
    # 1. Low Shelf (Warmth): 100Hz +3dB
    # 2. High Shelf (Presence): 8000Hz +2dB
    # 3. Compression: alimiter
    filter_str = "equalizer=f=100:t=q:w=1:g=3,equalizer=f=8000:t=q:w=1:g=2,alimiter=limit=0.9:attack=5:release=50"
    
    cmd = [
        "ffmpeg", "-y", "-i", input_path,
        "-af", filter_str,
        "-c:a", "libmp3lame", "-q:a", "2",
        temp_path
    ]
    
    try:
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        os.replace(temp_path, input_path)
    except Exception as e:
        print(f"Audio polish failed: {e}")

def create_audio_for_script(script_sections, run_id, script_type="long"):
    """
    Generates audio files for each section of the script.
    Returns: List of dicts with 'audio_path' and 'text'.
    """
    audio_dir = os.path.join(ASSETS_DIR, "temp_audio", run_id)
    os.makedirs(audio_dir, exist_ok=True)
    
    results = []
    
    print(f"Generating audio for {len(script_sections)} sections (Type: {script_type}).")
    for i, section in enumerate(script_sections):
        # Use voiceover if available (new format), else fallback to text (old format)
        voice_text = section.get("voiceover", section.get("text", ""))
        # Use on_screen_text if available, else fallback to voice_text
        highlight = section.get("on_screen_text", voice_text)
        
        if not voice_text:
            print(f"Section {i} has no voiceover/text.")
            continue
            
        filename = f"section_{i}.mp3"
        filepath = os.path.join(audio_dir, filename)
        
        # Async run wrapper
        try:
            print(f"Generating {filename}...")
            # Unpack tuple
            out_path, timestamps = asyncio.run(generate_voiceover(voice_text, filepath, script_type=script_type))
            results.append({
                "index": i,
                "text": highlight, 
                "voiceover_text": voice_text, 
                "audio_path": filepath,
                "timestamps": timestamps, # New detailed timing
                "duration_est": section.get("duration_seconds", 5) 
            })
            print(f"Generated {filename}")
        except Exception as e:
            print(f"Error generating voice for section {i}: {e}")
            
    print(f"Total audio clips generated: {len(results)}")
    return results
