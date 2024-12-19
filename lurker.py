from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters
from datetime import datetime, timedelta
import urllib3
import re
import os
from io import BytesIO
import aiohttp
from yarl import URL
from dotenv import load_dotenv
import json


# Loading bot token froma external env file
load_dotenv("BOT_TOKEN.env")
BOT_TOKEN = os.getenv("BOT_TOKEN")


# Disable warnings for insecure requests
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


# Global dictionary to store user data
user_data = {}
USER_DATA_FILE = "user_data.json"


# Storing the data in a JSON file
def save_user_data():
    try:
        with open(USER_DATA_FILE, "w") as file:
            json.dump(user_data, file)
    except Exception as e:
        print(f"Error saving user data: {e}")


# Retrieving the data from a stored file
def load_user_data():
    global user_data
    if os.path.exists(USER_DATA_FILE):
        try:
            with open(USER_DATA_FILE, "r") as file:
                user_data = json.load(file)
        except Exception as e:
            print(f"Error loading user data: {e}")


# Verifying whether a dob is correct 
async def dobVerifier(session, regno, dob):
    url = "https://erpsrm.com/srmhonline/valliammai/transaction/feepayment.jsp"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Content-Type": "application/x-www-form-urlencoded",
        "Origin": "https://erpsrm.com",
        "Referer": "https://erpsrm.com/srmhonline/valliammai/transaction/feepayment.jsp",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "same-origin",
        "Sec-Fetch-User": "?1",
        "TE": "trailers"
    }
    data = {"pageAction": "3", "regno": regno, "dob": dob}
    async with session.post(url, headers=headers, data=data, ssl=False) as response:
        text = await response.text()
        return "Invalid data, please check with correct information!" not in text


# Checking concurrent dob
async def dob_finder(regno, date, date_format="%d/%m/%Y") -> str:
    original_date = datetime.strptime(date, date_format)
    forward_days, backward_days = 1, 1

    async with aiohttp.ClientSession() as session:
        if await dobVerifier(session, regno, original_date.strftime(date_format)):
            return original_date.strftime(date_format)

        for i in range(1, 1000):
            current_date = (original_date + timedelta(days=forward_days)) if i % 2 == 0 else (original_date - timedelta(days=backward_days))
            forward_days, backward_days = (forward_days + 1, backward_days) if i % 2 == 0 else (forward_days, backward_days + 1)

            if await dobVerifier(session, regno, current_date.strftime(date_format)):
                return current_date.strftime(date_format)

        return "not found"


# Extracting student id from the response
def extract_student_id(paragraph):
    match = re.search(r"studentid:\s*(\d+)", paragraph)
    return match.group(1) if match else None


# Extracting filename from the response
def extract_image_filename(paragraph):
    match = re.search(r"funReloadImage\('([\w\d]+\.\w+)'\)", paragraph)
    return match.group(1) if match else None


#Extracting user-id
async def id_giver(regno, dob, user_id, session):
    url = "https://erpsrm.com/srmhonline/valliammai/transaction/feepayment.jsp"
    headers = {
        "accept": "text/html, */*; q=0.01",
        "content-type": "application/x-www-form-urlencoded",
        "origin": "https://erpsrm.com",
        "referer": "https://erpsrm.com/srmhonline/valliammai/transaction/feepayment.jsp",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
    }
    data = {"pageAction": "3", "regno": regno, "dob": dob}

    async with session.post(url, headers=headers, data=data) as response:
        text = await response.text()
        studid = extract_student_id(text)
        session_id = session.cookie_jar.filter_cookies(URL(url)).get("JSESSIONID")
        user_data[user_id] = {"studid": studid, "session_id": session_id}
        save_user_data()


# Extracting file
async def file_giver(studid, session):
    url = "https://erpsrm.com/srmhonline/valliammai/transaction/feepayment.jsp"
    session_id = str(session.cookie_jar.filter_cookies(URL(url)).get("JSESSIONID"))
    cookie_value = session_id.split("JSESSIONID=")[1]

    headers = {
        "content-type": "application/x-www-form-urlencoded",
        "cookie": cookie_value,
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
    }
    data = {"pageAction": "51", "studentid": studid}

    async with session.post(url, headers=headers, data=data) as response:
        text = await response.text()
        pic_name = extract_image_filename(text)
        return f"https://erpsrm.com/srmhonline/resources/sphotos/{pic_name}"


# Sending image to user
async def send_image_from_url(update, context, url, message_id):
    try:
        # Fetch the image from the URL
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                response.raise_for_status()
                image_data = BytesIO(await response.read())
                image_data.name = "image.jpg"

        # Replace the previous message with the image
        await context.bot.edit_message_media (
            chat_id=update.message.chat_id,
            message_id = message_id,
            media=InputMediaPhoto(media=image_data , caption="you gonna stroke with this pic? ewww... 🤮"),
            )
        await update.message.reply_text(f"credits: ")
        
    except aiohttp.ClientError as e:
        await update.message.reply_text("Failed to fetch the image: ")
    except Exception as e:
        await update.message.reply_text("Failed to replace the message: ")


# Determining the DOB range
async def automatic(update, context, regno, user_id, message_id):
    regno = int(regno)

    # Define date ranges for regno
    date_ranges = {
        (142224000000, 142224999999): "01/06/2006",
        (142223000000, 142223999999): "01/06/2005",
        (142222000000, 142222999999): "01/06/2004",
        (142221000000, 142221999999): "01/06/2003",
    }

    # Find the date corresponding to the regno range
    try:
        date = next(value for (low, high), value in date_ranges.items() if low < regno < high)
    except StopIteration:
        await update.message.reply_text("Search only for members currently enrolled in this college.")
        return

    dob = await dob_finder(regno=str(regno), date=date)
    async with aiohttp.ClientSession() as session:
        await id_giver(regno=str(regno), dob=dob, user_id=user_id, session=session)
        student_id = user_data[user_id]["studid"]
        link = await file_giver(studid=student_id, session=session)
        await send_image_from_url(update, context, link, message_id)


    """TELEGRAM HANDLERS"""

# Start command   
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Want photo of a SRM student?",
        reply_markup=InlineKeyboardMarkup(
            [[InlineKeyboardButton("    𓆩😈𓆪  GET PHOTO  𓆩😈𓆪    ", callback_data="get_photo")]]
        ),
    )


# Button usage
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    if user_id not in user_data:
        user_data[user_id] = {}

    if query.data == "get_photo":
        await query.edit_message_text("Enter register number:")
        user_data[user_id]["stage"] = "awaiting_registration"


# Handling user's response
async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):   
    user_id = update.message.from_user.id
    text = update.message.text.replace(" " , "")

    if user_id not in user_data:
        user_data[user_id] = {}

    stage = user_data[user_id].get("stage", "")
    if stage == "awaiting_registration":
        user_data[user_id]["registration_number"] = text
        user_data[user_id]["stage"] = ""
        
        if text[:4] == "1422" and len(text) == 12:
            try:
                int(text)
                message = await update.message.reply_animation(animation="https://i.giphy.com/media/v1.Y2lkPTc5MGI3NjExdzZ3aTdnYnk1aDczOHpzMGJ4cWk5anM3dWgxMnl5ODJ6MjZrNW9hdyZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/l3nWhI38IWDofyDrW/giphy.gif")
                message_id = message.message_id          
                await automatic(update=update, context=context, regno=text, user_id=user_id, message_id=message_id)
            except ValueError:
                await update.message.reply_text("Hey MF, You couldn’t even enter a register number Your brain must be running on dial-up because even a slow-loading webpage is faster than your ability to figure out the basics. Are you sure you’re not still using a flip phone for tech support? Even a goldfish has better memory skills than you at this point.")
        else:
            await update.message.reply_text("Hey MF, You couldn’t even enter a register number Your brain must be running on dial-up because even a slow-loading webpage is faster than your ability to figure out the basics. Are you sure you’re not still using a flip phone for tech support? Even a goldfish has better memory skills than you at this point.")


# Main function to set up the bot
def main():
    load_user_data()
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))
    print("Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
