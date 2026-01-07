import requests
import os
import random
import wikipedia
from app.config import PEXELS_API_KEY, ASSETS_DIR

def download_file(url, folder, filename):
    path = os.path.join(folder, filename)
    if os.path.exists(path):
        return path
    
    try:
        response = requests.get(url, stream=True, headers={'User-Agent': 'EasyMotoBot/1.0'})
        if response.status_code == 200:
            with open(path, 'wb') as f:
                for chunk in response.iter_content(1024):
                    f.write(chunk)
            return path
    except Exception as e:
        print(f"Error downloading {url}: {e}")
    return None

def fetch_wikimedia_images(query, limit=5):
    images = []
    try:
        results = wikipedia.search(query)
        if results:
            page = wikipedia.page(results[0], auto_suggest=False)
            for img in page.images:
                lower_img = img.lower()
                if lower_img.endswith(('.jpg', '.jpeg', '.png')) and 'svg' not in lower_img:
                    images.append(img)
                    if len(images) >= limit: break
    except Exception as e:
        print(f"Wikimedia fetch error: {e}")
    return images

def fetch_stock_media(query, orientation="landscape", limit=3, duration_min=4):
    """
    Fetches video URLs from Pexels.
    """
    if not PEXELS_API_KEY:
        print("Pexels API Key missing.")
        return []

    headers = {"Authorization": PEXELS_API_KEY}
    url = f"https://api.pexels.com/videos/search?query={query}&per_page={limit}&orientation={orientation}"
    
    try:
        response = requests.get(url, headers=headers)
        data = response.json()
        videos = []
        for vid in data.get("videos", []):
            files = vid.get("video_files", [])
            files.sort(key=lambda x: x["width"], reverse=True)
            if files:
                videos.append(files[0]["link"])
        return videos
    except Exception as e:
        print(f"Error fetching Pexels media: {e}")
        return []

def get_media_for_script(script_sections, run_id, script_type="long"):
    media_map = {}
    orientation = "portrait" if script_type == "shorts" else "landscape"
    
    # Create temp download dir for this run
    temp_dir = os.path.join(ASSETS_DIR, "temp_media", run_id)
    os.makedirs(temp_dir, exist_ok=True)

    for i, section in enumerate(script_sections):
        keywords = section.get("visual_keywords", "motorbike")
        
        saved_paths = []
        
        # 1. Try Wikimedia for specific parts/technical/bike name queries
        is_technical = any(x in keywords.lower() for x in ['engine', 'meter', 'spec', 'brake', 'suspension', 'parts'])
        if is_technical:
            wiki_urls = fetch_wikimedia_images(keywords)
            for j, url in enumerate(wiki_urls):
                filename = f"wiki_s{i}_{j}.jpg"
                lp = download_file(url, temp_dir, filename)
                if lp: saved_paths.append(lp)
        
        # 2. Add Pexels video. STRICT RULE: Prioritize specific matches.
        # User Rule: "Better to use the images than to use random video. if the specific topic model video is not found, we can use the images and add zoomin effects there."
        # This means: Don't fall back to "motorbike" videos if query is "Yamaha R15".
        
        # We assume 'keywords' is the specific query from the prompt.
        # Try fetching videos.
        vid_urls = fetch_stock_media(keywords, orientation=orientation, limit=2)
        
        # If videos found, use them (assuming stock search returned decent matches for query)
        for j, url in enumerate(vid_urls):
            filename = f"pex_s{i}_{j}.mp4"
            lp = download_file(url, temp_dir, filename)
            if lp: saved_paths.append(lp)
            
        # If we have NO media (images or videos) yet, OR only 1 video:
        # Increase Wikimedia search aggressively.
        if len(saved_paths) < 2:
            print(f"Low media count for {keywords}, prioritizing images over random video.")
            wiki_urls = fetch_wikimedia_images(keywords, limit=5)
            for j, url in enumerate(wiki_urls):
                filename = f"wiki_strict_s{i}_{j}.jpg"
                lp = download_file(url, temp_dir, filename)
                if lp: saved_paths.append(lp)
                
        # Fallback: If STILL empty, check if we haven't tried Wikimedia yet (technical check skipped it earlier?)
        # Just ensures we don't return empty list if possible.
        if not saved_paths:
             print("No specific media found. Trying split keywords.")
             # Last ditch: Split keywords? No, stay strict. Black screen or single image preferred over wrong video.
             pass
             print("No specific media found. Trying fallback to Wikimedia for keywords again.")
             wiki_urls = fetch_wikimedia_images(keywords) # Try again purely for images
             for j, url in enumerate(wiki_urls):
                 filename = f"fallback_wiki_s{i}_{j}.jpg"
                 lp = download_file(url, temp_dir, filename)
                 if lp: saved_paths.append(lp)
                 
        media_map[i] = saved_paths
    
    return media_map
