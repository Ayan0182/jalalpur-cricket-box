from flask import Flask, render_template, jsonify, request, session, redirect
import sqlite3
from datetime import datetime, timedelta, date
import bcrypt
from flask import Flask
import flask

app = Flask(__name__)
app.secret_key = "super-secret-admin-key"

# ================= DB =================
def get_db():
    conn = sqlite3.connect("database.db", timeout=10, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    c = conn.cursor()

    c.execute("""
    CREATE TABLE IF NOT EXISTS slots (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        slot_date TEXT,
        slot_time TEXT,
        price INTEGER,
        status TEXT,
        hold_until TEXT
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS bookings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        phone TEXT,
        slot_id INTEGER,
        status TEXT,
        created_at TEXT
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS admins (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password_hash BLOB,
        created_at TEXT
    )
    """)

    conn.commit()
    conn.close()

init_db()

# ================= CREATE DEFAULT ADMIN =================
def create_admin(username, password):
    conn = get_db()
    c = conn.cursor()
    hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt())

    try:
        c.execute(
            "INSERT INTO admins (username, password_hash, created_at) VALUES (?, ?, ?)",
            (username, hashed, datetime.now())
        )
        conn.commit()
    except sqlite3.IntegrityError:
        pass

    conn.close()

create_admin("admin", "admin123")

# ================= SLOT GENERATION =================
def generate_slots():
    conn = get_db()
    c = conn.cursor()
    today = date.today()

    for i in range(7):
        day = today + timedelta(days=i)
        is_weekend = day.weekday() in [5, 6]

        for hour in range(0, 24):
            slot_time = datetime.strptime(str(hour), "%H").strftime("%I:00 %p")

            if 7 <= hour < 18:
                price = 500
            else:
                price = 800 if is_weekend and hour >= 18 else 600

            c.execute("""
                SELECT COUNT(*) FROM slots
                WHERE slot_date=? AND slot_time=?
            """, (day.isoformat(), slot_time))

            if c.fetchone()[0] == 0:
                c.execute("""
                    INSERT INTO slots (slot_date, slot_time, price, status, hold_until)
                    VALUES (?, ?, ?, 'available', NULL)
                """, (day.isoformat(), slot_time, price))

    conn.commit()
    conn.close()

generate_slots()

# ================= USER ROUTES =================

# HOME PAGE
@app.route("/")
def home():
    return render_template("home.html")

# BOOKING PAGE
@app.route("/booking")
def booking():
    return render_template("index.html")

@app.route("/dates")
def get_dates():
    today = date.today()
    return jsonify([
        {
            "date": (today + timedelta(days=i)).isoformat(),
            "label": (today + timedelta(days=i)).strftime("%A, %b %d")
        } for i in range(7)
    ])

@app.route("/slots")
def get_slots():
    selected_date = request.args.get("date")
    if not selected_date:
        return jsonify([])

    conn = get_db()
    c = conn.cursor()

    now = datetime.now()
    c.execute("""
        UPDATE slots
        SET status='available', hold_until=NULL
        WHERE status='held' AND hold_until < ?
    """, (now,))
    conn.commit()

    c.execute("SELECT * FROM slots WHERE slot_date=?", (selected_date,))
    rows = c.fetchall()
    conn.close()

    return jsonify([
        {"id": r["id"], "time": r["slot_time"], "price": r["price"], "status": r["status"]}
        for r in rows
    ])

@app.route("/hold-slot", methods=["POST"])
def hold_slot():
    slot_id = request.json.get("slot_id")

    conn = get_db()
    c = conn.cursor()

    c.execute("SELECT status FROM slots WHERE id=?", (slot_id,))
    row = c.fetchone()

    if not row or row["status"] != "available":
        conn.close()
        return jsonify({"success": False})

    conn.close()
    return jsonify({"success": True})


@app.route("/confirm-booking", methods=["POST"])
def confirm_booking():
    data = request.json
    slot_ids = data.get("slot_ids", [])

    if not slot_ids:
        return jsonify({"success": False})

    conn = get_db()
    c = conn.cursor()

    for slot_id in slot_ids:
        c.execute("SELECT status FROM slots WHERE id=?", (slot_id,))
        row = c.fetchone()

        if not row or row["status"] != "available":
            conn.close()
            return jsonify({"success": False})

        c.execute("UPDATE slots SET status='booked' WHERE id=?", (slot_id,))
        c.execute("""
            INSERT INTO bookings (name, phone, slot_id, status, created_at)
            VALUES (?, ?, ?, 'confirmed', ?)
        """, (data["name"], data["phone"], slot_id, datetime.now()))

    conn.commit()
    conn.close()
    return jsonify({"success": True})

@app.route("/home-availability")
def home_availability():
    today = date.today().isoformat()

    conn = get_db()
    c = conn.cursor()

    c.execute("""
        SELECT status, COUNT(*) as count
        FROM slots
        WHERE slot_date=?
        GROUP BY status
    """, (today,))

    rows = c.fetchall()
    conn.close()

    available = 0
    booked = 0

    for r in rows:
        if r["status"] == "available":
            available = r["count"]
        elif r["status"] == "booked":
            booked = r["count"]

    return jsonify({
        "available": available,
        "booked": booked
    })



# ================= ADMIN AUTH =================
@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        conn = get_db()
        c = conn.cursor()
        c.execute("SELECT * FROM admins WHERE username=?", (username,))
        admin = c.fetchone()
        conn.close()

        if admin and bcrypt.checkpw(password.encode(), admin["password_hash"]):
            session["admin_id"] = admin["id"]
            return redirect("/admin")

        return render_template("admin_login.html", error="Invalid credentials")

    return render_template("admin_login.html")

@app.route("/admin/logout")
def admin_logout():
    session.clear()
    return redirect("/admin/login")

@app.route("/admin")
def admin():
    if not session.get("admin_id"):
        return redirect("/admin/login")
    return render_template("admin.html")

# ================= ADMIN SUMMARY =================
@app.route("/admin/summary")
def admin_summary():
    if not session.get("admin_id"):
        return jsonify({"error": "unauthorized"}), 401

    conn = get_db()
    c = conn.cursor()

    today = date.today()
    tomorrow = today + timedelta(days=1)

    c.execute("""
        SELECT COUNT(*) FROM bookings b
        JOIN slots s ON b.slot_id=s.id
        WHERE b.status='confirmed' AND s.slot_date=?
    """, (today.isoformat(),))
    today_count = c.fetchone()[0]

    c.execute("""
        SELECT COUNT(*) FROM bookings b
        JOIN slots s ON b.slot_id=s.id
        WHERE b.status='confirmed' AND s.slot_date=?
    """, (tomorrow.isoformat(),))
    tomorrow_count = c.fetchone()[0]

    c.execute("""
        SELECT COUNT(*) FROM bookings b
        JOIN slots s ON b.slot_id=s.id
        WHERE b.status='confirmed'
        AND strftime('%w', s.slot_date) IN ('0','6')
    """)
    weekend_count = c.fetchone()[0]

    c.execute("""
        SELECT SUM(s.price) FROM bookings b
        JOIN slots s ON b.slot_id=s.id
        WHERE b.status='confirmed'
    """)
    revenue = c.fetchone()[0] or 0

    conn.close()

    return jsonify({
        "today": today_count,
        "tomorrow": tomorrow_count,
        "weekend": weekend_count,
        "revenue": revenue
    })

@app.route("/admin/bookings")
def admin_bookings():
    if not session.get("admin_id"):
        return jsonify({"error": "unauthorized"}), 401

    conn = get_db()
    c = conn.cursor()

    c.execute("""
        SELECT b.id, b.name, b.phone, b.status,
               s.slot_date, s.slot_time, s.price
        FROM bookings b
        JOIN slots s ON b.slot_id=s.id
        ORDER BY s.slot_date DESC, s.slot_time
    """)
    rows = c.fetchall()
    conn.close()

    result = []
    for r in rows:
        d = datetime.strptime(r["slot_date"], "%Y-%m-%d")
        result.append({
            "booking_id": r["id"],
            "name": r["name"],
            "phone": r["phone"],
            "date": d.strftime("%d %b %Y"),
            "day": d.strftime("%A"),
            "time": r["slot_time"],
            "price": r["price"],
            "status": r["status"]
        })

    return jsonify(result)

@app.route("/admin/cancel-booking", methods=["POST"])
def cancel_booking():
    if not session.get("admin_id"):
        return jsonify({"success": False}), 401

    booking_id = request.json.get("booking_id")
    conn = get_db()
    c = conn.cursor()

    c.execute("SELECT slot_id FROM bookings WHERE id=?", (booking_id,))
    row = c.fetchone()

    if not row:
        conn.close()
        return jsonify({"success": False})

    c.execute("UPDATE bookings SET status='cancelled' WHERE id=?", (booking_id,))
    c.execute("UPDATE slots SET status='available' WHERE id=?", (row["slot_id"],))

    conn.commit()
    conn.close()
    return jsonify({"success": True})


# ================= DELETE CANCELLED BOOKING =================
@app.route("/admin/delete-booking", methods=["POST"])
def delete_booking():
    if not session.get("admin_id"):
        return jsonify({"success": False}), 401

    booking_id = request.json.get("booking_id")

    conn = get_db()
    c = conn.cursor()

    # allow delete only if cancelled
    c.execute("SELECT status FROM bookings WHERE id=?", (booking_id,))
    row = c.fetchone()

    if not row or row["status"] != "cancelled":
        conn.close()
        return jsonify({"success": False})

    c.execute("DELETE FROM bookings WHERE id=?", (booking_id,))
    conn.commit()
    conn.close()

    return jsonify({"success": True})



# ================= CHANGE PASSWORD =================
@app.route("/admin/change-password", methods=["POST"])
def change_password():
    if not session.get("admin_id"):
        return jsonify({"success": False, "message": "Unauthorized"}), 401

    data = request.get_json()
    old_password = data.get("old_password")
    new_password = data.get("new_password")

    if not old_password or not new_password:
        return jsonify({"success": False, "message": "Missing fields"}), 400

    conn = get_db()
    c = conn.cursor()

    c.execute("SELECT password_hash FROM admins WHERE id=?", (session["admin_id"],))
    row = c.fetchone()

    if not row:
        conn.close()
        return jsonify({"success": False, "message": "Admin not found"}), 404

    # ✅ verify old password
    if not bcrypt.checkpw(old_password.encode(), row["password_hash"]):
        conn.close()
        return jsonify({"success": False, "message": "Old password incorrect"}), 400

    # ✅ update new password
    new_hash = bcrypt.hashpw(new_password.encode(), bcrypt.gensalt())
    c.execute(
        "UPDATE admins SET password_hash=? WHERE id=?",
        (new_hash, session["admin_id"])
    )

    conn.commit()
    conn.close()

    return jsonify({"success": True})


# ================= RUN =================
if __name__ == "__main__":
    app.run(debug=True)
