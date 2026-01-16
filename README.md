# 📦 SmartStock Inventory Management System

SmartStock is a **real-world Inventory Management System** designed to manage products, stock movements, users, and reports with **role-based access** for **Admin** and **Employee**.

---

## 🚀 Features

### 🔐 Authentication & Roles
- Unified Login for **Admin & Employee**
- Role-based redirection after login
- Secure password hashing
- Session & localStorage based auth handling

---

### 👨‍💼 Admin Dashboard
- Add / Update / Delete products
- Manage employees (add, promote, demote, delete)
- Stock IN / OUT transactions
- Low stock & critical stock alerts (Email notifications)
- Inventory value calculation
- Download reports:
  - 📄 PDF
  - 📊 CSV
- View employee activity & transaction history

---

### 👷 Employee Dashboard (Read-Only)
- View products
- View stock transactions
- Today’s summary:
  - IN transactions
  - OUT transactions
  - Items moved today
- Low stock visibility
- Recent transactions
- Activity tracking (view-only access)

---

### 📦 Product Management
- Product name, category, supplier
- Cost price & quantity
- Low stock threshold
- Automatic stock update on transactions
- Inventory value calculation

---

### 📜 Transactions
- IN / OUT stock movement
- Date & time tracking (IST)
- Product-wise transaction history
- Daily summary calculations

---

### ⚠️ Alerts & Notifications
- Automatic **Low Stock Email Alert** to Admin
- Prevents duplicate alert emails
- Email log tracking in database

---

### 📊 Reports
- Inventory Report (PDF & CSV)
- Product-wise stock report
- Low stock report
- Transaction history report

---

## 🛠️ Tech Stack

### Backend
- Python
- Flask
- MongoDB
- PyMongo
- ReportLab (PDF generation)

### Frontend
- HTML5
- CSS3 (Modern Dark UI)
- JavaScript (Fetch API)

### Tools
- Git & GitHub
- VS Code


