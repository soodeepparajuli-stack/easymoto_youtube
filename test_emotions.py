
import asyncio
import edge_tts
import os

async def test_emotions():
    voice = "en-US-BrianNeural" # Typically supports styles
    
    # Define SSML with emotions using MINIMAL header (verified to not read header)
    # Styles: cheerful, excited, hopeful (wonder?)
    ssml_text = (
        "<speak>"
        "I am speaking in my normal, calm voice. "
        "<break time='600ms'/>"
        "<mstts:express-as style='cheerful'>"
        "Now I am speaking with happiness and cheer!"
        "</mstts:express-as>"
        "<break time='600ms'/>"
        "<mstts:express-as style='excited'>"
        "And now I am super excited and energetic!"
        "</mstts:express-as>"
        "<break time='600ms'/>"
        "<mstts:express-as style='hopeful'>"
        "I wonder what is out there in the vast universe?"
        "</mstts:express-as>"
        "</speak>"
    )
    
    print("Generating emotion sample with SSML...")
    output = "emotion_ssml_test.mp3"
    comm = edge_tts.Communicate(ssml_text, voice)
    await comm.save(output)
    
    if os.path.exists(output):
        print(f"Generated: {output}")
        print(f"Size: {os.path.getsize(output)} bytes")
    else:
        print("Failed to generate.")

if __name__ == "__main__":
    asyncio.run(test_emotions())
