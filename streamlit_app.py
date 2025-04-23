import streamlit as st
import requests
import json
import base64
import soundfile as sf
import numpy as np
import io
from datetime import datetime
import os
from elevenlabs import generate, set_api_key, play, Voice, VoiceSettings
from dotenv import load_dotenv
import time
import speech_recognition as sr
from pydub import AudioSegment
import tempfile
import pyaudio
import wave
from gtts import gTTS
import threading
import queue

# Load environment variables
load_dotenv()

# API Configuration
API_URL = "https://hack-dubai.onrender.com"

# Initialize ElevenLabs
try:
    set_api_key(os.getenv("ELEVENLABS_API_KEY"))
    if not os.getenv("ELEVENLABS_API_KEY"):
        raise ValueError("ELEVENLABS_API_KEY environment variable is not set")
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
if 'recording' not in st.session_state:
    st.session_state.recording = False
if 'stop_recording' not in st.session_state:
    st.session_state.stop_recording = False

def record_audio():
    """Record audio from microphone until stopped"""
    CHUNK = 1024
    FORMAT = pyaudio.paInt16
    CHANNELS = 1
    RATE = 44100
    
    p = pyaudio.PyAudio()
    
    stream = p.open(format=FORMAT,
                    channels=CHANNELS,
                    rate=RATE,
                    input=True,
                    frames_per_buffer=CHUNK)
    
    frames = []
    silence_threshold = 500  # Adjust this value based on your microphone sensitivity
    silence_duration = 0
    max_silence = 2  # seconds of silence before stopping
    
    st.write("Recording... Speak now")
    
    while not st.session_state.stop_recording:
        data = stream.read(CHUNK)
        frames.append(data)
        
        # Check for silence
        audio_data = np.frombuffer(data, dtype=np.int16)
        if np.abs(audio_data).mean() < silence_threshold:
            silence_duration += CHUNK / RATE
            if silence_duration > max_silence:
                break
        else:
            silence_duration = 0
    
    st.write("Finished recording")
    
    stream.stop_stream()
    stream.close()
    p.terminate()
    
    # Save the recorded data as a WAV file
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
        wf = wave.open(temp_file.name, 'wb')
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(p.get_sample_size(FORMAT))
        wf.setframerate(RATE)
        wf.writeframes(b''.join(frames))
        wf.close()
        return temp_file.name

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

def generate_and_play_audio(text):
    try:
        if st.session_state.audio_playing:
            return
            
        st.session_state.audio_playing = True
        
        # Configure voice settings
        voice = Voice(
            voice_id="21m00Tcm4TlvDq8ikWAM",  # Rachel's voice ID
            settings=VoiceSettings(
                stability=0.5,
                similarity_boost=0.75,
                style=0.0,
                use_speaker_boost=True
            )
        )
        
        # Generate and play audio using ElevenLabs
        audio = generate(
            text=text,
            voice=voice,
            model="eleven_monolingual_v1"
        )
        
        # Play the audio directly
        play(audio)
        
        # Set flag to show response after audio is done
        st.session_state.show_response = True
        st.session_state.audio_playing = False
    except Exception as e:
        st.error(f"Error playing audio: {e}")
        st.session_state.audio_playing = False
        st.session_state.show_response = True

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

# Add a "Speak" button at the bottom of the chat
if st.button("🎤 Speak", key="speak_button"):
    st.session_state.recording = True
    st.session_state.stop_recording = False
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
    st.session_state.recording = False
    st.session_state.stop_recording = False
    st.rerun() 