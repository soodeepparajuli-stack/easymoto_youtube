import google.generativeai as genai
import json
import os
import random
from datetime import datetime, timedelta
from groq import Groq
from app.config import GEMINI_API_KEY, GROQ_API_KEY
from app.content.prompts import LONG_FORM_PROMPT_TEMPLATE, SHORTS_PROMPT_TEMPLATE
from app.content.research import get_research_context
from app.models import SessionLocal, Bike, Script
from sqlalchemy.orm import Session

genai.configure(api_key=GEMINI_API_KEY)
groq_client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None

# Fallback topics (Bikes & Cars)
DEFAULT_TOPICS = [
    # Bikes
    {"make": "Yamaha", "model": "R15 V4", "category": "Sport", "type": "Motorbike"},
    {"make": "Royal Enfield", "model": "Classic 350", "category": "Cruiser", "type": "Motorbike"},
    {"make": "Honda", "model": "Dio", "category": "Scooter", "type": "Motorbike"},
    {"make": "TVS", "model": "Apache RTR 200", "category": "Naked", "type": "Motorbike"},
    # Cars
    {"make": "Nissan", "model": "GT-R R35", "category": "Supercar", "type": "Car"},
    {"make": "Toyota", "model": "Supra MK4", "category": "Sports Car", "type": "Car"},
    {"make": "Ford", "model": "Mustang GT", "category": "Muscle Car", "type": "Car"},
    {"make": "Porsche", "model": "911 GT3 RS", "category": "Supercar", "type": "Car"}
]

CONTENT_TYPES = [
    "Feature Breakdown",
    "Origin & History",
    "Comparison",
    "Ownership & Maintenance",
    "Explainer / Education"
]

def seed_bikes(db: Session):
    if db.query(Bike).count() == 0:
        for b_data in DEFAULT_TOPICS:
            # We store type in category for now to avoid schema migration during run
            # e.g. category="Car | Supercar"
            cat_str = f"{b_data['type']} | {b_data['category']}"
            bike = Bike(make=b_data["make"], model=b_data["model"], category=cat_str, specifications={})
            db.add(bike)
        db.commit()

def get_next_topic(db: Session):
    # Simple round-robin or least recently used
    seed_bikes(db)
    bike = db.query(Bike).order_by(Bike.last_featured_date.asc()).first()
    return bike

def get_todays_content_type():
    # Rotate based on day of year to ensure consistency across restarts
    day_of_year = datetime.now().timetuple().tm_yday
    return CONTENT_TYPES[day_of_year % len(CONTENT_TYPES)]

def generate_with_groq(prompt):
    if not groq_client:
        raise Exception("Groq API Key not found")
    
    chat_completion = groq_client.chat.completions.create(
        messages=[
            {
                "role": "user",
                "content": prompt,
            }
        ],
        model="llama-3.3-70b-versatile",
    )
    return chat_completion.choices[0].message.content

def generate_script(bike_model: str, script_type="long", content_type="General") -> dict:
    # 1. Gather Context
    research_summary = get_research_context(bike_model)
    
    # 2. Prepare Prompt
    if script_type == "long":
        prompt = LONG_FORM_PROMPT_TEMPLATE.format(
            topic=bike_model,
            content_type=content_type,
            research_context=research_summary
        )
    else:
        prompt = SHORTS_PROMPT_TEMPLATE.format(
            topic=bike_model,
            research_context=research_summary
        )
    
    prompt += "\n\nCRITICAL: Return ONLY valid JSON."

    data = None
    
    # Attempt 1: Gemini
    try:
        print("Attempting generation with Gemini...")
        # Trying gemini-2.0-flash-exp as 1.5-flash was 404
        model = genai.GenerativeModel('gemini-2.0-flash-exp')
        response = model.generate_content(prompt)
        text = response.text.replace('```json', '').replace('```', '').strip()
        data = json.loads(text)
        return data
    except Exception as e:
        print(f"Gemini generation failed: {e}")
    
    # Attempt 2: Groq
    if not data:
        try:
            print("Attempting generation with Groq (Llama3)...")
            text = generate_with_groq(prompt)
            # Clean up potential markdown code blocks from Llama
            text = text.replace('```json', '').replace('```', '').strip()
            # Find JSON start/end if extra text exists
            if '{' in text:
                text = text[text.find('{'):text.rfind('}')+1]
            data = json.loads(text)
            return data
        except Exception as e:
             print(f"Groq generation failed: {e}")

    if not data:
        raise Exception("Failed to generate script from both Gemini and Groq.")

def create_daily_scripts(target_type="all"):
    print(f"Starting create_daily_scripts (target={target_type})...")
    db = SessionLocal()
    try:
        bike = get_next_topic(db)
        if not bike:
            print("No bikes found.")
            return

        topic_name = f"{bike.make} {bike.model}"
        content_type = get_todays_content_type()
        
        print(f"Generating content for: {topic_name} (Type: {content_type})")

        # Generate Long Form
        if target_type in ["all", "long"]:
            long_script_data = generate_script(topic_name, "long", content_type)
            print(f"Long script title: {long_script_data.get('title')}")
            if long_script_data:
                script_entry = Script(bike_id=bike.id, type="long", title=long_script_data.get("title"), content=long_script_data)
                db.add(script_entry)
                print("Added long script to session.")
        
        # Generate Shorts
        if target_type in ["all", "shorts"]:
            short_script_data = generate_script(topic_name, "shorts")
            if short_script_data:
                script_entry = Script(bike_id=bike.id, type="shorts", title=short_script_data.get("title"), content=short_script_data)
                db.add(script_entry)
                print("Added shorts script to session.")

        # Update bike timestamp
        bike.last_featured_date = datetime.utcnow()
        db.commit()
        print("Scripts saved to database.")

    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"Error in create_daily_scripts: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    from datetime import datetime
    create_daily_scripts()
