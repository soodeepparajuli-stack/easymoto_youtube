
import os
import sys
import asyncio
from app.video.composer import assemble_video
from app.media.fetcher import get_media_for_script
from app.media.voice import generate_voiceover

# 1. Shorts Script (Hayabusa)
SCRIPT_SHORT = [
    {
        "index": 0,
        "visual_keywords": "Suzuki Hayabusa speed",
        "text": "The Suzuki Hayabusa is a legend of speed!",
        "voiceover_text": "The Suzuki Hayabusa is a legend of speed!"
    },
    {
        "index": 1,
        "visual_keywords": "Hayabusa instrument cluster speedometer",
        "text": "It was the first bike to break the 300 kmh barrier.",
        "voiceover_text": "It was the first bike to break the 300 kilometers per hour barrier."
    }
]

# 2. Long Script (Honda Super Cub)
SCRIPT_LONG = [
    {
        "index": 0,
        "visual_keywords": "Honda Super Cub classic",
        "text": "This is the Honda Super Cub. The most produced motor vehicle in history.",
        "voiceover_text": "This is the Honda Super Cub. The most produced motor vehicle in history."
    },
    {
        "index": 1,
        "visual_keywords": "Soichiro Honda portrait",
        "text": "Designed by Soichiro Honda, it changed the world of transport.",
        "voiceover_text": "Designed by Soichiro Honda, it changed the world of transport forever."
    },
    {
        "index": 2,
        "visual_keywords": "Honda Super Cub riding countryside",
        "text": "Reliable, efficient, and iconic. It is a masterpiece.",
        "voiceover_text": "Reliable, efficient, and iconic. It is truly a masterpiece of engineering."
    }
]

async def generate_video(script, title, is_shorts):
    print(f"--- Generating {title} ({'Shorts' if is_shorts else 'Long'}) ---")
    
    # Audio
    audio_data = []
    print("Generating Audio...")
    for section in script:
        idx = section['index']
        # Unique filenames
        fname = f"verif_{'short' if is_shorts else 'long'}_s{idx}.mp3"
        # Generate with GuyNeural (default in voice.py)
        path, stamps = await generate_voiceover(
            section['voiceover_text'], 
            fname, 
            script_type="shorts" if is_shorts else "long"
        )
        audio_data.append({
            "index": idx,
            "audio_path": path,
            "text": section['text'],
            "voiceover_text": section['voiceover_text'],
            "timestamps": stamps
        })
        
    # Media
    print("Fetching Media...")
    run_id = f"verif_{'short' if is_shorts else 'long'}"
    media_map = get_media_for_script(script, run_id, script_type="shorts" if is_shorts else "long")
    
    # Assemble
    print("Assembling Video...")
    out_file = f"final_verified_{'short' if is_shorts else 'long'}.mp4"
    assemble_video(
        {"title": title}, 
        media_map, 
        audio_data, 
        out_file, 
        is_shorts=is_shorts
    )
    print(f"Completed: {out_file}")
    return out_file

async def main():
    # Generate Short
    await generate_video(SCRIPT_SHORT, "Hayabusa Legend", True)
    
    # Generate Long
    await generate_video(SCRIPT_LONG, "Honda Cub History", False)

if __name__ == "__main__":
    asyncio.run(main())
