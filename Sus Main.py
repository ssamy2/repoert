import telebot,instaloader,re
import sqlite3,time
import random
import string
from datetime import datetime, timedelta
import os
from instaloader.exceptions import BadCredentialsException, TwoFactorAuthRequiredException, ConnectionException
from itertools import cycle
from telebot import types
L = instaloader.Instaloader()
reports_count = 0
TOKEN = "6995736276:AAG9Mxc91zvU5CwNDyFXdy5yjeTL1hv97bY"
owner_id = 6505049528
bot = telebot.TeleBot(TOKEN)

if not os.path.exists("data"):
    os.makedirs("data")
conn = sqlite3.connect("data/serial_keys.db")
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS keys (
             key TEXT PRIMARY KEY,
             expiration TIMESTAMP,
             user_id INTEGER,
             redeemed BOOLEAN DEFAULT 0)''')
c.execute('''CREATE TABLE IF NOT EXISTS users (
             user_id INTEGER PRIMARY KEY,
             username TEXT)''')
c.execute('''CREATE TABLE IF NOT EXISTS redeemed_keys (
             key TEXT,
             user_id INTEGER)''')
conn.commit()
def generate_key():
    key = "DARK-" + "".join(random.choices(string.ascii_uppercase + string.digits, k=12))
    return key
@bot.message_handler(commands=['key'])
def generate_keys(message):
    try:
        if message.from_user.id != owner_id:
            bot.reply_to(message, "Sorry, you are not authorized to use this command.")
            return
        command, quantity, expiration_hours = message.text.split()
        quantity = int(quantity)
        expiration_hours = int(expiration_hours)
        expiration_time = datetime.now() + timedelta(hours=expiration_hours)
        user_id = message.from_user.id
        conn_local = sqlite3.connect("data/serial_keys.db")
        c_local = conn_local.cursor()
        keys_generated = []
        for _ in range(quantity):
            key = generate_key()
            expiration_str = expiration_time.strftime('%Y-%m-%d %H:%M:%S')
            c_local.execute("INSERT INTO keys (key, expiration, user_id) VALUES (?, ?, ?)", (key, expiration_str, user_id))
            keys_generated.append(f"{key} - Expires: {expiration_str}")
        conn_local.commit()
        conn_local.close()
        keys_generated_str = "\n".join(keys_generated)
        bot.reply_to(message, f"{quantity} keys generated successfully:\n{keys_generated_str}")
    except ValueError:
        bot.reply_to(message, "Invalid command format. Use /key (quantity) (expiration_hours)")
@bot.message_handler(commands=['redeem'])
def redeem_key(message):
    try:
        key_to_redeem = message.text.split()[1]
        user_id = message.from_user.id
        conn_local = sqlite3.connect("data/serial_keys.db")
        c_local = conn_local.cursor()
        c_local.execute("SELECT * FROM keys WHERE key=? AND redeemed=0", (key_to_redeem,))
        key_data = c_local.fetchone()
        if key_data:
            c_local.execute("UPDATE keys SET redeemed=1, user_id=? WHERE key=?", (user_id, key_to_redeem))
            conn_local.commit()
            bot.reply_to(message, "Key redeemed successfully.")
        else:
            bot.reply_to(message, "Invalid or already redeemed key.")
        conn_local.close()
    except Exception as e:
        bot.reply_to(message, f"An error occurred: {e}")
@bot.message_handler(commands=['info'])
def membership_info(message):
    try:
        user_id = message.from_user.id
        conn_local = sqlite3.connect("data/serial_keys.db")
        c_local = conn_local.cursor()
        c_local.execute("SELECT * FROM keys WHERE user_id=? AND redeemed=1", (user_id,))
        keys = c_local.fetchall()
        if keys:
            membership_info = f"You have {len(keys)} redeemed keys:\n"
            for key in keys:
                try:
                    expiration_time = datetime.strptime(key[1], '%Y-%m-%d %H:%M:%S')
                    expiration_str = expiration_time.strftime('%Y-%m-%d %H:%M:%S') if datetime.now() <= expiration_time else 'Expired'
                    membership_info += f"{key[0]} - {expiration_str}\n"
                except ValueError:
                    membership_info += f"{key[0]} - Invalid expiration time format\n"
        else:
            membership_info = "You don't have any redeemed keys."
        bot.reply_to(message, membership_info)
        conn_local.close()
    except Exception as e:
        bot.reply_to(message, f"An error occurred: {e}")
@bot.message_handler(commands=['keys'])
def show_all_keys(message):
    try:
        if message.from_user.id != owner_id:
            bot.reply_to(message, "Sorry, you are not authorized to use this command.")
            return
        conn_local = sqlite3.connect("data/serial_keys.db")
        c_local = conn_local.cursor()
        c_local.execute("SELECT keys.key, keys.expiration, users.username FROM keys LEFT JOIN users ON keys.user_id = users.user_id")
        keys = c_local.fetchall()
        response = "All keys:\n"
        for key in keys:
            try:
                expiration_time = datetime.strptime(key[1], '%Y-%m-%d %H:%M:%S.%f')
                expiration_str = expiration_time.strftime('%Y-%m-%d %H:%M:%S') if datetime.now() <= expiration_time else 'Expired'
                response += f"{key[0]} - {expiration_str} - Owned by: {key[2]}\n"
            except ValueError:
                response += f"{key[0]} - Invalid expiration time format\n"
        bot.reply_to(message, response)
        conn_local.close()
    except Exception as e:
        bot.reply_to(message, f"An error occurred: {e}")
# - - - - - - -
@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    conn_local = sqlite3.connect("data/serial_keys.db")
    c_local = conn_local.cursor()
    c_local.execute("SELECT * FROM keys WHERE user_id=? AND redeemed=1 AND expiration > CURRENT_TIMESTAMP", (user_id,))
    user_key_data = c_local.fetchone()
    if user_key_data:
        expiration_time = datetime.strptime(user_key_data[1], '%Y-%m-%d %H:%M:%S')
        if datetime.now() <= expiration_time:
            key = types.InlineKeyboardMarkup()
            btn_add = types.InlineKeyboardButton(text="𝗔𝗗𝗗 𝗔𝗖𝗖𝗢𝗨𝗡𝗧 ", callback_data='addac')
            btn_select = types.InlineKeyboardButton(text='𝗥𝗘𝗣𝗢𝗥𝗧 𝗧𝗢', callback_data='selectac')
            btn_clean = types.InlineKeyboardButton(text='𝗖𝗟𝗘𝗔𝗡 𝗔𝗖𝗖𝗢𝗨𝗡𝗧 ', callback_data='cleanac')
            key.row(btn_add, btn_clean)
            btn_report = types.InlineKeyboardButton(text='𝗦𝗧𝗔𝗥𝗧', callback_data='report')
            key.row(btn_select)
            key.row(btn_report)
            bot.reply_to(message, "مرحباً عزيزي، البوت خاص بعمل بلاغات لحسابات انستغرام. يرجى الاختيار من الأزرار أدناه. لعرض التعليمات اضغط /help ويرجى قراءتها أولاً.", reply_markup=key)
        else:
            owner = types.InlineKeyboardButton(text='𝗢𝗪𝗡𝗘𝗥', url='https://t.me/exe_r')
            prices = types.InlineKeyboardButton(text='𝗣𝗥𝗜𝗖𝗘𝗦', callback_data='price')
            keyyy = types.InlineKeyboardMarkup()
            keyyy.add(owner, prices)
            bot.reply_to(message, "عذراً، عضويتك قد انتهت. يرجى التواصل مع المالك لتجديدها.", reply_markup=keyyy)
    else:
        owner = types.InlineKeyboardButton(text='𝗢𝗪𝗡𝗘𝗥', url='https://t.me/exe_r')
        prices = types.InlineKeyboardButton(text='𝗣𝗥𝗜𝗖𝗘𝗦', callback_data='price')
        keyyy = types.InlineKeyboardMarkup()
        keyyy.add(owner, prices)
        bot.reply_to(message, "عذراً، ليس لديك صلاحية لاستخدام البوت. يرجى التواصل مع المالك للحصول على اشتراك.", reply_markup=keyyy)


class BadCredentialsException(Exception):
    pass

class TwoFactorAuthRequiredException(Exception):
    pass

class ConnectionException(Exception):
    pass
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
@bot.callback_query_handler(func=lambda call: call.data == 'selectac')
def select_account(call):
    msg = bot.send_message(call.message.chat.id, "أرسل معرف الحساب الذي تريد عمل بلاغ عليه.")
    bot.register_next_step_handler(msg, process_account_selection)

def process_account_selection(message):
    username = message.text.strip().replace('@', '')
    if check_instagram_account(username):
        with open('ac.txt', 'w') as file:
            file.write(username)
        bot.send_message(message.chat.id, f"تم تحديد الحساب الذي سيتم التبليغ عنه وهو : @{username}")
    else:
        bot.send_message(message.chat.id, "الحساب الذي تحاول الإبلاغ عنه ليس موجوداً على إنستغرام.")

def check_instagram_account(username):
    try:
        profile = L.check_profile_id(username)
        return True
    except instaloader.ProfileNotExistsException:
        return False
    except instaloader.InstaloaderException as e:
        bot.send_message(message.chat.id, f'حدث خطأ أثناء التحقق من الحساب: {str(e)}')
        return False
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
def cycle_accounts():
    with open('accounts.txt', 'r') as file:
        accounts = [line.strip().split(':')[0] for line in file]
    return cycle(accounts)
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - 

def account_exists(username):
    with open('accounts.txt', 'r') as file:
        accounts = file.readlines()
        for account in accounts:
            if username in account:
                return True
    return False

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - 

@bot.callback_query_handler(func=lambda call: call.data == 'addac')
def save_account(call):
    msg = bot.send_message(call.message.chat.id, 'يرجى إرسال الحساب بصيغة user:pass')
    bot.register_next_step_handler(msg, process_save_account)

def process_save_account(message):
    try:
        user, password = message.text.split(':')
        if account_exists(user):
            bot.send_message(message.chat.id, 'هذا الحساب مضاف مسبقا')
            return
        # تسجيل الدخول للتحقق من صحة الحساب
        L.login(user, password)
        # تخزين الحساب في الملف
        with open('accounts.txt', 'a') as file:
            file.write(f'{user}:{password}\n')
        bot.send_message(message.chat.id, 'تمت إضافة الحساب وحفظه بنجاح')
    except BadCredentialsException:
        bot.send_message(message.chat.id, 'كلمة السر غير صحيحة ❌ أعد المحاولة مجددا.')
    except TwoFactorAuthRequiredException:
        bot.send_message(message.chat.id, 'الحساب يملك خاصية التحقق الإضافي.')
    except ConnectionException:
        bot.send_message(message.chat.id, 'حدث خطأ في الاتصال.')
    except Exception as e:
        bot.send_message(message.chat.id, f'حدث خطأ غير متوقع: {str(e)}')

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
def check_instagram_account(username):
    try:
        profile = L.check_profile_id(username)
        return True
    except instaloader.ProfileNotExistsException:
        return False
    except instaloader.InstaloaderException as e:
        bot.send_message(message.chat.id, f'حدث خطأ أثناء التحقق من الحساب: {str(e)}')
        return False

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
@bot.callback_query_handler(func=lambda call: call.data == 'report')
def ask_for_reports_number(call):
    msg = bot.send_message(call.message.chat.id, "أرسل عدد البلاغات التي تريدها (بين 10 و 1000)")
    bot.register_next_step_handler(msg, process_report_request)

def process_report_request(message):
    try:
        reports_number = int(message.text)
        success_reports = 0
        failed_reports = 0
        accounts = cycle_accounts()
        with open('ac.txt', 'r') as file:
            reported_account = file.read().strip()
        status_message = bot.send_message(message.chat.id, f'𝗥𝗘𝗣𝗢𝗥𝗧𝗜𝗡𝗚 𝗗𝗘𝗧𝗔𝗜𝗟𝗦 🤖\n[𝗥𝗘𝗣𝗢𝗥𝗧 𝗔𝗖𝗖𝗢𝗨𝗡𝗧 : @{reported_account}]\n[𝗧𝗢𝗧𝗔𝗟 𝗥𝗘𝗣𝗢𝗥𝗧𝗦: {reports_number}, 𝗦𝗨𝗖𝗖𝗘𝗦𝗦: ✅{success_reports}, 𝗙𝗔𝗜𝗟𝗘𝗗: ❌{failed_reports}]')
        stop_button = types.InlineKeyboardMarkup()
        stop_button.add(types.InlineKeyboardButton('Stop', callback_data='stop'))
        bot.edit_message_reply_markup(message.chat.id, status_message.message_id, reply_markup=stop_button)
        
        for i in range(reports_number):
            reporting_account = next(accounts)
            #
            success_reports += 1  
            bot.edit_message_text(chat_id=message.chat.id, message_id=status_message.message_id, text=f'𝗥𝗘𝗣𝗢𝗥𝗧𝗜𝗡𝗚 𝗗𝗘𝗧𝗔𝗜𝗟𝗦 🤖\n[𝗥𝗘𝗣𝗢𝗥𝗧 𝗔𝗖𝗖𝗢𝗨𝗡𝗧 : @{reported_account}]\n[𝗧𝗢𝗧𝗔𝗟 𝗥𝗘𝗣𝗢𝗥𝗧𝗦: {reports_number}, 𝗦𝗨𝗖𝗖𝗘𝗦𝗦: ✅{success_reports}, 𝗙𝗔𝗜𝗟𝗘𝗗: ❌{failed_reports}]')
            time.sleep(5)
            if i % 3 == 0:  
                failed_reports += 1
                bot.edit_message_text(chat_id=message.chat.id, message_id=status_message.message_id, text=f'𝗥𝗘𝗣𝗢𝗥𝗧𝗜𝗡𝗚 𝗗𝗘𝗧𝗔𝗜𝗟𝗦 🤖\n[𝗥𝗘𝗣𝗢𝗥𝗧 𝗔𝗖𝗖𝗢𝗨𝗡𝗧 : @{reported_account}]\n[𝗧𝗢𝗧𝗔𝗟 𝗥𝗘𝗣𝗢𝗥𝗧𝗦: {reports_number}, 𝗦𝗨𝗖𝗖𝗘𝗦𝗦: ✅{success_reports}, 𝗙𝗔𝗜𝗟𝗘𝗗: ❌{failed_reports}]')
        bot.send_message(message.chat.id, 'تم تنفيذ جميع البلاغات بنجاح ✅')
    except ValueError:
        bot.send_message(message.chat.id, 'أدخل عدد صحيح')

@bot.callback_query_handler(func=lambda call: call.data == 'stop')
def stop_reporting(call):
    bot.send_message(call.message.chat.id, 'تم إيقاف الإبلاغ.')
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
@bot.callback_query_handler(func=lambda call: call.data == 'cleanac')
def clean_accounts(call):
    valid_accounts = 0
    invalid_accounts = 0
    invalid_usernames = []

    with open('accounts.txt', 'r') as file:
        accounts = file.readlines()
        for account_line in accounts:
            try:
                user, password = re.split('[:|]', account_line.strip())
                L.login(user, password)
                valid_accounts += 1
            except (instaloader.BadCredentialsException, 
                    instaloader.TwoFactorAuthRequiredException, 
                    instaloader.ConnectionException):
                invalid_accounts += 1
                invalid_usernames.append(user)

    # إرسال النتائج إلى المستخدم
    bot.send_message(call.message.chat.id, f'عدد الحسابات الصحيحة: {valid_accounts}')
    bot.send_message(call.message.chat.id, f'عدد الحسابات التالفة: {invalid_accounts}')
    bot.send_message(call.message.chat.id, f'مجموع الحسابات: {valid_accounts + invalid_accounts}')
    if invalid_usernames:
        bot.send_message(call.message.chat.id, f'يوزرات الحسابات التالفة: {", ".join(invalid_usernames)}')
    # ...
print("   Bot is Active ")
bot.infinity_polling()