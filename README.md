# Telegram parser participants

Script for parsing all participants of Telegram chat/group/channel with saving their ID in a text file.

## Installation

1. Install Python 3.7 or later

2. Set dependencies:
`bash
pip install -r requirements.txt
`

## Configuration

1. Get API credentials:
   - Go to https://my.telegram.org
   - Enter your phone number
   - Go to "API development tools"
   - Create the application and copy the api_id and the api_hash

2. Open telegram_parser.py and replace:
   `python
   API_ID = 'YOUR_API_ID'
   API_HASH = 'YOUR_API_HASH'
   `
   to your actual values

## Use

Run the script:
`bash
python telegram_parser.py
`

At the first start you will need:
1. Enter the phone number (with country code, for example: +79001234567)
2. Enter the confirmation code that will come in Telegram
3. If two-factor authentication is enabled, enter a password

After the first login, the session will be saved in a file called 'telegram_session.session', and you won’t need to log on when you start again.

## Result

Participants ID saved to file
`
# of chat participants ID: -1003027642749
# Total participants found: 150

123456789
987654321 
`

## Important

- Make sure you have access to the chat/group/channel
- Private channels require administrator rights
- Do not abuse - too frequent requests can lead to a temporary lock
- Session file contains your authorized access - do not pass it on to third parties
