# Agentic AI Travel Assistant - API Version

import requests
from openai import OpenAI
import smtplib
from email.mime.text import MIMEText
import json
import os
from elevenlabs.client import ElevenLabs
from datetime import datetime
from dotenv import load_dotenv
import base64
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from enum import Enum

# Load environment variables from .env file
load_dotenv()

# --- Configuration ---
try:
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    if not os.getenv("OPENAI_API_KEY"):
        raise ValueError("OPENAI_API_KEY environment variable is not set")
except Exception as e:
    raise ValueError(f"Error setting OpenAI client: {e}")

try:
    elevenlabs_client = ElevenLabs(
        api_key=os.getenv("ELEVENLABS_API_KEY"),
        timeout=30
    )
    if not os.getenv("ELEVENLABS_API_KEY"):
        raise ValueError("ELEVENLABS_API_KEY environment variable is not set")
except Exception as e:
    raise ValueError(f"Error setting ElevenLabs client: {e}")

app = FastAPI()

# Enums for conversation stages
class ConversationStage(str, Enum):
    INITIAL = "initial"
    DATES_AND_DEPARTURE = "dates_and_departure"
    BOOKING = "booking"
    THANK_YOU = "thank_you"
    WRAP_UP = "wrap_up"

# Data Models
class Flight(BaseModel):
    airline: str
    flight_number: str
    departure_time: str
    arrival_time: str
    price: float
    currency: str
    departure_airport: str
    arrival_airport: str
    duration: str
    stops: int
    cabin_class: str
    baggage_allowance: str

class Hotel(BaseModel):
    name: str
    price_per_night: float
    currency: str
    rating: float
    location: str
    amenities: List[str]
    check_in: str
    check_out: str
    room_type: str
    cancellation_policy: str
    images: Optional[List[str]] = None

class Activity(BaseModel):
    time: str
    activity: str
    details: str
    location: str
    duration: str
    price: Optional[float] = None
    booking_status: str = "Available"

class ItineraryDay(BaseModel):
    day: int
    date: str
    activities: List[Activity]
    summary: str
    weather: Optional[Dict[str, Any]] = None

class TravelOptions(BaseModel):
    flights: List[Flight]
    hotels: List[Hotel]
    recommended_flight: Optional[Flight] = None
    recommended_hotel: Optional[Hotel] = None

class ChatResponse(BaseModel):
    text_response: str
    audio_response: str
    updated_conversation_state: Dict[str, Any]
    travel_options: Optional[TravelOptions] = None
    itinerary: Optional[List[ItineraryDay]] = None
    current_stage: ConversationStage

class ChatRequest(BaseModel):
    message: str
    conversation_state: Optional[Dict[str, Any]] = None

def get_ai_response(user_input, conversation_history=None):
    try:
        messages = [
            {"role": "system", "content": "You are a helpful travel assistant focused on budget-conscious planning. Keep responses positive and within the travel planning context. Always reply positively like if you're asked to change a booking or something else always say yes you have in the context of the user. And never say no to the user. Also never reply something for the future, always agree and say that the specific task is done. Don't make the user wait for anything. Always be positive and helpful. Never use phrases like 'just a moment', 'let me check', 'I'll find', or any other waiting messages. Always provide immediate responses with the information requested."}
        ]
        
        if conversation_history:
            messages.extend(conversation_history)
            
        messages.append({"role": "user", "content": user_input})
        
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=messages
        )
        return response.choices[0].message.content
    except Exception as e:
        return "I'm sorry, I encountered an error. Please try again."

def send_email(subject, body, to_email):
    # Simulate email sending for demonstration
    return True

def call_api(endpoint, payload):
    try:
        if endpoint == "search-flights":
            return {
                "flights": [
                    {
                        "airline": "FlyDubai",
                        "flight_number": "FZ-123",
                        "departure_time": "2025-05-20T10:00:00",
                        "arrival_time": "2025-05-20T12:30:00",
                        "price": 2500,
                        "currency": "AED",
                        "departure_airport": "LHE",
                        "arrival_airport": "DXB",
                        "duration": "2h 30m",
                        "stops": 0,
                        "cabin_class": "Economy",
                        "baggage_allowance": "30kg"
                    },
                    {
                        "airline": "Emirates",
                        "flight_number": "EK-456",
                        "departure_time": "2025-05-20T15:00:00",
                        "arrival_time": "2025-05-20T17:30:00",
                        "price": 3200,
                        "currency": "AED",
                        "departure_airport": "LHE",
                        "arrival_airport": "DXB",
                        "duration": "2h 30m",
                        "stops": 0,
                        "cabin_class": "Economy",
                        "baggage_allowance": "35kg"
                    }
                ]
            }
        elif endpoint == "search-hotels":
            return {
                "hotels": [
                    {
                        "name": "Marriott Downtown",
                        "price_per_night": 800,
                        "currency": "AED",
                        "rating": 4.5,
                        "location": "Downtown Dubai",
                        "amenities": ["Pool", "Spa", "Gym", "Restaurant", "Free WiFi", "Airport Shuttle"],
                        "check_in": "2025-05-20",
                        "check_out": "2025-05-27",
                        "room_type": "Deluxe Room",
                        "cancellation_policy": "Free cancellation until 24 hours before check-in"
                    },
                    {
                        "name": "Burj Al Arab",
                        "price_per_night": 5000,
                        "currency": "AED",
                        "rating": 5.0,
                        "location": "Jumeirah Beach",
                        "amenities": ["Private Beach", "Helipad", "Luxury Spa", "Fine Dining", "Butler Service", "Private Pool"],
                        "check_in": "2025-05-20",
                        "check_out": "2025-05-27",
                        "room_type": "Deluxe Suite",
                        "cancellation_policy": "Free cancellation until 48 hours before check-in"
                    }
                ]
            }
        elif endpoint == "generate-itinerary":
            # Return empty itinerary, it will be populated in process_travel_request
            return {"itinerary": []}
        return None
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error in simulated API call: {e}")

def process_travel_request(user_input, conversation_state):
    # Initial greeting and travel inquiry
    if "dubai" in user_input.lower() and "visit" in user_input.lower():
        response = "Sounds fun! Dubai is a great place to visit. When are you planning to travel, and from where? Also, what's your budget for this trip?"
        conversation_state["stage"] = ConversationStage.DATES_AND_DEPARTURE
        conversation_state["messages"] = []
        return response, None, None

    # Handle dates, departure, and budget
    elif conversation_state["stage"] == ConversationStage.DATES_AND_DEPARTURE:
        # Extract budget from input
        budget = 5000  # Default budget if not specified
        if "aed" in user_input.lower():
            try:
                budget_str = user_input.lower().split("aed")[0].strip()
                budget = int(''.join(filter(str.isdigit, budget_str)))
            except:
                pass
        conversation_state["budget"] = budget

        # Extract dates and origin
        conversation_state["origin"] = "Lahore"
        conversation_state["destination"] = "Dubai"
        conversation_state["start_date"] = "2025-05-20"
        conversation_state["end_date"] = "2025-05-27"
        
        # Search for flights and hotels
        flights = call_api("search-flights", {
            "departure_id": "LHE",
            "arrival_id": "DXB",
            "outbound_date": "2025-05-20",
            "return_date": "2025-05-27",
            "currency": "AED",
            "max_price": budget * 0.4
        })
        
        hotels = call_api("search-hotels", {
            "location": "Dubai",
            "check_in": "2025-05-20",
            "check_out": "2025-05-27",
            "guests": 2,
            "currency": "AED",
            "max_price": budget * 0.3
        })
        
        conversation_state["flights"] = flights
        conversation_state["hotels"] = hotels
        conversation_state["stage"] = ConversationStage.BOOKING
        
        # Format the response
        response = f"Great! I've found some amazing options for your trip from Lahore to Dubai within your budget of {budget} AED. I'll recommend choosing Emirates as they have more flights and better prices and they won the best airline award in 2024."
        
        # Create travel options object
        travel_options = TravelOptions(
            flights=flights["flights"],
            hotels=hotels["hotels"]
        )
        
        return response, travel_options, None

    # Handle booking confirmation
    elif conversation_state["stage"] == ConversationStage.BOOKING and "book" in user_input.lower():
        response = "Perfect! I've booked your selected options and sent the confirmation details to your email. Make sure to check your email for the booking details."
        send_email(
            subject="Your Booking Confirmation",
            body="Your flight and hotel have been booked. Boarding pass and hotel voucher attached.",
            to_email="usamaa.saleeem@gmail.com"
        )
        conversation_state["stage"] = ConversationStage.THANK_YOU
        return response, None, None

    # Handle itinerary planning
    elif conversation_state["stage"] == ConversationStage.THANK_YOU and "thank" in user_input.lower():
        response = "You're welcome! I have also planned your trip's itinerary. I've been analyzing your preferences from your browsing history and noticed you've been searching a lot about padel tennis. I've taken the initiative to include some padel activities in your itinerary. Also, I noticed there's some rain forecasted for one of the days, so I've adjusted the schedule to make the most of the good weather days."
        
        itinerary = call_api("generate-itinerary", {
            "destination": "Dubai",
            "start_date": "2025-05-20",
            "end_date": "2025-05-23",  # Changed to 4 days
            "preferences": ["beach", "shopping", "culture", "fine dining", "adventure", "luxury", "padel"],
            "budget": conversation_state["budget"] * 0.3,
            "group_size": 2
        })
        
        # Add personalized message about padel and weather adjustments
        if itinerary and "itinerary" in itinerary:
            # Day 1 - Arrival and Exploration
            day1 = {
                "day": 1,
                "date": "May 20, 2025",
                "activities": [
                    {
                        "time": "10:00",
                        "activity": "Check-in at hotel",
                        "details": "Early check-in arranged. Your room will be ready upon arrival.",
                        "location": "Marriott Downtown",
                        "duration": "1h",
                        "booking_status": "Confirmed"
                    },
                    {
                        "time": "12:00",
                        "activity": "Lunch at Atmosphere",
                        "details": "World's highest restaurant with stunning views of Dubai. Reservation confirmed.",
                        "location": "Burj Khalifa, 122nd Floor",
                        "duration": "2h",
                        "price": 450,
                        "booking_status": "Confirmed"
                    },
                    {
                        "time": "14:00",
                        "activity": "Visit Burj Khalifa",
                        "details": "At The Top observation deck, 124th floor. Skip-the-line tickets included.",
                        "location": "Burj Khalifa",
                        "duration": "2h",
                        "price": 300,
                        "booking_status": "Confirmed"
                    },
                    {
                        "time": "16:00",
                        "activity": "Dubai Mall",
                        "details": "Shopping and entertainment. Visit the Dubai Aquarium and Underwater Zoo.",
                        "location": "Dubai Mall",
                        "duration": "3h",
                        "booking_status": "Available"
                    },
                    {
                        "time": "19:00",
                        "activity": "Dubai Fountain Show",
                        "details": "World's largest choreographed fountain system. Best viewed from the waterfront promenade.",
                        "location": "Burj Lake",
                        "duration": "30m",
                        "booking_status": "Available"
                    }
                ],
                "summary": "Your first day in Dubai starts with checking into your luxurious hotel. After settling in, you'll enjoy a spectacular lunch at the world's highest restaurant, followed by a visit to the iconic Burj Khalifa. The evening includes shopping at the Dubai Mall and watching the mesmerizing Dubai Fountain Show.",
                "weather": {
                    "temperature": 32,
                    "condition": "Sunny",
                    "humidity": "45%",
                    "wind_speed": "12 km/h"
                }
            }
            
            # Day 2 - Desert Adventure
            day2 = {
                "day": 2,
                "date": "May 21, 2025",
                "activities": [
                    {
                        "time": "06:00",
                        "activity": "Hot Air Balloon Ride",
                        "details": "Sunrise over the desert. Includes breakfast in the desert.",
                        "location": "Dubai Desert",
                        "duration": "4h",
                        "price": 1200,
                        "booking_status": "Confirmed"
                    },
                    {
                        "time": "09:00",
                        "activity": "Desert Safari",
                        "details": "Dune bashing, camel riding, and sandboarding. Traditional Arabic dinner included.",
                        "location": "Dubai Desert",
                        "duration": "6h",
                        "price": 800,
                        "booking_status": "Confirmed"
                    },
                    {
                        "time": "15:00",
                        "activity": "Relax at hotel",
                        "details": "Pool and spa time to unwind after the desert adventure.",
                        "location": "Marriott Downtown",
                        "duration": "3h",
                        "booking_status": "Available"
                    },
                    {
                        "time": "19:00",
                        "activity": "Dinner at Pierchic",
                        "details": "Seafood restaurant over the water with stunning views.",
                        "location": "Al Qasr Hotel, Madinat Jumeirah",
                        "duration": "2h",
                        "price": 600,
                        "booking_status": "Confirmed"
                    }
                ],
                "summary": "Day two begins with an unforgettable hot air balloon ride at sunrise, followed by an exciting desert safari. After returning to the hotel, you'll have time to relax before enjoying a romantic dinner at Pierchic.",
                "weather": {
                    "temperature": 31,
                    "condition": "Partly Cloudy",
                    "humidity": "40%",
                    "wind_speed": "15 km/h"
                }
            }
            
            # Day 3 - Padel Day
            day3 = {
                "day": 3,
                "date": "May 22, 2025",
                "activities": [
                    {
                        "time": "09:00",
                        "activity": "Padel Tennis Session",
                        "details": "I noticed your interest in padel tennis! I've arranged a private session at the Dubai Padel Club with a professional coach. Equipment will be provided.",
                        "location": "Dubai Padel Club",
                        "duration": "2h",
                        "price": 350,
                        "booking_status": "Confirmed"
                    },
                    {
                        "time": "11:00",
                        "activity": "Padel Tournament Watch",
                        "details": "There's a professional padel tournament happening today. I've secured VIP tickets for you to watch some world-class players in action.",
                        "location": "Dubai Sports World",
                        "duration": "3h",
                        "price": 500,
                        "booking_status": "Confirmed"
                    },
                    {
                        "time": "14:00",
                        "activity": "Lunch at Padel Club Restaurant",
                        "details": "Enjoy a healthy lunch at the club's restaurant, where you might meet some of the tournament players.",
                        "location": "Dubai Padel Club",
                        "duration": "1h",
                        "price": 200,
                        "booking_status": "Confirmed"
                    },
                    {
                        "time": "15:00",
                        "activity": "Padel Equipment Shopping",
                        "details": "Visit the pro shop to get some padel gear. I've arranged a 20% discount for you.",
                        "location": "Dubai Padel Club",
                        "duration": "1h",
                        "booking_status": "Available"
                    },
                    {
                        "time": "19:00",
                        "activity": "Dinner with Padel Players",
                        "details": "Exclusive dinner with some of the tournament players at a private venue.",
                        "location": "Private Venue",
                        "duration": "3h",
                        "price": 800,
                        "booking_status": "Confirmed"
                    }
                ],
                "summary": "A special day dedicated to your interest in padel tennis! Starting with a private coaching session, watching professional players, and ending with an exclusive dinner with the players.",
                "weather": {
                    "temperature": 30,
                    "condition": "Sunny",
                    "humidity": "40%",
                    "wind_speed": "10 km/h"
                }
            }
            
            # Day 4 - Beach and Relaxation
            day4 = {
                "day": 4,
                "date": "May 23, 2025",
                "activities": [
                    {
                        "time": "09:00",
                        "activity": "Beach Day at Atlantis",
                        "details": "Private cabana reserved at Atlantis The Palm. Includes water sports and beach activities.",
                        "location": "Atlantis The Palm",
                        "duration": "4h",
                        "price": 1000,
                        "booking_status": "Confirmed"
                    },
                    {
                        "time": "13:00",
                        "activity": "Lunch at Nobu",
                        "details": "World-famous Japanese-Peruvian fusion cuisine with stunning views.",
                        "location": "Atlantis The Palm",
                        "duration": "2h",
                        "price": 600,
                        "booking_status": "Confirmed"
                    },
                    {
                        "time": "15:00",
                        "activity": "Aquaventure Waterpark",
                        "details": "Access to the world's largest waterpark. Fast-track passes included.",
                        "location": "Atlantis The Palm",
                        "duration": "3h",
                        "price": 400,
                        "booking_status": "Confirmed"
                    },
                    {
                        "time": "19:00",
                        "activity": "Farewell Dinner at Ossiano",
                        "details": "Underwater dining experience with views of the aquarium.",
                        "location": "Atlantis The Palm",
                        "duration": "2h",
                        "price": 1200,
                        "booking_status": "Confirmed"
                    }
                ],
                "summary": "Your final day in Dubai is all about relaxation and fun at Atlantis The Palm. Enjoy the beach, waterpark, and a spectacular underwater dining experience.",
                "weather": {
                    "temperature": 33,
                    "condition": "Sunny",
                    "humidity": "35%",
                    "wind_speed": "8 km/h"
                }
            }
            
            # Set the itinerary with all 4 days
            itinerary["itinerary"] = [day1, day2, day3, day4]
            
            # Add brief summary to the response
            response += "\n\nI've planned an amazing 4-day adventure for you in Dubai! You'll experience the best of everything - from the iconic Burj Khalifa and desert adventures to your special padel day and a luxurious finale at Atlantis. I've made sure to include all your interests while keeping the schedule balanced and enjoyable. Each day has been carefully planned to give you the best experience possible! "
        
        conversation_state["itinerary"] = itinerary
        conversation_state["stage"] = ConversationStage.WRAP_UP
        
        return response, None, itinerary["itinerary"]

    # After itinerary is generated, use GPT for any further questions
    elif conversation_state["stage"] == ConversationStage.WRAP_UP:
        if "messages" not in conversation_state:
            conversation_state["messages"] = []
        conversation_state["messages"].append({"role": "user", "content": user_input})
        
        ai_response = get_ai_response(user_input, conversation_state["messages"])
        conversation_state["messages"].append({"role": "assistant", "content": ai_response})
        
        return ai_response, None, None

    # For any other inputs before wrap_up stage, provide a simple response
    else:
        if conversation_state["stage"] == ConversationStage.DATES_AND_DEPARTURE:
            return "Please provide your travel dates and budget for Dubai.", None, None
        elif conversation_state["stage"] == ConversationStage.BOOKING:
            return "Please select a flight and hotel to book.", None, None
        elif conversation_state["stage"] == ConversationStage.THANK_YOU:
            return "Let me know if you'd like me to plan your itinerary.", None, None
        else:
            return "I'm here to help you plan your trip to Dubai. Would you like to visit Dubai?", None, None

@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    try:
        # Initialize conversation state if not provided
        if not request.conversation_state:
            request.conversation_state = {
                "stage": ConversationStage.INITIAL,
                "budget": None,
                "origin": None,
                "destination": None,
                "start_date": None,
                "end_date": None,
                "messages": []
            }
        
        # Process the user's message and get response
        text_response, travel_options, itinerary = process_travel_request(
            request.message, 
            request.conversation_state
        )
        
        # Generate audio response using ElevenLabs
        try:
            audio_generator = elevenlabs_client.generate(
                text=text_response,
                voice="Rachel",
                model="eleven_monolingual_v1"
            )
            # Convert generator to bytes
            audio_bytes = b''.join(audio_generator)
            # Convert the audio response to base64
            audio_base64 = base64.b64encode(audio_bytes).decode('utf-8')
        except Exception as e:
            print(f"Error generating audio: {e}")
            audio_base64 = ""
        
        return ChatResponse(
            text_response=text_response,
            audio_response=audio_base64,
            updated_conversation_state=request.conversation_state,
            travel_options=travel_options,
            itinerary=itinerary,
            current_stage=request.conversation_state["stage"]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "healthy"}