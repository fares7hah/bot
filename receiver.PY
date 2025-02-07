from flask import Flask, request, jsonify
import sqlite3
import re

# إنشاء أو الاتصال بقاعدة البيانات
conn = sqlite3.connect("bot_data.db")
cursor = conn.cursor()

# إنشاء جدول PENDING مع التعديلات المطلوبة
cursor.execute("""
CREATE TABLE IF NOT EXISTS PENDING (
    transaction_code INTEGER PRIMARY KEY,
    amount INTEGER NOT NULL
);
""")

# حفظ التغييرات وإغلاق الاتصال
conn.commit()
conn.close()

app = Flask(__name__)

# وظيفة لإضافة المعاملة إلى قاعدة البيانات
def add_pending_transaction(transaction_code, amount):
    conn = sqlite3.connect("bot_data.db")
    cursor = conn.cursor()

    try:
        cursor.execute("INSERT INTO PENDING (transaction_code, amount) VALUES (?, ?)", 
                       (transaction_code, amount))
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        conn.close()
        return False

# الدالة التي تستقبل الرسائل وتقوم باستخراج المبلغ ورمز المعاملة
@app.route('/receive_message', methods=['POST'])
def receive_message():
    # استلام الرسالة من العميل
    message = request.data.decode("utf-8")  # الحصول على النص المرسل

    # استخدام تعبيرات عادية لاستخراج المبلغ ورمز المعاملة
    match = re.search(r"تم استلام مبلغ (\d+) ل.س بنجاح\. رقم العملية هو (\d+)", message)

    if match:
        # استخراج المبلغ ورمز المعاملة
        amount = int(match.group(1))  # المبلغ
        transaction_code = match.group(2)  # الرمز

        # إضافة المعاملة إلى قاعدة البيانات
        success = add_pending_transaction(transaction_code, amount)

        if success:
            return jsonify({"status": "success", "message": "lets go my nigga"}), 200
        else:
            return jsonify({"status": "error", "message": "Failed to add the transaction!"}), 500
    else:
        return jsonify({"status": "error", "message": "The message is incorrect or its format is invalid!"}), 400

if __name__ == '__main__':
    app.run(debug=True)
