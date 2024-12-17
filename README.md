
# Telegram Photo Retriever Bot

## Description
This bot retrieves and sends student photos from a specific college's ERP system based on their registration number. The bot interacts with users through inline buttons and handles automated verification of dates of birth (DOB) to extract the correct student data.

---

## Features
- **User Interaction**: Users can initiate the bot using `/start` and input a registration number.
- **DOB Verification**: Automates searching for the correct date of birth by checking multiple dates sequentially.
- **Image Retrieval**: Fetches and sends student images using the ERP system's URL.
- **User Data Persistence**: Stores user session data in `user_data.json` for continuity.

---

## Prerequisites
- **Python 3.8+**
- **Telegram Bot Token**: Stored in a `BOT_TOKEN.env` file as an environment variable.
- **Required Libraries**: Install dependencies using `pip`.

```
pip install python-telegram-bot aiohttp python-dotenv yarl
```

---

## Setup Instructions
1. **Create a Bot**:
   - Create a Telegram bot using [BotFather](https://t.me/BotFather).
   - Save the bot token in a file named `BOT_TOKEN.env`:
     ```
     BOT_TOKEN=your_telegram_bot_token_here
     ```

2. **Install Dependencies**:
   Run the following command to install required Python libraries:
   ```
   pip install -r requirements.txt
   ```

3. **Run the Bot**:
   Execute the bot script:
   ```
   python lurker.py
   ```

4. **Interact**:
   - Start the bot with `/start`.
   - Follow on-screen prompts to input the registration number and retrieve the desired photo.

---

## File Details
- `lurker.py`: Main bot script.
- `BOT_TOKEN.env`: Environment file storing the Telegram bot token.
- `user_data.json`: JSON file for persisting user data.

---

## Notes
- Designed for educational or authorized use only. Unauthorized usage of student data or ERP systems is prohibited.
- Use responsibly and adhere to privacy guidelines.

---
