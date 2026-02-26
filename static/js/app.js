// ---------- LIVE TOTAL ----------
const qty = document.querySelector("input[name='quantity']");
const rate = document.querySelector("input[name='rate']");
const totalBox = document.querySelector(".total-box");

function calculateTotal() {
    const q = parseFloat(qty?.value || 0);
    const r = parseFloat(rate?.value || 0);
    if (totalBox) {
        totalBox.innerText = "Total Amount: ₹" + (q * r).toFixed(2);
    }
}

qty?.addEventListener("input", calculateTotal);
rate?.addEventListener("input", calculateTotal);

// ---------- VALIDATION ----------
document.querySelector("form")?.addEventListener("submit", function(e) {
    if (!qty.value || !rate.value) {
        alert("Please enter Quantity and Rate");
        e.preventDefault();
    }
});

// ---------- THEME ----------
function setTheme(mode) {
    document.body.classList.toggle("dark", mode === "dark");
    localStorage.setItem("theme", mode);
    updateThemeButtons();
}

function updateThemeButtons() {
    const lightBtn = document.getElementById("lightBtn");
    const darkBtn = document.getElementById("darkBtn");

    lightBtn?.classList.toggle("active", !document.body.classList.contains("dark"));
    darkBtn?.classList.toggle("active", document.body.classList.contains("dark"));
}

// Load saved theme
const savedTheme = localStorage.getItem("theme") || "light";
setTheme(savedTheme);
