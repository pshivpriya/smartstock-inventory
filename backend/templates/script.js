/* =====================================================
   ADMIN LOGIN SCRIPT
===================================================== */
document.addEventListener("DOMContentLoaded", function () {

  const adminLoginForm = document.getElementById("adminLoginForm");

  if (adminLoginForm) {
    adminLoginForm.addEventListener("submit", function (e) {
      e.preventDefault();

      const email = document.getElementById("loginEmail").value.trim();
      const password = document.getElementById("loginPassword").value;
      const msg = document.getElementById("adminLoginMessage");

      const admin = JSON.parse(localStorage.getItem("adminAccount"));

      if (!admin) {
        msg.textContent = "❌ Admin account not found. Please create one.";
        msg.style.color = "red";
        return;
      }

      if (admin.email !== email || admin.password !== password) {
        msg.textContent = "❌ Invalid credentials";
        msg.style.color = "red";
        return;
      }

      localStorage.setItem("adminLoggedIn", "true");
      msg.textContent = "✅ Login successful. Redirecting...";
      msg.style.color = "lightgreen";

      setTimeout(() => {
        window.location.href = "admin-dashboard.html";
      }, 1200);
    });
  }

  // Run ONLY on dashboard
  if (document.getElementById("lowStockAlert")) {
    checkLowStock();
  }
});

/* =====================================================
   LOW STOCK CHECK (FINAL FIX)
===================================================== */
function checkLowStock() {
  const products = JSON.parse(localStorage.getItem("products")) || [];
  let lowStockItems = [];

  products.forEach(p => {
    const quantity = Number(p.quantity) || 0;
    const lowLimit = Number(p.low) || 0;   // ✅ CORRECT FIELD

    if (quantity < lowLimit) {
      lowStockItems.push({
        name: p.name,
        quantity: quantity,
        lowLimit: lowLimit
      });
    }
  });

  // Update dashboard count
  const lowStockCountEl = document.getElementById("lowStock");
  if (lowStockCountEl) {
    lowStockCountEl.innerText = lowStockItems.length;
  }

  // Show alert & send email if ANY low stock exists
  if (lowStockItems.length > 0) {
    const alertBox = document.getElementById("lowStockAlert");
    if (alertBox) alertBox.style.display = "block";

    sendLowStockMail(lowStockItems);
  }
}

/* =====================================================
   SEND EMAIL TO BACKEND
===================================================== */
function sendLowStockMail(lowStockItems) {
  fetch("http://localhost:5000/low-stock-alert", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ lowStockItems })
  })
  .then(() => console.log("📧 Low stock email sent"))
  .catch(err => console.error("Email error:", err));
}
