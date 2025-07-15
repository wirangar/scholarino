# Scholarino Telegram Bot

A multilingual Telegram bot for answering questions about Italian scholarships.

## Features

- Answers questions based on scholarship documents (11 PDF files)
- Supports Persian, Italian, and English
- Personalized responses with user's name
- User registration system
- Saves all questions and user data to Google Sheets
- Works in both private chats and groups
- Simple and beautiful UI with main menu

## Setup

1. Clone this repository
2. Install dependencies: `pip install -r requirements.txt`
3. Create a `config.yaml` file based on `config.example.yaml`
4. Set up Google Sheets API credentials (see below)
5. Run the bot: `python main.py`

### Google Sheets Setup

1. Create a new Google Sheet and note its ID
2. Enable Google Sheets API in Google Cloud Console
3. Create a service account and download the credentials JSON file
4. Share your Google Sheet with the service account email

### Webhook Setup (for production)

1. Set `webhook.enabled` to `true` in `config.yaml`
2. Configure your webhook URL and port
3. Deploy to Render.com or another hosting provider

## Deployment to Render.com

1. Create a new Web Service on Render
2. Connect your GitHub repository
3. Set environment variables:
   - `TELEGRAM_TOKEN`: Your bot token
   - `GOOGLE_SHEETS_ID`: Your Google Sheet ID
   - Other configuration as needed
4. Deploy!

## License

MIT