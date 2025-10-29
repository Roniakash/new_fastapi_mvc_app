import json
import webbrowser
import tempfile
import os
import time
import sys
import datetime
import pygame
import difflib
from gtts import gTTS
import threading
import speech_recognition as sr
from fastapi import FastAPI, Form
from fastapi.responses import JSONResponse
import asyncio
import websockets
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# -----------------------------------------
# CONFIG
# -----------------------------------------
ASSISTANT_NAME = "Oxland"
COMPANY_NAME = "Oxbow Intellect Private Limited"
MODULES_FILE = "modules_routes.json"

app = FastAPI(title="Oxland Socket Voice Server")


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


recognizer = sr.Recognizer()


# -----------------------------------------
# CORE FUNCTIONS For Voice Assistant
# -----------------------------------------
def speak_and_print(text: str):
    """Speak out loud and print to console safely (English only)."""
    print(f"Assistant: {text}")
    try:
        tts = gTTS(text=text, lang="en")
        fd, path = tempfile.mkstemp(suffix=".mp3")
        os.close(fd)
        tts.save(path)

        pygame.mixer.init()
        pygame.mixer.music.load(path)
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
            time.sleep(0.1)

        pygame.mixer.music.stop()
        pygame.mixer.quit()
        os.remove(path)

    except Exception as e:
        print(f"[TTS error: {e}]")


def listen_once(recognizer: sr.Recognizer, mic: sr.Microphone):
    """Capture voice and return recognized text (waits indefinitely)."""
    with mic as source:
        recognizer.adjust_for_ambient_noise(source, duration=0.8)
        print("(Listening... waiting for user speech)")
        audio = recognizer.listen(source)

    print("(Processing... recognizing speech)")
    try:
        text = recognizer.recognize_google(audio, language="en-US")
        print(f"User: {text}")
        speak_and_print(f"You said: {text}")
        return text
    except sr.UnknownValueError:
        print("Speech not understood.")
        return None
    except sr.RequestError as e:
        print(f"Could not request results from speech service; {e}")
        return None


def get_time_based_greeting():
    """Return time-based greeting in English."""
    hour = datetime.datetime.now().hour
    if 5 <= hour < 12:
        return "Good morning"
    elif 12 <= hour < 15:
        return "Good noon"
    elif 15 <= hour < 18:
        return "Good afternoon"
    else:
        return "Good evening"


def check_identity_question(text: str):
    """Check if user asked about assistant or company."""
    if not text:
        return None
    t = text.lower()
    if "your name" in t or "assistant name" in t or "who are you" in t:
        return f"My name is {ASSISTANT_NAME}."
    if "company" in t or "which company" in t:
        return f"I work at {COMPANY_NAME}."
    return None


def match_tab(user_text, tab_names):
    """Fuzzy match user speech to a tab name."""
    if not user_text:
        return None
    user_text = user_text.lower()

    for name in tab_names:
        if name.lower() in user_text or user_text in name.lower():
            return name

    matches = difflib.get_close_matches(user_text, [t.lower() for t in tab_names], n=1, cutoff=0.6)
    if matches:
        for name in tab_names:
            if name.lower() == matches[0]:
                return name
    return None


def get_datetime_response():
    """Return date and time in English."""
    now = datetime.datetime.now()
    date_str = now.strftime("%A, %d %B %Y")
    time_str = now.strftime("%I:%M %p")
    return f"Today's date is {date_str}, and the current time is {time_str}."


# -----------------------------------------
# PLACE DETECTION FUNCTIONS
# -----------------------------------------
def detect_place_name(text: str):
    """Detect and return the place name mentioned in text."""
    if not text:
        return None

    text_lower = text.lower()
    keywords = ["go to", "navigate to", "open", "show", "location", "place", "map", "take me to"]

    if any(word in text_lower for word in keywords):
        words = text.split()
        place = None

        # Extract after prepositions
        for i, w in enumerate(words):
            if w.lower() in ["to", "in", "at", "of", "for"]:
                place = " ".join(words[i + 1:]).strip()
                break

        # Fallback – handle phrases like "show Delhi map"
        if not place:
            for word in keywords:
                if word in text_lower:
                    place = text_lower.replace(word, "").replace("map", "").strip()
                    break

        if place:
            return place.title()

    return None


# -----------------------------------------
# MAIN ASSISTANT LOGIC
# -----------------------------------------
def run_assistant(user_name: str):
    """Main assistant function (runs in a background thread)."""
    try:
        with open(MODULES_FILE, "r", encoding="utf-8") as f:
            modules = json.load(f)
    except Exception as e:
        print(f"Error loading modules file: {e}")
        return

    recognizer = sr.Recognizer()
    mic = sr.Microphone()

    greet = get_time_based_greeting()
    speak_and_print(f"{greet}, {user_name}! Welcome to Oxland.")
    speak_and_print("Now you can select a tab.")

    tab_names = list(modules.keys())
    print("Available Tabs:", ", ".join(tab_names))

    selected_tab = None
    while not selected_tab:
        response = listen_once(recognizer, mic)
        if not response:
            continue

        if "exit" in response.lower() or "quit" in response.lower():
            speak_and_print("Okay, exiting now. Goodbye!")
            sys.exit(0)

        if "my name" in response.lower():
            speak_and_print(f"Your name is {user_name}.")
            continue

        if any(word in response.lower() for word in ["time", "date", "day"]):
            speak_and_print(get_datetime_response())
            continue

        identity_answer = check_identity_question(response)
        if identity_answer:
            speak_and_print(identity_answer)
            continue

        selected_tab = match_tab(response, tab_names)
        if not selected_tab:
            speak_and_print("I didn't match that to any tab. Please say again.")

    url = modules.get(selected_tab)
    if url:
        speak_and_print("Opening the tab. Exiting. Goodbye!")
        print(f"Opening tab '{selected_tab}' -> {url}")
        webbrowser.open(url)
    else:
        speak_and_print("Sorry, I couldn't find that tab. Exiting.")


def run_location_assistant(user_name: str):
    recognizer = sr.Recognizer()
    mic = sr.Microphone()

    greet = get_time_based_greeting()
    speak_and_print(f"{greet}, {user_name}! Welcome to Oxland.")
    speak_and_print("Now you can select a location.")

    selected_location = None
    while not selected_location:
        response = listen_once(recognizer, mic)
        if not response:
            continue
        
        if "exit" in response.lower() or "quit" in response.lower():
            speak_and_print("Okay, exiting now. Goodbye!")
            sys.exit(0)

        if "my name" in response.lower():
            speak_and_print(f"Your name is {user_name}.")
            continue

        if any(word in response.lower() for word in ["time", "date", "day"]):
            speak_and_print(get_datetime_response())
            continue

        identity_answer = check_identity_question(response)
        if identity_answer:
            speak_and_print(identity_answer)
            continue

        location = listen_once(recognizer, mic)
        if not location:
            speak_and_print("Sorry, I didn't catch that.")
            return

    place = detect_place_name(location)
    if place:
        speak_and_print("Opening the tab.")
        print(f"Opening tab '{selected_location}' -> {place}")
    else:
        speak_and_print("Sorry, I couldn't find that tab. Exiting.")

    speak_and_print(f"Selected location: {place}")


# ---------------------------------------------------------
# EXAMPLE route (optional, keep your real routes)
# ---------------------------------------------------------
@app.get("/")
async def root():
    return {"message": "🎤 Oxland Socket Voice Server is running!"}


# ---------------------------------------------------------
# WebSocket handler
# ---------------------------------------------------------
async def handle_audio(websocket):
    print("🎧 New WebSocket client connected!")
    try:
        async for message in websocket:
            print(f"Received {len(message)} bytes of audio data")
    except websockets.exceptions.ConnectionClosed:
        print("❌ Client disconnected.")


# ---------------------------------------------------------
# Start WebSocket server (on port 9000)
# ---------------------------------------------------------
async def start_socket_server():
    print("🚀 Starting Oxland WebSocket server on ws://0.0.0.0:9000")
    async with websockets.serve(handle_audio, "0.0.0.0", 9000):
        await asyncio.Future()  # keeps running forever




@app.post("/Voice_Search")
def start_assistant(user_name: str = Form(...)):
    """Start the voice assistant from the frontend (runs in background)."""
    thread = threading.Thread(target=run_assistant, args=(user_name,))
    thread.start()
    return JSONResponse({
        "status": "started",
        "message": f"Assistant started for {user_name}."
    })


# 🎤 NEW ENDPOINT: LIVE VOICE PLACE DETECTION
@app.post("/Map_Voice_Search")
def start_location_assistant(user_name: str = Form(...)):
    """Start the voice assistant from the frontend (runs in background)."""
    # 🧵 Run detection in background thread (non-blocking)
    thread = threading.Thread(target=run_location_assistant, args=(user_name,))
    thread.start()

    return JSONResponse({
        "status": "started",
        "message": f"🎤 Assistant started for {user_name}."
    })

# ---------------------------------------------------------
# Run both FastAPI (port 8000) and Socket server (port 9000)
# ---------------------------------------------------------
if __name__ == "__main__":
    async def main():
        # Start WebSocket server (port 9000)
        loop = asyncio.get_running_loop()
        loop.create_task(start_socket_server())  # run socket server in background

        # Start FastAPI server (port 8000)
        config = uvicorn.Config(app, host="0.0.0.0", port=8000, log_level="info")
        server = uvicorn.Server(config)
        await server.serve()

    # ✅ Python 3.11+ compatible way
    asyncio.run(main())




app = FastAPI()




