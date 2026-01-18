from flask import Flask, request, jsonify, render_template, Response, redirect, url_for, session
from flask_cors import CORS
from pymongo import MongoClient
from bson import ObjectId
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
import pytz
import csv
from io import StringIO
import traceback

# ================= APP =================
app = Flask(__name__)

# CORS Configuration - More permissive for development
CORS(app, 
     supports_credentials=True,
     origins=["http://127.0.0.1:5000", "http://localhost:5000"],
     allow_headers=["Content-Type", "Authorization"],
     methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"])

# Secret key for sessions
app.secret_key = "smartstock_secret_key_2026"

# Session configuration
app.config.update(
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_SECURE=False,
    SESSION_COOKIE_HTTPONLY=True,
    PERMANENT_SESSION_LIFETIME=3600  # 1 hour
)

# ================= DATABASE =================
try:
    client = MongoClient("mongodb://localhost:27017", serverSelectionTimeoutMS=5000)
    # Test connection
    client.server_info()
    print("✅ MongoDB connected successfully")
    
    db = client["smartstock"]
    products = db["products"]
    transactions = db["transactions"]
    users = db["users"]
    
    # Create indexes for better performance
    users.create_index("email", unique=True)
    products.create_index("name")
    transactions.create_index("date")
    
except Exception as e:
    print(f"❌ MongoDB connection failed: {e}")
    print("Please ensure MongoDB is running on localhost:27017")

# =====================================================
# 🔐 HELPERS
# =====================================================
def login_required():
    return "email" in session

def admin_required():
    return "email" in session and session.get("role") == "admin"

# =====================================================
# 🌐 ROOT
# =====================================================
@app.route("/")
def home():
    return render_template("login.html")

@app.route("/login-page")
def login_page():
    return render_template("login.html")

# =====================================================
# 👤 CURRENT USER
# =====================================================
@app.route("/me")
def me():
    if "email" not in session:
        return jsonify({"error": "Not logged in"}), 401

    return jsonify({
        "email": session["email"],
        "role": session["role"]
    })

# =====================================================
# 📄 PAGE ROUTES
# =====================================================
@app.route("/admin/dashboard")
def admin_dashboard():
    if not admin_required():
        return redirect(url_for("login_page"))
    return render_template("admin-dashboard.html")

@app.route("/employee/dashboard")
def employee_dashboard():
    if not login_required():
        return redirect(url_for("login_page"))
    return render_template("employee-dashboard.html")

@app.route("/products")
def products_page():
    if not login_required():
        return redirect(url_for("login_page"))
    return render_template("products.html")

@app.route("/add/product")
def add_product_page():
    if not admin_required():
        return redirect(url_for("employee_dashboard"))
    return render_template("add-product.html")

@app.route("/transactions")
def transactions_page():
    if not login_required():
        return redirect(url_for("login_page"))
    return render_template("transactions.html")

@app.route("/manage/users")
def manage_users_page():
    if not admin_required():
        return redirect(url_for("employee_dashboard"))
    return render_template("manage-users.html")

@app.route("/register/employee")
def register_employee_page():
    if not admin_required():
        return redirect(url_for("employee_dashboard"))
    return render_template("register-employee.html")

@app.route("/reports")
def reports_page():
    if not admin_required():
        return redirect(url_for("employee_dashboard"))
    return render_template("reports.html")

# =====================================================
# 🔓 LOGOUT
# =====================================================
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login_page"))

# =====================================================
# 🔐 AUTH API (FIXED WITH BETTER ERROR HANDLING)
# =====================================================
@app.route("/login", methods=["POST"])
def login():
    try:
        data = request.json
        
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        email = data.get("email", "").strip()
        password = data.get("password", "")
        
        if not email or not password:
            return jsonify({"error": "Email and password are required"}), 400
        
        user = users.find_one({"email": email})
        
        if not user:
            return jsonify({"error": "Invalid credentials"}), 401
        
        if not check_password_hash(user["password"], password):
            return jsonify({"error": "Invalid credentials"}), 401
        
        # Set session
        session["email"] = user["email"]
        session["role"] = user.get("role", "employee")
        session.permanent = True
        
        print(f"✅ User logged in: {email} (Role: {session['role']})")
        
        return jsonify({
            "message": "Login successful",
            "role": user.get("role", "employee"),
            "email": user["email"]
        }), 200
        
    except Exception as e:
        print(f"❌ Login error: {str(e)}")
        traceback.print_exc()
        return jsonify({"error": "Server error during login"}), 500

@app.route("/register", methods=["POST"])
def register():
    try:
        if not admin_required():
            return jsonify({"error": "Unauthorized"}), 403

        data = request.json
        
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        email = data.get("email", "").strip()
        name = data.get("name", "").strip()
        password = data.get("password", "")
        role = data.get("role", "employee")
        
        if not email or not name or not password:
            return jsonify({"error": "All fields are required"}), 400

        if users.find_one({"email": email}):
            return jsonify({"error": "User already exists"}), 409

        users.insert_one({
            "name": name,
            "email": email,
            "password": generate_password_hash(password),
            "role": role,
            "createdAt": datetime.utcnow()
        })
        
        print(f"✅ New user registered: {email}")

        return jsonify({"message": "User registered successfully"}), 201
        
    except Exception as e:
        print(f"❌ Registration error: {str(e)}")
        traceback.print_exc()
        return jsonify({"error": "Server error during registration"}), 500

# =====================================================
# 👥 USERS API
# =====================================================
@app.route("/users")
def get_users():
    try:
        if not admin_required():
            return jsonify({"error": "Unauthorized"}), 403

        user_list = []
        for u in users.find():
            user_list.append({
                "id": str(u["_id"]),
                "name": u.get("name", ""),
                "email": u.get("email", ""),
                "role": u.get("role", "employee"),
                "createdAt": u.get("createdAt", datetime.utcnow()).strftime("%Y-%m-%d")
            })
        
        return jsonify(user_list), 200
        
    except Exception as e:
        print(f"❌ Get users error: {str(e)}")
        return jsonify({"error": "Failed to fetch users"}), 500

# =====================================================
# 📦 PRODUCTS API
# =====================================================
@app.route("/api/products")
def get_products():
    try:
        if not login_required():
            return jsonify({"error": "Unauthorized"}), 403
        
        result = []
        for p in products.find():
            result.append({
                "id": str(p["_id"]),
                "name": p.get("name", ""),
                "quantity": int(p.get("quantity", 0)),
                "lowStock": int(p.get("lowStock", 0)),
                "category": p.get("category", ""),
                "supplier": p.get("supplier", ""),
                "costPrice": float(p.get("costPrice", 0))
            })
        return jsonify(result), 200
        
    except Exception as e:
        print(f"❌ Get products error: {str(e)}")
        return jsonify({"error": "Failed to fetch products"}), 500

@app.route("/api/products", methods=["POST"])
def add_product():
    try:
        if not admin_required():
            return jsonify({"error": "Unauthorized"}), 403
        
        data = request.json
        
        products.insert_one({
            "name": data.get("name"),
            "category": data.get("category"),
            "supplier": data.get("supplier"),
            "quantity": int(data.get("quantity", 0)),
            "lowStock": int(data.get("lowStock", 0)),
            "costPrice": float(data.get("costPrice", 0)),
            "createdAt": datetime.utcnow()
        })
        
        return jsonify({"message": "Product added successfully"}), 201
        
    except Exception as e:
        print(f"❌ Add product error: {str(e)}")
        return jsonify({"error": "Failed to add product"}), 500

@app.route("/api/products/<product_id>", methods=["DELETE"])
def delete_product(product_id):
    try:
        if not admin_required():
            return jsonify({"error": "Unauthorized"}), 403
        
        result = products.delete_one({"_id": ObjectId(product_id)})
        
        if result.deleted_count == 0:
            return jsonify({"error": "Product not found"}), 404
        
        return jsonify({"message": "Product deleted successfully"}), 200
        
    except Exception as e:
        print(f"❌ Delete product error: {str(e)}")
        return jsonify({"error": "Failed to delete product"}), 500

# =====================================================
# 🔄 TRANSACTIONS
# =====================================================
@app.route("/add_transaction", methods=["POST"])
def add_transaction():
    try:
        if not login_required():
            return jsonify({"error": "Unauthorized"}), 403

        ist = pytz.timezone("Asia/Kolkata")
        ist_time = datetime.now(ist).replace(tzinfo=None)

        product_id = request.form.get("product_id")
        ttype = request.form.get("transaction_type")
        qty = int(request.form.get("quantity"))

        product = products.find_one({"_id": ObjectId(product_id)})
        if not product:
            return jsonify({"error": "Product not found"}), 404

        if ttype == "OUT" and qty > int(product["quantity"]):
            return jsonify({"error": "Insufficient stock"}), 400

        new_qty = product["quantity"] + qty if ttype == "IN" else product["quantity"] - qty
        products.update_one({"_id": ObjectId(product_id)}, {"$set": {"quantity": new_qty}})

        transactions.insert_one({
            "product_id": ObjectId(product_id),
            "productName": product["name"],
            "type": ttype,
            "quantity": qty,
            "date": ist_time,
            "user": session.get("email")
        })

        return jsonify({"success": True, "message": "Transaction added successfully"}), 200
        
    except Exception as e:
        print(f"❌ Add transaction error: {str(e)}")
        traceback.print_exc()
        return jsonify({"error": "Failed to add transaction"}), 500

# =====================================================
# 📜 TRANSACTION HISTORY (FIXED – FINAL)
# =====================================================
@app.route("/api/transactions")
def get_transactions():
    try:
        if not login_required():
            return jsonify({"error": "Unauthorized"}), 403

        data = []

        for t in transactions.find().sort("_id", -1).limit(100):

            # Resolve product name safely
            product_name = "Unknown Product"

            if "product_id" in t:
                try:
                    product = products.find_one({"_id": ObjectId(t["product_id"])})
                    if product:
                        product_name = product.get("name", "Unknown Product")
                except:
                    pass
            else:
                product_name = t.get("productName", "Unknown Product")

            # Ensure date is JSON-safe (ISO format for JS)
            tx_date = t.get("date")
            if isinstance(tx_date, datetime):
                tx_date = tx_date.isoformat()
            else:
                tx_date = str(tx_date)

            data.append({
                "productName": product_name,
                "type": t.get("type"),
                "quantity": int(t.get("quantity", 0)),
                "date": tx_date,          # ✅ FIXED
                "user": t.get("user", "N/A")
            })

        return jsonify(data), 200

    except Exception as e:
        print("❌ Get transactions error:", e)
        traceback.print_exc()
        return jsonify({"error": "Failed to fetch transactions"}), 500


# =====================================================
# 🔔 LOW STOCK
# =====================================================
@app.route("/low-stock")
def low_stock():
    try:
        items = []
        for p in products.find():
            low_stock_threshold = int(p.get("lowStock", 0))
            current_qty = int(p.get("quantity", 0))
            
            if low_stock_threshold > 0 and current_qty <= low_stock_threshold:
                items.append({
                    "name": p["name"],
                    "quantity": current_qty,
                    "lowStock": low_stock_threshold
                })
        
        return jsonify({"count": len(items), "items": items}), 200
        
    except Exception as e:
        print(f"❌ Low stock error: {str(e)}")
        return jsonify({"error": "Failed to fetch low stock items"}), 500
    
@app.route("/promote", methods=["POST"])
def promote_user():
    try:
        if not admin_required():
            return jsonify({"error": "Unauthorized"}), 403

        data = request.json
        email = data.get("email")

        if not email:
            return jsonify({"error": "Email is required"}), 400

        if email == session.get("email"):
            return jsonify({"error": "You cannot promote yourself"}), 400

        result = users.update_one(
            {"email": email},
            {"$set": {"role": "admin"}}
        )

        if result.matched_count == 0:
            return jsonify({"error": "User not found"}), 404

        return jsonify({"message": "User promoted to admin"}), 200

    except Exception as e:
        print("❌ Promote error:", e)
        return jsonify({"error": "Failed to promote user"}), 500
    
@app.route("/demote", methods=["POST"])
def demote_user():
    try:
        if not admin_required():
            return jsonify({"error": "Unauthorized"}), 403

        data = request.json
        email = data.get("email")

        if not email:
            return jsonify({"error": "Email is required"}), 400

        if email == session.get("email"):
            return jsonify({"error": "You cannot demote yourself"}), 400

        result = users.update_one(
            {"email": email},
            {"$set": {"role": "employee"}}
        )

        if result.matched_count == 0:
            return jsonify({"error": "User not found"}), 404

        return jsonify({"message": "User demoted to employee"}), 200

    except Exception as e:
        print("❌ Demote error:", e)
        return jsonify({"error": "Failed to demote user"}), 500
    
@app.route("/delete-user", methods=["POST"])
def delete_user():
    try:
        if not admin_required():
            return jsonify({"error": "Unauthorized"}), 403

        data = request.json
        email = data.get("email")

        if not email:
            return jsonify({"error": "Email is required"}), 400

        if email == session.get("email"):
            return jsonify({"error": "You cannot delete yourself"}), 400

        result = users.delete_one({"email": email})

        if result.deleted_count == 0:
            return jsonify({"error": "User not found"}), 404

        return jsonify({"message": "User deleted successfully"}), 200

    except Exception as e:
        print("❌ Delete user error:", e)
        return jsonify({"error": "Failed to delete user"}), 500




# =====================================================
# 💰 INVENTORY VALUE
# =====================================================
@app.route("/inventory-value")
def inventory_value():
    try:
        total = 0
        for p in products.find():
            qty = int(p.get("quantity", 0))
            cost = float(p.get("costPrice", 0))
            total += qty * cost
        
        return jsonify({"inventoryValue": round(total, 2)}), 200
        
    except Exception as e:
        print(f"❌ Inventory value error: {str(e)}")
        return jsonify({"error": "Failed to calculate inventory value"}), 500

# =====================================================
# 📊 DASHBOARD STATS
# =====================================================
@app.route("/api/stats")
def get_stats():
    try:
        if not login_required():
            return jsonify({"error": "Unauthorized"}), 403
        
        total_products = products.count_documents({})
        low_stock_count = products.count_documents({
            "$expr": {"$lte": ["$quantity", "$lowStock"]}
        })
        
        total_value = sum(
            int(p.get("quantity", 0)) * float(p.get("costPrice", 0))
            for p in products.find()
        )
        
        recent_transactions = transactions.count_documents({
            "date": {"$gte": datetime.utcnow().replace(hour=0, minute=0, second=0)}
        })
        
        return jsonify({
            "totalProducts": total_products,
            "lowStockItems": low_stock_count,
            "inventoryValue": round(total_value, 2),
            "todayTransactions": recent_transactions
        }), 200
        
    except Exception as e:
        print(f"❌ Stats error: {str(e)}")
        return jsonify({"error": "Failed to fetch statistics"}), 500

# =====================================================
# 📤 EXPORT CSV
# =====================================================
@app.route("/export/inventory-csv")
def export_inventory_csv():
    try:
        if not admin_required():
            return redirect(url_for("login_page"))

        output = StringIO()
        writer = csv.writer(output)
        writer.writerow(["Name", "Category", "Supplier", "Qty", "LowStock", "Cost", "Total Value"])

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
                round(qty * cost, 2)
            ])

        output.seek(0)
        return Response(
            output.getvalue(),
            mimetype="text/csv",
            headers={"Content-Disposition": "attachment; filename=inventory.csv"}
        )
        
    except Exception as e:
        print(f"❌ Export error: {str(e)}")
        return jsonify({"error": "Failed to export CSV"}), 500

# =====================================================
# 🏥 HEALTH CHECK
# =====================================================
@app.route("/health")
def health_check():
    try:
        # Check MongoDB connection
        client.server_info()
        return jsonify({
            "status": "healthy",
            "database": "connected",
            "timestamp": datetime.utcnow().isoformat()
        }), 200
    except Exception as e:
        return jsonify({
            "status": "unhealthy",
            "database": "disconnected",
            "error": str(e)
        }), 503

# =====================================================
# ❌ ERROR HANDLERS
# =====================================================
@app.errorhandler(404)
def not_found(e):
    return jsonify({"error": "Resource not found"}), 404

@app.errorhandler(500)
def internal_error(e):
    print(f"❌ Internal server error: {str(e)}")
    return jsonify({"error": "Internal server error"}), 500

# ================= RUN =================
if __name__ == "__main__":
    print("=" * 50)
    print("🚀 SmartStock Backend Starting...")
    print("=" * 50)
    print(f"📅 Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🌐 Running on: http://127.0.0.1:5000")
    print(f"🔧 Debug mode: ON")
    print("=" * 50)
    
    app.run(debug=True, host="127.0.0.1", port=5000)