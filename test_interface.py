import streamlit as st
import requests
import json
import base64
import soundfile as sf
import numpy as np
import io
from datetime import datetime
import os

# API Configuration
API_URL = "https://hack-dubai.onrender.com"

# Create logs directory if it doesn't exist
if not os.path.exists("logs"):
    os.makedirs("logs")

# Initialize session state
if 'conversation_state' not in st.session_state:
    st.session_state.conversation_state = None
if 'messages' not in st.session_state:
    st.session_state.messages = []
if 'request_history' not in st.session_state:
    st.session_state.request_history = []

# Helper functions
def save_request_to_file(payload, response_data):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"logs/request_{timestamp}.json"
    
    data = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "payload": payload,
        "response": response_data
    }
    
    with open(filename, 'w') as f:
        json.dump(data, f, indent=2)

def play_audio(audio_base64):
    try:
        if not audio_base64:
            return
            
        # Decode base64 audio
        audio_bytes = base64.b64decode(audio_base64)
        
        # Create a BytesIO object
        audio_buffer = io.BytesIO(audio_bytes)
        
        # Read the audio data
        audio_data, sample_rate = sf.read(audio_buffer)
        
        # Play the audio
        st.audio(audio_data, sample_rate=sample_rate)
    except Exception as e:
        st.error(f"Error playing audio: {e}")

def display_travel_options(options):
    if options:
        st.subheader("Travel Options")
        
        if options.flights:
            st.write("### Flights")
            for flight in options.flights:
                st.write(f"**{flight.airline}** - {flight.flight_number}")
                st.write(f"From: {flight.departure_airport} at {flight.departure_time}")
                st.write(f"To: {flight.arrival_airport} at {flight.arrival_time}")
                st.write(f"Price: {flight.price} {flight.currency}")
                st.write("---")
        
        if options.hotels:
            st.write("### Hotels")
            for hotel in options.hotels:
                st.write(f"**{hotel.name}** - {hotel.rating}★")
                st.write(f"Location: {hotel.location}")
                st.write(f"Price per night: {hotel.price_per_night} {hotel.currency}")
                st.write(f"Room Type: {hotel.room_type}")
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

# Streamlit UI
st.title("Travel Assistant")

# Create two columns for chat and debug info
col1, col2 = st.columns([2, 1])

with col1:
    # Display chat history
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.write(message["content"])
            if message.get("audio"):
                play_audio(message["audio"])

    # User input
    if prompt := st.chat_input("What would you like to know?"):
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
            # Make API call
            response = requests.post(f"{API_URL}/api/chat", json=payload)
            response_data = response.json()

            # Save request and response to file
            save_request_to_file(payload, response_data)

            # Add to request history
            st.session_state.request_history.append({
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "input": payload,
                "output": response_data
            })

            # Update conversation state
            st.session_state.conversation_state = response_data["updated_conversation_state"]

            # Add assistant response to chat history with audio
            st.session_state.messages.append({
                "role": "assistant",
                "content": response_data["text_response"],
                "audio": response_data["audio_response"]
            })
            
            # Display assistant response
            with st.chat_message("assistant"):
                st.write(response_data["text_response"])
                
                # Play audio if available
                if response_data["audio_response"]:
                    play_audio(response_data["audio_response"])
                
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
        st.session_state.request_history = []
        st.rerun()

with col2:
    st.subheader("API Request History")
    
    # Display request history in reverse chronological order
    for request in reversed(st.session_state.request_history):
        with st.expander(f"Request at {request['timestamp']}"):
            st.write("**Input Payload:**")
            st.json(request['input'])
            st.write("**API Response:**")
            st.json(request['output'])
    
    # Display list of saved request files
    st.subheader("Saved Request Files")
    if os.path.exists("logs"):
        files = sorted(os.listdir("logs"), reverse=True)
        for file in files:
            if file.endswith(".json"):
                with st.expander(file):
                    with open(f"logs/{file}", 'r') as f:
                        data = json.load(f)
                        st.write("**Timestamp:**", data["timestamp"])
                        st.write("**Payload:**")
                        st.json(data["payload"])
                        st.write("**Response:**")
                        st.json(data["response"])

# Display current conversation state
with st.expander("Debug: Current Conversation State"):
    st.json(st.session_state.conversation_state) 