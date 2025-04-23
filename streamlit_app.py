import streamlit as st
import requests
import json
import os
from elevenlabs import generate, set_api_key, play, Voice, VoiceSettings
from dotenv import load_dotenv
import time
import speech_recognition as sr
import tempfile
import sounddevice as sd
import soundfile as sf
import numpy as np

# Load environment variables
load_dotenv()

# API Configuration
API_URL = "https://hack-dubai.onrender.com"

# Initialize ElevenLabs
try:
    elevenlabs_key = "sk_6c840a3af881081d5a6439c98f4ff287526a62ccecab3fd4"
    if not elevenlabs_key:
        st.warning("⚠️ ElevenLabs API key not found. Please set the ELEVENLABS_API_KEY environment variable.")
    else:
        set_api_key(elevenlabs_key)
except Exception as e:
    st.error(f"Error setting up ElevenLabs: {e}")

# Initialize session state
if 'conversation_state' not in st.session_state:
    st.session_state.conversation_state = None
if 'messages' not in st.session_state:
    st.session_state.messages = []
if 'last_message_time' not in st.session_state:
    st.session_state.last_message_time = 0
if 'audio_playing' not in st.session_state:
    st.session_state.audio_playing = False
if 'show_response' not in st.session_state:
    st.session_state.show_response = False

def transcribe_audio(audio_file):
    try:
        # Initialize recognizer
        recognizer = sr.Recognizer()
        
        # Read the audio file
        with sr.AudioFile(audio_file) as source:
            audio = recognizer.record(source)
            
        # Transcribe the audio
        text = recognizer.recognize_google(audio)
        
        # Clean up the temporary file
        os.unlink(audio_file)
        
        return text
    except Exception as e:
        st.error(f"Error transcribing audio: {e}")
        return None

def play_audio(text):
    try:
        # Configure voice settings for faster, more natural speech
        voice = Voice(
            voice_id="21m00Tcm4TlvDq8ikWAM",  # Rachel's voice ID
            settings=VoiceSettings(
                stability=0.5,
                similarity_boost=0.75,
                style=0.0,
                use_speaker_boost=True,
                speed=1.2  # Increase speed by 20%
            )
        )
        
        # Generate audio using ElevenLabs
        audio = generate(
            text=text,
            voice=voice,
            model="eleven_monolingual_v1"
        )
        
        # Save to temporary file
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as temp_file:
            temp_file.write(audio)
            temp_file.flush()
            
        # Play the audio file
        os.system(f"afplay {temp_file.name}")
        
        # Clean up
        os.unlink(temp_file.name)
        
    except Exception as e:
        if "Invalid API key" in str(e):
            st.error("❌ Invalid ElevenLabs API key. Please check your ELEVENLABS_API_KEY environment variable.")
        else:
            st.error(f"Error playing audio: {e}")

def display_travel_options(options):
    if options:
        st.subheader("Travel Options")
        
        if "flights" in options:
            st.write("### Flights")
            for flight in options["flights"]:
                st.write(f"**{flight['airline']}** - {flight['flight_number']}")
                st.write(f"From: {flight['departure_airport']} at {flight['departure_time']}")
                st.write(f"To: {flight['arrival_airport']} at {flight['arrival_time']}")
                st.write(f"Price: {flight['price']} {flight['currency']}")
                st.write("---")
        
        if "hotels" in options:
            st.write("### Hotels")
            for hotel in options["hotels"]:
                st.write(f"**{hotel['name']}** - {hotel['rating']}★")
                st.write(f"Location: {hotel['location']}")
                st.write(f"Price per night: {hotel['price_per_night']} {hotel['currency']}")
                st.write(f"Room Type: {hotel['room_type']}")
                st.write("---")

def display_itinerary(itinerary):
    if itinerary:
        st.subheader("Your Itinerary")
        for day in itinerary:
            st.write(f"### Day {day['day']} - {day['date']}")
            st.write(f"**Summary:** {day['summary']}")
            
            if day['weather']:
                st.write("**Weather:**")
                st.write(f"Temperature: {day['weather']['temperature']}°C")
                st.write(f"Condition: {day['weather']['condition']}")
            
            st.write("**Activities:**")
            for activity in day['activities']:
                st.write(f"**{activity['time']}** - {activity['activity']}")
                st.write(f"Location: {activity['location']}")
                st.write(f"Duration: {activity['duration']}")
                if activity.get('price'):
                    st.write(f"Price: {activity['price']} AED")
                st.write("---")

def record_audio():
    """Record audio until 2 seconds of silence"""
    fs = 44100  # Sample rate
    recording = []
    silence_threshold = 0.01  # Adjust this value based on your microphone sensitivity
    silence_duration = 0
    max_silence = 2  # seconds of silence before stopping
    
    def callback(indata, frames, time, status):
        nonlocal silence_duration
        if status:
            print(status)
        
        # Check for silence
        volume_norm = np.linalg.norm(indata) / len(indata)
        if volume_norm < silence_threshold:
            silence_duration += frames / fs
        else:
            silence_duration = 0
        
        recording.append(indata.copy())
    
    st.write("Recording... Speak now")
    
    # Start recording
    stream = sd.InputStream(
        samplerate=fs,
        channels=1,
        callback=callback
    )
    
    stream.start()
    
    # Wait for silence
    while silence_duration < max_silence:
        time.sleep(0.1)
    
    # Stop recording
    stream.stop()
    stream.close()
    
    st.write("Recording finished")
    
    # Convert recording to numpy array
    recording = np.concatenate(recording, axis=0)
    
    # Save to temporary file
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
        sf.write(temp_file.name, recording, fs)
        return temp_file.name

# Streamlit UI
st.title("Voice Travel Assistant")

# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])
        if message.get("travel_options"):
            display_travel_options(message["travel_options"])
        if message.get("itinerary"):
            display_itinerary(message["itinerary"])

# Add record button
if st.button("🎤 Start Recording"):
    audio_file = record_audio()
    prompt = transcribe_audio(audio_file)
    
    if prompt:
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.write(prompt)

        # Prepare request payload
        payload = {
            "message": prompt,
            "conversation_state": st.session_state.conversation_state
        }

        try:
            # Show loading spinner while waiting for response
            with st.spinner("Generating response..."):
                # Make API call
                response = requests.post(f"{API_URL}/api/chat", json=payload)
                response_data = response.json()

                # Update conversation state
                st.session_state.conversation_state = response_data["updated_conversation_state"]

                # Add timestamp to track the most recent message
                current_time = time.time()
                st.session_state.last_message_time = current_time

                # Reset show response flag
                st.session_state.show_response = False

                # Play audio response
                play_audio(response_data["text_response"])

                # Add assistant response to chat history
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": response_data["text_response"],
                    "timestamp": current_time,
                    "travel_options": response_data.get("travel_options"),
                    "itinerary": response_data.get("itinerary")
                })
                
                # Display assistant response
                with st.chat_message("assistant"):
                    st.write(response_data["text_response"])
                    
                    # Display travel options if available
                    if response_data.get("travel_options"):
                        display_travel_options(response_data["travel_options"])
                    
                    # Display itinerary if available
                    if response_data.get("itinerary"):
                        display_itinerary(response_data["itinerary"])

        except Exception as e:
            st.error(f"Error: {str(e)}")

# Add clear chat button
if st.button("Clear Chat"):
    st.session_state.messages = []
    st.session_state.conversation_state = None
    st.session_state.last_message_time = 0
    st.session_state.audio_playing = False
    st.session_state.show_response = False
    st.rerun()
