
import os
import sys
import asyncio
from app.video.composer import assemble_video
from app.config import ASSETS_DIR, SHORTS_SIZE
from app.media.fetcher import get_media_for_script

# Mock Script
SCRIPT = [
    {
        "index": 0,
        "visual_keywords": "Kawasaki Ninja H2 speed",
        "text": "The Kawasaki Ninja H2 is a beast of speed!",
        "voiceover_text": "The Kawasaki Ninja H2 is a beast of speed!"
    },
    {
        "index": 1,
        "visual_keywords": "motorcycle supercharger engine",
        "text": "Its supercharger makes it faster than a jet.",
        "voiceover_text": "Its supercharger makes it faster than a jet."
    }
]

async def main():
    print("Generating New Shorts Test (Strict Media)...")
    
    # 1. Audio
    # Generate real audio with GuyNeural
    from app.media.voice import generate_voiceover
    audio_data = []
    
    for section in SCRIPT:
        idx = section['index']
        fname = f"test_short_s{idx}.mp3"
        path, stamps = await generate_voiceover(section['voiceover_text'], fname, script_type="shorts")
        audio_data.append({
            "index": idx,
            "audio_path": path,
            "text": section['text'],
            "voiceover_text": section['voiceover_text'],
            "timestamps": stamps
        })
        
    # 2. Media
    # Real fetch to test Strictness
    media_map = get_media_for_script(SCRIPT, "test_run_verify")
    
    # 3. Assemble
    out_file = "final_test_shorts.mp4"
    assemble_video({"title": "Ninja H2"}, media_map, audio_data, out_file, is_shorts=True)
    
    print(f"Done: {out_file}")

if __name__ == "__main__":
    asyncio.run(main())
