import sqlite3
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

# اتصال بقاعدة البيانات وإنشاء الجداول إذا لم تكن موجودة
conn = sqlite3.connect('bot_data.db')
cursor = conn.cursor()

# إنشاء جداول قاعدة البيانات
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

cursor.execute("""
CREATE TABLE IF NOT EXISTS PENDING (
    transaction_code INTEGER PRIMARY KEY,
    amount INTEGER NOT NULL
);
""")

cursor.execute('''
    CREATE TABLE IF NOT EXISTS banned_users (
        user_id INTEGER PRIMARY KEY
    )
''')
cursor.execute('''
    CREATE TABLE IF NOT EXISTS recharge_codes (
        game TEXT,
        amount INTEGER,
        code TEXT,
        PRIMARY KEY (game, amount, code)
    )
''')
cursor.execute('''
    CREATE TABLE IF NOT EXISTS admins (
        user_id INTEGER PRIMARY KEY
    )
''')
cursor.execute('''
        CREATE TABLE IF NOT EXISTS bot_status (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            status TEXT NOT NULL DEFAULT 'running'
        )
    ''')
cursor.execute("""
CREATE TABLE IF NOT EXISTS inquiries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    username TEXT,
    inquiry TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
""")
# إضافة الإدمن الافتراضي (يتم استبدال `DEFAULT_ADMIN_ID` بمعرف الإدمن الرئيسي)
DEFAULT_ADMIN_ID = 7311510779  # استبدل بـ معرفك الخاص
cursor.execute('INSERT OR IGNORE INTO admins (user_id) VALUES (?)', (DEFAULT_ADMIN_ID,))

conn.commit()
conn.close()

# دوال قاعدة البيانات
def add_admin_name_columns():
    conn = sqlite3.connect('bot_data.db')
    cursor = conn.cursor()
    try:
        cursor.execute('ALTER TABLE admins ADD COLUMN first_name TEXT')
        cursor.execute('ALTER TABLE admins ADD COLUMN last_name TEXT')
        conn.commit()
    except sqlite3.OperationalError:
        pass  # تجاهل الخطأ إذا كانت الأعمدة موجودة بالفعل
    finally:
        conn.close()

# ff

def add_name_columns():
    conn = sqlite3.connect('bot_data.db')
    cursor = conn.cursor()
    try:
        cursor.execute('ALTER TABLE banned_users ADD COLUMN first_name TEXT')
        cursor.execute('ALTER TABLE banned_users ADD COLUMN last_name TEXT')
        conn.commit()
    except sqlite3.OperationalError:
        pass  # تجاهل الخطأ إذا كانت الأعمدة موجودة بالفعل
    finally:
        conn.close()

add_name_columns()

def is_admin(user_id):
    conn = sqlite3.connect('bot_data.db')
    cursor = conn.cursor()
    cursor.execute('SELECT user_id FROM admins WHERE user_id = ?', (user_id,))
    is_admin = cursor.fetchone() is not None
    conn.close()
    return is_admin

def add_admin(user_id):
    conn = sqlite3.connect('bot_data.db')
    cursor = conn.cursor()
    cursor.execute('INSERT OR IGNORE INTO admins (user_id) VALUES (?)', (user_id,))
    conn.commit()
    conn.close()

def remove_admin(user_id):
    conn = sqlite3.connect('bot_data.db')
    cursor = conn.cursor()
    cursor.execute('DELETE FROM admins WHERE user_id = ?', (user_id,))
    conn.commit()
    conn.close()

def add_user(user_id, first_name=None, last_name=None, game=None):
    with sqlite3.connect('bot_data.db') as conn:
        cursor = conn.cursor()

        # إدراج المستخدم إذا لم يكن موجودًا
        cursor.execute('''
            INSERT OR IGNORE INTO users (user_id, first_name, last_name, game) 
            VALUES (?, ?, ?, ?)
        ''', (user_id, first_name, last_name, game))
        
        conn.commit()

def get_user(user_id):
    conn = sqlite3.connect('bot_data.db')
    cursor = conn.cursor()
    cursor.execute('SELECT first_name, last_name, points, purchases FROM users WHERE user_id = ?', (user_id,))
    user = cursor.fetchone()
    conn.close()
    return user

def update_users_table():
    with sqlite3.connect('bot_data.db') as conn:
        cursor = conn.cursor()
        # إضافة الأعمدة الجديدة إذا لم تكن موجودة
        cursor.execute("ALTER TABLE users ADD COLUMN first_name TEXT DEFAULT ''")
        cursor.execute("ALTER TABLE users ADD COLUMN last_name TEXT DEFAULT ''")
        
        conn.commit()

def update_user_points(user_id, points):
    conn = sqlite3.connect('bot_data.db')
    cursor = conn.cursor()
    cursor.execute('UPDATE users SET points = points + ? WHERE user_id = ?', (points, user_id))
    conn.commit()
    conn.close()

def add_banned_user(user_id):
    conn = sqlite3.connect('bot_data.db')
    cursor = conn.cursor()
    cursor.execute('INSERT OR IGNORE INTO banned_users (user_id) VALUES (?)', (user_id,))
    conn.commit()
    conn.close()

def is_user_banned(user_id):
    conn = sqlite3.connect('bot_data.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM banned_users WHERE user_id = ?', (user_id,))
    result = cursor.fetchone()
    conn.close()
    return result is not None

def add_recharge_code(game, amount, code):
    conn = sqlite3.connect('bot_data.db')
    cursor = conn.cursor()
    cursor.execute('INSERT INTO recharge_codes (game, amount, code) VALUES (?, ?, ?)', (game, amount, code))
    conn.commit()
    conn.close()

# الحصول على الأكواد بناءً على اللعبة والمبلغ
def get_recharge_codes(game, amount):
    conn = sqlite3.connect('bot_data.db')
    cursor = conn.cursor()
    cursor.execute('SELECT code FROM recharge_codes WHERE game = ? AND amount = ?', (game, amount))
    codes = cursor.fetchall()
    conn.close()
    return [code[0] for code in codes]

def is_bot_running():
    with sqlite3.connect('bot_data.db') as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT status FROM bot_status ORDER BY id DESC LIMIT 1")
        result = cursor.fetchone()
        return result and result[0] == "running"

def stop_bot():
    with sqlite3.connect('bot_data.db') as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO bot_status (status) VALUES ('stopped')")
        conn.commit()

def start_bot():
    with sqlite3.connect('bot_data.db') as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO bot_status (status) VALUES ('running')")
        conn.commit()

def setup_prices_table():
    conn = sqlite3.connect('bot_data.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS item_prices (
            item TEXT PRIMARY KEY,
            price INTEGER NOT NULL
        )
    ''')
    # إضافة العناصر الافتراضية إن لم تكن موجودة
    default_items = [
        ("ببجي", 15000),
        ("فري فاير", 15000),
        ("عضوية شهرية", 45000),
        ("عضوية إسبوعية", 15000),
        ("تصريح المستوى", 20000)
    ]
    for item, price in default_items:
        cursor.execute('INSERT OR IGNORE INTO item_prices (item, price) VALUES (?, ?)', (item, price))
    conn.commit()
    conn.close()

setup_prices_table()


# Bot token and admin ID
import os

TOKEN = os.getenv("TOKEN")
bot = telebot.TeleBot(TOKEN)

def initialize_user_data(user_id, first_name='', last_name=''):
    # الاتصال بقاعدة البيانات باستخدام `with` لضمان إغلاق الاتصال بشكل آمن
    with sqlite3.connect('bot_data.db') as conn:
        cursor = conn.cursor()

        # التحقق إذا كان المستخدم محظورًا
        cursor.execute('SELECT 1 FROM banned_users WHERE user_id = ?', (user_id,))
        if cursor.fetchone():
            return  # إذا كان المستخدم محظورًا، لا يتم تهيئة البيانات

        # التحقق إذا كان المستخدم موجودًا في جدول users
        cursor.execute('SELECT 1 FROM users WHERE user_id = ?', (user_id,))
        if not cursor.fetchone():
            # التحقق إذا كان المستخدم مشرفًا
            cursor.execute('SELECT 1 FROM admins WHERE user_id = ?', (user_id,))
            admin = cursor.fetchone()

            # إعطاء نقاط البداية للمشرفين
            initial_points = 69696969 if admin else 0

            # إدخال بيانات المستخدم
            cursor.execute('''
                INSERT INTO users (user_id, first_name, last_name, purchases, points, game) 
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (user_id, first_name or '', last_name or '', 0, initial_points, None))
            conn.commit()

def is_user_banned(user_id):
    conn = sqlite3.connect('bot_data.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM banned_users WHERE user_id = ?', (user_id,))
    result = cursor.fetchone()
    conn.close()
    return result is not None

# دالة لإنشاء القائمة الرئيسية باستخدام الأزرار المدمجة
# تعديل دالة القائمة الرئيسية
def main_menu(message):
    user_id = message.from_user.id
    
    # التحقق إذا كان المستخدم محظورًا
    if is_user_banned(user_id):
        # تعديل الرسالة الأصلية لعرض رسالة الحظر بدلاً من إرسال رسالة جديدة
        bot.edit_message_text(
            chat_id=message.chat.id,
            message_id=message.message_id,
            text="لقد تم حظرك من البوت"
        )
        return  # إيقاف الدالة للمستخدمين المحظورين
    
    # إذا لم يكن المستخدم محظورًا، يتم عرض القائمة الرئيسية
    markup = InlineKeyboardMarkup(row_width=1)
    markup.add(
        InlineKeyboardButton("شحن العاب | Recharge games 🎮🔥", callback_data="recharge"),
        InlineKeyboardButton("شراء بوتات | Buy bots 🤖✨", callback_data="buy_bots"),
        InlineKeyboardButton("حسابي | My account 🧾👤", callback_data="account"),
        InlineKeyboardButton("المساعدة و الدعم | Help & support 👨🏼‍💻ℹ️", callback_data="support"),
        InlineKeyboardButton("بوت الأيداع | Referral bot 💵🤖", url="https://t.me/firequaza_ida3_bot")
    )
    
    # التحقق من قاعدة البيانات لمعرفة ما إذا كان المستخدم إداريًا
    conn = sqlite3.connect('bot_data.db')
    cursor = conn.cursor()
    cursor.execute('SELECT 1 FROM admins WHERE user_id = ?', (user_id,))
    is_admin = cursor.fetchone() is not None
    conn.close()
    
    # إضافة زر لوحة التحكم إذا كان المستخدم إداريًا
    if is_admin:
        markup.add(InlineKeyboardButton("قائمة الأدمن | Admin panel ⚙️⚡", callback_data="admin_panel"))
    
    # الرد على رسالة المستخدم الحالية بدلاً من إرسال رسالة جديدة
    bot.reply_to(
        message,
        f"مَرحَباً {message.from_user.first_name} 🤍 \n\nأهلا و سهلا بك في متجر Firequaza 🔥🐉\n لشحن شدات PUBG , جواهر و عضويات FREE FIRE و شـراء الـبـوتـات 💎💵 \n\nإختر أحد الأزرار هنا ⬇️✨",
        reply_markup=markup
    )


    # دالة للعودة إلى القائمة الرئيسية
@bot.callback_query_handler(func=lambda call: call.data == "back_to_main_menu")
def back_to_menu(call):
    user_id = call.from_user.id
    first_name = call.from_user.first_name  # استخراج الاسم الأول

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

    # إعداد لوحة الأزرار للقائمة الرئيسية
    markup = InlineKeyboardMarkup(row_width=1)
    markup.add(
        InlineKeyboardButton("شحن الألعاب | Recharge games 🎮🔥", callback_data="recharge"),
        InlineKeyboardButton("شراء بوتات | Buy bots 🤖✨", callback_data="buy_bots"),
        InlineKeyboardButton("حسابي | My account 🧾👤", callback_data="account"),
        InlineKeyboardButton("المساعدة و الدعم | Help & support 👨🏼‍💻ℹ️", callback_data="support"),
        InlineKeyboardButton("بوت الإيداع | Referral bot 💵🤖", url="https://t.me/firequaza_ida3_bot")
    )

    # التحقق مما إذا كان المستخدم إداريًا
    is_admin = False
    with sqlite3.connect('bot_data.db') as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT 1 FROM admins WHERE user_id = ?', (user_id,))
        is_admin = cursor.fetchone() is not None

    # إضافة زر لوحة التحكم إذا كان المستخدم من المدراء
    if is_admin:
        markup.add(InlineKeyboardButton("قائمة الأدمن | Admin panel ⚙️⚡", callback_data="admin_panel"))

    # تعديل الرسالة الحالية بالقائمة الرئيسية مع الاسم الأول فقط
    bot.edit_message_text(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text=f"مرحبا {first_name} 🤍 \n\nأهلا و سهلا بك في متجر Firequaza 🔥🐉\n لشحن شدات PUBG , جواهر و عضويات FREE FIRE و شراء البوتات 💎💵 \n\إختر أحد الأزار هنا ⬇️✨",
        reply_markup=markup
    )
    
@bot.message_handler(commands=['start'])
def send_welcome(message):
    # الحصول على بيانات المستخدم
    user_id = message.from_user.id
    first_name = message.from_user.first_name or " - "
    last_name = message.from_user.last_name or " - "
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
                bot.send_message(
                    message.chat.id, 
                    "سيتم تشغيل البوت قريبا ‼️."
                )
                return
        # التحقق إذا كان المستخدم محظورًا
        cursor.execute('SELECT * FROM banned_users WHERE user_id = ?', (user_id,))
        banned_user = cursor.fetchone()

        if banned_user:
            # إذا كان المستخدم محظورًا
            bot.send_message(
                message.chat.id, 
                "لقد تم حظرك من البوت ⛔"
            )
            return
        # إذا لم يكن محظورًا، يتم تسجيل بياناته
        initialize_user_data(user_id, first_name, last_name)
    # عرض القائمة الرئيسية
    main_menu(message)

@bot.callback_query_handler(func=lambda call: call.data == "buy_bots")
def buy_bots(call):
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
    markup = InlineKeyboardMarkup(row_width=1)
    markup.add(
        InlineKeyboardButton("شراء بوت | buy a bot 🤖", callback_data="شراء بوت | buy a bot 🤖"),
        InlineKeyboardButton("الرجوع ↩", callback_data="back_to_main_menu")
    )

    bot.edit_message_text(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text="مرحبا بك في قسم شراء بوتات 🤖⚡:",
        reply_markup=markup
    )

@bot.callback_query_handler(func=lambda call: call.data == "شراء بوت | buy a bot 🤖")
def send_bot_purchase_info(call):
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
    bot.send_message(
        chat_id=call.message.chat.id,
        text="لشراء بوتات بأسعار جيدة تواصل معنا على الرقم 0967500378 عن طريق WhatsApp"
    )

@bot.callback_query_handler(func=lambda call: call.data.startswith("process_purchase_"))
def process_purchase(call):
    try:
        user_id = call.from_user.id
        data = call.data.split("_")
        bot_type = data[2]  # نوع البوت
        price = int(data[3])  # السعر

        conn = sqlite3.connect('bot_data.db')
        cursor = conn.cursor()

        # التحقق إذا كان المستخدم محظورًا
        cursor.execute('SELECT * FROM banned_users WHERE user_id = ?', (user_id,))
        banned_user = cursor.fetchone()
        if banned_user:
            bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)
            bot.send_message(
                chat_id=call.message.chat.id,
                text="لقد تم حظرك من البوت ⛔"
            )
            return

        # التحقق من حالة البوت
        cursor.execute('SELECT status FROM bot_status ORDER BY id DESC LIMIT 1')
        bot_status = cursor.fetchone()
        if bot_status and bot_status[0] == 'stopped':
            cursor.execute('SELECT 1 FROM admins WHERE user_id = ?', (user_id,))
            is_admin = cursor.fetchone() is not None
            if not is_admin:
                bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)
                bot.send_message(
                    chat_id=call.message.chat.id,
                    text="سيتم تشغيل البوت قريبا ‼️."
                )
                return

        # التحقق من بيانات المستخدم
        cursor.execute('SELECT points, purchases FROM users WHERE user_id = ?', (user_id,))
        user_data = cursor.fetchone()
        if not user_data:
            bot.send_message(call.message.chat.id, "❌ لم يتم العثور على بيانات المستخدم.")
            return

        user_points, user_purchases = user_data

        if user_points < price:
            markup = InlineKeyboardMarkup(row_width=2)
            markup.row(
                InlineKeyboardButton("الرجوع إلى البداية 🔙", callback_data="back_to_main_menu"),
                InlineKeyboardButton("الرجوع ↩", callback_data="buy_bots")
            )
            bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)
            bot.send_message(
                chat_id=call.message.chat.id,
                text="ليس لديك رصيد S.P.F كافي لإتمام العملية ❌.",
                reply_markup=markup
            )
            return

        # خصم النقاط وتحديث عدد المشتريات
        new_points = user_points - price
        new_purchases = user_purchases + 1
        cursor.execute(
            'UPDATE users SET points = ?, purchases = ? WHERE user_id = ?',
            (new_points, new_purchases, user_id)
        )
        conn.commit()

        # إعداد زر الرجوع
        markup = InlineKeyboardMarkup(row_width=2)
        markup.row(
            InlineKeyboardButton("الرجوع إلى البداية 🔙", callback_data="back_to_main_menu"),
            InlineKeyboardButton("الرجوع ↩", callback_data="buy_bots")
        )

        # رسالة النجاح
        bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)
        bot.send_message(
            chat_id=call.message.chat.id,
            text=f"شكرا لشراؤك من متجر Firequaza ❤️‍🔥. تم خصم {price} S.P.F ☑️.\n"
                 f"للحصول على بوت {bot_type}، تواصل مع الرقم 0999999 لاستلام طلبك 📞",
            reply_markup=markup
        )

    except Exception as e:
        markup = InlineKeyboardMarkup(row_width=2)
        markup.row(
            InlineKeyboardButton("الرجوع إلى البداية 🔙", callback_data="back_to_main_menu"),
            InlineKeyboardButton("الرجوع     ↩", callback_data="buy_bots")
        )
        bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)
        bot.send_message(
            chat_id=call.message.chat.id,
            text=f"❌ حدث خطأ غير متوقع: {e}",
            reply_markup=markup
        )
    finally:
        conn.close()

faq = {
    "كيف أشحن رصيد S.P.F 💲؟": "عليكَِ أن ترسلَ المبلغ المراد الحصُول علَيه من رصيد S.P.F و \n🔥 عن طريق سيريتل كاش في بوت الإيداع حيث تقوم بإرسال صورة العمليَّة ثمَّ يقوم الادمن بفحصها و إعطاؤكَِ رصيد في المتجر \n (كل 1 ليرة سورية تعادل 1 S.P.F 💵)",
    "ما هي آلية الشَّحن 💎؟": "البوت يعمل مع كودات شحن جواهر فري فاير بقيمة 100 جوهرة و شدات ببجي بقيمة 60 ✨ \n و عند طلب قيمة أكبر يتم إرسال أكثر من كود و تقوم بشحنهم عن طريق موقع ززززز",
    "كيف أصبح آدمن؟ 👤": "قم بالتواصل مع صاحب البوت عن طريق زر التواصل مع الآدمنز أو الرقم : 089090909",
}

@bot.callback_query_handler(func=lambda call: call.data == "support")
def support_callback(call):
    user_id = call.from_user.id
    with sqlite3.connect('bot_data.db') as conn:
        cursor = conn.cursor()

        # التحقق من حالة البوت
        cursor.execute('SELECT status FROM bot_status ORDER BY id DESC LIMIT 1')
        bot_status = cursor.fetchone()

        if bot_status and bot_status[0] == 'stopped':
            # التحقق مما إذا كان المستخدم إداريًا
            cursor.execute('SELECT 1 FROM admins WHERE user_id = ?', (user_id,))
            is_admin = cursor.fetchone()

            if not is_admin:
                # إذا كان البوت متوقفًا والمستخدم ليس إداريًا
                bot.edit_message_text(
                    chat_id=call.message.chat.id,
                    message_id=call.message.message_id,
                    text="سيتم تشغيل البوت قريبا ‼️.",
                )
                return

        # التحقق إذا كان المستخدم محظورًا
        if is_user_banned(user_id):
            bot.edit_message_text(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                text="لقد تم حظرك من البوت ⛔"
            )
            return

    # إعداد الأزرار مع الأسئلة الشائعة
    markup = InlineKeyboardMarkup()

# إضافة أزرار الأسئلة الشائعة
    for question, answer in faq.items():
        markup.add(InlineKeyboardButton(question, callback_data=f"faq_{question}"))

# إضافة زر "التكلم مع مدير 💬" وزر "الــرُّجُــوع ↩" مرة واحدة فقط
    markup.add(InlineKeyboardButton("التكلم مع الادمنز 💬", callback_data="contact_admin"))
    markup.add(InlineKeyboardButton("الرجوع ↩", callback_data="back_to_main_menu"))

# تعديل الرسالة الحالية
    bot.edit_message_text(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text="اختر احد الاسئلة الموجودة هنا او تواصل مع المدراء هنا ⬇️",
        reply_markup=markup
    )

@bot.callback_query_handler(func=lambda call: call.data.startswith("faq_"))
def handle_faq(call):
    question = call.data[4:]
    answer = faq.get(question, "عذرًا، هذا السؤال غير موجود.")
    markup = InlineKeyboardMarkup(row_width=2)
    markup.row(
            InlineKeyboardButton("الرجوع إلى البداية 🔙", callback_data="back_to_main_menu"),
            InlineKeyboardButton("الرجوع ↩", callback_data="support")
        )
    bot.edit_message_text(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text=f"*{question}:*\n\n{answer}",
        reply_markup=markup,
        parse_mode="Markdown"
    )

@bot.callback_query_handler(func=lambda call: call.data == "contact_admin")
def contact_admin(call):
    markup = InlineKeyboardMarkup()
    markup.add(
        InlineKeyboardButton("إلـغــاء ❌", callback_data="cancel_support")
    )
    # تعديل الرسالة بدلاً من حذفها
    bot.edit_message_text(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text="📝 اكتب رسالتك ليتم إرسالها إلى المدراء:",
        reply_markup=markup
    )
    bot.register_next_step_handler_by_chat_id(call.message.chat.id, forward_to_admin, call.from_user.id)

@bot.callback_query_handler(func=lambda call: call.data == "cancel_support")
def cancel_support(call):
    # إلغاء متابعة الخطوة التالية
    bot.clear_step_handler_by_chat_id(chat_id=call.message.chat.id)
    user_id = call.from_user.id
    first_name = call.from_user.first_name  # استخراج الاسم الأول

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

    # إعداد لوحة الأزرار للقائمة الرئيسية
    markup = InlineKeyboardMarkup(row_width=1)
    markup.add(
        InlineKeyboardButton("شحن الألعاب | Recharge games 🎮🔥", callback_data="recharge"),
        InlineKeyboardButton("شراء بوتات | Buy bots 🤖✨", callback_data="buy_bots"),
        InlineKeyboardButton("حسابي | My account 🧾👤", callback_data="account"),
        InlineKeyboardButton("المساعدة و الدعم | Help & support 👨🏼‍💻ℹ️", callback_data="support"),
        InlineKeyboardButton("بوت الإيداع | Referral bot 💵🤖", url="https://t.me/firequaza_ida3_bot")
    )

    # التحقق مما إذا كان المستخدم إداريًا
    is_admin = False
    with sqlite3.connect('bot_data.db') as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT 1 FROM admins WHERE user_id = ?', (user_id,))
        is_admin = cursor.fetchone() is not None

    # إضافة زر لوحة التحكم إذا كان المستخدم من المدراء
    if is_admin:
        markup.add(InlineKeyboardButton("قائمة الأدمن | Admin panel ⚙️⚡", callback_data="admin_panel"))

    # تعديل الرسالة الحالية بالقائمة الرئيسية مع الاسم الأول فقط
    bot.edit_message_text(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text=f"مَرحَباً {first_name} 🤍 \n\nأهلا و سهلاً بك في متجر Firequaza 🔥🐉\n لشحن شدات PUBG , جواهر و عضويات FREE FIRE و شـراء البوتات 💎💵 \n\nإختر أحد الأزرار هنا ⬇️✨",
        reply_markup=markup
    )

def forward_to_admin(message, user_id):
    try:
        # الحصول على معرف المدراء من قاعدة البيانات
        conn = sqlite3.connect("bot_data.db")
        cursor = conn.cursor()
        cursor.execute("SELECT user_id FROM admins")
        admins = cursor.fetchall()

        if not admins:
            bot.send_message(message.chat.id, "❌ لا يوجد مدراء لاستلام الرسالة.")
            return

        # حفظ الرسالة في قاعدة البيانات
        cursor.execute(
            "INSERT INTO inquiries (user_id, username, inquiry) VALUES (?, ?, ?)",
            (user_id, message.from_user.username or "غير معروف", message.text)
        )
        conn.commit()

        # إرسال الرسالة إلى المدراء مع زر "الرد على المستخدم"
        for admin in admins:
            admin_id = admin[0]
            markup = InlineKeyboardMarkup(row_width=2)
            markup.add(InlineKeyboardButton("الرد على المستخدم 📩", callback_data=f"reply_to_user_{user_id}_{message.message_id}"))
            
            bot.send_message(
                admin_id,
                f"سؤال من المستخدم @{message.from_user.username or 'غير معروف'} (ID: {user_id}):\n\n{message.text}",
                reply_markup=markup
            )

        conn.close()

        # إعداد الأزرار لتأكيد الإرسال للمستخدم
        markup = InlineKeyboardMarkup(row_width=2)
        markup.row(
            InlineKeyboardButton("الرجوع إلى البداية 🔙", callback_data="back_to_main_menu"),
            InlineKeyboardButton("الرجوع ↩", callback_data="support")
        )

        # تأكيد الإرسال للمستخدم مع زر الرجوع
        bot.send_message(
            chat_id=message.chat.id,
            text="تم إرسال سؤالك إلى الأدمنز ✅.\n سيتم الرد عليك قريبا 🙏🏼.",
            reply_markup=markup
        )

    except Exception as e:
        bot.send_message(message.chat.id, f"❌ حدث خطأ أثناء إرسال الرسالة: {e}")


@bot.callback_query_handler(func=lambda call: call.data.startswith("reply_to_user"))
def reply_to_user(call):
    try:
        # استخراج المعرفات
        data = call.data.split('_')
        user_id = int(data[3])
        message_id = int(data[4])

        # إعداد أزرار الإلغاء والرجوع
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("إلغاء ✖️", callback_data="cancel_support"))

        # استبدال الرسالة السابقة بطلب الرد من الإداري
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text="اكتب الرد على سؤال المستخدم 📥:",
            reply_markup=markup
        )
        
        # انتظار الرد من الإداري
        bot.register_next_step_handler(call.message, process_reply_content, user_id, message_id)
    
    except Exception as e:
        bot.send_message(call.message.chat.id, f"❌ حدث خطأ أثناء العملية: {e}")


def process_reply_content(message, user_id, message_id):
    try:
        # نص الرسالة المُدخل من الإداري
        custom_reply = message.text.strip()

        # إرسال الرد للمستخدم مع عمل رد على السؤال
        bot.send_message(
            user_id,
            f"{custom_reply} ",
            reply_to_message_id=message_id
        )

        # إعداد أزرار الرجوع إلى القائمة الرئيسية
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("الرجوع ↩", callback_data="admin_panel"))

        # استبدال الرسالة السابقة بالرد على الرسالة
        bot.send_message(
            message.chat.id,
            f"تـم إرسال ردك إلى المستخدم {user_id} بـنـجـاح ✅.",
            reply_markup=markup
        )

    except Exception as e:
        bot.send_message(message.chat.id, f"❌ حدث خطأ أثناء إرسال الرد: {e}")


@bot.callback_query_handler(func=lambda call: call.data == "account")
def show_account_info(call):
    user_id = call.from_user.id

    # الاتصال بقاعدة البيانات
    with sqlite3.connect('bot_data.db') as conn:
        cursor = conn.cursor()

        # التحقق من حالة البوت
        cursor.execute('SELECT status FROM bot_status ORDER BY id DESC LIMIT 1')
        bot_status = cursor.fetchone()

        # التحقق مما إذا كان البوت متوقفًا
        if bot_status and bot_status[0] == 'stopped':
            # التحقق مما إذا كان المستخدم إداريًا
            cursor.execute('SELECT 1 FROM admins WHERE user_id = ?', (user_id,))
            is_admin = cursor.fetchone()

            if not is_admin:
                # إذا لم يكن المستخدم إداريًا، يتم إعلامه بأن البوت متوقف
                bot.answer_callback_query(
                    call.id,
                    "سيتم تشغيل البوت قريبا ‼️.",
                    show_alert=True
                )
                return

        # التحقق إذا كان المستخدم محظورًا
        cursor.execute('SELECT * FROM banned_users WHERE user_id = ?', (user_id,))
        banned_user = cursor.fetchone()

        if banned_user:
            # إذا كان المستخدم محظورًا
            bot.answer_callback_query(
                call.id,
                "لقد تم حظرك من البوت ⛔",
                show_alert=True
            )
            return

        # إذا لم يكن المستخدم محظورًا، استرجاع بياناته
        cursor.execute('SELECT purchases, points FROM users WHERE user_id = ?', (user_id,))
        user = cursor.fetchone()

        if user:
            # استرجاع النقاط والمشتريات من قاعدة البيانات
            purchases = user[0]  # assuming purchases is the 1st column in the result
            points = user[1]     # assuming points is the 2nd column in the result

            # عرض المعلومات كإشعار
            bot.answer_callback_query(
                call.id,
                f"🔹 المعرف الخاص بك : {user_id}\n🔸 عدد مرات الشراء : {purchases}\n💰 رصيدك : {points} S.P.F",
                show_alert=True
            )
        else:
            bot.answer_callback_query(
                call.id,
                "⚠️ لم يتم العثور على حسابك في النظام.",
                show_alert=True
            )

# دالة لإظهار خيارات الشحن
@bot.callback_query_handler(func=lambda call: call.data == "recharge")
def show_recharge_options(call):
    user_id = call.from_user.id

    # الاتصال بقاعدة البيانات
    with sqlite3.connect('bot_data.db') as conn:
        cursor = conn.cursor()

        # التحقق من حالة البوت
        cursor.execute('SELECT status FROM bot_status ORDER BY id DESC LIMIT 1')
        bot_status = cursor.fetchone()

        if bot_status and bot_status[0] == 'stopped':
            # التحقق مما إذا كان المستخدم إداريًا
            cursor.execute('SELECT 1 FROM admins WHERE user_id = ?', (user_id,))
            is_admin = cursor.fetchone()

            if not is_admin:
                # إذا كان البوت متوقفًا والمستخدم ليس إداريًا
                bot.edit_message_text(
                    chat_id=call.message.chat.id,
                    message_id=call.message.message_id,
                    text="سيتم نتشغيل البوت قريبا ‼️.",
                )
                return

        # التحقق إذا كان المستخدم محظورًا
        if is_user_banned(user_id):
            bot.edit_message_text(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                text="لقد تم حظرك من البوت ⛔"
            )
            return

        # تهيئة بيانات المستخدم
        initialize_user_data(user_id)

        # إعداد الأزرار مع زر الالــرجــوع ↩
        markup = InlineKeyboardMarkup(row_width=1)
        markup.add(
            InlineKeyboardButton("ببجي | PUBG 💵🪖", callback_data="game_pubg"),
            InlineKeyboardButton("فري فاير | FREE FIRE 💎🔥", callback_data="game_freefire"),
            InlineKeyboardButton("↩ الرجوع", callback_data="back_to_main_menu")
        )

        try:
            # تعديل الرسالة الأصلية بدلاً من إرسال رسالة جديدة
            bot.edit_message_text(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                text="🎮⬇️ *اختر اللعبة التي تريد شحنها :*",
                parse_mode="Markdown",
                reply_markup=markup
            )
        except Exception as e:
            # التعامل مع أي خطأ غير متوقع
            bot.send_message(
                chat_id=call.message.chat.id,
                text=f"❌ حدث خطأ أثناء معالجة طلبك: {e}"
            )

# دالة لإظهار المبالغ التي يمكن شحنها حسب اللعبة
@bot.callback_query_handler(func=lambda call: call.data.startswith("game_"))
def show_recharge_amounts(call):
    user_id = call.from_user.id

    # التحقق من حالة البوت
    with sqlite3.connect('bot_data.db') as conn:
        cursor = conn.cursor()

        cursor.execute('SELECT status FROM bot_status ORDER BY id DESC LIMIT 1')
        bot_status = cursor.fetchone()

        if bot_status and bot_status[0] == 'stopped':
            # التحقق مما إذا كان المستخدم إداريًا
            cursor.execute('SELECT 1 FROM admins WHERE user_id = ?', (user_id,))
            is_admin = cursor.fetchone()

            if not is_admin:
                # إذا كان البوت متوقفًا والمستخدم ليس إداريًا
                bot.edit_message_text(
                    chat_id=call.message.chat.id,
                    message_id=call.message.message_id,
                    text="سيتم تشغيل البوت قريبا ‼️.",
                )
                return

    # التحقق إذا كان المستخدم محظورًا
    if is_user_banned(user_id):
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text="لقد تم حظرك من البوت ⛔"
        )
        return

    # التحقق من بيانات المستخدم في قاعدة البيانات
    initialize_user_data(user_id)

    # استخراج اللعبة من بيانات الاستعلام
    game = call.data.split("_")[1]

    # تحديد اسم اللعبة
    game_name = "ببجي" if game == "pubg" else "فري فاير"

    # تحديث اللعبة في قاعدة البيانات
    with sqlite3.connect('bot_data.db') as conn:
        cursor = conn.cursor()
        cursor.execute('UPDATE users SET game = ? WHERE user_id = ?', (game_name, user_id))
        conn.commit()

    # تحديد العملة وخيارات الشحن بناءً على اللعبة
    if game == "pubg":
        currency = "شدة"
        recharge_options = [
            (60, "شدة"), (120, "شدة"), (180, "شدة"), (300, "شدة"), (600, "شدة")
        ]
    else:
        currency = "جوهرة"
        recharge_options = [
            (100, "جوهرة"), (200, "جوهرة"), (300, "جوهرة"), (500, "جوهرة"), (1000, "جوهرة")
        ]

    # إعداد الأزرار مع زر الرجوع
    markup = InlineKeyboardMarkup()
    for amount, currency_name in recharge_options:
        markup.add(InlineKeyboardButton(f"{amount} {currency_name}", callback_data=f"recharge_{amount}"))

    # إضافة الأزرار الإضافية فقط إذا كانت اللعبة "فري فاير"
    if game == "freefire":
        markup.add(InlineKeyboardButton(" العضوية الإسبوعية | Weekly Membership 🟪⭐", callback_data="membership_عضوية إسبوعية"))
        markup.add(InlineKeyboardButton("العصوية الهشرية | Monthly Membership 🟨🌟", callback_data="membership_عضوية شهرية"))
        markup.add(InlineKeyboardButton("تصريح المستوى | Level Up Pass 🔥✨", callback_data="membership_تصريح المستوى"))

    markup.add(InlineKeyboardButton("الرجوع إلى البداية 🔙", callback_data="back_to_main_menu"))
    markup.add(InlineKeyboardButton("الرجوع ↩", callback_data="recharge"))

    # تعديل الرسالة الأصلية بدلاً من إرسال رسالة جديدة
    try:
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=f"🤍⬇️ * اختر قيمة الشحن ل{game_name}:*",
            parse_mode="Markdown",
            reply_markup=markup
        )
    except Exception as e:
        # التعامل مع أي خطأ غير متوقع
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=f"❌ حدث خطأ أثناء معالجة طلبك: {e}"
        )


@bot.callback_query_handler(func=lambda call: call.data == "back_to_menu")
def back_to_main_menu(call):
    user_id = call.from_user.id
    first_name = call.from_user.first_name
    last_name = call.from_user.last_name or ""  # إذا كان اسم العائلة غير موجود، نتركه فارغًا

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
                bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)
                bot.send_message(
                    call.message.chat.id,
                    "سيتم تشغيل البوت قريبا ‼️."
                )
                return

    # حذف الرسالة القديمة
    bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)

    # تحقق مما إذا كان المستخدم محظورًا
    if is_user_banned(user_id):
        bot.send_message(
            call.message.chat.id,
            "لقد تم حظرك من البوت ⛔"
        )
        return  # إيقاف الدالة إذا كان المستخدم محظورًا

    # التحقق مما إذا كان المستخدم إداريًا
    is_admin = False
    with sqlite3.connect('bot_data.db') as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT 1 FROM admins WHERE user_id = ?', (user_id,))
        is_admin = cursor.fetchone() is not None

    # إعداد لوحة الأزرار للقائمة الرئيسية
    markup = InlineKeyboardMarkup(row_width=1)
    markup.add(
        InlineKeyboardButton("شحن الألعاب | Recharge games 🎮🔥", callback_data="recharge"),
        InlineKeyboardButton("شراء بوتات | Buy bots 🤖✨", callback_data="buy_bots"),
        InlineKeyboardButton("حسابي | My account 🧾👤", callback_data="account"),
        InlineKeyboardButton("المساعدة و الدعم | Help & support 👨🏼‍💻ℹ️", callback_data="support"),
        InlineKeyboardButton("بوت الإيداع | Referral bot 💵🤖", url="https://t.me/firequaza_ida3_bot"),
    )

    # إضافة زر لوحة التحكم إذا كان المستخدم من المدراء
    if is_admin:
        markup.add(InlineKeyboardButton("قائمة الأدمِن | Admin panel ⚙️⚡", callback_data="admin_panel"))

    # إرسال رسالة جديدة بالقائمة الرئيسية
    bot.send_message(
        call.message.chat.id,
        f"مَرحَباً {first_name} 🤍 \n\أهلا و سهلا بك في متجر Firequaza 🔥🐉\n لشحن شدات PUBG , جواهر و عضويات FREE FIRE و وشراء البوتات 💎💵 \n\nإختَر أحد الأزرارِ هنا ⬇️✨",
        reply_markup=markup
    )

@bot.callback_query_handler(func=lambda call: call.data.startswith("membership_"))
def show_membership_confirmation(call):
    user_id = call.from_user.id

    # الاتصال بقاعدة البيانات
    conn = sqlite3.connect('bot_data.db')
    cursor = conn.cursor()

    # التحقق إذا كان المستخدم محظورًا
    cursor.execute('SELECT * FROM banned_users WHERE user_id = ?', (user_id,))
    banned_user = cursor.fetchone()

    if banned_user:
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text="لقد تم حظرك من البوت ⛔"
        )
        return

    # التحقق إذا كان البوت متوقفًا
    cursor.execute('SELECT status FROM bot_status ORDER BY id DESC LIMIT 1')
    bot_status = cursor.fetchone()
    
    # إذا كانت حالة البوت "stopped"، منع المستخدمين العاديين من المتابعة
    if bot_status and bot_status[0] == 'stopped':
        # التحقق إذا كان المستخدم إداريًا
        cursor.execute('SELECT 1 FROM admins WHERE user_id = ?', (user_id,))
        is_admin = cursor.fetchone() is not None

        if not is_admin:
            bot.edit_message_text(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                text="سيتم تشغيل البوت قريبا ‼️."
            )
            return

    membership_type = call.data.split("_")[1]

    # تحديد المسار بناءً على نوع العضوية
    if membership_type == "عضوية إسبوعية":
        image_path = "ffW.jpg"
    elif membership_type == "عضوية شهرية":
        image_path = "ffM.jpg"
    elif membership_type == "تصريح المستوى":
        image_path = "ffS.jpg"
    else:
        bot.send_message(call.message.chat.id, "❌ نوع العضوية غير صحيح.")
        return

    # استخراج السعر من قاعدة البيانات
    cursor.execute('SELECT price FROM item_prices WHERE item = ?', (membership_type,))
    price_data = cursor.fetchone()

    if not price_data:
        bot.send_message(call.message.chat.id, "❌ لم يتم العثور على سعر السلعة في قاعدة البيانات.")
        return

    price = price_data[0]

    # التحقق من التوفر
    cursor.execute(
        'SELECT COUNT(*) FROM recharge_codes WHERE game = ?',
        (membership_type,)
    )
    available_codes = cursor.fetchone()[0]
    availability = "متوفر ✔️" if available_codes > 0 else "غير متزفر ✖️"

    # إعداد رسالة التأكيد
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("تأكيد ✅", callback_data=f"confirm_membership_{membership_type}_{price}"))
    markup.add(InlineKeyboardButton("إلغاء ↩", callback_data="back_to_menu"))

    with open(image_path, "rb") as img:
        bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)    
        bot.send_photo(
            chat_id=call.message.chat.id,
            photo=img,
            caption=(
                f"اسم السلعة 📝 : {membership_type}\n"
                f"السعر 💸 : {price} S.P.F\n"
                f"الحالة : {availability}\n\n"
                "هل تريد تأكيد عملية شراؤك ❔"
            ),
            reply_markup=markup
        )

@bot.callback_query_handler(func=lambda call: call.data.startswith("confirm_membership_"))
def confirm_membership(call):
    try:
        user_id = call.from_user.id
        data = call.data.split("_")
        membership_type = data[2]

        conn = sqlite3.connect('bot_data.db')
        cursor = conn.cursor()

        # التحقق إذا كان المستخدم محظورًا
        cursor.execute('SELECT * FROM banned_users WHERE user_id = ?', (user_id,))
        banned_user = cursor.fetchone()

        if banned_user:
            bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)
            bot.send_message(
                chat_id=call.message.chat.id,
                text="لقد تم حظرك من البوت ⛔"
            )
            return

        # التحقق من حالة البوت
        cursor.execute('SELECT status FROM bot_status ORDER BY id DESC LIMIT 1')
        bot_status = cursor.fetchone()
        if bot_status and bot_status[0] == 'stopped':
            cursor.execute('SELECT 1 FROM admins WHERE user_id = ?', (user_id,))
            is_admin = cursor.fetchone() is not None
            if not is_admin:
                bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)
                bot.send_message(
                    chat_id=call.message.chat.id,
                    text="سيتم تشغيل البوت قريبا ‼️."
                )
                return

        # استخراج السعر من قاعدة البيانات بناءً على نوع العضوية
        cursor.execute('SELECT price FROM item_prices WHERE item = ?', (membership_type,))
        price_data = cursor.fetchone()
        if not price_data:
            bot.send_message(call.message.chat.id, "❌ لم يتم العثور على سعر السلعة في قاعدة البيانات.")
            return

        price = price_data[0]

        # التحقق من نقاط المستخدم
        cursor.execute('SELECT points, purchases FROM users WHERE user_id = ?', (user_id,))
        user_data = cursor.fetchone()
        if not user_data:
            bot.send_message(call.message.chat.id, "❌ لم يتم العثور على بيانات المستخدم.")
            return

        user_points, user_purchases = user_data

        if user_points < price:
            markup = InlineKeyboardMarkup(row_width=2)
            markup.row(
            InlineKeyboardButton("الرجوع إلى البداية 🔙", callback_data="back_to_main_menu"),
            InlineKeyboardButton("الرجوع ↩", callback_data="recharge")
        )  
            bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)
            bot.send_message(
                chat_id=call.message.chat.id,
                text="ليس لديك رصيد S.P.F كافي لإتمام العملية ❌.",
                reply_markup=markup
            )
            return

        # استرجاع كود العضوية من قاعدة البيانات
        cursor.execute('SELECT code FROM recharge_codes WHERE game = ? LIMIT 1', (membership_type,))
        code_data = cursor.fetchone()
        if not code_data:
            markup = InlineKeyboardMarkup(row_width=2)
            markup.row(
            InlineKeyboardButton("الرجوع إلى البداية 🔙", callback_data="back_to_main_menu"),
            InlineKeyboardButton("الرجوع ↩", callback_data="recharge")
        )  
            bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)
            bot.send_message(
                chat_id=call.message.chat.id,
                text="معتذر منك , لا يوجد أكواد في الوقت الحالي 😔",
                reply_markup=markup
            )
            return

        code = code_data[0]

        # خصم النقاط وتحديث المستخدم
        new_points = user_points - price
        new_purchases = user_purchases + 1  # زيادة عدد المشتريات
        cursor.execute('UPDATE users SET points = ?, purchases = ? WHERE user_id = ?', (new_points, new_purchases, user_id))

        # حذف الكود المستخدم من قاعدة البيانات
        cursor.execute('DELETE FROM recharge_codes WHERE game = ? AND code = ?', (membership_type, code))

        conn.commit()

        # إعداد زر الالــرجــوع ↩
        markup = InlineKeyboardMarkup(row_width=2)
        markup.row(
            InlineKeyboardButton("الرجوع إلى البداية 🔙", callback_data="back_to_main_menu"),
            InlineKeyboardButton("الرجوع ↩", callback_data="recharge")
        )  
        # إرسال الكود للمستخدم
        bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)
        bot.send_message(
            chat_id=call.message.chat.id,
            text=f"شكرا لشرئك من متجر Firequaza ❤️‍🔥 ,تم خصم {price} S.P.F ☑️.\n🎁 كود {membership_type} الخاص بك:\n{code}",
            reply_markup=markup
        )

    except Exception as e:
        markup = InlineKeyboardMarkup(row_width=2)
        markup.row(
            InlineKeyboardButton("الرجوع إلى البداية 🔙", callback_data="back_to_main_menu"),
            InlineKeyboardButton("الرجوع ↩", callback_data="recharge")
        )  
        bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)
        bot.send_message(
            chat_id=call.message.chat.id,
            text=f"❌ حدث خطأ غير متوقع: {e}",
            reply_markup=markup
        )
    finally:
        conn.close()

@bot.callback_query_handler(func=lambda call: call.data.startswith("recharge_"))
def process_recharge(call):
    user_id = call.from_user.id

    # التحقق من حالة البوت
    with sqlite3.connect('bot_data.db') as conn:
        cursor = conn.cursor()

        cursor.execute('SELECT status FROM bot_status ORDER BY id DESC LIMIT 1')
        bot_status = cursor.fetchone()

        if bot_status and bot_status[0] == 'stopped':
            # التحقق مما إذا كان المستخدم إداريًا
            cursor.execute('SELECT 1 FROM admins WHERE user_id = ?', (user_id,))
            is_admin = cursor.fetchone()

            if not is_admin:
                bot.edit_message_text(
                    chat_id=call.message.chat.id,
                    message_id=call.message.message_id,
                    text="سيتم تشغيل البوت قريبا ‼️.",
                )
                return

    # التحقق إذا كان المستخدم محظورًا
    if is_user_banned(user_id):
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text="لقد تم حظرك من البوت ⛔"
        )
        return

    try:
        # استرجاع بيانات المستخدم من قاعدة البيانات
        conn = sqlite3.connect('bot_data.db')
        cursor = conn.cursor()
        cursor.execute('SELECT game, points FROM users WHERE user_id = ?', (user_id,))
        user_data = cursor.fetchone()

        if not user_data:
            bot.send_message(call.message.chat.id, "❌ لم يتم العثور على بيانات المستخدم.")
            return

        game, user_points = user_data
        amount = int(call.data.split("_")[1])

        # استرجاع السعر من جدول الأسعار
        cursor.execute('SELECT price FROM item_prices WHERE item = ?', (game,))
        price_data = cursor.fetchone()

        if not price_data:
            bot.send_message(call.message.chat.id, "❌ لم يتم العثور على سعر اللعبة في قاعدة البيانات.")
            return

        price_per_unit = price_data[0]

        if game == "ببجي" and amount % 60 == 0:
            points_needed = (amount // 60) * price_per_unit
            required_codes = amount // 60
            currency = "شدة"
            image_path = "pubg.jpg"
        elif game == "فري فاير" and amount % 100 == 0:
            points_needed = (amount // 100) * price_per_unit
            required_codes = amount // 100
            currency = "جوهرة"
            image_path = "ff.jpg"
        else:
            bot.send_message(call.message.chat.id, "يرجى اختيار اللعبة والفئة بشكل صحيح.")
            return

        # التحقق من توفر الأكواد
        cursor.execute(
            'SELECT COUNT(*) FROM recharge_codes WHERE game = ? AND amount = ?',
            (game, amount // required_codes)
        )
        available_codes = cursor.fetchone()[0]
        availability = "مُـتـوَفِّـر ✔️" if available_codes >= required_codes else "غير متوفر ✖️"

        conn.close()

        # إعداد رسالة التأكيد
        markup = InlineKeyboardMarkup()
        markup.add(
            InlineKeyboardButton("تأكيد ✅", callback_data=f"confirm_recharge_{amount}"),
            InlineKeyboardButton("إلغاء ↩", callback_data="back_to_menu")
        )

        bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)  # حذف الرسالة الأصلية

        bot.send_photo(
            call.message.chat.id,
            photo=open(image_path, "rb"),
            caption=(
                f"اسم السلعة 📝 : {amount} {currency} \n"
                f"السعر 💸 : {points_needed} S.P.F\n"
                f"الحالة : {availability}\n\n"
                "هل تريد تأكيد عملية شراؤك ❔"
            ),
            reply_markup=markup
        )

    except Exception as e:
        bot.send_message(call.message.chat.id, "حدث خطأ غير متوقع: " + str(e))

# دالة للتعامل مع تأكيد الشحن بعد ضغط المستخدم على زر "تأكيد"
@bot.callback_query_handler(func=lambda call: call.data.startswith("confirm_recharge_"))
def confirm_recharge(call):
    try:
        user_id = call.from_user.id
        amount = int(call.data.split("_")[2])  # استخراج المبلغ من callback_data

        # الاتصال بقاعدة البيانات
        with sqlite3.connect('bot_data.db') as conn:
            cursor = conn.cursor()

            # التحقق من حالة البوت
            cursor.execute('SELECT status FROM bot_status ORDER BY id DESC LIMIT 1')
            bot_status = cursor.fetchone()

            if bot_status and bot_status[0] == 'stopped':
                # التحقق مما إذا كان المستخدم إداريًا
                cursor.execute('SELECT 1 FROM admins WHERE user_id = ?', (user_id,))
                is_admin = cursor.fetchone() is not None

                if not is_admin:
                    bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)
                    bot.send_message(
                        chat_id=call.message.chat.id,
                        text="سيتم تشغيل البوت قريبا ‼️."
                    )
                    return

            # التحقق إذا كان المستخدم محظورًا
            if is_user_banned(user_id):
                bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)
                bot.send_message(
                    chat_id=call.message.chat.id,
                    text="لقد تم حظرك من البوت ⛔"
                )
                return

            # استرجاع بيانات المستخدم
            cursor.execute('SELECT game, points, purchases FROM users WHERE user_id = ?', (user_id,))
            user_data = cursor.fetchone()
            if not user_data:
                markup = InlineKeyboardMarkup()
                markup.add(InlineKeyboardButton("الرجوع ↩", callback_data="back_to_main_menu"))
                bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)
                bot.send_message(
                    chat_id=call.message.chat.id,
                    text="❌ لم يتم العثور على بيانات المستخدم.",
                    reply_markup=markup
                )
                return

            game, user_points, user_purchases = user_data

            # استرجاع السعر لكل وحدة من جدول الأسعار
            cursor.execute('SELECT price FROM item_prices WHERE item = ?', (game,))
            price_data = cursor.fetchone()
            if not price_data:
                bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)
                bot.send_message(
                    chat_id=call.message.chat.id,
                    text="❌ لم يتم العثور على سعر اللعبة في قاعدة البيانات."
                )
                return

            price_per_unit = price_data[0]

            # تحديد النقاط المطلوبة والكودات بناءً على اللعبة والمبلغ
            if game == "ببجي" and amount % 60 == 0:
                points_needed = (amount // 60) * price_per_unit
                codes_needed = amount // 60
            elif game == "فري فاير" and amount % 100 == 0:
                points_needed = (amount // 100) * price_per_unit
                codes_needed = amount // 100
            else:
                markup = InlineKeyboardMarkup()
                markup.add(InlineKeyboardButton("الرجوع ↩", callback_data="back_to_main_menu"))
                bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)
                bot.send_message(
                    chat_id=call.message.chat.id,
                    text="❌ المبلغ غير صحيح للعبة المحددة.",
                    reply_markup=markup
                )
                return

            # التحقق من رصيد النقاط
            if user_points < points_needed:
                markup = InlineKeyboardMarkup(row_width=2)
                markup.row(
                InlineKeyboardButton("الرجوع إلى البداية 🔙", callback_data="back_to_main_menu"),
                InlineKeyboardButton("الرجوع ↩", callback_data="recharge")
            )  
                bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)
                bot.send_message(
                    chat_id=call.message.chat.id,
                    text="ليس لديك رصيد S.P.F كافي لإتمام العملية ❌.",
                    reply_markup=markup
                )
                return

            # استرجاع الأكواد من قاعدة البيانات
            cursor.execute('SELECT code FROM recharge_codes WHERE game = ? AND amount = ?', 
                           (game, 60 if game == "ببجي" else 100))
            available_codes = cursor.fetchall()

            if len(available_codes) < codes_needed:
                markup = InlineKeyboardMarkup(row_width=2)
                markup.row(
            InlineKeyboardButton("الرجوع إلى البداية 🔙", callback_data="back_to_main_menu"),
            InlineKeyboardButton("الرجوع ↩", callback_data="recharge")
        )  
                if len(available_codes) == 0:
                    bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)
                    bot.send_message(
                        chat_id=call.message.chat.id,
                        text="نعتذر منك , لا يوجد أكواد في الوقت الحالي 😔",
                        reply_markup=markup
                    )
                else:
                    bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)
                    bot.send_message(
                        chat_id=call.message.chat.id,
                        text=f"نعتذر منك 😔 , لا يوجد سوى {len(available_codes)} من الأكواد متاحة لفئة {game}.\n يرجى اختير فئة أقل أو الإنتظار حتى توفر الأكواد 🙏🏼.",
                        reply_markup=markup
                    )
                return

            # تخصيص الأكواد للمستخدم
            codes_to_send = [code[0] for code in available_codes[:codes_needed]]

            # تحديث النقاط وزيادة عدد المشتريات
            new_points = user_points - points_needed
            new_purchases = user_purchases + 1
            cursor.execute('UPDATE users SET points = ?, purchases = ? WHERE user_id = ?', (new_points, new_purchases, user_id))

            # حذف الأكواد المستخدمة
            for code in codes_to_send:
                cursor.execute('DELETE FROM recharge_codes WHERE code = ?', (code,))

            # تأكيد إلــغــاء ✖️
            conn.commit()

            # إرسال الأكواد للمستخدم
            codes_text = "\n".join(codes_to_send)
            markup = InlineKeyboardMarkup(row_width=2)
            markup.row(
            InlineKeyboardButton("الرجوع إلى البداية 🔙", callback_data="back_to_main_menu"),
            InlineKeyboardButton("الرجوع ↩", callback_data="recharge")
        )  
            bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)
            bot.send_message(
                chat_id=call.message.chat.id,
                text=f"شكرا لشرائك من متجر Firequaza ❤️‍🔥 ,تم خصم {points_needed} S.P.F ☑️.\n🎁 كود {game} الخاص بك:\n{codes_text}",
                reply_markup=markup
            )

    except Exception as e:
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("الرجوع ↩", callback_data="back_to_main_menu"))
        bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)
        bot.send_message(
            chat_id=call.message.chat.id,
            text=f"❌ حدث خطأ غير متوقع: {e}",
            reply_markup=markup
        )


# دالة للتعامل مع زر "لوحة التحكم"
@bot.callback_query_handler(func=lambda call: call.data == "admin_panel")
def admin_panel(call):
    if is_admin(call.from_user.id):
        markup = InlineKeyboardMarkup(row_width=3)

        # الصف الأول: إضافة أكواد - عرض الأكواد - حذف الأكواد
        markup.row(
            InlineKeyboardButton("إضافة أكواد ➕", callback_data="admin_add_code"),
            InlineKeyboardButton("عـرض أكواد 📃", callback_data="show_codes"),
            InlineKeyboardButton("إزالة أكواد ➖", callback_data="remove_code")
        )

        # الصف الثاني: عرض معلومات المستخدم
        markup.row(
            InlineKeyboardButton("معلومات المستخدم ℹ️", callback_data="show_user_info")
        )

        # الصف الثالث: تعديل رصيد - تصفير رصيد
        markup.row(
            InlineKeyboardButton("تعديل رصيد S.P.F ⚙️", callback_data="admin_add_points"),
            InlineKeyboardButton("تصفير رصيد S.P.F 📉", callback_data="reset_balance")
        )

        markup.row(
                    InlineKeyboardButton("عـرض أسئلة المستخدمين 📑", callback_data="view_inquiries"),
        )
        # الصف الرابع: تعديل الأسعار
        markup.row(
            InlineKeyboardButton("تعديل الأسعار 🤑", callback_data="change_prices"),
            InlineKeyboardButton("عرض الأسعار 📋", callback_data="view_prices")
        )

        # الصف الخامس: حظر مستخدم - قائمة المحظورين - إلغاء حظر مستخدم
        markup.row(
            InlineKeyboardButton("حظر مستخدم ⛔", callback_data="ban_user"),
            InlineKeyboardButton("قائمة المحظورين 📜", callback_data="banned_list"),
            InlineKeyboardButton("إلغاء حظر مستخدم ✅", callback_data="unban_user")
        )

        # الصف السادس: رسالة لمستخدم - إذاعة
        markup.row(
            InlineKeyboardButton("رسالة لمستخدم ✉️", callback_data="send_message_to_user"),
            InlineKeyboardButton("إرسال إذاعة 📢", callback_data="broadcast_message")
        )

        # الصف السابع: إضافة إداري - قائمة الإداريين - إزالة إداري
        markup.row(
            InlineKeyboardButton("إضافة آدمن ➕", callback_data="addd_admin"),
            InlineKeyboardButton("قائمة الآدمنز 📖", callback_data="admin_list"),
            InlineKeyboardButton("إزالـة آدمن ➖", callback_data="remove_admin")
        )

        # الصف الثامن: تشغيل البوت - إيقاف البوت
        markup.row(
            InlineKeyboardButton("تشغيل البوت ☑️", callback_data="start_bot"),
            InlineKeyboardButton("إيقاف البوت ❎", callback_data="stop_bot")
        )

        # الصف الأخير: الــرجــوع ↩
        markup.row(
            InlineKeyboardButton("الرجوع ↩", callback_data="back_to_main_menu")
        )

        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text="مرحبا بك أيها الادمن 👨🏼‍💻.\n اختر واحدة من الخيارات هنا ⬇️.",
            reply_markup=markup
        )
    else:
        # رسالة تحذير مع زر الالــرجــوع ↩
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("الرجوع ↩", callback_data="back_to_main_menu"))
        
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text="❌ هذا الخيار متاح فقط للمدير.",
            reply_markup=markup
        )

@bot.callback_query_handler(func=lambda call: call.data == "view_inquiries")
def view_inquiries(call):
    user_id = call.from_user.id

    # تحقق مما إذا كان المستخدم إداريًا
    if not is_admin(user_id):
        bot.answer_callback_query(call.id, "❌ هذه الميزة مخصصة للمدراء فقط.")
        return

    # جلب الاستفسارات من قاعدة البيانات
    with sqlite3.connect("bot_data.db") as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, user_id, username, inquiry FROM inquiries ORDER BY created_at DESC")
        inquiries = cursor.fetchall()

    if not inquiries:
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("الرجوع ↩", callback_data="admin_panel"))
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text="📭 لا توجد استفسارات جديدة.",
            reply_markup=markup
        )
        return

    # إعداد قائمة الاستفسارات مع الأزرار
    markup = InlineKeyboardMarkup()
    for inquiry in inquiries[:10]:  # عرض 10 استفسارات كحد أقصى
        inquiry_id, user_id, username, text = inquiry
        display_name = f"@{username}" if username else f"ID: {user_id}"
        markup.add(InlineKeyboardButton(f"{display_name} - {text[:20]}...", callback_data=f"view_inquiry_{inquiry_id}"))

    markup.add(InlineKeyboardButton("الرجوع ↩", callback_data="admin_panel"))

    bot.edit_message_text(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text="قائمة الاستفسارات و الأسئلة المحفوظة 📜:",
        reply_markup=markup
    )

@bot.callback_query_handler(func=lambda call: call.data.startswith("view_inquiry_"))
def view_inquiry_detail(call):
    inquiry_id = int(call.data.split("_")[2])

    # جلب تفاصيل الاستفسار من قاعدة البيانات
    with sqlite3.connect("bot_data.db") as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT user_id, username, inquiry, created_at FROM inquiries WHERE id = ?", (inquiry_id,))
        inquiry = cursor.fetchone()

    if not inquiry:
        bot.answer_callback_query(call.id, "❌ لم يتم العثور على هذا الاستفسار.")
        return

    user_id, username, inquiry_text, created_at = inquiry
    display_name = f"@{username}" if username else f"ID: {user_id}"
    text = (
        f"📌 **تفاصيل الاستفسار:**\n\n"
        f"👤 المستخدم: {display_name}\n"
        f"🕒 التاريخ: {created_at}\n"
        f"💬 النص:\n{inquiry_text}"
    )

    # إضافة أزرار الرجوع
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("الرجوع ↩", callback_data="view_inquiries"))

    bot.edit_message_text(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text=text,
        reply_markup=markup,
        parse_mode="Markdown"
    )

# وظيفة لحفظ استفسار المستخدم في قاعدة البيانات
def save_user_inquiry(user_id, username, inquiry):
    with sqlite3.connect("bot_data.db") as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO inquiries (user_id, username, inquiry) VALUES (?, ?, ?)",
            (user_id, username, inquiry)
        )
        conn.commit()

@bot.callback_query_handler(func=lambda call: call.data == "view_prices")
def view_prices(call):
    try:
        # الاتصال بقاعدة البيانات لاستخراج الأسعار
        conn = sqlite3.connect("bot_data.db")
        cursor = conn.cursor()

        # استرجاع الأسعار حسب الفئات
        cursor.execute("SELECT item, price FROM item_prices WHERE item IN (?, ?, ?, ?, ?)", 
                       ("ببجي", "فري فاير", "عضوية شهرية", "عضوية إسبوعية", "تصريح المستوى" ))
        prices = cursor.fetchall()
        conn.close()

        # إذا لم يتم العثور على أسعار
        if not prices:
            bot.edit_message_text(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                text="❌ لم يتم العثور على أي أسعار في قاعدة البيانات.",
            )
            return

        # بناء رسالة تحتوي على الأسعار
        prices_text = "💵 **أسعار الفئات الحالية:**\n\n"
        for item, price in prices:
            prices_text += f"🔹 {item}: {price} S.P.F\n"

        # إضافة زر للرجوع
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("الرجوع ↩", callback_data="admin_panel"))

        # إرسال الأسعار إلى الإدمن
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=prices_text,
            reply_markup=markup,
            parse_mode="Markdown"
        )
    except Exception as e:
        bot.send_message(call.message.chat.id, f"❌ حدث خطأ غير متوقع: {e}")


@bot.callback_query_handler(func=lambda call: call.data == "change_prices")
def admin_change_prices(call):
    try:
        markup = InlineKeyboardMarkup(row_width=1)
        markup.add(
            InlineKeyboardButton("ببجي | PUBG 🪖", callback_data="change_price_ببحي"),
            InlineKeyboardButton("فري فاير | FREE FIRE 🔥", callback_data="change_price_فري فاير"),
        )
        markup.add(
            InlineKeyboardButton("العضوية الإسبوعية | Weekly membership 🟣", callback_data="change_price_عضوية إسبوعية"),
            InlineKeyboardButton("العضوية الشهرية | Monthly membership 🟡", callback_data="change_price_عضوية شهرية"),
            InlineKeyboardButton("تصريح المستوى | Level up pass 💎", callback_data="change_price_تصريح مستوى"),
        )
        markup.add(InlineKeyboardButton("الرجوع ↩", callback_data="admin_panel"))

        # تعديل الرسالة الحالية
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text="اختر الفئة التي تريد تغيير سعرها 💙:\n(سيتم تغيير سعر كود الفئة المختارة 💰)",
            reply_markup=markup
        )
    except Exception as e:
        bot.send_message(call.message.chat.id, f"❌ حدث خطأ غير متوقع: {e}")


@bot.callback_query_handler(func=lambda call: call.data.startswith("change_price_"))
def admin_set_new_price(call):
    try:
        item = call.data.split("_")[2]
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("إلغاء ✖️", callback_data="cancel_operation"))

        # تعديل الرسالة الحالية
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=f"أرسـل السعر الجديد لفئة {item} 📥:",
            reply_markup=markup
        )
        bot.register_next_step_handler_by_chat_id(call.message.chat.id, lambda msg: save_new_price(msg, item))
    except Exception as e:
        bot.send_message(call.message.chat.id, f"❌ حدث خطأ غير متوقع: {e}")


def save_new_price(message, item):
    try:
        new_price = int(message.text.strip())
        if new_price <= 0:
            raise ValueError("عذراً 😬 , يجب أن يكون السعر الجديد رقما موجبا ➕.")

        # تحديث السعر في قاعدة البيانات
        conn = sqlite3.connect('bot_data.db')
        cursor = conn.cursor()
        cursor.execute('UPDATE item_prices SET price = ? WHERE item = ?', (new_price, item))
        conn.commit()
        conn.close()

        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("الرجوع ↩", callback_data="admin_panel"))

        # إرسال رسالة تأكيد
        bot.send_message(
            chat_id=message.chat.id,
            text=f"تم تحديث سعر كود {item} إلى {new_price} S.P ✅.",
            reply_markup=markup
        )
    except ValueError:
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("إلغاء ✖️", callback_data="cancel_operation"))
        msg = bot.send_message(
            chat_id=message.chat.id,
            text="عـذراً 😬 , يجب أن يكون السعر الجديد رقما موجبا ➕. حاول مرة أخرى 🔁",
            reply_markup=markup
        )
        bot.register_next_step_handler(msg, save_new_price, item)
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ حدث خطأ غير متوقع: {e}")

@bot.callback_query_handler(func=lambda call: call.data == "stop_bot")
def handle_stop_bot(call):
    user_id = call.from_user.id

    # التحقق مما إذا كان المستخدم إداريًا
    with sqlite3.connect('bot_data.db') as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT 1 FROM admins WHERE user_id = ?', (user_id,))
        is_admin = cursor.fetchone() is not None

    if not is_admin:
        bot.answer_callback_query(call.id, "❌ ليس لديك صلاحية تنفيذ هذا الإجراء.")
        return

    # التحقق من حالة البوت
    with sqlite3.connect('bot_data.db') as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT status FROM bot_status ORDER BY id DESC LIMIT 1')
        bot_status = cursor.fetchone()

    if bot_status and bot_status[0] == "stopped":
        # إذا كان البوت متوقفًا بالفعل
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("الرجوع ↩", callback_data="admin_panel"))
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text="البوت متوقف حاليا بالفعل ⚠️.",
            reply_markup=markup
        )
        return
    # إيقاف البوت
    stop_bot()
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("الرجوع ↩", callback_data="admin_panel"))
    bot.edit_message_text(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text="تم إيقاف تشغيل البوت ✅. \n لا يمكن لأي مستخدم القيام بأي شيء , فقط الأدمنز ❌",
        reply_markup=markup
    )

@bot.callback_query_handler(func=lambda call: call.data == "start_bot")
def handle_start_bot(call):
    # الاتصال بقاعدة البيانات
    with sqlite3.connect('bot_data.db') as conn:
        cursor = conn.cursor()

        # التحقق من حالة البوت
        cursor.execute('SELECT status FROM bot_status ORDER BY id DESC LIMIT 1')
        bot_status = cursor.fetchone()

        if bot_status and bot_status[0] == 'running':
            # إذا كان البوت قيد التشغيل بالفعل
            markup = InlineKeyboardMarkup()
            markup.add(InlineKeyboardButton("الرجوع ↩", callback_data="admin_panel"))
            bot.edit_message_text(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                text="البوت مشغل حاليا بالفعل ✅.",
                reply_markup=markup
            )
        else:
            # إذا كان البوت متوقفًا، يتم تشغيله
            cursor.execute("INSERT INTO bot_status (status) VALUES ('running')")
            conn.commit()

            markup = InlineKeyboardMarkup()
            markup.add(InlineKeyboardButton("الرجوع ↩", callback_data="admin_panel"))
            bot.edit_message_text(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                text="تم تشغيل البوت ينجاح ✅.",
                reply_markup=markup
            )

@bot.callback_query_handler(func=lambda call: call.data == "send_message_to_user")
def admin_send_message_start(call):
    # بدء عملية إرسال رسالة إلى مستخدم
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("إلغاء ✖️", callback_data="cancel_operation"))
    bot.edit_message_text(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text="أدخل معرف ID المستخدم المراد إرسال الرسالة له 📥:",
        reply_markup=markup
    )
    bot.register_next_step_handler(call.message, process_user_id_for_message)

def process_user_id_for_message(message):
    try:
        user_id = int(message.text.strip())  # الحصول على معرف المستخدم

        # إعداد أزرار الإلغاء والالــرجــوع ↩
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("إالغاء ✖️", callback_data="cancel_action"))
        # حفظ معرف المستخدم للمرحلة التالية
        bot.send_message(
            chat_id=message.chat.id,
            text="الآن، أرسل الرسالة المراد إرسالها 📨:",
            reply_markup=markup
        )
        bot.register_next_step_handler(message, process_message_content, user_id)

    except ValueError:
        # إذا كان الإدخال غير صحيح
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("الرجوع ↩", callback_data="admin_panel"))

        bot.send_message(
            chat_id=message.chat.id,
            text="عذرا 😬 , يجب أن يكون معرف ID المستخدم رقما صحيحا 🔢.",
            reply_markup=markup
        )

def process_message_content(message, user_id):
    try:
        # نص الرسالة المُدخل
        custom_message = message.text.strip()

        # إرسال الرسالة للمستخدم
        bot.send_message(
            user_id,
            custom_message
        )

        # إعلام المسؤول بنجاح إلــغــاء ✖️
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("الرجوع ↩", callback_data="admin_panel"))

        bot.send_message(
            chat_id=message.chat.id,
            text=f"تم إرسال الرسالة إلى المستخدم {user_id} بـنـجـاح ✅.",
            reply_markup=markup
        )

    except Exception as e:
        # إذا لم يكن بالإمكان إرسال الرسالة (ربما لم يبدأ المستخدم المحادثة)
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("الرجوع ↩", callback_data="admin_panel"))

        bot.send_message(
            chat_id=message.chat.id,
            text=f"❌ تعذر إرسال الرسالة للمستخدم {user_id}. السبب: {e}",
            reply_markup=markup
        )

@bot.callback_query_handler(func=lambda call: call.data == "reset_balance")
def prompt_reset_balance(call):
    if is_admin(call.from_user.id):
        # استبدال الرسالة الأصلية برسالة طلب المعرف
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("إلغاء ✖️", callback_data="cancel_operation"))

        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text="أرسل معرف ID المستخدم الذي ترغب في تصفير رصيد S.P.F الخاص به 📥:",
            reply_markup=markup
        )
        bot.register_next_step_handler_by_chat_id(call.message.chat.id, process_reset_balance)
    else:
        # إذا لم يكن المستخدم إداريًا
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text="❌ هذا الخيار متاح فقط للمدير."
        )

def process_reset_balance(message):
    try:
        user_id = int(message.text.strip())  # الحصول على معرف المستخدم

        # الاتصال بقاعدة البيانات
        with sqlite3.connect('bot_data.db') as conn:
            cursor = conn.cursor()

            # التحقق إذا كان المستخدم موجودًا
            cursor.execute('SELECT first_name, last_name FROM users WHERE user_id = ?', (user_id,))
            user_data = cursor.fetchone()
            if not user_data:
                # إذا لم يتم العثور على المستخدم
                markup = InlineKeyboardMarkup()
                markup.add(InlineKeyboardButton("الرجوع ↩", callback_data="admin_panel"))
                bot.send_message(  # نستخدم send_message بدلاً من edit_message_text
                    chat_id=message.chat.id,
                    text=f"المستخدم بمعرف {user_id} غير موجود ❌.",
                    reply_markup=markup
                )
                return

            first_name, last_name = user_data

            # تصفير الرصيد
            cursor.execute('UPDATE users SET points = 0 WHERE user_id = ?', (user_id,))
            conn.commit()

        # إرسال رسالة للمستخدم
        try:
            bot.send_message(
                chat_id=user_id,
                text=(
                    f"🔔 عزيزي {first_name} {last_name},\n"
                    "تم تصفير رصيدك من S.P.F بواسطة الآدمن 📉.\n"
                    "لأي استفسارات، يمكنك التواصل معه عن طريق الدعم 📨."
                )
            )
        except Exception:
            # تجاهل الخطأ إذا لم يكن بالإمكان إرسال الرسالة
            pass

        # رسالة نجاح إلــغــاء ✖️ للإداري
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("الرجوع ↩", callback_data="admin_panel"))
        bot.send_message(
            chat_id=message.chat.id,
            text=f"✅ تم تصفير رصيد المستخدم {first_name} {last_name} (معرف {user_id}) بنجاح.",
            reply_markup=markup
        )

    except ValueError:
        # إذا كان الإدخال غير صحيح
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("الرجوع ↩", callback_data="admin_panel"))
        bot.send_message(
            chat_id=message.chat.id,
            text="عذرا 😬 , يجب أن يكون معرف ID المستخدم رقما صحيحا 🔢.",
            reply_markup=markup
        )
    except Exception as e:
        # في حال حدوث خطأ غير متوقع
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("الرجوع ↩", callback_data="admin_panel"))
        bot.send_message(
            chat_id=message.chat.id,
            text=f"❌ حدث خطأ غير متوقع: {e}",
            reply_markup=markup
        )

@bot.callback_query_handler(func=lambda call: call.data == "show_user_info")
def show_user_info(call):
    if is_admin(call.from_user.id):  # التحقق إذا كان المستخدم إداريًا
        # إعداد الأزرار مع زر إلغاء إلــغــاء ✖️ وزر الالــرجــوع ↩
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("الرجوع ↩", callback_data="cancel_operation"))

        # تعديل الرسالة الحالية لطلب معرف المستخدم
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text="أدخل معرف ID المستخدم الذي ترغب في عرض معلوماته 📥:",
            reply_markup=markup
        )

        # الانتقال إلى الخطوة التالية لمعالجة المعرف
        bot.register_next_step_handler_by_chat_id(call.message.chat.id, process_user_info)
    else:
        # إذا لم يكن المستخدم إداريًا
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("الرجوع ↩", callback_data="admin_panel"))

        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text="❌ هذا الخيار متاح فقط للمدير.",
            reply_markup=markup
        )

def process_user_info(message):
    try:
        user_id = int(message.text.strip())  # الحصول على معرف المستخدم
        conn = sqlite3.connect('bot_data.db')  # الاتصال بقاعدة البيانات
        cursor = conn.cursor()

        # جلب معلومات المستخدم
        cursor.execute('SELECT first_name, last_name, points, purchases FROM users WHERE user_id = ?', (user_id,))
        user_data = cursor.fetchone()

        # التحقق إذا كان المستخدم محظورًا
        cursor.execute('SELECT 1 FROM banned_users WHERE user_id = ?', (user_id,))
        is_banned = cursor.fetchone() is not None

        # التحقق إذا كان المستخدم إداريًا
        cursor.execute('SELECT 1 FROM admins WHERE user_id = ?', (user_id,))
        is_admin_user = cursor.fetchone() is not None

        conn.close()

        # إعداد زر الالــرجــوع ↩
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("الرجوع ↩", callback_data="admin_panel"))

        if user_data:
            first_name, last_name, points, purchases = user_data
            first_name = first_name or "غير متوفر"
            last_name = last_name or "غير متوفر"

            user_info_text = (
                f"📋 معلومات المستخدم:\n"
                f"🔹 معرف ID المستخدم: {user_id}\n"
                f"👤 الاسم الكامل: {first_name} {last_name}\n"
                f"⭐ رصيد S.P.F: {points}\n"
                f"🛒 عدد المشتريات: {purchases}\n"
                f"🚫 محظور: {'نعم' if is_banned else 'لا'}\n"
                f"👑 آدمن: {'نعم' if is_admin_user else 'لا'}"
            )
        else:
            user_info_text = f"❌ لا توجد بيانات للمستخدم بمعرف {user_id}."

        # إرسال رسالة جديدة لعرض المعلومات
        bot.send_message(
            message.chat.id,
            user_info_text,
            reply_markup=markup
        )

    except ValueError:
        # إذا كان الإدخال غير صحيح
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("الرجوع ↩", callback_data="admin_panel"))

        bot.send_message(
            message.chat.id,
            "عذرا 😬 , يجب أن يكون معرف ID المستخدم رقما صحيحا 🔢.",
            reply_markup=markup
        )
    except Exception as e:
        # في حال حدوث خطأ غير متوقع
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("الرجوع ↩", callback_data="admin_panel"))

        bot.send_message(
            message.chat.id,
            f"❌ حدث خطأ غير متوقع: {e}",
            reply_markup=markup
        )

@bot.callback_query_handler(func=lambda call: call.data == "admin_add_code")
def add_code_callback(call):
    # التأكد من أن المستخدم هو المدير من قاعدة البيانات
    if is_admin(call.from_user.id):
        # إعداد الأزرار
        markup = InlineKeyboardMarkup(row_width=1)
        markup.add(
            InlineKeyboardButton("ببجي | PUBG 🪖", callback_data="add_pubg"),
            InlineKeyboardButton("فري فاير | FREE FIRE 🔥", callback_data="add_freefire"),
        )
        markup.add(
            InlineKeyboardButton("العضوية الاسبوعية | Weekly membership 🟣", callback_data="add_weekly"),
            InlineKeyboardButton("العضوية الشهرية | Monthly membership 🟡", callback_data="add_monthly"),
            InlineKeyboardButton("تصريح المستوى | Level up pass 💎", callback_data="add_level")
        )
        markup.add(InlineKeyboardButton("الرجوع ↩", callback_data="admin_panel"))
        
        # تعديل الرسالة الموجودة بدلاً من إرسال واحدة جديدة
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text="اختر الفئة لإضافة الكود ⬇️:",
            reply_markup=markup
        )
    else:
        bot.send_message(call.message.chat.id, "❌ هذا الخيار متاح فقط للمدير.")


@bot.callback_query_handler(func=lambda call: call.data.startswith("add_"))
def ask_code_value(call):
    # تحديد اللعبة أو نوع العضوية بناءً على الاختيار
    if call.data == "add_pubg":
        game = "ببجي"
        amount = 60  # قيمة الشحن لببجي
    elif call.data == "add_freefire":
        game = "فري فاير"
        amount = 100  # قيمة الشحن لفري فاير
    elif call.data == "add_weekly":
        game = "عضوية إسبوعية"
        amount = 29000  # سعر العضوية الإسبوعية
    elif call.data == "add_monthly":
        game = "عضوية شهرية"
        amount = 100000  # سعر العضوية الشهرية
    elif call.data == "add_level":
        game = "تصريح المستوى"
        amount = 17000  # سعر تصريح المستوى
    else:
        bot.send_message(call.message.chat.id, "❌ اختيار غير صالح.")
        return

    # إعداد الأزرار مع زر الإلغاء
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("إلــغــاء ✖️", callback_data="cancel_operation"))

    # تعديل الرسالة الحالية بدلاً من حذفها
    bot.edit_message_text(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text="أرسـل الـكـود 📥:",
        reply_markup=markup
    )
    bot.register_next_step_handler_by_chat_id(call.message.chat.id, lambda msg: process_add_code(msg, game, amount))


def process_add_code(message, game, amount):
    # إذا كان المستخدم اختار الإلغاء، لا تتم متابعة إلــغــاء ✖️
    if message.text is None:
        return
    
    code = message.text.strip()
    
    # إعداد زر الالــرجــوع ↩
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("الرجوع ↩", callback_data="admin_panel"))

    conn = sqlite3.connect('bot_data.db')
    cursor = conn.cursor()
    # عرض
    # التحقق مما إذا كان الكود موجودًا مسبقًا في قاعدة البيانات
    cursor.execute('SELECT * FROM recharge_codes WHERE game = ? AND amount = ? AND code = ?', (game, amount, code))
    result = cursor.fetchone()

    if result:
        bot.send_message(
            message.chat.id, 
            f"⚠ الكود '{code}' تم استخدامه من قبل.",
            reply_markup=markup
        )
    else:
        # إدخال الكود الجديد في قاعدة البيانات
        cursor.execute('INSERT INTO recharge_codes (game, amount, code) VALUES (?, ?, ?)', (game, amount, code))
        conn.commit()
        bot.send_message(
            message.chat.id, 
            f"تم إضافة الكود '{code}' إلى {game} ✅.",
            reply_markup=markup
        )

    conn.close()

@bot.callback_query_handler(func=lambda call: call.data == "show_codes")
def show_codes(call):
    if is_admin(call.from_user.id):
        try:
            # الاتصال بقاعدة البيانات لجلب الأكواد المتاحة
            conn = sqlite3.connect('bot_data.db')
            cursor = conn.cursor()

            # جلب الأكواد المتاحة لكل لعبة
            cursor.execute('SELECT game, code FROM recharge_codes ORDER BY game')
            codes_data = cursor.fetchall()
            conn.close()

            # إعداد زر الالــرجــوع ↩ إلى لوحة الإدارة
            markup = InlineKeyboardMarkup()
            markup.add(InlineKeyboardButton("الرجوع ↩", callback_data="admin_panel"))

            if not codes_data:
                # تعديل الرسالة الأصلية للإشارة إلى عدم وجود أكواد
                bot.edit_message_text(
                    chat_id=call.message.chat.id,
                    message_id=call.message.message_id,
                    text="لا يوجد أكواد متاحة حاليا ❌.",
                    reply_markup=markup
                )
                return

            # تنسيق عرض الأكواد حسب اللعبة
            codes_text = "الأكواد المتاحة 📋:\n\n"
            current_game = None
            for game, code in codes_data:
                if game != current_game:
                    codes_text += f"\n--- {game} ---\n"
                    current_game = game
                codes_text += f"🔹 {code}\n"

            # تعديل الرسالة الأصلية لعرض الأكواد
            bot.edit_message_text(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                text=codes_text,
                reply_markup=markup
            )

        except Exception as e:
            # تعديل الرسالة الأصلية عند حدوث خطأ مع زر الالــرجــوع ↩
            markup = InlineKeyboardMarkup()
            markup.add(InlineKeyboardButton("الرجوع ↩", callback_data="admin_panel"))

            bot.edit_message_text(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                text="❌ حدث خطأ غير متوقع: " + str(e),
                reply_markup=markup
            )
    else:
        # تعديل الرسالة الأصلية إذا لم يكن المستخدم إداريًا مع زر الالــرجــوع ↩
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("الرجوع ↩", callback_data="admin_panel"))

        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text="❌ هذا الخيار متاح فقط للمدير.",
            reply_markup=markup
        )

@bot.callback_query_handler(func=lambda call: call.data == "remove_code")
def remove_code(call):
    user_id = call.from_user.id

    # التحقق إذا كان المستخدم أدمن
    if not is_admin(user_id):
        # إعداد زر الالــرجــوع ↩ إلى لوحة الإدارة
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("الرجوع ↩", callback_data="admin_panel"))
        
        # تعديل الرسالة الأصلية إذا لم يكن المستخدم إداريًا
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text="❌ لا تمتلك صلاحيات لحذف الأكواد.",
            reply_markup=markup
        )
        return

    # إعداد قائمة أزرار لاختيار الفئة
    markup = InlineKeyboardMarkup(row_width=1)
    markup.add(
        InlineKeyboardButton("ببجي | PUBG 🪖", callback_data="remove_code_pubg"),
        InlineKeyboardButton("فري فاير | FREE FIRE 🔥", callback_data="remove_code_freefire")
    )
    markup.add(
        InlineKeyboardButton("العضوية الاسبوعية | Weekly membership 🟣", callback_data="remove_code_weekly"),
        InlineKeyboardButton("العضوية الشهرية | Monthly membership 🟡", callback_data="remove_code_monthly"),
        InlineKeyboardButton("تصربح المستوي | Level up pass 💎", callback_data="remove_code_level")
    )
    markup.add(InlineKeyboardButton("الرجوع ↩", callback_data="admin_panel"))

    # تعديل الرسالة الأصلية مع إضافة زر الالــرجــوع ↩
    bot.edit_message_text(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text="اختر الفئة المراد حذف الكود منها ⬇️:",
        reply_markup=markup
    )

@bot.callback_query_handler(func=lambda call: call.data.startswith("remove_code_"))
def process_game_selection(call):
    # تحديد اللعبة أو نوع العضوية بناءً على البيانات المرسلة
    if call.data == "remove_code_pubg":
        category = "ببجي"
    elif call.data == "remove_code_freefire":
        category = "فري فاير"
    elif call.data == "remove_code_weekly":
        category = "عضوية إسبوعية"
    elif call.data == "remove_code_monthly":
        category = "عضوية شهرية"
    elif call.data == "remove_code_level":
        category = "تصريح المستوى"
    else:
        bot.send_message(call.message.chat.id, "❌ اختيار غير صالح.")
        return

    # إعداد الأزرار مع زر إلغاء إلــغــاء ✖️
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("إلغاء ✖️", callback_data="cancel_operation"))

    # تعديل الرسالة الحالية بدلاً من حذفها
    bot.edit_message_text(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text=f"أدخل الكود الذي ترغب في حذفه من الفئة {category} 📥:",
        reply_markup=markup
    )

    # الانتقال إلى الخطوة التالية لمعالجة الكود
    bot.register_next_step_handler_by_chat_id(call.message.chat.id, process_code_removal, category)

# دالة حذف الكود
def process_code_removal(message, category):
    try:
        # الكود المدخل من قبل الإداري
        code_to_remove = message.text.strip()

        # الاتصال بقاعدة البيانات لحذف الكود
        conn = sqlite3.connect('bot_data.db')
        cursor = conn.cursor()

        # التحقق مما إذا كان هناك كود متاح لهذه الفئة
        cursor.execute('SELECT code FROM recharge_codes WHERE game = ? AND code = ?', (category, code_to_remove))
        code_data = cursor.fetchone()

        # إنشاء زر الالــرجــوع ↩
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("الرجوع ↩", callback_data="admin_panel"))

        if not code_data:
            bot.send_message(
                chat_id=message.chat.id,
                text=f"❌ لا يوجد كود {code_to_remove} في الفئة {category}.",
                reply_markup=markup
            )
        else:
            # حذف الكود من قاعدة البيانات
            cursor.execute('DELETE FROM recharge_codes WHERE game = ? AND code = ?', (category, code_to_remove))
            conn.commit()
            bot.send_message(
                chat_id=message.chat.id,
                text=f"تم إزالة الكود ال {category} بنجاح ✅:\nالكود المحذوف 🔷: {code_to_remove}",
                reply_markup=markup
            )

        conn.close()

    except Exception as e:
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("الرجوع ↩", callback_data="admin_panel"))
        bot.send_message(
            chat_id=message.chat.id,
            text="❌ حدث خطأ غير متوقع: " + str(e),
            reply_markup=markup
        )

@bot.callback_query_handler(func=lambda call: call.data == "admin_list")
def show_admin_list(call):
    if is_admin(call.from_user.id):  # التحقق من كون المستخدم إداري
        # إضافة الأعمدة إلى جدول الإداريين إذا كانت غير موجودة
        add_admin_name_columns()

        # إعداد زر الالــرجــوع ↩
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("الرجوع ↩", callback_data="admin_panel"))

        # الاتصال بقاعدة البيانات
        conn = sqlite3.connect('bot_data.db')
        cursor = conn.cursor()

        # استعلام للحصول على قائمة الإداريين
        cursor.execute('SELECT user_id, first_name, last_name FROM admins')
        admins = cursor.fetchall()

        # إذا لم يكن هناك إداريين
        if not admins:
            bot.edit_message_text(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                text="لا يوجد ادمنز حاليا 👤.",
                reply_markup=markup
            )
        else:
            # بناء قائمة الإداريين
            admin_list = "قائمة الادمنز 📋:\n"
            for user_id, first_name, last_name in admins:
                admin_list += f"- {first_name} {last_name} (ID: {user_id})\n"

            # تعديل الرسالة الأصلية لعرض قائمة الإداريين مع زر الالــرجــوع ↩
            bot.edit_message_text(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                text=admin_list,
                reply_markup=markup
            )

        # إغلاق الاتصال بقاعدة البيانات
        conn.close()

    else:
        # إذا لم يكن المستخدم هو المدير
        bot.send_message(call.message.chat.id, "❌ هذا الخيار متاح فقط للمدير.")

# دالة لبدء عملية إضافة إداري
@bot.callback_query_handler(func=lambda call: call.data == "addd_admin")
def prompt_add_admin(call):
    if is_admin(call.from_user.id):
        # إعداد الأزرار مع زر إلغاء إلــغــاء ✖️
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("إلغاء ✖️", callback_data="cancel_operation"))

        # تعديل الرسالة الحالية لطلب معرف المستخدم
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text="أرسـل معرف ID المستخدم الذي ترغب في تعيينه كأدمن 📥:",
            reply_markup=markup
        )

        # تسجيل الخطوة التالية لمعالجة إدخال معرف المستخدم
        bot.register_next_step_handler_by_chat_id(call.message.chat.id, process_add_admin)
    else:
        bot.send_message(call.message.chat.id, "❌ هذا الخيار متاح فقط للمدير.")

# دالة لمعالجة إضافة الإداري الجديد
def process_add_admin(message):
    try:
        new_admin_id = int(message.text.strip())

        # جلب معلومات المستخدم (الاسم الأول والاسم الثاني)
        user_info = bot.get_chat(new_admin_id)
        first_name = user_info.first_name
        last_name = user_info.last_name if user_info.last_name else ""  # إذا لم يكن لديه اسم ثاني

        # إضافة الإداري الجديد إلى قاعدة البيانات مع الاسم الأول والثاني
        conn = sqlite3.connect('bot_data.db')
        cursor = conn.cursor()
        cursor.execute(
            'INSERT INTO admins (user_id, first_name, last_name) VALUES (?, ?, ?)', 
            (new_admin_id, first_name, last_name)
        )
        conn.commit()
        conn.close()

        # إعداد زر الالــرجــوع ↩
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("الرجوع ↩", callback_data="admin_panel"))

        # إرسال الرسالة بنجاح مع زر الالــرجــوع ↩
        bot.send_message(
            message.chat.id, 
            f"تم تعيين المستخدم {first_name} {last_name} (ID: {new_admin_id}) كإداري بنجاح ✅.",
            reply_markup=markup
        )

    except ValueError:
        # إعداد زر الالــرجــوع ↩ في حال الخطأ
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("الرجوع ↩", callback_data="admin_panel"))

        # إرسال رسالة الخطأ مع زر الالــرجــوع ↩
        bot.send_message(
            message.chat.id, 
            "عذرا 😬 , يجب أن يكون معرف ID المستخدم رقما صحيحا 🔢.",
            reply_markup=markup
        )

    except Exception as e:
        # إعداد زر الالــرجــوع ↩ في حال حدوث خطأ آخر
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("الرجوع ↩", callback_data="admin_panel"))

        # إرسال رسالة الخطأ العام مع زر الالــرجــوع ↩
        bot.send_message(
            message.chat.id, 
            f"❌ حدث خطأ غير متوقع: {e}",
            reply_markup=markup
        )

# دالة لبدء عملية إزالة إداري
@bot.callback_query_handler(func=lambda call: call.data == "remove_admin")
def prompt_remove_admin(call):
    if is_admin(call.from_user.id):
        # إعداد الأزرار مع زر إلغاء إلــغــاء ✖️
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("إلغاء ✖️", callback_data="cancel_operation"))

        # تعديل الرسالة الحالية لطلب معرف المستخدم مع الأزرار
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text="أرسل معرف ID المستخدم الذي ترغب في إزالته من الادمنز 📥:",
            reply_markup=markup
        )

        # تسجيل الخطوة التالية لمعالجة إدخال معرف المستخدم
        bot.register_next_step_handler_by_chat_id(call.message.chat.id, process_remove_admin)
    else:
        bot.send_message(call.message.chat.id, "❌ هذا الخيار متاح فقط للمدير.")

# دالة لمعالجة إزالة الإداري
def process_remove_admin(message):
    try:
        admin_id = int(message.text.strip())
        
        # تحقق إذا كان الإدمن هو الإدمن الافتراضي
        if admin_id == int(DEFAULT_ADMIN_ID):  # استبدل DEFAULT_ADMIN_ID بالمعرف الفعلي للإدمن الافتراضي
            markup = InlineKeyboardMarkup()
            markup.add(InlineKeyboardButton("الرجوع ↩", callback_data="admin_panel"))
            bot.send_message(
                message.chat.id,
                "❌ لا يمكن إزالة الإدمن الافتراضي.",
                reply_markup=markup
            )
        else:
            # إزالة الإدمن
            remove_admin(admin_id)
            markup = InlineKeyboardMarkup()
            markup.add(InlineKeyboardButton("الرجوع ↩", callback_data="admin_panel"))
            bot.send_message(
                message.chat.id,
                f"✅ تم إزالة المستخدم {admin_id} من الإداريين بنجاح.",
                reply_markup=markup
            )
    except ValueError:
        # إعداد زر الالــرجــوع ↩ في حال الخطأ
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("الرجوع ↩", callback_data="admin_panel"))
        bot.send_message(
            message.chat.id,
            "❌ الرجاء إدخال معرف صالح.",
            reply_markup=markup
        )

@bot.callback_query_handler(func=lambda call: call.data == "admin_add_points")
def admin_add_points(call):
    if is_admin(call.from_user.id):
        # إعداد الأزرار مع زر إلغاء إلــغــاء ✖️
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("إلغاء ✖️", callback_data="cancel_operation"))
        
        # تعديل الرسالة الحالية بدلاً من حذفها
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text="📌 أدخل معرف المستخدم الذي تريد تعديل نقاطه:",
            reply_markup=markup
        )
        bot.register_next_step_handler_by_chat_id(call.message.chat.id, process_user_id_for_points)
    else:
        bot.send_message(call.message.chat.id, "❌ هذا الخيار متاح فقط للمدير.")

# دالة لمعالجة معرف المستخدم
def process_user_id_for_points(message):
    try:
        user_id = int(message.text.strip())
        # التأكد من أن المستخدم موجود في قاعدة البيانات
        initialize_user_data(user_id)

        # إعداد الأزرار مع زر إلغاء إلــغــاء ✖️ وزر الالــرجــوع ↩ إلى لوحة الإدارة
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("إلغاء ✖️", callback_data="cancel_operation"))
        # الانتقال إلى خطوة إدخال كمية النقاط        
        msg = bot.send_message(message.chat.id, "📌 أدخل كمية النقاط التي تريد إضافتها أو خصمها (استخدم قيم سالبة للخصم):", reply_markup=markup)
        bot.register_next_step_handler(msg, process_points_amount, user_id)

    except ValueError:
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("الرجوع ↩", callback_data="admin_panel"))
        bot.send_message(message.chat.id, "عذرا 😬 , يجب أن يكون معرف ID المستخدم رقما صحيحا 🔢.", reply_markup=markup)
        
    except Exception as e:
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("الرجوع ↩", callback_data="admin_panel"))
        bot.edit_message_text(
        chat_id=message.chat.id,
        message_id=message.message_id,
        text=f"❌ حدث خطأ غير متوقع: {e}",
        reply_markup=markup
    )

# دالة لمعالجة كمية النقاط
def process_points_amount(message, user_id):
    try:
        points = int(message.text.strip())
        
        # فتح اتصال بقاعدة البيانات
        conn = sqlite3.connect('bot_data.db')
        cursor = conn.cursor()

        # الحصول على الرصيد الحالي للمستخدم
        cursor.execute('SELECT points FROM users WHERE user_id = ?', (user_id,))
        result = cursor.fetchone()
        
        if result is None:
            markup = InlineKeyboardMarkup()
            markup.add(InlineKeyboardButton("الرجوع ↩", callback_data="admin_panel"))
            bot.send_message(message.chat.id, "❌ المستخدم غير موجود في قاعدة البيانات.", reply_markup=markup)
            conn.close()
            return
        
        current_points = result[0]

        # التحقق من أن الخصم لا يجعل الرصيد أقل من الصفر
        if points < 0 and abs(points) > current_points:
            markup = InlineKeyboardMarkup()
            markup.add(InlineKeyboardButton("الرجوع ↩", callback_data="admin_panel"))
            bot.send_message(message.chat.id, f"❌ لا يمكن خصم {abs(points)} S.P.F لأن رصيد المستخدم الحالي هو {current_points} S.P.F فقط.", reply_markup=markup)
            conn.close()
            return

        # تحديث الرصيد للمستخدم في قاعدة البيانات
        new_points = current_points + points
        cursor.execute('UPDATE users SET points = ? WHERE user_id = ?', (new_points, user_id))
        conn.commit()
        conn.close()

        # إرسال رسالة التأكيد إلى المدير
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("الرجوع ↩", callback_data="admin_panel"))
        bot.send_message(
            message.chat.id, 
            f"✅ {'تمت إضافة' if points > 0 else 'تم خصم'} {abs(points)} S.P.F للمستخدم {user_id}. الرصيد الحالي: {new_points} S.P.F.",
            reply_markup=markup
        )

        # إعلام المستخدم بالتحديث
        bot.send_message(user_id, f"{'استلمت' if points > 0 else 'تم خصم'} {abs(points)} S.P.F من المدير. رصيدك الحالي هو {new_points} S.P.F.")
        
    except ValueError:
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("الرجوع ↩", callback_data="admin_panel"))
        bot.send_message(message.chat.id, "❌ تنسيق غير صحيح. يرجى إدخال عدد النقاط كرقم.", reply_markup=markup)
    except Exception as e:
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("الرجوع ↩", callback_data="admin_panel"))
        bot.send_message(message.chat.id, f"❌ حدث خطأ غير متوقع: {e}", reply_markup=markup)

# دالة لإرسال إعلان
@bot.callback_query_handler(func=lambda call: call.data == "broadcast_message")
def broadcast_message_step1(call):
    if is_admin(call.from_user.id):
        # إعداد الأزرار مع زر إلغاء إلــغــاء ✖️
        markup = InlineKeyboardMarkup()
        markup.add(
            InlineKeyboardButton("إلغاء ✖️", callback_data="cancel_operation")
        )
        
        # تعديل الرسالة الحالية لطلب إدخال الرسالة الموجهة للمستخدمين
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text="أدخل الرسالة التي تريد إرسالها لجميع المستخدمين:",
            reply_markup=markup
        )
        
        # تسجيل الخطوة التالية لمعالجة إدخال الرسالة
        bot.register_next_step_handler_by_chat_id(call.message.chat.id, process_broadcast_message)
    else:
        bot.send_message(call.message.chat.id, "❌ هذا الخيار متاح فقط للمدير.")

# دالة عامة لإلغاء إلــغــاء ✖️
@bot.callback_query_handler(func=lambda call: call.data == "cancel_operation")
def cancel_operation(call):
    if is_admin(call.from_user.id):
        bot.clear_step_handler_by_chat_id(chat_id=call.message.chat.id)
        markup = InlineKeyboardMarkup(row_width=3)

        # الصف الأول: إضافة أكواد - عرض الأكواد - حذف الأكواد
        markup.row(
            InlineKeyboardButton("إضافة أكواد ➕", callback_data="admin_add_code"),
            InlineKeyboardButton("عـرض أكواد 📃", callback_data="show_codes"),
            InlineKeyboardButton("إزالة أكواد ➖", callback_data="remove_code")
        )

        # الصف الثاني: عرض معلومات المستخدم
        markup.row(
            InlineKeyboardButton("معلومات المستخدم ℹ️", callback_data="show_user_info")
        )

        # الصف الثالث: تعديل رصيد - تصفير رصيد
        markup.row(
            InlineKeyboardButton("تعديل رصيد S.P.F ⚙️", callback_data="admin_add_points"),
            InlineKeyboardButton("تصفير رصيد S.P.F 📉", callback_data="reset_balance")
        )

        markup.row(
                    InlineKeyboardButton("عـرض أسئلة المستخدمين 📑", callback_data="view_inquiries"),
        )
        # الصف الرابع: تعديل الأسعار
        markup.row(
            InlineKeyboardButton("تعديل الأسعار 🤑", callback_data="change_prices"),
            InlineKeyboardButton("عرض الأسعار 📋", callback_data="view_prices")
        )

        # الصف الخامس: حظر مستخدم - قائمة المحظورين - إلغاء حظر مستخدم
        markup.row(
            InlineKeyboardButton("حظر مستخدم ⛔", callback_data="ban_user"),
            InlineKeyboardButton("قائمة المحظورين 📜", callback_data="banned_list"),
            InlineKeyboardButton("إلغاء حظر مستخدم ✅", callback_data="unban_user")
        )

        # الصف السادس: رسالة لمستخدم - إذاعة
        markup.row(
            InlineKeyboardButton("رسالة لمستخدم ✉️", callback_data="send_message_to_user"),
            InlineKeyboardButton("إرسال إذاعة 📢", callback_data="broadcast_message")
        )

        # الصف السابع: إضافة إداري - قائمة الإداريين - إزالة إداري
        markup.row(
            InlineKeyboardButton("إضافة آدمن ➕", callback_data="addd_admin"),
            InlineKeyboardButton("قائمة الآدمنز 📖", callback_data="admin_list"),
            InlineKeyboardButton("إزاـة آدمن ➖", callback_data="remove_admin")
        )

        # الصف الثامن: تشغيل البوت - إيقاف البوت
        markup.row(
            InlineKeyboardButton("تشغيل البوت ☑️", callback_data="start_bot"),
            InlineKeyboardButton("إيقاف البوت ❎", callback_data="stop_bot")
        )

        # الصف الأخير: الــرجــوع ↩
        markup.row(
            InlineKeyboardButton("الرجوع ↩", callback_data="back_to_main_menu")
        )

        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text="مرحبا بك أيها الادمن 👨🏼‍💻.\n اختر واحدةة من الخيارات هنا ⬇️.",
            reply_markup=markup
        )
    else:
        # رسالة تحذير مع زر الالــرجــوع ↩
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("الرجوع ↩", callback_data="back_to_main_menu"))
        
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text="❌ هذا الخيار متاح فقط للمدير.",
            reply_markup=markup
        )

# دالة لمعالجة الرسالة بعد إدخالها من المدير
def process_broadcast_message(message):
    # تحقق من إلغاء إلــغــاء ✖️
    if message.text == "/cancel":
        return  # إذا تم الإلغاء، توقف عن المتابعة

    announcement = message.text
    sent_count = 0
    if message.text is None:
        return  # إذا تم إلغاء إلــغــاء ✖️، لن يتم تنفيذ باقي الدالة

    announcement = message.text
    sent_count = 0

    try:
        # الاتصال بقاعدة البيانات
        conn = sqlite3.connect('bot_data.db')
        cursor = conn.cursor()

        # استرجاع جميع معرّفات المستخدمين من قاعدة البيانات
        cursor.execute('SELECT user_id FROM users')
        user_ids = cursor.fetchall()

        # استرجاع قائمة المستخدمين المحظورين
        cursor.execute('SELECT user_id FROM banned_users')
        banned_users = [row[0] for row in cursor.fetchall()]  # تحويل الـ tuples إلى قائمة معرفات

        conn.close()

        # إرسال الرسالة لكل مستخدم إلا المحظورين
        for user_id_tuple in user_ids:
            user_id = user_id_tuple[0]  # تحويل الكائن tuple إلى قيمة المعرف

            # إذا كان المستخدم محظورًا، نتجاهل إرسال الرسالة له
            if user_id in banned_users:
                continue

            try:
                bot.send_message(user_id, f"📢 إعلان من المدير:\n\n{announcement}")
                sent_count += 1
            except Exception:
                pass

        # إعداد زر الالــرجــوع ↩ للمدير
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("الرجوع ↩", callback_data="admin_panel"))

        # تأكيد عدد الرسائل المرسلة للمدير مع زر الالــرجــوع ↩
        bot.send_message(
            message.chat.id,
            f"تم إرسال الإعلان إلى {sent_count} مستخدم.",
            reply_markup=markup
        )
    
    except Exception as e:
        # إذا حدث خطأ أثناء التعامل مع قاعدة البيانات أو إرسال الرسائل
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("الرجوع ↩", callback_data="admin_panel"))
        
        bot.send_message(
            message.chat.id,
            f"حدث خطأ أثناء إرسال الإعلان: {e}",
            reply_markup=markup
        )

# دالة لحظر مستخدمين
@bot.callback_query_handler(func=lambda call: call.data == "ban_user")
def ban_user_step1(call):
    if is_admin(call.from_user.id):
        # إعداد الأزرار مع زر إلغاء إلــغــاء ✖️ وزر الالــرجــوع ↩ إلى لوحة الإدارة
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("إلغاء ✖️", callback_data="cancel_operation"))

        # تعديل الرسالة الحالية بدلاً من حذفها
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text="أدخل معرف المستخدم (ID) للفرد الذي تريد حظره:",
            reply_markup=markup
        )
        # الانتقال للخطوة التالية
        bot.register_next_step_handler_by_chat_id(call.message.chat.id, process_ban_user)
    else:
        bot.send_message(call.message.chat.id, "❌ هذا الخيار متاح فقط للمدير.")

# دالة لمعالجة حظر المستخدم
def process_ban_user(message):
    try:
        # الحصول على معرف المستخدم المراد حظره
        user_id = int(message.text.strip())

        # إعداد الأزرار مع زر إلغاء إلــغــاء ✖️ وزر الالــرجــوع ↩ إلى لوحة الإدارة
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("الرجوع ↩", callback_data="admin_panel"))

        # فتح اتصال بقاعدة البيانات
        conn = sqlite3.connect('bot_data.db')
        cursor = conn.cursor()

        # التحقق مما إذا كان المستخدم إداريًا
        cursor.execute('SELECT * FROM admins WHERE user_id = ?', (user_id,))
        if cursor.fetchone():
            bot.send_message(
                message.chat.id,
                f"لا يمكن حظر المستخدم بمعرف ID : {user_id} لأنه آدمن ❌.",
                reply_markup=markup
            )
            conn.close()
            return

        # جلب بيانات المستخدم باستخدام دالة get_chat
        user_info = bot.get_chat(user_id)
        first_name = user_info.first_name or "بدون اسم"
        last_name = user_info.last_name or "بدون اسم"

        # التحقق مما إذا كان المستخدم محظورًا بالفعل في قاعدة البيانات
        cursor.execute('SELECT * FROM banned_users WHERE user_id = ?', (user_id,))
        result = cursor.fetchone()

        if result:
            bot.send_message(
                message.chat.id,
                f"⚠ المستخدم بمعرف {user_id} محظور بالفعل.",
                reply_markup=markup
            )
        else:
            # إضافة المستخدم مع الاسم الأول واسم العائلة إلى قائمة المحظورين
            cursor.execute(
                'INSERT INTO banned_users (user_id, first_name, last_name) VALUES (?, ?, ?)',
                (user_id, first_name, last_name)
            )
            conn.commit()

            # إرسال رسالة للمستخدم المحظور
            try:
                bot.send_message(
                    user_id,
                    "لقد تم حظرك من البوت ⛔ , تواصل مع الأدمنز للإستفسار عن الموضوع ⚠️"
                )
            except Exception:
                # إذا كان من غير الممكن إرسال الرسالة للمستخدم
                pass

            # إعلام الإداري بنجاح إلــغــاء ✖️
            bot.send_message(
                message.chat.id,
                f"تم حظر المستخدم بمعرف {user_id} - {first_name} {last_name} بنجاح ✅.",
                reply_markup=markup
            )

        conn.close()

    except Exception as e:
        # التعامل مع أي خطأ غير متوقع
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("الرجوع ↩", callback_data="admin_panel"))
        bot.send_message(
            message.chat.id,
            f"❌ حدث خطأ غير متوقع: {e}",
            reply_markup=markup
        )

    except ValueError:
        bot.send_message(
            message.chat.id, 
            "عذرا 😬 , يجب أن يكون معرف ID المستخدم رقما صحيحا 🔢.", 
            reply_markup=markup
        )
    except Exception as e:
        bot.send_message(
            message.chat.id, 
            f"حدث خطأ غير متوقع: {e}", 
            reply_markup=markup
        )

# دالة لإلغاء حظر مستخدم
@bot.callback_query_handler(func=lambda call: call.data == "unban_user")
def unban_user_step1(call):
    if is_admin(call.from_user.id):  # تحقق إذا كان المستخدم إداريًا
        # إعداد الأزرار مع زر إلغاء إلــغــاء ✖️
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("إلغاء ✖️", callback_data="cancel_operation"))

        # تعديل الرسالة الحالية بدلاً من حذفها
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text="أدخل معرف المستخدم (ID) للفرد الذي تريد إلغاء حظره 📥:",
            reply_markup=markup
        )
        # الانتقال للخطوة التالية
        bot.register_next_step_handler_by_chat_id(call.message.chat.id, process_unban_user)
    else:
        bot.send_message(call.message.chat.id, "❌ هذا الخيار متاح فقط للمدير.")

# دالة لمعالجة إلغاء حظر المستخدم
def process_unban_user(message):
    try:
        # الحصول على معرف المستخدم المراد إلغاء حظره
        user_id = int(message.text.strip())

        # إعداد الأزرار مع زر إلغاء إلــغــاء ✖️ وزر الالــرجــوع ↩ إلى لوحة الإدارة
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("الرجوع ↩", callback_data="admin_panel"))

        # فتح اتصال بقاعدة البيانات
        conn = sqlite3.connect('bot_data.db')
        cursor = conn.cursor()

        # التحقق إذا كان المستخدم موجودًا في قائمة المحظورين
        cursor.execute('SELECT * FROM banned_users WHERE user_id = ?', (user_id,))
        banned_user = cursor.fetchone()

        if not banned_user:
            bot.send_message(
                message.chat.id,
                f"المستخدم يمعرف ID: {user_id} ليس محظورا ⚠.",
                reply_markup=markup
            )
            conn.close()
            return

        # إزالة المستخدم من قائمة المحظورين
        cursor.execute('DELETE FROM banned_users WHERE user_id = ?', (user_id,))
        conn.commit()

        # إرسال رسالة للمستخدم بأنه تم إلغاء حظره
        try:
            bot.send_message(
                user_id,
                "تم إلغاء حظرك من استخدام البوت 🔥. مرحبا بك من جديد 🎉. !"
            )
        except Exception:
            # إذا كان من غير الممكن إرسال الرسالة للمستخدم
            pass

        # إعلام الإداري بنجاح إلــغــاء ✖️
        bot.send_message(
            message.chat.id,
            f"تم إالغاء حظر المستخدم بمعرف ID : {user_id} بنجاح ✅.",
            reply_markup=markup
        )

        conn.close()

    except Exception as e:
        # التعامل مع أي خطأ غير متوقع
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("الرجوع ↩", callback_data="admin_panel"))
        bot.send_message(
            message.chat.id,
            f"❌ حدث خطأ غير متوقع: {e}",
            reply_markup=markup
        )

# دالة لعرض قائمة المحظورين
@bot.callback_query_handler(func=lambda call: call.data == "banned_list")
def show_banned_list(call):
    if is_admin(call.from_user.id):
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("الرجوع ↩", callback_data="admin_panel"))

        conn = sqlite3.connect('bot_data.db')
        cursor = conn.cursor()

        # استعلام للحصول على قائمة المستخدمين المحظورين مع الأسماء
        cursor.execute('SELECT user_id, first_name, last_name FROM banned_users')
        banned_users = cursor.fetchall()

        if not banned_users:
            bot.edit_message_text(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                text="🚫 لا يوجد مستخدمون محظورون حالياً.",
                reply_markup=markup
            )
        else:
            banned_list = "قائمة المستخدمين المحظورين    📋:\n"
            for user_id, first_name, last_name in banned_users:
                banned_list += f"- {first_name} {last_name} (ID: {user_id})\n"

            bot.edit_message_text(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                text=banned_list,
                reply_markup=markup
            )

        conn.close()
    else:
        bot.send_message(call.message.chat.id, "❌ هذا الخيار متاح فقط للمدير.")

# تشغيل البوت
bot.polling(none_stop=True, interval=0.5)
print("success")
