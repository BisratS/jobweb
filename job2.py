import os
import json
import logging
import requests
import asyncio
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

WP_API_URL = os.getenv("WORDPRESS_API_URL")
BOT_TOKEN = os.getenv("BOT_TOKEN")


logging.basicConfig(level=logging.INFO)

def create_application():
    return Application.builder().token(BOT_TOKEN).build()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[InlineKeyboardButton("Employer", callback_data="employer"),
                 InlineKeyboardButton("Candidate", callback_data="candidate")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Welcome! Choose your role:", reply_markup=reply_markup)

async def role_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    role_callback_data = query.data

    if role_callback_data == "employer":
        context.user_data["role"] = "wp_job_board_pro_employer" 
    elif role_callback_data == "candidate":
        context.user_data["role"] = "wp_job_board_pro_candidate"

    await query.message.reply_text("Send your first name:")
    context.user_data["next_step"] = "first_name"

async def process_user_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    next_step = context.user_data.get("next_step")
    user_input = update.message.text
    
    if next_step == "first_name":
        context.user_data["first_name"] = user_input
        await update.message.reply_text("Send your last name:")
        context.user_data["next_step"] = "last_name"
    elif next_step == "last_name":
        context.user_data["last_name"] = user_input
        await update.message.reply_text("Send your email:")
        context.user_data["next_step"] = "email"
    elif next_step == "email":
        context.user_data["email"] = user_input
        await update.message.reply_text("Choose a password:")
        context.user_data["next_step"] = "password"
    elif next_step == "password":
        context.user_data["password"] = user_input
        await register_user(update, context)

async def register_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    username = str(f"tg_{user_id}")
    role = context.user_data.get("role")
    first_name = context.user_data.get("first_name")
    last_name = context.user_data.get("last_name")
    email = context.user_data.get("email")
    password = context.user_data.get("password")

    if not all([role, first_name, last_name, email, password]):
        await update.message.reply_text("Missing information. Please restart with /start.")
        return

    payload = {
    "username": username,
    "email": email,
    "first_name": first_name,
    "last_name": last_name,
    "password": password,
    "role": role,
}
    logging.info(f"API Request Payload: {json.dumps(payload)}")

    api_username = os.getenv("WORDPRESS_API_USERNAME")
    api_password = os.getenv("WORDPRESS_API_PASSWORD")
    headers = {
            'Content-Type': 'application/json',
            'User-Agent': 'PostmanRuntime/7.43.0'
        }

    logging.info(f"Sending POST request to: {WP_API_URL} with Basic Auth")
    response = requests.post(
        WP_API_URL,
        json=payload,
        auth=(api_username, api_password),
        headers = headers
    )
    logging.info(f"API Response Status Code: {response.status_code}")
    logging.info(f"API Response Content: {response.text}")

    if response.status_code == 200:
        try:
            data = response.json()
            login_url = data.get("login_url")
            approval_pending = data.get("approval_pending", False)
            meta_key = data.get("meta_key")
            meta_value = data.get("meta_value")
            user_id_wp = data.get("user_id")

            log_message = f"Registration successful. User ID: {user_id_wp}, Meta Key: {meta_key}, Meta Value: {meta_value}, Approval Pending: {approval_pending}"
            if login_url:
                log_message += f", Login URL: {login_url}"
            logging.info(log_message)


            if approval_pending:
                await update.message.reply_text("Registration successful! Your Employer account is now pending admin approval. You will be notified once your account is approved.")
            elif login_url:
                await update.message.reply_text(f"Registration successful! Click to login: [Login]({login_url})", parse_mode="Markdown")
            else:
                await update.message.reply_text("Registration successful!")


        except json.JSONDecodeError:
            await update.message.reply_text("Registration successful, but there was an issue processing the server response. Please check your website directly.")


    else:
        try:
            error_data = response.json()
            error_message = error_data.get("error", "Registration failed. Try again later.")
        except json.JSONDecodeError:
            error_message = "Registration failed due to an unexpected error. Please try again later."

        if error_message == 'User already exists':
            reply_text = "Registration failed: Username or email is already registered. Please use different details."
        elif error_message == 'Missing parameters':
            reply_text = "Registration failed: Some required information was missing. Please make sure you provided all details."
        else:
            reply_text = f"Registration failed: {error_message}. Please try again later."

        await update.message.reply_text(reply_text)

def main():
    app = create_application()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(role_selection))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, process_user_input))
    
    loop = asyncio.get_event_loop()
    loop.create_task(app.run_polling())
    loop.run_forever()

if __name__ == "__main__":
    main()