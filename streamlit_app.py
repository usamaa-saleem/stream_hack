import streamlit as st
import requests
import json
import os
from elevenlabs import generate, set_api_key, play, Voice, VoiceSettings
from dotenv import load_dotenv
import time

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

def display_travel_options(options):
    if options:
        for flight in options.get("flights", []):
            st.write(f"**Flight:** {flight['airline']} {flight['flight_number']}")
            st.write(f"From: {flight['departure_airport']} at {flight['departure_time']}")
            st.write(f"To: {flight['arrival_airport']} at {flight['arrival_time']}")
            st.write(f"Price: {flight['price']} {flight['currency']}")
            st.write("---")
        
        for hotel in options.get("hotels", []):
            st.write(f"**Hotel:** {hotel['name']} ({hotel['rating']}★)")
            st.write(f"Location: {hotel['location']}")
            st.write(f"Price per night: {hotel['price_per_night']} {hotel['currency']}")
            st.write(f"Room Type: {hotel['room_type']}")
            st.write("---")

def display_itinerary(itinerary):
    if itinerary:
        for day in itinerary:
            st.write(f"**Day {day['day']} - {day['date']}**")
            st.write(f"Summary: {day['summary']}")
            
            if day.get('weather'):
                st.write(f"Weather: {day['weather']['temperature']}°C, {day['weather']['condition']}")
            
            for activity in day['activities']:
                st.write(f"• {activity['time']} - {activity['activity']}")
                st.write(f"  Location: {activity['location']}")
                st.write(f"  Duration: {activity['duration']}")
                if activity.get('price'):
                    st.write(f"  Price: {activity['price']} AED")
            st.write("---")

def generate_and_play_audio(text):
    try:
        if st.session_state.audio_playing:
            return
            
        st.session_state.audio_playing = True
        
        voice = Voice(
            voice_id="21m00Tcm4TlvDq8ikWAM",
            settings=VoiceSettings(
                stability=0.5,
                similarity_boost=0.75,
                style=0.0,
                use_speaker_boost=True
            )
        )
        
        audio = generate(
            text=text,
            voice=voice,
            model="eleven_monolingual_v1"
        )
        
        play(audio)
        
        st.session_state.show_response = True
        st.session_state.audio_playing = False
    except Exception as e:
        st.error(f"Error playing audio: {e}")
        st.session_state.audio_playing = False
        st.session_state.show_response = True

# Streamlit UI
st.title("Travel Assistant")

# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])
        if message.get("travel_options"):
            display_travel_options(message["travel_options"])
        if message.get("itinerary"):
            display_itinerary(message["itinerary"])

# User input
if prompt := st.chat_input("What would you like to know?"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.write(prompt)

    try:
        with st.spinner("Generating response..."):
            response = requests.post(f"{API_URL}/api/chat", json={
                "message": prompt,
                "conversation_state": st.session_state.conversation_state
            })
            response_data = response.json()

            st.session_state.conversation_state = response_data["updated_conversation_state"]
            current_time = time.time()
            st.session_state.last_message_time = current_time
            st.session_state.show_response = False

            generate_and_play_audio(response_data["text_response"])

            st.session_state.messages.append({
                "role": "assistant",
                "content": response_data["text_response"],
                "timestamp": current_time,
                "travel_options": response_data.get("travel_options"),
                "itinerary": response_data.get("itinerary")
            })
            
            with st.chat_message("assistant"):
                st.write(response_data["text_response"])
                if response_data.get("travel_options"):
                    display_travel_options(response_data["travel_options"])
                if response_data.get("itinerary"):
                    display_itinerary(response_data["itinerary"])

    except Exception as e:
        st.error(f"Error: {str(e)}")

# Clear chat button
if st.button("Clear Chat"):
    st.session_state.messages = []
    st.session_state.conversation_state = None
    st.session_state.last_message_time = 0
    st.session_state.audio_playing = False
    st.session_state.show_response = False
    st.rerun() 