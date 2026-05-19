// 🚀 Smooth Fade-in Animation
document.addEventListener("DOMContentLoaded", () => {
    document.querySelectorAll(".card").forEach((card, index) => {
        card.style.opacity = 0;
        card.style.transform = "translateY(20px)";

        setTimeout(() => {
            card.style.transition = "all 0.5s ease";
            card.style.opacity = 1;
            card.style.transform = "translateY(0)";
        }, index * 100);
    });
});

// 💡 Auto-hide Alerts after 3 seconds
setTimeout(() => {
    document.querySelectorAll(".alert").forEach(alert => {
        alert.style.transition = "opacity 0.5s ease";
        alert.style.opacity = 0;

        setTimeout(() => alert.remove(), 500);
    });
}, 3000);

// 🔢 Format numbers nicely (₹)
document.querySelectorAll("td, .card-text").forEach(el => {
    let text = el.innerText;
    if (!isNaN(text.replace(/[^0-9.-]+/g,""))) {
        let num = parseFloat(text.replace(/[^0-9.-]+/g,""));
        if (!isNaN(num)) {
            el.innerText = "₹ " + num.toLocaleString("en-IN", {
                minimumFractionDigits: 2
            });
        }
    }
});

// 🔥 Highlight high expense rows
document.querySelectorAll("tr").forEach(row => {
    if (row.innerText.includes("Expense")) {
        row.style.fontWeight = "500";
    }
});

// 🧠 Smart Insight Popup (No HTML change needed)
window.addEventListener("load", () => {
    let income = document.body.innerText.match(/Total Income.*₹ ([\d,\.]+)/);
    let expense = document.body.innerText.match(/Total Expenses.*₹ ([\d,\.]+)/);

    if (income && expense) {
        let inc = parseFloat(income[1].replace(/,/g, ""));
        let exp = parseFloat(expense[1].replace(/,/g, ""));

        setTimeout(() => {
            if (exp > inc) {
                alert("⚠️ Warning: Your expenses are higher than your income!");
            } else {
                console.log("✅ You are managing your finances well!");
            }
        }, 1500);
    }
});