const peso = new Intl.NumberFormat("es-CO", { style: "currency", currency: "COP", maximumFractionDigits: 0 });

const fallbackIconPaths = {
  "search": '<circle cx="11" cy="11" r="6"></circle><path d="m16 16 4 4"></path>',
  "shield-check": '<path d="M12 3 5 6v6c0 5 3.5 8 7 9 3.5-1 7-4 7-9V6l-7-3Z"></path><path d="m9 12 2 2 4-5"></path>',
  "badge-check": '<circle cx="12" cy="12" r="8"></circle><path d="m8.5 12 2.2 2.2 4.8-5"></path>',
  "sparkles": '<path d="M12 3l1.3 4.2L17.5 9l-4.2 1.8L12 15l-1.3-4.2L6.5 9l4.2-1.8L12 3Z"></path><path d="M19 14l.8 2.2L22 17l-2.2.8L19 20l-.8-2.2L16 17l2.2-.8L19 14Z"></path>',
  "credit-card": '<rect x="3" y="6" width="18" height="12" rx="2"></rect><path d="M3 10h18"></path><path d="M7 15h4"></path>',
  "car-front": '<path d="M6 16h12l-1-6H7l-1 6Z"></path><path d="M8 16v2"></path><path d="M16 16v2"></path><circle cx="8" cy="13" r="1"></circle><circle cx="16" cy="13" r="1"></circle>',
  "car": '<path d="M5 14h14l-1.5-5h-11L5 14Z"></path><path d="M7 14v3"></path><path d="M17 14v3"></path><circle cx="8" cy="17" r="1"></circle><circle cx="16" cy="17" r="1"></circle>',
  "plug-zap": '<path d="M8 2v6"></path><path d="M16 2v6"></path><path d="M6 8h12v4a6 6 0 0 1-12 0V8Z"></path><path d="m13 14-2 4h3l-2 4"></path>',
  "plug": '<path d="M8 2v6"></path><path d="M16 2v6"></path><path d="M6 8h12v4a6 6 0 0 1-12 0V8Z"></path>',
  "wallet": '<path d="M4 7h16v12H4a2 2 0 0 1-2-2V5a2 2 0 0 0 2 2Z"></path><path d="M16 12h4v4h-4a2 2 0 0 1 0-4Z"></path>',
  "gem": '<path d="M6 3h12l4 6-10 12L2 9l4-6Z"></path><path d="M2 9h20"></path><path d="m9 9 3 12 3-12"></path>',
  "map": '<path d="m3 6 6-3 6 3 6-3v15l-6 3-6-3-6 3V6Z"></path><path d="M9 3v15"></path><path d="M15 6v15"></path>',
  "route": '<circle cx="6" cy="6" r="2"></circle><circle cx="18" cy="18" r="2"></circle><path d="M8 6h5a3 3 0 0 1 0 6h-2a3 3 0 0 0 0 6h5"></path>',
  "list-checks": '<path d="m4 6 1.5 1.5L8 5"></path><path d="M11 6h9"></path><path d="m4 12 1.5 1.5L8 11"></path><path d="M11 12h9"></path><path d="m4 18 1.5 1.5L8 17"></path><path d="M11 18h9"></path>',
  "gauge": '<path d="M4 14a8 8 0 1 1 16 0"></path><path d="m12 14 4-5"></path><path d="M6 18h12"></path>',
  "cpu": '<rect x="7" y="7" width="10" height="10" rx="2"></rect><path d="M9 1v4"></path><path d="M15 1v4"></path><path d="M9 19v4"></path><path d="M15 19v4"></path><path d="M1 9h4"></path><path d="M1 15h4"></path><path d="M19 9h4"></path><path d="M19 15h4"></path>',
  "building-2": '<path d="M6 22V3h12v19"></path><path d="M9 7h1"></path><path d="M14 7h1"></path><path d="M9 11h1"></path><path d="M14 11h1"></path><path d="M9 15h1"></path><path d="M14 15h1"></path><path d="M4 22h16"></path>',
  "users": '<circle cx="9" cy="8" r="3"></circle><path d="M3 20a6 6 0 0 1 12 0"></path><circle cx="17" cy="9" r="2"></circle><path d="M15 16a5 5 0 0 1 6 4"></path>',
  "user": '<circle cx="12" cy="8" r="4"></circle><path d="M4 21a8 8 0 0 1 16 0"></path>',
  "briefcase-business": '<rect x="3" y="7" width="18" height="13" rx="2"></rect><path d="M9 7V5h6v2"></path><path d="M3 12h18"></path>',
  "home": '<path d="m3 11 9-8 9 8"></path><path d="M5 10v11h14V10"></path>',
  "circle-help": '<circle cx="12" cy="12" r="9"></circle><path d="M9.5 9a2.5 2.5 0 0 1 5 1c0 2-2.5 2-2.5 4"></path><path d="M12 18h.01"></path>',
  "piggy-bank": '<path d="M5 11a7 7 0 0 1 13 3v4H7l-2-3H3v-4h2Z"></path><path d="M10 8V5h4v3"></path><circle cx="15" cy="13" r="1"></circle>',
  "baby": '<circle cx="12" cy="10" r="5"></circle><path d="M9 14c1.5 1.5 4.5 1.5 6 0"></path><path d="M9 9h.01"></path><path d="M15 9h.01"></path>',
  "zap": '<path d="M13 2 4 14h7l-1 8 10-13h-7l1-7Z"></path>',
  "armchair": '<path d="M6 10V7a4 4 0 0 1 8 0v3"></path><path d="M4 11h16v8H4z"></path><path d="M6 19v3"></path><path d="M18 19v3"></path>',
  "shuffle": '<path d="M4 7h3l10 10h3"></path><path d="M17 7h3"></path><path d="M4 17h3l3-3"></path><path d="m17 4 3 3-3 3"></path><path d="m17 14 3 3-3 3"></path>',
  "truck": '<path d="M3 7h11v10H3z"></path><path d="M14 11h4l3 3v3h-7"></path><circle cx="7" cy="18" r="2"></circle><circle cx="17" cy="18" r="2"></circle>',
  "lightbulb": '<path d="M9 18h6"></path><path d="M10 22h4"></path><path d="M8 14a6 6 0 1 1 8 0c-1 1-1 2-1 3H9c0-1 0-2-1-3Z"></path>',
  "arrow-left": '<path d="m12 19-7-7 7-7"></path><path d="M19 12H5"></path>',
  "arrow-right": '<path d="M5 12h14"></path><path d="m12 5 7 7-7 7"></path>',
  "rotate-ccw": '<path d="M3 12a9 9 0 1 0 3-6.7"></path><path d="M3 3v6h6"></path>',
  "badge-dollar-sign": '<circle cx="12" cy="12" r="8"></circle><path d="M12 7v10"></path><path d="M9.5 9.5c0-1.2 5-1.2 5 1 0 2-5 1-5 3 0 2.2 5 2.2 5 1"></path>',
  "crown": '<path d="m3 8 4 4 5-7 5 7 4-4v10H3V8Z"></path><path d="M3 18h18"></path>',
  "bus-front": '<path d="M7 4h10a3 3 0 0 1 3 3v10H4V7a3 3 0 0 1 3-3Z"></path><path d="M6 10h12"></path><circle cx="8" cy="15" r="1"></circle><circle cx="16" cy="15" r="1"></circle><path d="M7 21h2"></path><path d="M15 21h2"></path>',
  "gauge-circle": '<circle cx="12" cy="12" r="9"></circle><path d="m12 12 4-4"></path><path d="M8 16h8"></path>',
  "road": '<path d="M6 20 10 4"></path><path d="m14 4 4 16"></path><path d="M12 8v2"></path><path d="M12 14v2"></path>',
  "navigation": '<path d="m3 11 18-8-8 18-2-8-8-2Z"></path>',
  "car-taxi-front": '<path d="M6 16h12l-1-6H7l-1 6Z"></path><path d="M9 7h6"></path><path d="M8 16v2"></path><path d="M16 16v2"></path><circle cx="8" cy="13" r="1"></circle><circle cx="16" cy="13" r="1"></circle>',
};

function icons() {
  if (window.lucide) {
    window.lucide.createIcons();
    return;
  }
  document.querySelectorAll("i[data-lucide]").forEach((el) => {
    const name = el.dataset.lucide;
    const paths = fallbackIconPaths[name] || '<circle cx="12" cy="12" r="8"></circle>';
    el.innerHTML = `<svg viewBox="0 0 24 24" aria-hidden="true" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">${paths}</svg>`;
    el.classList.add("icon-fallback");
  });
}

function initButtonFeedback() {
  document.addEventListener("click", (event) => {
    const target = event.target.closest("button, .btn, .sell-link, .shopping-lanes a, .section-switcher a, .action-card, .choice-card");
    if (!target) return;
    target.classList.add("is-clicked");
    window.setTimeout(() => target.classList.remove("is-clicked"), 240);
  });
}

function initRoleFields() {
  const select = document.querySelector("#roleSelect");
  const customerFields = document.querySelectorAll(".customer-field");
  const businessFields = document.querySelectorAll(".business-field");
  const insurerFields = document.querySelectorAll(".insurer-field");
  const businessRequiredFields = document.querySelectorAll("[data-business-required='true']");
  if (!select) return;
  const setGroup = (fields, visible, required) => {
    fields.forEach((field) => {
      field.hidden = !visible;
      field.querySelectorAll("input, select, textarea").forEach((input) => {
        input.required = Boolean(visible && required);
        input.disabled = !visible;
      });
    });
  };
  const sync = () => {
    const isCustomer = select.value === "customer";
    const isBusiness = select.value === "dealer" || select.value === "insurer";
    const isInsurer = select.value === "insurer";
    setGroup(customerFields, isCustomer, true);
    setGroup(businessFields, isBusiness, true);
    setGroup(insurerFields, isInsurer, true);
    businessRequiredFields.forEach((field) => {
      field.querySelectorAll("input, select, textarea").forEach((input) => {
        input.required = isBusiness;
      });
    });
  };
  select.addEventListener("change", sync);
  sync();
}

function initHeroShowcase() {
  const wrap = document.querySelector("[data-showcase-carousel]");
  if (!wrap) return;
  const slides = [...wrap.querySelectorAll("[data-showcase-slide]")];
  const dots = [...wrap.querySelectorAll("[data-showcase-dot]")];
  if (slides.length < 2) return;
  let index = Math.max(0, slides.findIndex((slide) => slide.classList.contains("is-active")));
  let timer;

  const paint = (nextIndex) => {
    index = (nextIndex + slides.length) % slides.length;
    slides.forEach((slide, slideIndex) => slide.classList.toggle("is-active", slideIndex === index));
    dots.forEach((dot, dotIndex) => dot.classList.toggle("is-active", dotIndex === index));
  };

  const restart = () => {
    window.clearInterval(timer);
    timer = window.setInterval(() => paint(index + 1), 4200);
  };

  dots.forEach((dot, dotIndex) => {
    dot.addEventListener("click", () => {
      paint(dotIndex);
      restart();
    });
  });
  wrap.addEventListener("mouseenter", () => window.clearInterval(timer));
  wrap.addEventListener("mouseleave", restart);
  paint(index);
  restart();
}

function parseMoneyInput(value) {
  const digits = String(value || "").replace(/[^\d]/g, "");
  return digits ? Number(digits) : 0;
}

function parseDecimalInput(value) {
  const normalized = String(value || "").replace(",", ".").replace(/[^\d.]/g, "");
  const parsed = Number.parseFloat(normalized);
  return Number.isFinite(parsed) ? parsed : 0;
}

function fixedPayment(principal, monthlyRate, months) {
  if (!principal || !months) return 0;
  if (!monthlyRate) return principal / months;
  return principal * (monthlyRate / (1 - Math.pow(1 + monthlyRate, -months)));
}

function setText(id, value) {
  const el = document.querySelector(id);
  if (el) el.textContent = peso.format(Math.max(0, Math.round(value || 0)));
}

function initFinanceTools() {
  const lab = document.querySelector(".finance-lab");
  const credit = document.querySelector("#creditSimulator");
  const ownership = document.querySelector("#ownershipSimulator");
  if (!lab || !credit || !ownership) return;

  const priceInput = document.querySelector("#creditPrice");
  const downInput = document.querySelector("#creditDown");
  const termInput = document.querySelector("#creditTerm");
  const rateInput = document.querySelector("#creditRate");
  const soatInput = document.querySelector("#tcoSoat");
  const insuranceInput = document.querySelector("#tcoInsurance");
  const maintenanceInput = document.querySelector("#tcoMaintenance");
  const fuelInput = document.querySelector("#tcoFuel");
  const taxInput = document.querySelector("#tcoTax");
  let lastPayment = 0;

  function calculate() {
    const price = parseMoneyInput(priceInput.value) || Number(lab.dataset.basePrice || 0);
    const down = Math.min(parseMoneyInput(downInput.value), price);
    const financed = Math.max(0, price - down);
    const months = Number(termInput.value || 60);
    const monthlyRate = parseDecimalInput(rateInput.value) / 100;
    lastPayment = fixedPayment(financed, monthlyRate, months);
    const suggestedIncome = lastPayment / 0.3;

    const soatMonthly = parseMoneyInput(soatInput.value) / 12;
    const insuranceMonthly = (price * (parseDecimalInput(insuranceInput.value) / 100)) / 12;
    const maintenance = parseMoneyInput(maintenanceInput.value);
    const fuel = parseMoneyInput(fuelInput.value);
    const taxMonthly = parseMoneyInput(taxInput.value) / 12;
    const ownershipMonthly = lastPayment + soatMonthly + insuranceMonthly + maintenance + fuel + taxMonthly;

    setText("#financeAmount", financed);
    setText("#financePayment", lastPayment);
    setText("#financeIncome", suggestedIncome);
    setText("#ownershipMonthly", ownershipMonthly);
    setText("#ownershipAnnual", ownershipMonthly * 12);
  }

  [priceInput, downInput, termInput, rateInput, soatInput, insuranceInput, maintenanceInput, fuelInput, taxInput].forEach((input) => {
    input?.addEventListener("input", calculate);
    input?.addEventListener("change", calculate);
  });
  calculate();
}

function esc(value) {
  return String(value ?? "").replace(/[&<>"']/g, (char) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#039;" }[char]));
}

function card(item) {
  return `
    <article class="listing-card">
      <a class="media" href="/listing/${item.id}">
        <img src="${esc(item.image_url)}" alt="${esc(item.title)}" loading="lazy">
        ${item.verified ? '<span class="badge">Verificado</span>' : ""}
      </a>
      <div class="card-body">
        <a class="card-title" href="/listing/${item.id}">${esc(item.title)}</a>
        <strong class="price">${item.price_formatted || peso.format(item.price)}</strong>
        <div class="specs"><span>${item.year}</span><span>${item.mileage_formatted} km</span><span>${esc(item.fuel_type)}</span><span>${esc(item.transmission)}</span></div>
        <div class="dealer-line"><i data-lucide="${item.verified ? "shield-check" : "badge-check"}"></i> ${item.verified ? "Concesionario verificado" : "Concesionario registrado"} · ${esc(item.neighborhood)}</div>
      </div>
    </article>`;
}

function chatRecommendationCard(item) {
  return `
    <article class="chat-result-card">
      <a href="/listing/${item.id}"><img src="${esc(item.image_url)}" alt="${esc(item.title)}" loading="lazy"></a>
      <div>
        <strong>${item.fit_score}/100</strong>
        <h3>${esc(item.title)}</h3>
        <p>${item.price_formatted || peso.format(item.price)}</p>
        <a class="btn secondary full" href="/listing/${item.id}">Ver ficha</a>
      </div>
    </article>`;
}

function appendChatBubble(messages, text, kind = "bot") {
  if (!messages) return null;
  const bubble = document.createElement("div");
  bubble.className = `chat-bubble ${kind}`;
  bubble.textContent = text;
  messages.appendChild(bubble);
  messages.scrollTop = messages.scrollHeight;
  return bubble;
}

function initChatAdvisor() {
  const form = document.querySelector("#chatAdvisorForm");
  const input = document.querySelector("#chatAdvisorInput");
  const messages = document.querySelector("#chatMessages");
  const results = document.querySelector("#chatRecommendations");
  const examples = document.querySelectorAll("[data-chat-prompt]");
  if (!form || !input || !messages || !results) return;

  async function sendPrompt(prompt) {
    const text = String(prompt || "").trim();
    if (!text) return;
    appendChatBubble(messages, text, "user");
    input.value = "";
    input.disabled = true;
    const button = form.querySelector("button");
    if (button) button.disabled = true;
    const thinking = appendChatBubble(messages, "Estoy cruzando tu mensaje con el inventario activo...", "bot is-thinking");
    try {
      const res = await fetch("/api/chat-advisor", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: text }),
      });
      if (!res.ok) throw new Error("chat_failed");
      const data = await res.json();
      if (thinking) thinking.remove();
      appendChatBubble(messages, data.reply, "bot");
      if (data.profile) saveAdvisorProfile(data.profile);
      results.innerHTML = data.recommendations?.length
        ? data.recommendations.map(chatRecommendationCard).join("")
        : '<div class="empty mini">No encontramos opciones activas con ese perfil.</div>';
      icons();
    } catch (_error) {
      if (thinking) thinking.remove();
      appendChatBubble(messages, "No pude calcular la recomendacion ahora. Intenta otra vez en unos segundos.", "bot");
    } finally {
      input.disabled = false;
      if (button) button.disabled = false;
      input.focus();
    }
  }

  form.addEventListener("submit", (event) => {
    event.preventDefault();
    sendPrompt(input.value);
  });

  examples.forEach((button) => {
    button.addEventListener("click", () => {
      input.value = button.dataset.chatPrompt || "";
      sendPrompt(input.value);
    });
  });
}

const advisorFieldLabels = {
  usage: "Uso",
  budget: "Presupuesto",
  people: "Personas",
  daily_km: "Km diarios",
  charging_access: "Carga EV",
  priority: "Prioridad",
  preferred_type: "Tipo",
};
const advisorRequiredFields = ["usage", "budget", "people", "daily_km", "charging_access", "priority", "preferred_type"];

const advisorValueLabels = {
  usage: { city: "Ciudad", family: "Familia", work: "Trabajo", travel: "Viajes" },
  budget: {
    55000000: "Hasta $55M",
    120000000: "Hasta $120M",
    250000000: "Hasta $250M",
    500000000: "Hasta $500M",
    1000000000: "Hasta $1.000M",
  },
  people: { 2: "1-2", 4: "3-4", 5: "5", 7: "6+" },
  daily_km: { 25: "Menos de 25", 50: "25-50", 90: "50-90", 130: "90+" },
  charging_access: { home: "Casa/trabajo", public: "Carga pública", none: "No claro" },
  priority: { economy: "Ahorro", safety: "Seguridad", family: "Familia", performance: "Desempeño", comfort: "Confort" },
  preferred_type: { any: "Flexible", suv: "SUV", sedan: "Sedán", hatchback: "Hatchback", pickup: "Pickup", electric: "Eléctrico" },
};

function advisorProfile(form) {
  return Object.fromEntries(new FormData(form).entries());
}

function advisorChipHtml(profile) {
  const entries = advisorRequiredFields.filter((key) => profile[key]).map((key) => [key, profile[key]]);
  if (!entries.length) return "<span>Sin respuestas todavía</span>";
  return entries.map(([key, value]) => {
    const label = advisorFieldLabels[key] || key;
    const readable = advisorValueLabels[key]?.[value] || value;
    return `<span><small>${esc(label)}</small><strong>${esc(readable)}</strong></span>`;
  }).join("");
}

function saveAdvisorProfile(profile) {
  const raw = JSON.stringify(profile);
  try { window.localStorage.setItem("cartrustProfile", raw); } catch (_error) {}
  try { window.sessionStorage.setItem("cartrustProfile", raw); } catch (_error) {}
  try { document.cookie = `cartrustProfile=${encodeURIComponent(raw)}; path=/; max-age=2592000; samesite=lax`; } catch (_error) {}
}

function readAdvisorProfile() {
  try {
    const raw = window.localStorage.getItem("cartrustProfile") || window.sessionStorage.getItem("cartrustProfile");
    if (raw) return raw;
  } catch (_error) {}
  try {
    const match = String(document.cookie || "").match(/(?:^|; )cartrustProfile=([^;]+)/);
    return match ? decodeURIComponent(match[1]) : null;
  } catch (_error) {
    return null;
  }
}

function clearAdvisorProfile() {
  try { window.localStorage.removeItem("cartrustProfile"); } catch (_error) {}
  try { window.sessionStorage.removeItem("cartrustProfile"); } catch (_error) {}
  try { document.cookie = "cartrustProfile=; path=/; max-age=0; samesite=lax"; } catch (_error) {}
}

function initFilters() {
  const form = document.querySelector("#marketFilters");
  const grid = document.querySelector("#listingGrid");
  const count = document.querySelector("#resultCount");
  if (!form || !grid) return;
  let timer;
  async function refresh() {
    const params = new URLSearchParams(new FormData(form));
    const res = await fetch(`/api/listings?${params}`);
    const items = await res.json();
    count.textContent = items.length;
    grid.innerHTML = items.length ? items.map(card).join("") : '<div class="empty">No encontramos carros con esos filtros.</div>';
    history.replaceState({}, "", `/?${params}#catalogo`);
    icons();
  }
  form.addEventListener("submit", (event) => { event.preventDefault(); refresh(); });
  form.addEventListener("input", () => { clearTimeout(timer); timer = setTimeout(refresh, 350); });
  form.addEventListener("change", refresh);
}

function initAdvisor() {
  const form = document.querySelector("#quizForm");
  const box = document.querySelector("#advisorResults");
  const steps = [...document.querySelectorAll(".quiz-step")];
  const progress = document.querySelector("#quizProgress");
  const counter = document.querySelector("#stepCounter");
  const title = document.querySelector("#stepTitle");
  const tip = document.querySelector("#advisorTip");
  const prev = document.querySelector("#prevStep");
  const next = document.querySelector("#nextStep");
  const submit = document.querySelector("#submitQuiz");
  const reset = document.querySelector("#resetQuiz");
  const stepButtons = [...document.querySelectorAll("#advisorStepper [data-step]")];
  const chips = document.querySelector("#profileChips");
  const previewTitle = document.querySelector("#previewTitle");
  const previewCopy = document.querySelector("#previewCopy");
  const previewPercent = document.querySelector("#previewPercent");
  const previewRing = document.querySelector(".preview-ring");
  if (!form || !box) return;
  let index = 0;

  function answeredCount(profile = advisorProfile(form)) {
    return advisorRequiredFields.filter((field) => profile[field]).length;
  }

  function activeAnswered() {
    const active = steps[index];
    const field = active?.dataset.field;
    return Boolean(field && form.querySelector(`input[name="${field}"]:checked`));
  }

  function updatePreview() {
    const profile = advisorProfile(form);
    const count = answeredCount(profile);
    const pct = Math.round((count / advisorRequiredFields.length) * 100);
    if (chips) chips.innerHTML = advisorChipHtml(profile);
    if (previewPercent) previewPercent.textContent = `${pct}%`;
    if (previewRing) previewRing.style.setProperty("--preview", pct);
    if (previewTitle) previewTitle.textContent = count ? "Perfil tomando forma" : "Perfil en construcción";
    if (previewCopy) {
      previewCopy.textContent = count === advisorRequiredFields.length
        ? "Listo. Ya podemos calcular tu recomendación con el inventario activo."
        : `${count} de ${advisorRequiredFields.length} señales listas. Sigue avanzando para afinar el match.`;
    }
  }

  function paintStep() {
    const profile = advisorProfile(form);
    steps.forEach((step, stepIndex) => step.classList.toggle("is-active", stepIndex === index));
    const active = steps[index];
    const pct = Math.round((index / Math.max(steps.length - 1, 1)) * 100);
    if (progress) progress.style.width = `${pct}%`;
    if (counter) counter.textContent = `Pregunta ${index + 1} de ${steps.length}`;
    if (title) title.textContent = active?.dataset.title || "Asesor";
    if (tip) tip.textContent = active?.dataset.tip || "";
    if (prev) prev.disabled = index === 0;
    if (next) next.hidden = index === steps.length - 1;
    if (submit) submit.hidden = index !== steps.length - 1;
    if (next) next.disabled = !activeAnswered();
    if (submit) submit.disabled = answeredCount(profile) !== advisorRequiredFields.length;
    stepButtons.forEach((button, buttonIndex) => {
      const field = steps[buttonIndex]?.dataset.field;
      const unlocked = buttonIndex === 0 || advisorRequiredFields.slice(0, buttonIndex).every((key) => profile[key]);
      button.classList.toggle("is-active", buttonIndex === index);
      button.classList.toggle("is-complete", Boolean(field && profile[field]));
      button.disabled = !unlocked;
      button.setAttribute("aria-current", buttonIndex === index ? "step" : "false");
    });
    updatePreview();
    icons();
  }

  form.addEventListener("change", (event) => {
    updatePreview();
    if (event.target.matches('input[type="radio"]')) {
      if (index < steps.length - 1) {
        window.setTimeout(() => {
          index += 1;
          paintStep();
        }, 180);
      } else {
        paintStep();
      }
    }
  });

  prev?.addEventListener("click", () => {
    index = Math.max(0, index - 1);
    paintStep();
  });

  next?.addEventListener("click", () => {
    if (!activeAnswered()) {
      steps[index]?.classList.add("needs-answer");
      window.setTimeout(() => steps[index]?.classList.remove("needs-answer"), 500);
      return;
    }
    index = Math.min(steps.length - 1, index + 1);
    paintStep();
  });

  reset?.addEventListener("click", () => {
    form.reset();
    clearAdvisorProfile();
    index = 0;
    box.innerHTML = "";
    paintStep();
  });

  stepButtons.forEach((button) => {
    button.addEventListener("click", () => {
      if (button.disabled) return;
      index = Number(button.dataset.step) || 0;
      paintStep();
    });
  });

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    const profile = advisorProfile(form);
    if (answeredCount(profile) !== advisorRequiredFields.length) {
      const firstMissing = advisorRequiredFields.findIndex((field) => !profile[field]);
      index = Math.max(0, firstMissing);
      paintStep();
      steps[index]?.classList.add("needs-answer");
      window.setTimeout(() => steps[index]?.classList.remove("needs-answer"), 500);
      return;
    }
    box.innerHTML = '<div class="advisor-loading"><strong>Calculando conveniencia...</strong><span>Estamos cruzando tu perfil con el inventario activo.</span></div>';
    if (submit) submit.disabled = true;
    let data;
    try {
      const res = await fetch("/api/quiz/recommend", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(profile),
      });
      if (!res.ok) throw new Error("recommendation_failed");
      data = await res.json();
    } catch (_error) {
      box.innerHTML = '<div class="empty">No pudimos calcular la recomendación en este momento. Intenta de nuevo en unos segundos.</div>';
      if (submit) submit.disabled = false;
      return;
    }
    saveAdvisorProfile(data.profile);
    if (!data.recommendations.length) {
      box.innerHTML = '<div class="empty">No encontramos carros activos para recomendar.</div>';
      if (submit) submit.disabled = false;
      return;
    }
    const [best, ...alternatives] = data.recommendations;
    const reasons = best.fit_reasons?.length ? best.fit_reasons : ["Es la opción con mayor afinidad frente a tus respuestas."];
    box.innerHTML = `
      <div class="advisor-results-head">
        <span class="eyebrow">Resultado</span>
        <h2>Tu mejor match marca ${best.fit_score}/100.</h2>
        <p>Guardamos este perfil en tu navegador para comparar cualquier ficha contra esta recomendación.</p>
      </div>
      <article class="best-match" style="--score:${best.fit_score}">
        <a class="best-media" href="/listing/${best.id}">
          <img src="${esc(best.image_url)}" alt="${esc(best.title)}">
          <span class="badge">Recomendado</span>
        </a>
        <div class="best-body">
          <div class="best-score"><span>${best.fit_score}</span><small>/100</small></div>
          <div>
            <h3>${esc(best.title)}</h3>
            <strong class="price">${best.price_formatted}</strong>
            <div class="specs"><span>${best.year}</span><span>${best.mileage_formatted} km</span><span>${esc(best.fuel_type)}</span><span>${esc(best.transmission)}</span></div>
          </div>
          <div class="reason-box">
            <strong>Por qué encaja</strong>
            <ul>${reasons.map((reason) => `<li>${esc(reason)}</li>`).join("")}</ul>
          </div>
          <div class="advisor-result-actions">
            <a class="btn primary" href="/listing/${best.id}">Ver ficha completa</a>
            <a class="btn secondary" href="/carga">Ver carga EV</a>
            <a class="btn quiet" href="/referencias">Ver precios referencia</a>
          </div>
        </div>
      </article>
      <div class="profile-summary">
        <strong>Perfil usado para el cálculo</strong>
        <div>${advisorChipHtml(profile)}</div>
      </div>
      <div class="alternative-grid">
        ${alternatives.map((item, altIndex) => `
          <article class="recommendation-card">
            <a href="/listing/${item.id}"><img src="${esc(item.image_url)}" alt="${esc(item.title)}"></a>
            <div>
              <strong>${altIndex === 0 ? "Alternativa fuerte" : "Otra opción"} · ${item.fit_score}/100</strong>
              <h3>${esc(item.title)}</h3>
              <p>${item.price_formatted}</p>
              <a class="btn secondary full" href="/listing/${item.id}">Comparar ficha</a>
            </div>
          </article>`).join("")}
      </div>`;
    if (submit) submit.disabled = false;
    box.scrollIntoView({ behavior: "smooth", block: "start" });
    icons();
  });
  paintStep();
}

async function initComparison() {
  const panel = document.querySelector("#comparisonPanel");
  if (!panel) return;
  const raw = readAdvisorProfile();
  if (!raw) return;
  const res = await fetch(`/api/listings/${panel.dataset.listingId}/score`, { method: "POST", headers: { "Content-Type": "application/json" }, body: raw });
  const data = await res.json();
  panel.querySelector(".score-empty").hidden = true;
  const result = panel.querySelector(".score-result");
  result.hidden = false;
  result.querySelector(".score-ring").style.setProperty("--score", data.relative_score);
  result.querySelector("#relativeScore").textContent = data.relative_score;
  result.querySelector("#scoreNarrative").textContent = `Este carro marca ${data.selected_score}/100 frente al recomendado (${data.benchmark.fit_score}/100).`;
  result.querySelector("#scoreReasons").innerHTML = data.reasons.map((x) => `<li>${esc(x)}</li>`).join("");
  result.querySelector("#benchmarkLink").href = `/listing/${data.benchmark.id}`;
}

async function loadStations(map, markers) {
  const city = document.querySelector("#citySelect")?.value || "Medellin";
  const list = document.querySelector("#stationList");
  const count = document.querySelector("#stationCount");
  const source = document.querySelector("#stationSource");
  if (!list) return;
  const res = await fetch(`/api/charging-stations?city=${encodeURIComponent(city)}`);
  const data = await res.json();
  markers.clearLayers();
  count.textContent = `${data.stations.length} estaciones`;
  source.textContent = data.source_label;
  list.innerHTML = data.stations.length ? "" : '<div class="station-item">No hay estaciones reportadas para esta consulta.</div>';
  if (data.center) map.setView([data.center.latitude, data.center.longitude], 12);
  const bounds = [];
  data.stations.forEach((station) => {
    const pos = [station.latitude, station.longitude];
    bounds.push(pos);
    L.marker(pos).addTo(markers).bindPopup(`<strong>${esc(station.title)}</strong><br>${esc(station.address)}<br>${esc(station.operator)}`);
    list.insertAdjacentHTML("beforeend", `<div class="station-item"><strong>${esc(station.title)}</strong><p>${esc(station.address)}</p><small>${esc(station.connections)}</small></div>`);
  });
  if (bounds.length) map.fitBounds(bounds, { padding: [24, 24], maxZoom: 13 });
}

function initMap() {
  const el = document.querySelector("#chargingMap");
  if (!el || !window.L) return;
  const map = L.map(el).setView([6.2442, -75.5812], 12);
  L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", { maxZoom: 19, attribution: "&copy; OpenStreetMap" }).addTo(map);
  const markers = L.layerGroup().addTo(map);
  loadStations(map, markers);
  document.querySelector("#citySelect")?.addEventListener("change", () => loadStations(map, markers));
  document.querySelector("#reloadStations")?.addEventListener("click", () => loadStations(map, markers));
}

document.addEventListener("DOMContentLoaded", () => {
  icons();
  initButtonFeedback();
  initHeroShowcase();
  initFinanceTools();
  initRoleFields();
  initChatAdvisor();
  initFilters();
  initAdvisor();
  initComparison();
  initMap();
});
