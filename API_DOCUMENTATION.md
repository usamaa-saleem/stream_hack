# Travel Assistant API Documentation

## Base URL
```
http://localhost:8000
```

## Authentication
No authentication required for this version.

## Endpoints

### 1. Chat Endpoint
**Endpoint:** `/api/chat`  
**Method:** POST  
**Description:** Main endpoint for interacting with the travel assistant.

#### Request Body
```json
{
    "message": "string",
    "conversation_state": {
        "stage": "string",
        "budget": "number",
        "origin": "string",
        "destination": "string",
        "start_date": "string",
        "end_date": "string",
        "messages": [
            {
                "role": "string",
                "content": "string"
            }
        ]
    }
}
```

#### Response
```json
{
    "text_response": "string",
    "audio_response": "string (base64 encoded)",
    "updated_conversation_state": {
        "stage": "string",
        "budget": "number",
        "origin": "string",
        "destination": "string",
        "start_date": "string",
        "end_date": "string",
        "messages": [
            {
                "role": "string",
                "content": "string"
            }
        ]
    },
    "travel_options": {
        "flights": [
            {
                "airline": "string",
                "flight_number": "string",
                "departure_time": "string",
                "arrival_time": "string",
                "price": "number",
                "currency": "string",
                "departure_airport": "string",
                "arrival_airport": "string",
                "duration": "string",
                "stops": "number",
                "cabin_class": "string",
                "baggage_allowance": "string"
            }
        ],
        "hotels": [
            {
                "name": "string",
                "price_per_night": "number",
                "currency": "string",
                "rating": "number",
                "location": "string",
                "amenities": ["string"],
                "check_in": "string",
                "check_out": "string",
                "room_type": "string",
                "cancellation_policy": "string"
            }
        ],
        "recommended_flight": "object",
        "recommended_hotel": "object"
    },
    "itinerary": [
        {
            "day": "number",
            "date": "string",
            "activities": [
                {
                    "time": "string",
                    "activity": "string",
                    "details": "string",
                    "location": "string",
                    "duration": "string",
                    "price": "number",
                    "booking_status": "string"
                }
            ],
            "summary": "string",
            "weather": {
                "temperature": "number",
                "condition": "string",
                "humidity": "string",
                "wind_speed": "string"
            }
        }
    ],
    "current_stage": "string",
    "suggested_responses": ["string"]
}
```

### 2. Health Check
**Endpoint:** `/health`  
**Method:** GET  
**Description:** Check if the API is running.

#### Response
```json
{
    "status": "healthy"
}
```

## Conversation Stages
The conversation progresses through these stages:
1. `initial` - Starting point
2. `dates_and_departure` - Collecting travel dates and departure info
3. `booking` - Handling flight and hotel bookings
4. `thank_you` - After booking confirmation
5. `wrap_up` - Final stage for itinerary and additional requests

## Integration Steps

### 1. Initial Setup
1. Install required dependencies:
```bash
pip install fastapi uvicorn python-dotenv openai elevenlabs pydantic
```

2. Create a `.env` file with:
```
OPENAI_API_KEY=your_openai_key
ELEVENLABS_API_KEY=your_elevenlabs_key
```

### 2. Frontend Integration
1. Initialize conversation state:
```javascript
let conversationState = {
    stage: "initial",
    budget: null,
    origin: null,
    destination: null,
    start_date: null,
    end_date: null,
    messages: []
};
```

2. Make API calls:
```javascript
async function sendMessage(message) {
    const response = await fetch('http://localhost:8000/api/chat', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            message: message,
            conversation_state: conversationState
        })
    });
    
    const data = await response.json();
    // Update conversation state
    conversationState = data.updated_conversation_state;
    return data;
}
```

3. Handle audio responses:
```javascript
function playAudio(base64Audio) {
    const audio = new Audio('data:audio/wav;base64,' + base64Audio);
    audio.play();
}
```

### 3. Error Handling
- Check for HTTP 500 errors
- Handle network errors
- Validate response data structure

## Postman Collection
```json
{
    "info": {
        "name": "Travel Assistant API",
        "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
    },
    "item": [
        {
            "name": "Chat",
            "request": {
                "method": "POST",
                "header": [
                    {
                        "key": "Content-Type",
                        "value": "application/json"
                    }
                ],
                "body": {
                    "mode": "raw",
                    "raw": "{\n    \"message\": \"I want to visit Dubai\",\n    \"conversation_state\": null\n}"
                },
                "url": {
                    "raw": "http://localhost:8000/api/chat",
                    "protocol": "http",
                    "host": ["localhost"],
                    "port": "8000",
                    "path": ["api", "chat"]
                }
            }
        },
        {
            "name": "Health Check",
            "request": {
                "method": "GET",
                "url": {
                    "raw": "http://localhost:8000/health",
                    "protocol": "http",
                    "host": ["localhost"],
                    "port": "8000",
                    "path": ["health"]
                }
            }
        }
    ]
}
```

## Testing
1. Start the backend server:
```bash
uvicorn test:app --reload
```

2. Test the API using Postman or curl:
```bash
curl -X POST http://localhost:8000/api/chat \
-H "Content-Type: application/json" \
-d '{"message": "I want to visit Dubai", "conversation_state": null}'
```

## Notes
- The API is designed to maintain conversation state
- Audio responses are base64 encoded
- All dates should be in YYYY-MM-DD format
- Currency is in AED by default
- The API uses GPT-3.5-turbo for text generation
- ElevenLabs is used for text-to-speech 

## Example Input Payloads by State

### 1. Initial State
```json
{
    "message": "I want to visit Dubai",
    "conversation_state": null
}
```

### 2. Dates and Departure State
```json
{
    "message": "I want to travel from Lahore with a budget of 5000 AED",
    "conversation_state": {
        "stage": "dates_and_departure",
        "budget": 5000,
        "origin": "Lahore",
        "destination": "Dubai",
        "start_date": "2025-05-20",
        "end_date": "2025-05-27"
    }
}
```

### 3. Booking State
```json
{
    "message": "Book the first option",
    "conversation_state": {
        "stage": "booking",
        "budget": 5000,
        "origin": "Lahore",
        "destination": "Dubai",
        "start_date": "2025-05-20",
        "end_date": "2025-05-27"
    }
}
```

### 4. Thank You State
```json
{
    "message": "Thank you, please plan my itinerary",
    "conversation_state": {
        "stage": "thank_you",
        "budget": 5000,
        "origin": "Lahore",
        "destination": "Dubai",
        "start_date": "2025-05-20",
        "end_date": "2025-05-27"
    }
}
```

### 5. Wrap Up State
```json
{
    "message": "What are the best restaurants near my hotel?",
    "conversation_state": {
        "stage": "wrap_up",
        "budget": 5000,
        "origin": "Lahore",
        "destination": "Dubai",
        "start_date": "2025-05-20",
        "end_date": "2025-05-27"
    }
}
``` 