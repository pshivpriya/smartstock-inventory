from flask import Flask, request, jsonify, render_template, Response
from flask_cors import CORS
from pymongo import MongoClient
from bson import ObjectId
from datetime import datetime, date
from werkzeug.security import generate_password_hash, check_password_hash
import smtplib
from email.mime.text import MIMEText
import pytz
import csv
from io import StringIO, BytesIO

# PDF imports
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors

# ================= APP =================
app = Flask(__name__)
CORS(app)

# ================= DATABASE =================
client = MongoClient("mongodb://localhost:27017")
db = client["smartstock"]

products = db["products"]
transactions = db["transactions"]
users = db["users"]
email_logs = db["email_logs"]

# ================= EMAIL CONFIG =================
EMAIL = "smartstock.notify@gmail.com"
EMAIL_PASSWORD = "nbmzrgcrtvlujtpn"
ADMIN_EMAIL = "pentishivapriya@gmail.com"

# =====================================================
# 🌐 ROOT
# =====================================================
@app.route("/")
def home():
    return render_template("login.html")


# =====================================================
# 📄 PAGE ROUTES
# =====================================================
@app.route("/admin/login")
def admin_login_page():
    return render_template("login.html")

@app.route("/admin/dashboard")
def admin_dashboard_page():
    return render_template("admin-dashboard.html")

@app.route("/products")
def products_page():
    return render_template("products.html")

@app.route("/add/product")
def add_product_page():
    return render_template("add-product.html")

@app.route("/transactions")
def transactions_page():
    return render_template("transactions.html")

@app.route("/login-page")
def login_page():
    return render_template("login.html")


@app.route("/employee/login")
def employee_login_page():
    return render_template("login.html")

@app.route("/employee/dashboard")
def employee_dashboard():
    return render_template("employee-dashboard.html")

@app.route("/manage/users")
def manage_users_page():
    return render_template("manage-users.html")

@app.route("/reports")
def reports_page():
    return render_template("reports.html")

@app.route("/register/employee")
def register_employee_page():
    return render_template("register-employee.html")

@app.route("/admin/signup")
def admin_signup_page():
    admin = users.find_one({"role": "admin"})
    if admin:
        return render_template("login.html")
    return render_template("admin-signup.html")

def send_low_stock_email(product_name, quantity, low_stock):
    subject = "⚠️ Low Stock Alert - SmartStock"
    body = f"""
Hello Admin,

⚠️ LOW STOCK ALERT ⚠️

Product: {product_name}
Current Quantity: {quantity}
Low Stock Threshold: {low_stock}

Please restock this item soon.

- SmartStock System
"""

    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = EMAIL
    msg["To"] = ADMIN_EMAIL

    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(EMAIL, EMAIL_PASSWORD)
        server.send_message(msg)
        server.quit()

        email_logs.insert_one({
            "product": product_name,
            "sentAt": datetime.now()
        })

        print("📧 Low stock email sent")

    except Exception as e:
        print("❌ Email error:", e)

# =====================================================
# 🔍 ADMIN EXISTS
# =====================================================
@app.route("/admin/exists", methods=["GET"])
def admin_exists():
    return jsonify({"exists": users.find_one({"role": "admin"}) is not None})

# =====================================================
# 🔐 AUTH
# =====================================================
@app.route("/register", methods=["POST"])
def register():
    data = request.json

    if data.get("role") == "admin" and users.find_one({"role": "admin"}):
        return jsonify({"error": "Admin already exists"}), 409

    if users.find_one({"email": data["email"]}):
        return jsonify({"error": "User already exists"}), 409

    users.insert_one({
        "name": data["name"],
        "email": data["email"],
        "password": generate_password_hash(data["password"]),
        "role": data.get("role", "employee"),
        "createdAt": datetime.utcnow()
    })
    return jsonify({"message": "User registered successfully"}), 201

@app.route("/login", methods=["POST"])
def login():
    data = request.json
    user = users.find_one({"email": data["email"]})

    if not user or not check_password_hash(user["password"], data["password"]):
        return jsonify({"error": "Invalid credentials"}), 401

    return jsonify({
        "message": "Login successful",
        "name": user["name"],
        "email": user["email"],
        "role": user["role"]
    })

# =====================================================
# 👥 USERS API (🔥 MISSING FIX – ADDED)
# =====================================================
@app.route("/users", methods=["GET"])
def get_users():
    try:
        result = []
        for u in users.find():
            result.append({
                "name": u.get("name", ""),
                "email": u.get("email", ""),
                "role": u.get("role", "employee")
            })
        return jsonify(result)
    except Exception as e:
        print("Users API error:", e)
        return jsonify({"error": "Server error"}), 500

# =====================================================
# 📦 PRODUCTS API
# =====================================================
@app.route("/api/products", methods=["GET"])
def get_products():
    return jsonify([{
        "id": str(p["_id"]),
        "name": p.get("name", ""),
        "category": p.get("category", ""),
        "supplier": p.get("supplier", ""),
        "quantity": int(p.get("quantity", 0)),
        "lowStock": int(p.get("lowStock", 0)),
        "costPrice": float(p.get("costPrice", 0))
    } for p in products.find()])

@app.route("/add-product", methods=["POST"])
def add_product():
    data = request.json
    products.insert_one({
        "name": data["name"],
        "category": data["category"],
        "supplier": data["supplier"],
        "quantity": int(data["quantity"]),
        "costPrice": float(data["costPrice"]),
        "lowStock": int(data["lowStock"]),
        "createdAt": datetime.utcnow()
    })
    return jsonify({"message": "Product added successfully"}), 201

# =====================================================
# 🔄 ADD TRANSACTION
# =====================================================
@app.route("/add_transaction", methods=["POST"])
def add_transaction():
    ist = pytz.timezone("Asia/Kolkata")

    # Convert to IST, then REMOVE timezone info (MongoDB-safe)
    ist_time = datetime.now(ist).replace(tzinfo=None)
    print("🔥 SAVING IST TIME:", ist_time)

    product_id = request.form.get("product_id")
    transaction_type = request.form.get("transaction_type")
    qty = int(request.form.get("quantity"))

    product = products.find_one({"_id": ObjectId(product_id)})
    if not product:
        return jsonify({"error": "Product not found"}), 404

    current_qty = int(product["quantity"])

    if transaction_type == "OUT" and qty > current_qty:
        return jsonify({"error": "Insufficient stock"}), 400

    new_qty = current_qty - qty if transaction_type == "OUT" else current_qty + qty

    products.update_one(
        {"_id": ObjectId(product_id)},
        {"$set": {"quantity": new_qty}}
    )
    # 🔔 LOW STOCK CHECK (FIXED)
    low_stock = int(product.get("lowStock", 0))

    already_sent = email_logs.find_one({
        "product": product["name"]
    })

    if new_qty <= low_stock and not already_sent:
        send_low_stock_email(
            product["name"],
            new_qty,
            low_stock
        )

    transactions.insert_one({
        "product_id": ObjectId(product_id),
        "type": transaction_type,
        "quantity": qty,
        "date": ist_time
    })

    return jsonify({"success": True})

# =====================================================
# 📧 LOW STOCK EMAIL
# =====================================================
def send_low_stock_email(product_name, quantity, low_stock):
    subject = "⚠️ Low Stock Alert - SmartStock"
    body = f"""
Hello Admin,

⚠️ LOW STOCK ALERT ⚠️

Product: {product_name}
Current Quantity: {quantity}
Low Stock Threshold: {low_stock}

Please restock this item soon.

- SmartStock System
"""

    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = EMAIL
    msg["To"] = ADMIN_EMAIL

    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(EMAIL, EMAIL_PASSWORD)
        server.send_message(msg)
        server.quit()

        email_logs.insert_one({
            "product": product_name,
            "sentAt": datetime.now()
        })

        print("📧 Low stock email sent")

    except Exception as e:
        print("❌ Email error:", e)



# =====================================================
# 📜 TRANSACTION HISTORY API (FIXED)
# =====================================================
@app.route("/api/transactions", methods=["GET"])
def get_transactions():
    result = []

    for t in transactions.find().sort("_id", -1):
        product_name = "Unknown Product"

        pid = t.get("product_id")
        if pid:
            try:
                product = products.find_one({"_id": ObjectId(pid)})
                if product:
                    product_name = product.get("name", "Unknown Product")
            except:
                pass

        dt = t.get("date")

        result.append({
            "_id": str(t.get("_id")),
            "productName": product_name,
            "type": t.get("type", ""),
            "quantity": t.get("quantity", 0),
            "date": dt.strftime("%d/%m/%Y, %I:%M:%S %p") if dt else ""
        })

    return jsonify(result)


# =====================================================
# 📊 DASHBOARD DATA
# =====================================================
@app.route("/low-stock", methods=["GET"])
def low_stock():
    items = [{
        "name": p["name"],
        "quantity": p["quantity"],
        "lowStock": p["lowStock"]
    } for p in products.find() if int(p["quantity"]) < int(p["lowStock"])]
    return jsonify({"count": len(items), "items": items})

@app.route("/inventory-value", methods=["GET"])
def inventory_value():
    total = sum(
        int(p["quantity"]) * float(p["costPrice"])
        for p in products.find()
    )
    return jsonify({"inventoryValue": total})

# =====================================================
# 📊 CHART DATA APIS
# =====================================================
@app.route("/api/chart/stock-quantity", methods=["GET"])
def stock_quantity_chart():
    return jsonify([
        {"name": p.get("name", ""), "quantity": int(p.get("quantity", 0))}
        for p in products.find()
    ])

@app.route("/api/chart/inventory-value", methods=["GET"])
def inventory_value_chart():
    return jsonify([
        {
            "name": p.get("name", ""),
            "value": int(p.get("quantity", 0)) * float(p.get("costPrice", 0))
        }
        for p in products.find()
    ])

# =====================================================
# 📤 EXPORT INVENTORY CSV
# =====================================================
@app.route("/export/inventory-csv", methods=["GET"])
def export_inventory_csv():
    output = StringIO()
    writer = csv.writer(output)

    writer.writerow([
        "Product Name", "Category", "Supplier",
        "Quantity", "Low Stock", "Cost Price", "Total Value"
    ])

    for p in products.find():
        qty = int(p.get("quantity", 0))
        cost = float(p.get("costPrice", 0))
        writer.writerow([
            p.get("name", ""),
            p.get("category", ""),
            p.get("supplier", ""),
            qty,
            p.get("lowStock", 0),
            cost,
            qty * cost
        ])

    output.seek(0)
    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=inventory_report.csv"}
    )

# =====================================================
# 📄 EXPORT INVENTORY PDF
# =====================================================
@app.route("/export/inventory-pdf", methods=["GET"])
def export_inventory_pdf():
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)

    styles = getSampleStyleSheet()
    elements = [Paragraph("<b>SmartStock Inventory Report</b>", styles["Title"])]

    data = [["Product", "Category", "Supplier", "Qty", "Cost", "Total"]]

    for p in products.find():
        qty = int(p.get("quantity", 0))
        cost = float(p.get("costPrice", 0))
        data.append([
            p.get("name", ""),
            p.get("category", ""),
            p.get("supplier", ""),
            qty,
            f"₹{cost}",
            f"₹{qty * cost}"
        ])

    table = Table(data, repeatRows=1)
    table.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 1, colors.black),
        ("BACKGROUND", (0, 0), (-1, 0), colors.darkblue),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("ALIGN", (3, 1), (-1, -1), "CENTER")
    ]))

    elements.append(table)
    doc.build(elements)
    buffer.seek(0)

    return Response(
        buffer,
        mimetype="application/pdf",
        headers={"Content-Disposition": "attachment; filename=inventory_report.pdf"}
    )
    # =====================================================
# 🔼 PROMOTE USER TO ADMIN
# =====================================================
@app.route("/promote", methods=["POST"])
def promote_user():
    data = request.json
    email = data.get("email")

    if not email:
        return jsonify({"error": "Email required"}), 400

    user = users.find_one({"email": email})
    if not user:
        return jsonify({"error": "User not found"}), 404

    if user.get("role") == "admin":
        return jsonify({"error": "User already admin"}), 400

    users.update_one(
        {"email": email},
        {"$set": {"role": "admin"}}
    )

    return jsonify({"message": "User promoted to admin"})


# =====================================================
# ❌ DELETE USER
# =====================================================
@app.route("/delete-user", methods=["POST"])
def delete_user():
    data = request.json
    email = data.get("email")

    if not email:
        return jsonify({"error": "Email required"}), 400

    user = users.find_one({"email": email})
    if not user:
        return jsonify({"error": "User not found"}), 404

    if user.get("role") == "admin":
        return jsonify({"error": "Cannot delete admin"}),  403

    users.delete_one({"email": email})
    return jsonify({"message": "User deleted successfully"})
# =====================================================
# 🔽 DEMOTE ADMIN TO EMPLOYEE (SAFE)
# =====================================================
@app.route("/demote", methods=["POST"])
def demote_user():
    data = request.json or {}
    email = data.get("email")
    requester = data.get("requester")

    if not email or not requester:
        return jsonify({"error": "Invalid request"}), 400

    if email == requester:
        return jsonify({"error": "You cannot demote yourself"}), 403

    user = users.find_one({"email": email})
    if not user:
        return jsonify({"error": "User not found"}), 404

    if user.get("role") != "admin":
        return jsonify({"error": "User is not an admin"}), 400

    admin_count = users.count_documents({"role": "admin"})
    if admin_count <= 1:
        return jsonify({"error": "At least one admin required"}), 403

    users.update_one(
        {"email": email},
        {"$set": {"role": "employee"}}
    )

    return jsonify({"message": "Admin demoted successfully"})


# ================= RUN =================
if __name__ == "__main__":
    print("🚀 SmartStock backend running...")
    app.run(debug=True)