# Voice Travel Assistant

A Streamlit application that helps users plan their travel using voice commands.

## Features

- Voice input for natural interaction
- Travel planning assistance
- Flight and hotel recommendations
- Itinerary generation
- Voice responses using ElevenLabs

## Setup

1. Clone this repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Set up environment variables:
   - Create a `.env` file
   - Add your ElevenLabs API key:
     ```
     ELEVENLABS_API_KEY=your_api_key_here
     ```

## Running Locally

```bash
streamlit run streamlit_app.py
```

## Deployment

This app is designed to be deployed on Streamlit Cloud. To deploy:

1. Push your code to a GitHub repository
2. Go to [Streamlit Cloud](https://streamlit.io/cloud)
3. Connect your GitHub repository
4. Set the following secrets in Streamlit Cloud:
   - `ELEVENLABS_API_KEY`: Your ElevenLabs API key

## Usage

1. Click the "Start Recording" button
2. Speak your travel request
3. Wait for the response
4. View travel options and itinerary

## Requirements

- Python 3.8+
- Streamlit
- ElevenLabs API key
- Microphone access 