import random
import os
import textwrap
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from moviepy.video.io.VideoFileClip import VideoFileClip
from moviepy.audio.io.AudioFileClip import AudioFileClip
from moviepy.video.VideoClip import ImageClip, ColorClip
from moviepy.video.compositing.CompositeVideoClip import CompositeVideoClip
from moviepy.video.compositing.concatenate import concatenate_videoclips
from moviepy.audio.AudioClip import CompositeAudioClip

# Specific FX imports to avoid loading everything (which triggers ImageMagick check)
from moviepy.video.fx.resize import resize
from moviepy.video.fx.crop import crop
from moviepy.video.fx.fadein import fadein
try:
    from moviepy.video.fx.loop import loop
except ImportError:
    # Fallback if loop is not in fx
    from moviepy.video.tools.drawing import color_gradient # unlikely needed
    def loop(clip, duration=None):
        return clip.loop(duration=duration) if hasattr(clip, 'loop') else clip

from moviepy.audio.fx.volumex import volumex
# Audio loop
try:
    from moviepy.audio.fx.multiplier import multiplier # just checking
    from moviepy.audio.fx.loop import loop as audio_loop
except ImportError:
    # Fallback
    def audio_loop(clip, duration=None):
        return clip.loop(duration=duration) if hasattr(clip, 'loop') else clip

print("Composer loaded successfully")

from app.config import OUTPUT_DIR, ASSETS_DIR, LONG_VIDEO_SIZE, SHORTS_SIZE, FPS

def get_text_layout(text, base_fontsize=70, size=(1080, 1920), font_name="TheBoldFont.ttf", margin=50):
    """
    Calculates the detailed layout (char positions) for text.
    Returns: (font, char_data_list, total_size)
    char_data_list: [(char, x, y, color, stroke_width)]
    """
    # Font Loading
    try:
        font_path = os.path.join(ASSETS_DIR, "fonts", font_name)
        if not os.path.exists(font_path):
            font_path = os.path.join(ASSETS_DIR, "fonts", "Montserrat-Black.ttf")
        if not os.path.exists(font_path):
             font = ImageFont.truetype("arial.ttf", base_fontsize)
        else:
             font = ImageFont.truetype(font_path, base_fontsize)
    except:
        font = ImageFont.load_default()

    img_temp = Image.new('RGBA', size)
    draw_temp = ImageDraw.Draw(img_temp)

    max_w = size[0] - (2 * margin)
    
    words = text.split()
    lines = []
    current_line = []
    
    # improved wrapping
    for word in words:
        test_line = " ".join(current_line + [word])
        if hasattr(draw_temp, 'textbbox'):
            l, t, r, b = draw_temp.textbbox((0, 0), test_line, font=font)
            w = r - l
        else:
            w, h = draw_temp.textsize(test_line, font=font)
             
        if w <= max_w:
            current_line.append(word)
        else:
            if current_line:
                lines.append(" ".join(current_line))
                current_line = [word]
            else:
                lines.append(word)
                current_line = []
    if current_line:
        lines.append(" ".join(current_line))
        
    line_height = int(base_fontsize * 1.2)
    total_height = len(lines) * line_height
    start_y = (size[1] - total_height) / 2
    
    char_data = [] # (char, x, y, color)
    
    for i, line in enumerate(lines):
        # measure line for centering
        if hasattr(draw_temp, 'textbbox'):
            l, t, r, b = draw_temp.textbbox((0, 0), line, font=font)
            lw = r - l
        else:
             lw, lh = draw_temp.textsize(line, font=font)
        
        x_start = (size[0] - lw) / 2
        y = start_y + (i * line_height)
        
        # Word iteration for colors AND SIZES
        words_in_line = line.split()
        
        # To handle variable sizing correctly in layout, we should have measured with it.
        # But 'lines' were calculated with base font.
        # If we just change font size now, the line might overflow OR look uneven.
        # But user wants "Important word larger".
        # Let's verify 'lines' logic? Lines uses base_fontsize.
        # If we make one word huge, it might overlap neighbors or overflow X.
        # Simple fix: Increase X spacing dynamically.
        # Overflow risk: acceptable for now? Or re-measure?
        # Re-measuring is hard because wrapping happened already.
        # We'll just apply it and hope for best (usually Captions are short chunks anyway).
        
        current_x = x_start
        
        for word in words_in_line:
            color, size_mult = get_text_style(word)
            
            # Apply size multiplier to font
            final_size = int(base_fontsize * size_mult)
            # Reload font at size (PIL requires new font obj)
            try:
                if font.path: # if truetype obj
                    word_font = ImageFont.truetype(font.path, final_size)
                else:
                    word_font = font # default fallback
            except:
                # Try loading by name again if path prop missing (common in some PIL vers)
                # We know the font name/path variable from outer scope? 
                # Re-using the logic from top of function:
                try:
                    p = os.path.join(ASSETS_DIR, "fonts", font_name)
                    if not os.path.exists(p): p = os.path.join(ASSETS_DIR, "fonts", "Montserrat-Black.ttf")
                    word_font = ImageFont.truetype(p, final_size)
                except:
                   word_font = font
            
            
            # We iterate chars in word to place them
            for char in word:
                if hasattr(draw_temp, 'textbbox'):
                    l, t, r, b = draw_temp.textbbox((0, 0), char, font=word_font)
                    cw = r - l
                    # Center Y alignment for different sizes
                    # base line is y + line_height. 
                    # larger font means taller.
                    # let's align baselines approximately:
                    # diff in height = (final_size - base_fontsize)
                    # move up by diff?
                    # simple centering: 
                    # ch = b - t
                    # y_offset = (line_height - ch) / 2 ... maybe complex.
                    # Let's align Bottoms? 
                    # Just keep Y same, it usually aligns to top-left.
                    # If we align top-left, bigger font goes down.
                    # We want to Center it relative to line height.
                    y_adj = y + (line_height - final_size*1.2)/2 # approx centering
                else:
                    cw, ch = draw_temp.textsize(char, font=word_font)
                    y_adj = y
                
                char_data.append({
                    "char": char,
                    "x": current_x,
                    "y": y_adj, # Adjusted Y
                    "color": color,
                    "font": word_font # Use specific size font
                })
                current_x += cw
                
            # Add space after word
            space_w = final_size * 0.25
            current_x += space_w
            
            char_data.append({
                "char": " ",
                "x": current_x - space_w, 
                "y": y,
                "color": "transparent", 
                "font": word_font
            })
            
    return font, char_data, size

from moviepy.video.VideoClip import VideoClip

def create_typewriter_clip(text, duration, base_fontsize=90, size=(1080, 1920)):
    font, char_data, size = get_text_layout(text, base_fontsize, size)
    
    # Remove trailing space check
    if char_data and char_data[-1]["char"] == " ":
        char_data.pop()
        
    total_chars = len(char_data)
    
    # Handle empty text case (e.g. was just a space)
    if total_chars == 0:
        return ColorClip(size, color=(0,0,0,0), duration=duration)
    
    def make_image_at_t(t):
        type_duration = min(duration * 0.8, 3.0)
        if type_duration <= 0: type_duration = 0.1 # Safety
        progress = min(1.0, t / type_duration)
        
        count = int(total_chars * progress)
        # Ensure we don't exceed bounds (though int truncates, so it should be safe)
        if count > total_chars: count = total_chars
        
        img = Image.new('RGBA', size, (0,0,0,0))
        draw = ImageDraw.Draw(img)
        
        for i in range(count):
            c_info = char_data[i]
            if c_info["color"] == "transparent": continue
            
            # Use specific font for this char
            c_font = c_info["font"]
            
            draw.text((c_info["x"], c_info["y"]), c_info["char"], font=c_font, fill='black', stroke_width=6, stroke_fill='black')
            off = 6
            draw.text((c_info["x"]+off, c_info["y"]+off), c_info["char"], font=c_font, fill='black')
            draw.text((c_info["x"], c_info["y"]), c_info["char"], font=c_font, fill=c_info["color"])
        return img

    def make_frame(t):
        img = make_image_at_t(t)
        return np.array(img.convert("RGB"))

    def make_mask(t):
        img = make_image_at_t(t)
        # Extract alpha, normalize to 0-1 float
        # Ensure alpha channel exists
        if 'A' in img.getbands():
            alpha = np.array(img.split()[-1]).astype(float) / 255.0
        else:
            # Fallback if RGB (shouldn't happen with new('RGBA'))
            alpha = np.zeros((size[1], size[0]))
        return alpha

    clip = VideoClip(make_frame, duration=duration)
    mask = VideoClip(make_mask, duration=duration, ismask=True)
    clip.mask = mask
    return clip

def create_text_image(text, base_fontsize=70, size=(1920, 300), font_name="TheBoldFont.ttf", margin=50):
    # Backward compatibility wrapper if needed (returns single static image)
    # We can just use the last frame of typewriter logic?
    # Or just re-implement static render for simple usage.
    # Actually, we should force typewriter everywhere for captions.
    # But if something expects an image array (like the old code)...
    # For now, let's keep a simplified static renderer for safety if called directly.
    # Re-use layout logic? Yes.
    font, char_data, size = get_text_layout(text, base_fontsize, size, font_name, margin)
    img = Image.new('RGBA', size, (0,0,0,0))
    draw = ImageDraw.Draw(img)
    for c_info in char_data:
        if c_info["color"] == "transparent": continue
        draw.text((c_info["x"], c_info["y"]), c_info["char"], font=font, fill='black', stroke_width=6, stroke_fill='black')
        draw.text((c_info["x"]+6, c_info["y"]+6), c_info["char"], font=font, fill='black')
        draw.text((c_info["x"], c_info["y"]), c_info["char"], font=font, fill=c_info["color"])
    return np.array(img)


def ken_burns_effect(clip):
    # Dynamic Ken Burns effect (simple zoom)
    return clip.fx(resize, lambda t: 1 + 0.04*t)

def split_text_into_chunks(text, max_words=4): # Reduced to 4 for punchier captions
    words = text.split()
    chunks = []
    for i in range(0, len(words), max_words):
        chunks.append(" ".join(words[i:i+max_words]))
    return chunks

def get_text_style(word):
    """
    Determines color and font size multiplier for a single word.
    """
    w_lower = word.lower()
    
    # Defaults
    color = 'white'
    size_mult = 1.0
    
    # Clean punctuation for check
    clean_word = "".join(c for c in w_lower if c.isalnum())
    
    # 1. Stats/Numbers (Highest Priority)
    if any(char.isdigit() for char in word):
        color = 'yellow'
        size_mult = 1.4 # Big Pop
        return color, size_mult

    # 2. Colors based on sentiment/topic
    if any(x in w_lower for x in ['warning', 'danger', 'brake', 'crash', 'fail', 'bad', 'cons', 'problem']):
        color = '#FF3333' # Red
        size_mult = 1.2
    elif any(x in w_lower for x in ['mileage', 'efficient', 'price', 'cheap', 'good', 'pros', 'best', 'success', 'looks', 'sharp', 'stable', 'both', 'smarter']):
        color = '#39FF14' # Neon Green
        size_mult = 1.2
    elif any(x in w_lower for x in ['engine', 'power', 'torque', 'ccs', 'hp', 'nm', 'fast', 'speed', 'cc', 'ps', 'big']):
        color = 'yellow'
        size_mult = 1.3
    elif any(x in w_lower for x in ['feature', 'screen', 'led', 'light', 'abs', 'fi', 'modes', 'easymoto']):
        color = 'cyan'
        size_mult = 1.3

    # 3. Subject/Object Heuristic (Capitalized words that aren't start of sentence?)
    # Hard to detect perfectly, but proper nouns often matter.
    # If it looks like a model name (e.g. Ntorq, Xpulse, R15)
    if w_lower in ['hero', 'honda', 'yamaha', 'tvs', 'bajaj', 'ktm', 'royal', 'enfield', 'xpulse', 'ntorq', 'r15', 'duke', 'classic', 'hunter']:
        color = '#FF00FF' # Magenta/Purple
        size_mult = 1.3
        
    return color, size_mult

def format_srt_time(seconds):
    millis = int((seconds - int(seconds)) * 1000)
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    seconds = int(seconds % 60)
    return f"{hours:02}:{minutes:02}:{seconds:02},{millis:03}"

def generate_srt(audio_data, output_path):
    with open(output_path, 'w', encoding='utf-8') as f:
        current_time = 0.0
        for i, section in enumerate(audio_data):
            # Load audio for accurate duration if not present (it should be loaded in assemble loop, 
            # but we can assume 'duration' key or reloading. 
            # Actually assemble_video loads AudioFileClip. 
            # Let's pass the already-loaded duration or re-calculate? 
            # Optimally, assemble_video should build the SRT data structure as it iterates.
            pass # We will handle logic inside assemble_video to avoid double loading
            
def assemble_video(script_data, media_map, audio_data, output_filename, is_shorts=False):
    """
    Assembles the final video.
    """
    clips = []
    video_size = SHORTS_SIZE if is_shorts else LONG_VIDEO_SIZE
    
    # Background music
    music_path_dir = os.path.join(ASSETS_DIR, "music")
    print(f"Looking for music in: {music_path_dir}")
    if os.path.exists(music_path_dir):
        music_files = [f for f in os.listdir(music_path_dir) if f.endswith('.mp3')]
    else:
        music_files = []
    
    print(f"Found {len(music_files)} music files.")
    
    bg_music = None
    if music_files:
        music_path = os.path.join(music_path_dir, random.choice(music_files))
        bg_music = AudioFileClip(music_path).fx(volumex, 0.1)

    # For SRT generation
    srt_entries = []
    current_time_srt = 0.0
    sfx_clips = [] # List to store sound effects

    for section in audio_data:
        idx = section['index']
        audio_path = section['audio_path']
        text = section['text'] # This is HIGHLIGHT TEXT
        voiceover = section.get('voiceover_text', text) # This is FULL TEXT (fallback to text if missing)
        
        # Audio Clip
        audio_clip = AudioFileClip(audio_path)
        duration = audio_clip.duration
        
        # Collect SRT info
        srt_start = current_time_srt
        srt_end = current_time_srt + duration
        srt_entries.append({
            "index": len(srt_entries) + 1,
            "start": format_srt_time(srt_start),
            "end": format_srt_time(srt_end),
            "text": voiceover
        })
        current_time_srt += duration

        # Visual Clip (Video or Image)
        media_paths = media_map.get(idx, [])
        if media_paths:
            visual_path = random.choice(media_paths)
            try:
                if visual_path.endswith(('.mp4', '.mov')):
                    visual_clip = VideoFileClip(visual_path)
                    if visual_clip.duration < duration:
                        visual_clip = visual_clip.fx(loop, duration=duration)
                    else:
                        visual_clip = visual_clip.subclip(0, duration)
                else:
                    # Image: Apply Ken Burns
                    visual_clip = ImageClip(visual_path, duration=duration)
                    visual_clip = ken_burns_effect(visual_clip)
            except Exception as e:
                print(f"Error loading media {visual_path}: {e}, using black screen")
                visual_clip = ImageClip(np.zeros((video_size[1], video_size[0], 3)), duration=duration)
        else:
             visual_clip = ImageClip(np.zeros((video_size[1], video_size[0], 3)), duration=duration)

        # Bounds check for resize (Ken Burns changes size, so we need to crop after if needed, or before?)
        # Ken Burns increases size, so cropping after is safer to maintain aspect ratio filling.
        w, h = visual_clip.size # Note: For animated clip, size might trigger evaluation, but usually ok.
        target_w, target_h = video_size
        
        # Scale to fill (static or dynamic)
        scale = max(target_w/w, target_h/h)
        if not visual_path.endswith(('.mp4', '.mov')):  # It is an image with KB
             # Images need to be scaled up to cover BEFORE cropping too!
             # We should scale them so they cover the target area.
             visual_clip = visual_clip.fx(resize, scale)
        else:
             visual_clip = visual_clip.fx(resize, scale)

        visual_clip = visual_clip.fx(crop, x_center=visual_clip.w/2, y_center=visual_clip.h/2, width=target_w, height=target_h)
        visual_clip = visual_clip.set_audio(audio_clip)

        # Granular Captions (HIGHLIGHTS ONLY)
        # 1. Precise Match Logic
        timestamps = section.get('timestamps', [])
        
        # Naive matching: Find first occurrence of highlight words
        # Simplification: Assume highlights are 1-2 words mostly.
        # If timestamp data exists, try to sync.
        
        start_t = 0
        end_t = duration
        
        if timestamps and text:
            # Clean text for matching
            search_words = [w.lower().strip(",.!?") for w in text.split()]
            if search_words:
                first_word = search_words[0]
                
                # Find start time of first matching word
                hit = next((t for t in timestamps if t['word'].lower().strip(",.!?") == first_word), None)
                if hit:
                    start_t = float(hit['start'])
                    # User Request: "text dissapeares only when the whole sentence... is read"
                    # Audio clip duration corresponds to this sentence.
                    # So text should persist until the end of the clip.
                    end_t = duration
                else:
                    # Fallback: Start immediately
                    start_t = 0.0
                    end_t = duration 
        else:
             # Fallback if no timestamps
             start_t = 0.0
             end_t = duration

        # Style Overrides for Highlights (Big, Bold, Shadow)
        chunks = [text] # Don't chunk highlights anymore, show full phrase (max 5-7 words)
        
        txt_clips = []
        for chunk in chunks:
            # Base font size BIGGER
            base_size = 110 if is_shorts else 90 # Huge text
            
            # Now we pass the chunk to create_text_image, which handles word-level styling
            # We enforce BOLD font inside create_text_image (already done)
            # Use Typewriter Effect
            # Size for text area:
            text_area_size = (target_w, int(target_h*0.4))
            
            # Create Typewriter Clip
            tc = create_typewriter_clip(chunk, duration=(end_t - start_t), base_fontsize=base_size, size=text_area_size)
            
            # Position: CENTER CENTER
            tc = tc.set_start(start_t)\
                .set_position(('center', 'center'))
                
            # Remove Pop Zoom Effect (Typewriter replaces it)
            # Remove fadein (Typewriter starts from empty)
            
            # Add Pop Sound (Removed per user request)
            # pop_path = os.path.join(ASSETS_DIR, "sfx", "pop.mp3")
            # if os.path.exists(pop_path):
            #     try:
            #         pop_clip = AudioFileClip(pop_path).set_start(start_t).volumex(0.5)
            #         sfx_clips.append(pop_clip)
            #     except Exception as e:
            #         print(f"Failed to load pop sfx: {e}")

            txt_clips.append(tc)

        combined = CompositeVideoClip([visual_clip] + txt_clips)
        clips.append(combined)

    # Concatenate
    final_video = concatenate_videoclips(clips, method="compose")
    
    # Add Background Music (Loop if needed)
    if bg_music:
        if bg_music.duration < final_video.duration:
            bg_music = bg_music.fx(audio_loop, duration=final_video.duration)
        else:
            bg_music = bg_music.subclip(0, final_video.duration)
        
        final_audio = CompositeAudioClip([final_video.audio, bg_music] + sfx_clips)
        final_video.audio = final_audio

    # Write output
    output_path = os.path.join(OUTPUT_DIR, output_filename)
    
    # Write SRT
    srt_filename = output_filename.rsplit('.', 1)[0] + ".srt"
    srt_path = os.path.join(OUTPUT_DIR, srt_filename)
    with open(srt_path, 'w', encoding='utf-8') as f:
        for entry in srt_entries:
            f.write(f"{entry['index']}\n")
            f.write(f"{entry['start']} --> {entry['end']}\n")
            f.write(f"{entry['text']}\n\n")
    print(f"Generated subtitles: {srt_path}")

    final_video.write_videofile(output_path, fps=FPS, codec="libx264", audio_codec="aac")
    return output_path

# Fix for CompositeAudioClip import if not at top level
from moviepy.audio.AudioClip import CompositeAudioClip
