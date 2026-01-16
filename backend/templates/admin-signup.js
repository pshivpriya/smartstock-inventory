document.addEventListener("DOMContentLoaded", function () {

  const form = document.getElementById("adminSignupForm");

  form.addEventListener("submit", function (e) {
    e.preventDefault();

    const name = adminName.value.trim();
    const email = adminEmail.value.trim();
    const password = adminPassword.value;
    const confirm = adminConfirmPassword.value;
    const msg = document.getElementById("adminSignupMessage");

    if (!name || !email || !password || !confirm) {
      msg.textContent = "❌ Please fill all fields";
      msg.style.color = "red";
      return;
    }

    if (password !== confirm) {
      msg.textContent = "❌ Passwords do not match";
      msg.style.color = "red";
      return;
    }

    localStorage.setItem(
      "adminAccount",
      JSON.stringify({ name, email, password })
    );

    msg.textContent = "✅ Account created successfully. Redirecting to login...";
    msg.style.color = "lightgreen";

    setTimeout(() => {
      window.location.href = "/admin/login";
    }, 1200);
  });
});
