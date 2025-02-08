import sqlite3
from flask import Flask, request, jsonify
import re
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

conn = sqlite3.connect('bot_data.db')
cursor = conn.cursor()
print("1")
# إنشاء الجداول في قاعدة البيانات
cursor.execute('''
    CREATE TABLE IF NOT EXISTS banned_users (
        user_id INTEGER PRIMARY KEY
    )
''')
cursor.execute('''
    CREATE TABLE IF NOT EXISTS admins (
        user_id INTEGER PRIMARY KEY
    )
''')

cursor.execute("""
CREATE TABLE IF NOT EXISTS PENDING (
    transaction_code INTEGER PRIMARY KEY,
    amount INTEGER NOT NULL
);
""")

cursor.execute('''
    CREATE TABLE IF NOT EXISTS bot_status (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        status TEXT NOT NULL DEFAULT 'running'
    )
''')

cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        first_name TEXT,
        last_name TEXT,
        game TEXT,
        points INTEGER DEFAULT 0,
        purchases INTEGER DEFAULT 0
    )
''')
print("2")
DEFAULT_ADMIN_ID = 6931799020  # استبدل بـ معرفك الخاص
cursor.execute('INSERT OR IGNORE INTO admins (user_id) VALUES (?)', (DEFAULT_ADMIN_ID,))

conn.commit()
conn.close()

print("3")

print("5")

# إعدادات البوت
import os

TOKEN = os.getenv("TOKEN1")
bot = telebot.TeleBot(TOKEN)


def is_bot_running():
    with sqlite3.connect('bot_data.db') as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT status FROM bot_status ORDER BY id DESC LIMIT 1")
        result = cursor.fetchone()
        return result and result[0] == "running"


def is_user_banned(user_id):
    conn = sqlite3.connect('bot_data.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM banned_users WHERE user_id = ?', (user_id,))
    result = cursor.fetchone()
    conn.close()
    return result is not None

def is_admin(user_id):
    conn = sqlite3.connect('bot_data.db')
    cursor = conn.cursor()
    cursor.execute('SELECT user_id FROM admins WHERE user_id = ?', (user_id,))
    is_admin = cursor.fetchone() is not None
    conn.close()
    return is_admin

# دالة الترحيب عند بدء المحادثة
@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = message.from_user.id
    # الاتصال بقاعدة البيانات
    with sqlite3.connect('bot_data.db') as conn:
        cursor = conn.cursor()
        # التحقق إذا كان المستخدم إداريًا
        cursor.execute('SELECT 1 FROM admins WHERE user_id = ?', (user_id,))
        is_admin = cursor.fetchone() is not None
        # التحقق من حالة البوت إذا لم يكن المستخدم إداريًا
        if not is_admin:
            cursor.execute('SELECT status FROM bot_status ORDER BY id DESC LIMIT 1')
            bot_status = cursor.fetchone()
            if bot_status and bot_status[0] == 'stopped':
                # إذا كان البوت متوقفًا
                bot.reply_to(
                    message, 
                    "سيتم تشغيل البوت قريبا ‼️."
                )
                return
        # التحقق إذا كان المستخدم محظورًا
        cursor.execute('SELECT * FROM banned_users WHERE user_id = ?', (user_id,))
        banned_user = cursor.fetchone()

        if banned_user:
            # إذا كان المستخدم محظورًا
            bot.reply_to(
                message, 
                "لقد تم حظرك من البوت ⛔"
            )
            return
    
    markup = InlineKeyboardMarkup()
    markup.add(
        InlineKeyboardButton("💵 الإيداع اليدوي", callback_data='manual_deposit'),
        InlineKeyboardButton("⚡ الإيداع التلقائي", callback_data='auto_deposit'),
        InlineKeyboardButton("ℹ️ كيفية الإيداع", callback_data='how_to_deposit')
    )
    bot.reply_to(
        message,
        "مرحباً! اختر طريقة الإيداع:",
        reply_markup=markup
    )
print("farse")

@bot.callback_query_handler(func=lambda call: call.data == 'manual_deposit')
def manual_deposit(call):
    user_id = call.from_user.id
    # التحقق مما إذا كان البوت متوقفًا
    with sqlite3.connect('bot_data.db') as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT status FROM bot_status ORDER BY id DESC LIMIT 1')
        bot_status = cursor.fetchone()
        if bot_status and bot_status[0] == "stopped":
            # التحقق مما إذا كان المستخدم إداريًا
            cursor.execute('SELECT 1 FROM admins WHERE user_id = ?', (user_id,))
            is_admin = cursor.fetchone() is not None

            if not is_admin:
                bot.edit_message_text(
                    chat_id=call.message.chat.id,
                    message_id=call.message.message_id,
                    text="سيتم تشغيل البوت قريبا ‼️."
                )
                return

    # تحقق مما إذا كان المستخدم محظورًا
    if is_user_banned(user_id):
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text="لقد تم حظرك من البوت ⛔"
        )
        return 
    
    # تعديل الرسالة الأصلية وإضافة زر "العودة"
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("🔙 العودة", callback_data='go_back'))
    
    bot.edit_message_text(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text="يرجى الدفع عبر سيريتيل كاش باستخدام التحويل اليدوي:\n\n0991971467\n\nثم أرسل صورة عملية التحويل هنا.",
        reply_markup=markup
    )

@bot.callback_query_handler(func=lambda call: call.data == 'go_back')
def go_back(call):
    user_id = call.from_user.id
    # التحقق مما إذا كان البوت متوقفًا
    with sqlite3.connect('bot_data.db') as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT status FROM bot_status ORDER BY id DESC LIMIT 1')
        bot_status = cursor.fetchone()
        if bot_status and bot_status[0] == "stopped":
            # التحقق مما إذا كان المستخدم إداريًا
            cursor.execute('SELECT 1 FROM admins WHERE user_id = ?', (user_id,))
            is_admin = cursor.fetchone() is not None

            if not is_admin:
                bot.edit_message_text(
                    chat_id=call.message.chat.id,
                    message_id=call.message.message_id,
                    text="سيتم تشغيل البوت قريبا ‼️."
                )
                return

    # تحقق مما إذا كان المستخدم محظورًا
    if is_user_banned(user_id):
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text="لقد تم حظرك من البوت ⛔"
        )
        return 
    
    # حذف رسالة "العودة"
    bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)

    # إعادة إرسال الرسالة الأساسية مع الأزرار
    markup = InlineKeyboardMarkup()
    markup.add(
        InlineKeyboardButton("💵 الإيداع اليدوي", callback_data='manual_deposit'),
        InlineKeyboardButton("⚡ الإيداع التلقائي", callback_data='auto_deposit'),
        InlineKeyboardButton("ℹ️ كيفية الإيداع", callback_data='how_to_deposit')
    )
    
    bot.send_message(
        call.message.chat.id,
        "مرحباً! اختر طريقة الإيداع:",
        reply_markup=markup
    )


@bot.callback_query_handler(func=lambda call: call.data == 'auto_deposit')
def auto_deposit(call):
    user_id = call.from_user.id
    
    # التحقق مما إذا كان البوت متوقفًا
    with sqlite3.connect('bot_data.db') as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT status FROM bot_status ORDER BY id DESC LIMIT 1')
        bot_status = cursor.fetchone()
        
        if bot_status and bot_status[0] == "stopped":
            # التحقق مما إذا كان المستخدم إداريًا
            cursor.execute('SELECT 1 FROM admins WHERE user_id = ?', (user_id,))
            is_admin = cursor.fetchone() is not None

            if not is_admin:
                bot.edit_message_text(
                    chat_id=call.message.chat.id,
                    message_id=call.message.message_id,
                    text="سيتم تشغيل البوت قريبًا ‼️."
                )
                return

    # تحقق مما إذا كان المستخدم محظورًا
    if is_user_banned(user_id):
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text="لقد تم حظرك من البوت ⛔"
        )
        return 

    # تعديل الرسالة الأساسية لاستبدالها بزر "إلغاء"
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("❌ إلغاء", callback_data='cancel_deposit'))
    
    bot.edit_message_text(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text="⚡ أنت الآن في وضع الإيداع التلقائي. أدخل رمز التحويل:",
        reply_markup=markup
    )

    # تسجيل الخطوة التالية لمعالجة إدخال المستخدم
    bot.register_next_step_handler(call.message, process_code)


def process_code(message):
    user_id = message.from_user.id
    # الاتصال بقاعدة البيانات
    with sqlite3.connect('bot_data.db') as conn:
        cursor = conn.cursor()
        # التحقق إذا كان المستخدم إداريًا
        cursor.execute('SELECT 1 FROM admins WHERE user_id = ?', (user_id,))
        is_admin = cursor.fetchone() is not None
        # التحقق من حالة البوت إذا لم يكن المستخدم إداريًا
        if not is_admin:
            cursor.execute('SELECT status FROM bot_status ORDER BY id DESC LIMIT 1')
            bot_status = cursor.fetchone()
            if bot_status and bot_status[0] == 'stopped':
                # إذا كان البوت متوقفًا
                bot.reply_to(
                    message, 
                    "سيتم تشغيل البوت قريبا ‼️."
                )
                return
        # التحقق إذا كان المستخدم محظورًا
        cursor.execute('SELECT * FROM banned_users WHERE user_id = ?', (user_id,))
        banned_user = cursor.fetchone()

        if banned_user:
            # إذا كان المستخدم محظورًا
            bot.reply_to(
                message, 
                "لقد تم حظرك من البوت ⛔"
            )
            return
    
    code = message.text
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("❌ إلغاء", callback_data='cancel_deposit'))
    msg = bot.reply_to(message, "💰 أدخل قيمة الدفع:", reply_markup=markup)
    bot.register_next_step_handler(msg, lambda m: verify_auto_deposit(m, code))

@bot.callback_query_handler(func=lambda call: call.data == 'cancel_deposit')
def cancel_deposit(call):
    user_id = call.from_user.id
    # التحقق مما إذا كان البوت متوقفًا
    with sqlite3.connect('bot_data.db') as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT status FROM bot_status ORDER BY id DESC LIMIT 1')
        bot_status = cursor.fetchone()
        if bot_status and bot_status[0] == "stopped":
            # التحقق مما إذا كان المستخدم إداريًا
            cursor.execute('SELECT 1 FROM admins WHERE user_id = ?', (user_id,))
            is_admin = cursor.fetchone() is not None

            if not is_admin:
                bot.edit_message_text(
                    chat_id=call.message.chat.id,
                    message_id=call.message.message_id,
                    text="سيتم تشغيل البوت قريبا ‼️."
                )
                return

    # تحقق مما إذا كان المستخدم محظورًا
    if is_user_banned(user_id):
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text="لقد تم حظرك من البوت ⛔"
        )
        return 
    
    # حذف رسالة "إلغاء"
    # إعادة إرسال الرسالة الأساسية مع الأزرار
    markup = InlineKeyboardMarkup()
    markup.add(
        InlineKeyboardButton("💵 الإيداع اليدوي", callback_data='manual_deposit'),
        InlineKeyboardButton("⚡ الإيداع التلقائي", callback_data='auto_deposit'),
        InlineKeyboardButton("ℹ️ كيفية الإيداع", callback_data='how_to_deposit')
    )
    bot.clear_step_handler_by_chat_id(chat_id=call.message.chat.id)

    bot.edit_message_text(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text="مرحبًا! اختر طريقة الإيداع:",
        reply_markup=markup
    )
@bot.callback_query_handler(func=lambda call: call.data == 'cancel')
def cancel_deposit(call):
    user_id = call.from_user.id
    # التحقق مما إذا كان البوت متوقفًا
    with sqlite3.connect('bot_data.db') as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT status FROM bot_status ORDER BY id DESC LIMIT 1')
        bot_status = cursor.fetchone()
        if bot_status and bot_status[0] == "stopped":
            # التحقق مما إذا كان المستخدم إداريًا
            cursor.execute('SELECT 1 FROM admins WHERE user_id = ?', (user_id,))
            is_admin = cursor.fetchone() is not None

            if not is_admin:
                bot.edit_message_text(
                    chat_id=call.message.chat.id,
                    message_id=call.message.message_id,
                    text="سيتم تشغيل البوت قريبا ‼️."
                )
                return

    # تحقق مما إذا كان المستخدم محظورًا
    if is_user_banned(user_id):
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text="لقد تم حظرك من البوت ⛔"
        )
        return 
    
    # حذف رسالة "إلغاء"
    # إعادة إرسال الرسالة الأساسية مع الأزرار
    markup = InlineKeyboardMarkup()
    markup.add(
        InlineKeyboardButton("💵 الإيداع اليدوي", callback_data='manual_deposit'),
        InlineKeyboardButton("⚡ الإيداع التلقائي", callback_data='auto_deposit'),
        InlineKeyboardButton("ℹ️ كيفية الإيداع", callback_data='how_to_deposit')
    )
    bot.edit_message_text(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text="مرحبًا! اختر طريقة الإيداع:",
        reply_markup=markup
    )

def verify_auto_deposit(message, code):
    user_id = message.from_user.id
    # الاتصال بقاعدة البيانات
    with sqlite3.connect('bot_data.db') as conn:
        cursor = conn.cursor()
        # التحقق إذا كان المستخدم إداريًا
        cursor.execute('SELECT 1 FROM admins WHERE user_id = ?', (user_id,))
        is_admin = cursor.fetchone() is not None
        # التحقق من حالة البوت إذا لم يكن المستخدم إداريًا
        if not is_admin:
            cursor.execute('SELECT status FROM bot_status ORDER BY id DESC LIMIT 1')
            bot_status = cursor.fetchone()
            if bot_status and bot_status[0] == 'stopped':
                # إذا كان البوت متوقفًا
                bot.reply_to(
                    message, 
                    "سيتم تشغيل البوت قريبا ‼️."
                )
                return
        # التحقق إذا كان المستخدم محظورًا
        cursor.execute('SELECT * FROM banned_users WHERE user_id = ?', (user_id,))
        banned_user = cursor.fetchone()

        if banned_user:
            # إذا كان المستخدم محظورًا
            bot.reply_to(
                message, 
                "لقد تم حظرك من البوت ⛔"
            )
            return
    
    amount = message.text
    conn = sqlite3.connect('bot_data.db')
    cursor = conn.cursor()
    
    # التحقق من وجود تحويل مع الكود والمبلغ في جدول PENDING
    cursor.execute('SELECT * FROM PENDING WHERE transaction_code = ? AND amount = ?', (code, amount))
    pending_transaction = cursor.fetchone()

    if pending_transaction:
        # إذا تم العثور على التحويل، نقوم بتحديث النقاط للمستخدم
        cursor.execute('SELECT user_id FROM users WHERE user_id = ?', (message.from_user.id,))
        user = cursor.fetchone()
        
        if user:
            # تحديث النقاط بناءً على المبلغ المدفوع
            cursor.execute('UPDATE users SET points = points + ? WHERE user_id = ?', (amount, message.from_user.id))
        else:
            # إذا لم يكن المستخدم موجودًا في جدول users، نقوم بإضافته
            cursor.execute('INSERT INTO users (user_id, first_name, last_name, game, points) VALUES (?, ?, ?, ?, ?)',
                           (message.from_user.id, message.from_user.first_name, message.from_user.last_name, 'GameName', amount))
        
        # بعد التحديث، نقوم بحذف السجل من جدول PENDING (لأن التحويل تم)
        cursor.execute('DELETE FROM PENDING WHERE transaction_code = ? AND amount = ?', (code, amount))
        conn.commit()
        
        # إرسال رسالة تأكيد للمستخدم
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("الرجوع ↩", callback_data="cancel"))
        bot.reply_to(message, f"✅ تم تأكيد الإيداع بنجاح! لقد حصلت على {amount} نقطة.", reply_markup=markup)
    else:
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("الرجوع ↩", callback_data="cancel"))
        bot.reply_to(message, "❌ لم يتم العثور على بيانات تحويل مطابقة.", reply_markup=markup)
    
    conn.close()


@bot.callback_query_handler(func=lambda call: call.data == 'how_to_deposit')
def how_to_deposit(call):
    user_id = call.from_user.id
    # التحقق مما إذا كان البوت متوقفًا
    with sqlite3.connect('bot_data.db') as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT status FROM bot_status ORDER BY id DESC LIMIT 1')
        bot_status = cursor.fetchone()
        if bot_status and bot_status[0] == "stopped":
            # التحقق مما إذا كان المستخدم إداريًا
            cursor.execute('SELECT 1 FROM admins WHERE user_id = ?', (user_id,))
            is_admin = cursor.fetchone() is not None

            if not is_admin:
                bot.edit_message_text(
                    chat_id=call.message.chat.id,
                    message_id=call.message.message_id,
                    text="سيتم تشغيل البوت قريبا ‼️."
                )
                return

    # تحقق مما إذا كان المستخدم محظورًا
    if is_user_banned(user_id):
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text="لقد تم حظرك من البوت ⛔"
        )
        return  # إيقاف الدالة إذا كان المستخدم محظورًا


    # حذف الرسالة الأساسية
    bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)

    # إرسال التعليمات خطوة بخطوة مع الصور
    steps = [
        ("حمل تطبيق اقرب اليك اذا لم يكن موجود لديك وعندما تدخل اليه اضغط على سيرياتيل كاش", "how_to_deposit_1.jpg"),
        ("أنشئ حساب سيرياتيل كاش اذا لم يكن موجود عندك ثم قم بالضغط على التحويل اليدوي", "how_to_deposit_2.jpg"),
        ("ادخل رقم 0991971467 في الخانة المخصصة له مرتين ثم ادخل المبلغ المراد ايداعه واكده", "how_to_deposit_3.jpg")
    ]

    for text, image in steps:
        bot.send_message(call.message.chat.id, text)
        bot.send_photo(call.message.chat.id, photo=open(image, 'rb'))

    # إعادة إرسال الرسالة الأساسية مع الأزرار بعد عرض التعليمات
    markup = InlineKeyboardMarkup()
    markup.add(
        InlineKeyboardButton("💵 الإيداع اليدوي", callback_data='manual_deposit'),
        InlineKeyboardButton("⚡ الإيداع التلقائي", callback_data='auto_deposit'),
        InlineKeyboardButton("ℹ️ كيفية الإيداع", callback_data='how_to_deposit')
    )

    bot.send_message(
        call.message.chat.id,
        "مرحباً! اختر طريقة الإيداع:",
        reply_markup=markup
    )



# دالة لمعالجة الصور المرسلة من المستخدمين
user_pending_messages = {}  # تخزين معرف الرسالة لكل مستخدم

@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    user_id = message.from_user.id
    # الاتصال بقاعدة البيانات
    with sqlite3.connect('bot_data.db') as conn:
        cursor = conn.cursor()
        # التحقق إذا كان المستخدم إداريًا
        cursor.execute('SELECT 1 FROM admins WHERE user_id = ?', (user_id,))
        is_admin = cursor.fetchone() is not None
        # التحقق من حالة البوت إذا لم يكن المستخدم إداريًا
        if not is_admin:
            cursor.execute('SELECT status FROM bot_status ORDER BY id DESC LIMIT 1')
            bot_status = cursor.fetchone()
            if bot_status and bot_status[0] == 'stopped':
                # إذا كان البوت متوقفًا
                bot.reply_to(
                    message, 
                    "سيتم تشغيل البوت قريبا ‼️."
                )
                return
        # التحقق إذا كان المستخدم محظورًا
        cursor.execute('SELECT * FROM banned_users WHERE user_id = ?', (user_id,))
        banned_user = cursor.fetchone()

        if banned_user:
            # إذا كان المستخدم محظورًا
            bot.reply_to(
                message, 
                "لقد تم حظرك من البوت ⛔"
            )
            return

    user_id = message.from_user.id
    username = message.from_user.username or "غير متوفر"
    photo_id = message.photo[-1].file_id

    markup = InlineKeyboardMarkup()
    markup.add(
        InlineKeyboardButton("✅ قبول", callback_data=f"accept_{user_id}"),
        InlineKeyboardButton("❌ رفض", callback_data=f"reject_{user_id}")
    )

    conn = sqlite3.connect('bot_data.db')
    cursor = conn.cursor()
    cursor.execute('SELECT user_id FROM admins')
    admins = cursor.fetchall()
    conn.close()

    for admin in admins:
        admin_id = admin[0]
        bot.send_photo(
            admin_id,
            photo_id,
            caption=f"📸 صورة عملية التحويل من المستخدم:\n🔹 معرف: {user_id}\n🔸 اسم المستخدم: @{username}",
            reply_markup=markup
        )

    # إرسال رسالة تأكيد وحفظ معرفها
    sent_message = bot.reply_to(message, "🔄 تم إرسال صورة عملية التحويل للإدمن. سيتم إبلاغك عند مراجعة طلبك.")
    user_pending_messages[user_id] = sent_message.message_id

@bot.callback_query_handler(func=lambda call: call.data.startswith("accept_") or call.data.startswith("reject_"))
def process_request(call):
    user_id = call.from_user.id
    # التحقق مما إذا كان البوت متوقفًا
    with sqlite3.connect('bot_data.db') as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT status FROM bot_status ORDER BY id DESC LIMIT 1')
        bot_status = cursor.fetchone()
        if bot_status and bot_status[0] == "stopped":
            # التحقق مما إذا كان المستخدم إداريًا
            cursor.execute('SELECT 1 FROM admins WHERE user_id = ?', (user_id,))
            is_admin = cursor.fetchone() is not None

            if not is_admin:
                bot.edit_message_text(
                    chat_id=call.message.chat.id,
                    message_id=call.message.message_id,
                    text="سيتم تشغيل البوت قريبا ‼️."
                )
                return

    # تحقق مما إذا كان المستخدم محظورًا
    if is_user_banned(user_id):
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text="لقد تم حظرك من البوت ⛔"
        )
        return  # إيقاف الدالة إذا كان المستخدم محظورًا


    user_id = int(call.data.split("_")[1])  # استخراج معرف المستخدم
    action = call.data.split("_")[0]
    bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)  # حذف رسالة الإداري

    # حذف رسالة التأكيد للمستخدم إذا كانت مسجلة
    if user_id in user_pending_messages:
        try:
            bot.delete_message(chat_id=user_id, message_id=user_pending_messages[user_id])
            del user_pending_messages[user_id]  # إزالة المستخدم من القائمة
        except Exception as e:
            print(f"خطأ في حذف الرسالة: {e}")

    if action == "accept":
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("الرجوع ↩", callback_data="cancel"))
        bot.send_message(user_id, "✅ تم قبول طلبك! سيتم إرسال النقاط لك على المتجر.", reply_markup=markup)
        bot.send_message(call.message.chat.id, "تم قبول الطلب وإبلاغ المستخدم.")
    elif action == "reject":
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("الرجوع ↩", callback_data="cancel"))
        bot.send_message(user_id, "❌ تم رفض طلبك.", reply_markup=markup)
        bot.send_message(call.message.chat.id, "تم رفض الطلب وإبلاغ المستخدم.")
# تشغيل البوت
bot.polling(none_stop=True)
