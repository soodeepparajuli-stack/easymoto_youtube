import os
import uuid
from app.models import SessionLocal, Script, Video, UploadLog
from app.content.generator import create_daily_scripts
from app.media.fetcher import get_media_for_script
from app.media.voice import create_audio_for_script
from app.video.composer import assemble_video
from app.uploader.youtube import upload_video

def process_script(db, script):
    print(f"Processing script: {script.title} ({script.type})")
    run_id = str(uuid.uuid4())
    
    # 1. Parse content
    content = script.content
    print(f"Script content type: {type(content)}")
    if isinstance(content, str):
        import json
        try:
            content = json.loads(content)
            print("Parsed content from string.")
        except:
            print("Failed to parse content string.")
            
    sections = content.get("sections", [])
    print(f"Found {len(sections)} sections.")
    
    # 2. Fetch Media
    print("Fetching media...")
    media_map = get_media_for_script(sections, run_id, script.type)
    
    # 3. Generate Voice
    print("Generating voiceover...")
    audio_data = create_audio_for_script(sections, run_id, script_type=script.type)
    
    # 4. Assemble Video
    print("Assembling video...")
    output_filename = f"{script.type}_{run_id}.mp4"
    video_path = assemble_video(script.content, media_map, audio_data, output_filename, is_shorts=(script.type == "shorts"))
    
    # 5. Save Video Record
    print(f"Video created at: {video_path}")
    video_record = Video(script_id=script.id, filepath=video_path)
    db.add(video_record)
    db.commit()
    
    # 6. Upload
    from app import config
    if not config.DRY_RUN:
        print("Uploading to YouTube...")
        tags = content.get("keywords", [])
        vid_id = upload_video(video_path, content.get("title"), content.get("description"), tags)
        
        if vid_id:
            log = UploadLog(video_id=video_record.id, youtube_id=vid_id, status="success")
            db.add(log)
            db.commit()
            print(f"Uploaded successfully: https://youtu.be/{vid_id}")
        else:
            print("Upload skipped or failed.")
    else:
        print("DRY RUN: Upload skipped.")
        
    # 7. Cleanup
    cleanup_run_artifacts(run_id)

def cleanup_run_artifacts(run_id):
    """
    Removes temporary assets for a specific run.
    """
    import shutil
    from app.config import ASSETS_DIR
    
    print(f"Cleaning up artifacts for run {run_id}...")
    
    # Paths to clean
    # Audio: assets/temp_audio/{run_id}
    audio_path = os.path.join(ASSETS_DIR, "temp_audio", run_id)
    # Media: assets/temp_media/{run_id}
    media_path = os.path.join(ASSETS_DIR, "temp_media", run_id)
    
    try:
        if os.path.exists(audio_path):
            shutil.rmtree(audio_path)
            print(f"Removed audio temp: {audio_path}")
        if os.path.exists(media_path):
            shutil.rmtree(media_path)
            print(f"Removed media temp: {media_path}")
    except Exception as e:
        print(f"Cleanup failed (non-critical): {e}")

def run_daily_job(target_type="all"):
    # 1. Generate Scripts
    create_daily_scripts(target_type=target_type)
    
    # 2. Process New Scripts
    db = SessionLocal()
    try:
        # Find scripts that don't have a linked video yet
        query = db.query(Script).outerjoin(Video).filter(Video.id == None)
        
        if target_type != "all":
            query = query.filter(Script.type == target_type)
            
        pending_scripts = query.all()
        
        for script in pending_scripts:
            try:
                process_script(db, script)
            except Exception as e:
                print(f"Failed to process script {script.id}: {e}")
                
    finally:
        db.close()

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--type", type=str, default="all", choices=["all", "long", "shorts"], help="Type of video to generate")
    parser.add_argument("--dry-run", action="store_true", help="Skip upload")
    args = parser.parse_args()
    
    # Propagate DRY_RUN via config module modification or env argument?
    # Config reads env var.
    # But dry_run arg is handled inside process_script via config.DRY_RUN check.
    # We should update config.DRY_RUN or rely on process_script checking logic?
    # process_script checks 'config.DRY_RUN' on line 49.
    # We need to monkeypatch or set environment var?
    # Easiest: Monkeypatch since we are in main execution.
    from app import config
    if args.dry_run:
        config.DRY_RUN = True
        
    run_daily_job(target_type=args.type)
