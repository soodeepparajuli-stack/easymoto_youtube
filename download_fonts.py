
import os
import requests

def download_file(url, filepath):
    print(f"Downloading {url} to {filepath}...")
    try:
        r = requests.get(url)
        r.raise_for_status()
        with open(filepath, 'wb') as f:
            f.write(r.content)
        print("Done.")
    except Exception as e:
        print(f"Failed: {e}")

def main():
    fonts_dir = os.path.join("assets", "fonts")
    os.makedirs(fonts_dir, exist_ok=True)
    
    fonts = {
        "Montserrat-Black.ttf": "https://raw.githubusercontent.com/JulietaUla/Montserrat/master/fonts/ttf/Montserrat-Black.ttf",
        "TheBoldFont.ttf": "https://dl.dafont.com/dl/?f=the_bold_font"
    }
    
    for name, url in fonts.items():
        download_file(url, os.path.join(fonts_dir, name))

if __name__ == "__main__":
    main()
