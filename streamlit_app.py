import streamlit as st
import requests
import os
from dotenv import load_dotenv
from elevenlabs.client import ElevenLabs
import speech_recognition as sr
from streamlit_webrtc import webrtc_streamer, WebRtcMode, RTCConfiguration, AudioProcessorBase
import numpy as np
from pydub import AudioSegment
import io
import tempfile
import queue

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []
if "travel_options" not in st.session_state:
    st.session_state.travel_options = None
if "itinerary" not in st.session_state:
    st.session_state.itinerary = None
if "audio_queue" not in st.session_state:
    st.session_state.audio_queue = queue.Queue()

# Load environment variables
load_dotenv()

# Initialize ElevenLabs API
try:
    elevenlabs_key = os.getenv("ELEVENLABS_API_KEY")
    if not elevenlabs_key:
        st.warning("⚠️ ElevenLabs API key not found. Please set the ELEVENLABS_API_KEY environment variable.")
    else:
        client = ElevenLabs(api_key=elevenlabs_key)
except Exception as e:
    st.error(f"Error setting up ElevenLabs: {e}")

# Configure WebRTC
RTC_CONFIGURATION = RTCConfiguration(
    {"iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]}
)

class AudioProcessor(AudioProcessorBase):
    def __init__(self):
        super().__init__()
        if "audio_queue" not in st.session_state:
            st.session_state.audio_queue = queue.Queue()
        self.audio_queue = st.session_state.audio_queue

    def recv(self, frame):
        # Add audio frame to queue
        self.audio_queue.put(frame.to_ndarray())
        return frame

def process_audio(audio_data):
    """Process recorded audio data."""
    try:
        # Convert audio data to WAV format
        audio_segment = AudioSegment(
            data=audio_data.tobytes(),
            sample_width=2,
            frame_rate=44100,
            channels=1
        )
        
        # Save to temporary file
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
            audio_segment.export(temp_file.name, format="wav")
            
            # Initialize recognizer
            recognizer = sr.Recognizer()
            
            # Read the audio file
            with sr.AudioFile(temp_file.name) as source:
                audio = recognizer.record(source)
                
                # Recognize speech using Google Speech Recognition
                try:
                    text = recognizer.recognize_google(audio)
                    return text
                except sr.UnknownValueError:
                    return "Could not understand audio"
                except sr.RequestError as e:
                    return f"Error with the speech recognition service: {e}"
    except Exception as e:
        return f"Error processing audio: {str(e)}"

def process_message(text):
    """Process user message and get response from API."""
    try:
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": text})
        
        # Make API request
        response = requests.post(
            "http://localhost:8000/chat",
            json={"message": text}
        )
        
        if response.status_code == 200:
            data = response.json()
            
            # Update travel options and itinerary if present
            if "travel_options" in data:
                st.session_state.travel_options = data["travel_options"]
            if "itinerary" in data:
                st.session_state.itinerary = data["itinerary"]
            
            # Add assistant response to chat history
            st.session_state.messages.append({
                "role": "assistant",
                "content": data["response"]
            })
            
            return data["response"]
        else:
            error_msg = f"Error: {response.status_code} - {response.text}"
            st.session_state.messages.append({
                "role": "assistant",
                "content": error_msg
            })
            return error_msg
    except Exception as e:
        error_msg = f"Error processing message: {str(e)}"
        st.session_state.messages.append({
            "role": "assistant",
            "content": error_msg
        })
        return error_msg

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

def main():
    st.title("Travel Assistant")
    
    # Create two columns for chat and travel info
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("Chat")
        
        # Audio recording using WebRTC
        webrtc_ctx = webrtc_streamer(
            key="audio",
            mode=WebRtcMode.SENDONLY,
            rtc_configuration=RTC_CONFIGURATION,
            media_stream_constraints={"audio": True},
            audio_processor_factory=AudioProcessor
        )
        
        # Process audio from queue
        if "audio_queue" in st.session_state and not st.session_state.audio_queue.empty():
            audio_data = st.session_state.audio_queue.get()
            text = process_audio(audio_data)
            if text:
                response = process_message(text)
                st.write(f"You said: {text}")
                st.write(f"Assistant: {response}")
        
        # Display chat history
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.write(message["content"])
                if message.get("travel_options"):
                    display_travel_options(message["travel_options"])
                if message.get("itinerary"):
                    display_itinerary(message["itinerary"])
    
    with col2:
        st.subheader("Travel Information")
        
        # Display travel options if available
        if st.session_state.travel_options:
            st.write("### Selected Travel Options")
            for option in st.session_state.travel_options:
                st.write(f"- {option}")
        
        # Display itinerary if available
        if st.session_state.itinerary:
            st.write("### Your Itinerary")
            for day, activities in st.session_state.itinerary.items():
                st.write(f"**{day}**")
                for activity in activities:
                    st.write(f"- {activity}")

if __name__ == "__main__":
    main()