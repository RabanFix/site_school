/* ====================================================
   МБОУ Школа №147 | Работа — Основной JS
   ==================================================== */

document.addEventListener("DOMContentLoaded", () => {
  initBurger();
  initCounters();
  initAutocomplete();
  initFormValidation();
  autoCloseFlash();
});

/* ── Burger menu ───────────────────────────────────── */
function initBurger() {
  const btn = document.getElementById("burgerBtn");
  const menu = document.getElementById("mobileMenu");
  if (!btn || !menu) return;
  btn.addEventListener("click", () => {
    menu.classList.toggle("open");
    btn.classList.toggle("open");
  });
}

/* ── Counter animation ─────────────────────────────── */
function initCounters() {
  document.querySelectorAll("[data-target]").forEach((el) => {
    const target = +el.dataset.target;
    let current = 0;
    const step = target / 50;
    const timer = setInterval(() => {
      current = Math.min(current + step, target);
      el.textContent = Math.round(current);
      if (current >= target) clearInterval(timer);
    }, 30);
  });
}

/* ── Autocomplete search ───────────────────────────── */
function initAutocomplete() {
  const input = document.getElementById("heroSearchInput");
  const list = document.getElementById("searchAutocomplete");
  if (!input || !list) return;

  let timer;
  input.addEventListener("input", () => {
    clearTimeout(timer);
    const q = input.value.trim();
    if (q.length < 2) {
      list.classList.remove("open");
      return;
    }
    timer = setTimeout(async () => {
      try {
        const res = await fetch(`/api/search?q=${encodeURIComponent(q)}`);
        const data = await res.json();
        list.innerHTML = "";
        if (!data.length) {
          list.classList.remove("open");
          return;
        }
        data.forEach((item) => {
          const li = document.createElement("li");
          li.innerHTML = `<a href="/vacancies/${item.id}">
            <span>${highlight(item.title, q)}</span>
            <span style="color:var(--success);font-size:12px;">${item.salary}</span>
          </a>`;
          list.appendChild(li);
        });
        list.classList.add("open");
      } catch (e) {
        console.error(e);
      }
    }, 280);
  });

  document.addEventListener("click", (e) => {
    if (!input.contains(e.target) && !list.contains(e.target))
      list.classList.remove("open");
  });
}

function highlight(text, q) {
  const re = new RegExp(`(${q})`, "gi");
  return text.replace(re, '<strong style="color:var(--primary)">$1</strong>');
}

/* ── Form validation ───────────────────────────────── */
function initFormValidation() {
  document.querySelectorAll("form[novalidate]").forEach((form) => {
    form.addEventListener("submit", (e) => {
      let valid = true;
      form.querySelectorAll("[required]").forEach((field) => {
        field.style.borderColor = "";
        if (!field.value.trim()) {
          field.style.borderColor = "var(--danger)";
          field.style.boxShadow = "0 0 0 3px rgba(239,68,68,.15)";
          valid = false;
          field.addEventListener(
            "input",
            () => {
              field.style.borderColor = "";
              field.style.boxShadow = "";
            },
            { once: true },
          );
        }
      });
      if (!valid) {
        e.preventDefault();
        showToast("Заполните обязательные поля", "error");
        form
          .querySelector("[required]:invalid, [required][style]")
          ?.scrollIntoView({
            behavior: "smooth",
            block: "center",
          });
      }
    });
  });
}

/* ── Auto-close flash after 5s ─────────────────────── */
function autoCloseFlash() {
  document.querySelectorAll(".flash").forEach((el) => {
    setTimeout(() => {
      el.style.transition = "opacity .4s";
      el.style.opacity = "0";
      setTimeout(() => el.remove(), 400);
    }, 5000);
  });
}

/* ── Toast ─────────────────────────────────────────── */
function showToast(message, type = "success") {
  const icons = { success: "✅", error: "❌", info: "ℹ️" };
  const container = document.getElementById("toastContainer");
  if (!container) return;
  const t = document.createElement("div");
  t.className = `toast toast--${type}`;
  t.innerHTML = `<span style="font-size:20px;">${icons[type] || "📢"}</span>
                 <span style="font-size:14px;font-weight:500;">${message}</span>`;
  container.appendChild(t);
  setTimeout(() => {
    t.style.transition = "all .3s";
    t.style.opacity = "0";
    t.style.transform = "translateX(100%)";
    setTimeout(() => t.remove(), 300);
  }, 3500);
}
