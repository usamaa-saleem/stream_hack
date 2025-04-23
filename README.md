# Travel Assistant Chatbot

A Streamlit-based travel assistant chatbot that helps users plan their trips, book flights, and hotels.

## Features

- Natural language conversation interface
- Flight and hotel booking assistance
- Itinerary planning
- Voice response using ElevenLabs
- Persistent chat history

## Setup

1. Clone the repository:
```bash
git clone https://github.com/usamaa-saleem/stream_hack.git
cd stream_hack
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Create a `.env` file with your API keys:
```
ELEVENLABS_API_KEY=your_api_key_here
```

4. Run the app:
```bash
streamlit run streamlit_app.py
```

## Deployment

The app is ready to be deployed on Streamlit Cloud. Simply connect your GitHub repository to Streamlit Cloud and deploy the `streamlit_app.py` file.

## Environment Variables

- `ELEVENLABS_API_KEY`: Your ElevenLabs API key for voice generation 