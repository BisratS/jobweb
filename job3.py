import os
import requests
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ConversationHandler,
    CallbackContext,
    filters,
)


WORDPRESS_URL = os.getenv("WORDPRESS_API_URL")
WORDPRESS_USERNAME = os.getenv("WORDPRESS_API_USERNAME")
WORDPRESS_PASSWORD = os.getenv("WORDPRESS_API_PASSWORD")
TELEGRAM_BOT_TOKEN = os.getenv("BOT_TOKEN")


EMAIL, PASSWORD, FIRST_NAME, LAST_NAME, ROLE = range(5)

user_data = {}

ROLE_OPTIONS = {
    "Employer": "wp_job_board_pro_employer",
    "Candidate": "wp_job_board_pro_candidate",
}


async def start(update: Update, context: CallbackContext) -> int:
    user_data["username"] = str(update.message.from_user.id)
    await update.message.reply_text(
        "Welcome! Let's create a new user. Please enter your email address:"
    )
    return EMAIL

async def ask_password(update: Update, context: CallbackContext) -> int:
    user_data["email"] = update.message.text
    await update.message.reply_text("Next, please enter a password:")
    return PASSWORD

async def ask_first_name(update: Update, context: CallbackContext) -> int:
    user_data["password"] = update.message.text
    await update.message.reply_text("Almost done! Please enter your first name:")
    return FIRST_NAME

async def ask_last_name(update: Update, context: CallbackContext) -> int:
    user_data["first_name"] = update.message.text
    await update.message.reply_text("Finally, please enter your last name:")
    return LAST_NAME

async def ask_role(update: Update, context: CallbackContext) -> int:
    user_data["last_name"] = update.message.text

    reply_keyboard = [[role] for role in ROLE_OPTIONS.keys()]
    await update.message.reply_text(
        "Please choose your role:",
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True),
    )
    return ROLE

async def create_user(update: Update, context: CallbackContext) -> int:
    selected_role = update.message.text
    user_data["roles"] = [ROLE_OPTIONS.get(selected_role)]

    success, message = await create_wordpress_user( 
        user_data["username"],
        user_data["email"],
        user_data["password"],
        user_data["first_name"],
        user_data["last_name"],
        user_data["roles"],
    )

    if success:
        await update.message.reply_text(f"✅ User created successfully!\n{message}")
    else:
        await update.message.reply_text(f"❌ Failed to create user: {message}")

    user_data.clear()
    return ConversationHandler.END

async def cancel(update: Update, context: CallbackContext) -> int:
    await update.message.reply_text("User creation canceled.")
    user_data.clear()
    return ConversationHandler.END

async def create_wordpress_user(username, email, password, first_name, last_name, roles):
    url = f"{WORDPRESS_URL}"
    data = {
        "username": username,
        "email": email,
        "password": password,
        "first_name": first_name,
        "last_name": last_name,
        "roles": roles,
    }
    headers = {"Content-Type": "application/json"}
    try:
        response = requests.post(
            url, json=data, headers=headers, auth=(WORDPRESS_USERNAME, WORDPRESS_PASSWORD)
        )
        response.raise_for_status()
        return True, "User created successfully!"
    except requests.exceptions.RequestException as e:
        return False, f"Failed to create user: Network error - {e}"
    except Exception as e:
        error_message = response.json().get('message', 'Unknown error') if 'response' in locals() and response else 'Unknown error'
        return False, f"Failed to create user: {error_message} - {e}"


def main() -> None:
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()


    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            EMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_password)],
            PASSWORD: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_first_name)],
            FIRST_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_last_name)],
            LAST_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_role)],
            ROLE: [MessageHandler(filters.TEXT & ~filters.COMMAND, create_user)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    application.add_handler(conv_handler)

    application.run_polling()

if __name__ == "__main__":
    main()