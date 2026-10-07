import { CONFIRM_MS, IDLE_MS, MAX_QTY } from "./config.js";
import { api, esc, formatBRL, showError } from "./common.js";

const el = {
  idle: document.getElementById("idle"),
  idleError: document.getElementById("idle-error"),
  start: document.getElementById("start"),
  menu: document.getElementById("menu"),
  tabs: document.getElementById("tabs"),
  grid: document.getElementById("grid"),
  cart: document.getElementById("cart"),
  count: document.getElementById("count"),
  total: document.getElementById("total"),
  reviewBtn: document.getElementById("review-btn"),
  review: document.getElementById("review"),
  reviewItems: document.getElementById("review-items"),
  reviewTotal: document.getElementById("review-total"),
  error: document.getElementById("error"),
  back: document.getElementById("back"),
  confirmBtn: document.getElementById("confirm-btn"),
  confirm: document.getElementById("confirm"),
  orderNumber: document.getElementById("order-number"),
};

const state = {
  products: [],
  category: null,
  cart: new Map(),
  submitting: false,
};

let idleTimer = null;
let confirmTimer = null;

const categories = () => [...new Set(state.products.map((p) => p.category))];
const productById = (id) => state.products.find((p) => p.id === id);
const cartLines = () =>
  [...state.cart].map(([id, quantity]) => ({ product: productById(id), quantity }));
const cartTotal = () =>
  cartLines().reduce((sum, l) => sum + l.product.price_cents * l.quantity, 0);
const cartCount = () => [...state.cart.values()].reduce((sum, q) => sum + q, 0);

function show(view) {
  for (const name of ["idle", "menu", "review", "confirm"]) {
    el[name].classList.toggle("hidden", name !== view);
  }
}

function armIdleTimer() {
  clearTimeout(idleTimer);
  idleTimer = setTimeout(() => {
    if (state.submitting) {
      armIdleTimer();
      return;
    }
    goIdle();
  }, IDLE_MS);
}

function goIdle() {
  clearTimeout(idleTimer);
  clearTimeout(confirmTimer);
  state.cart.clear();
  state.submitting = false;
  showError(el.error, null);
  showError(el.idleError, null);
  show("idle");
}

async function loadProducts() {
  state.products = await api("/produtos");
  if (!categories().includes(state.category)) {
    state.category = categories()[0] ?? null;
  }
}

async function start() {
  el.start.disabled = true;
  try {
    await loadProducts();
  } catch {
    showError(
      el.idleError,
      "Não foi possível carregar o cardápio. Toque em Tentar de novo.",
      "Tentar de novo",
      start,
    );
    el.start.disabled = false;
    return;
  }
  el.start.disabled = false;
  showError(el.idleError, null);
  render();
  show("menu");
  armIdleTimer();
}

function renderTabs() {
  el.tabs.innerHTML = categories()
    .map(
      (name) =>
        `<button class="aba" role="tab" data-category="${esc(name)}" aria-selected="${name === state.category}">${esc(name)}</button>`,
    )
    .join("");
}

function renderGrid() {
  el.grid.innerHTML = state.products
    .filter((p) => p.category === state.category)
    .map(
      (p) => `
      <article class="cartao cartao-produto">
        <div class="icone" aria-hidden="true">${esc(p.icon)}</div>
        <h2 class="t-produto m-0">${esc(p.name)}</h2>
        <div class="t-preco">${formatBRL(p.price_cents)}</div>
        <button class="btn btn-primario w-full" data-add="${p.id}">Adicionar</button>
      </article>`,
    )
    .join("");
}

function renderCart() {
  const lines = cartLines();
  el.cart.classList.toggle("hidden", lines.length === 0);
  el.cart.innerHTML = lines
    .map(
      ({ product, quantity }) => `
      <div class="flex items-center gap-3" data-line="${product.id}">
        <div class="flex-1">
          <div class="t-produto">${esc(product.icon)} ${esc(product.name)}</div>
          <div class="text-amarelo font-bold">${formatBRL(product.price_cents * quantity)}</div>
        </div>
        <button class="btn btn-secundario btn-quadrado" data-dec="${product.id}" aria-label="Diminuir ${esc(product.name)}">−</button>
        <div class="t-produto w-12 text-center" aria-live="polite">${quantity}</div>
        <button class="btn btn-secundario btn-quadrado" data-inc="${product.id}" aria-label="Aumentar ${esc(product.name)}" ${quantity >= MAX_QTY ? "disabled" : ""}>+</button>
        <button class="btn btn-perigo" data-remove="${product.id}">Remover</button>
      </div>`,
    )
    .join("");
}

function renderBar() {
  const count = cartCount();
  el.count.textContent = count === 1 ? "1 item" : `${count} itens`;
  el.total.textContent = formatBRL(cartTotal());
  el.reviewBtn.disabled = count === 0;
}

function renderReview() {
  el.reviewItems.innerHTML = cartLines()
    .map(
      ({ product, quantity }) => `
      <div class="cartao p-4 flex items-center gap-4">
        <div class="text-[56px] leading-none" aria-hidden="true">${esc(product.icon)}</div>
        <div class="flex-1">
          <div class="t-produto">${quantity}× ${esc(product.name)}</div>
          <div class="text-suave">${formatBRL(product.price_cents)} cada</div>
        </div>
        <div class="t-preco">${formatBRL(product.price_cents * quantity)}</div>
      </div>`,
    )
    .join("");
  el.reviewTotal.textContent = formatBRL(cartTotal());
  el.back.disabled = state.submitting;
  el.confirmBtn.disabled = state.submitting || state.cart.size === 0;
  el.confirmBtn.textContent = state.submitting ? "Aguarde…" : "Confirmar pedido";
}

function openReview() {
  if (state.cart.size === 0) return;
  showError(el.error, null);
  renderReview();
  show("review");
  armIdleTimer();
}

function backToMenu() {
  if (state.submitting) return;
  showError(el.error, null);
  render();
  show("menu");
  armIdleTimer();
}

function render() {
  renderTabs();
  renderGrid();
  renderCart();
  renderBar();
}

function changeQuantity(id, delta) {
  const next = (state.cart.get(id) ?? 0) + delta;
  if (next <= 0) {
    state.cart.delete(id);
  } else {
    state.cart.set(id, Math.min(next, MAX_QTY));
  }
  renderCart();
  renderBar();
}

async function submit() {
  if (state.submitting || state.cart.size === 0) return;
  state.submitting = true;
  showError(el.error, null);
  renderReview();
  const items = [...state.cart].map(([product_id, quantity]) => ({ product_id, quantity }));
  try {
    const order = await api("/pedidos", {
      method: "POST",
      body: JSON.stringify({ items }),
    });
    state.submitting = false;
    clearTimeout(idleTimer);
    state.cart.clear();
    el.orderNumber.textContent = order.number;
    show("confirm");
    confirmTimer = setTimeout(goIdle, CONFIRM_MS);
  } catch {
    state.submitting = false;
    renderReview();
    showError(
      el.error,
      "Não foi possível enviar o pedido. Toque em Tentar de novo.",
      "Tentar de novo",
      submit,
    );
  }
}

document.addEventListener("pointerdown", () => {
  if (!el.menu.classList.contains("hidden") || !el.review.classList.contains("hidden")) {
    armIdleTimer();
  }
});

el.start.addEventListener("click", start);
el.reviewBtn.addEventListener("click", openReview);
el.back.addEventListener("click", backToMenu);
el.confirmBtn.addEventListener("click", submit);

el.tabs.addEventListener("click", (event) => {
  const tab = event.target.closest("[data-category]");
  if (!tab) return;
  state.category = tab.dataset.category;
  renderTabs();
  renderGrid();
});

el.grid.addEventListener("click", (event) => {
  const add = event.target.closest("[data-add]");
  if (add) changeQuantity(Number(add.dataset.add), 1);
});

el.cart.addEventListener("click", (event) => {
  const dec = event.target.closest("[data-dec]");
  const inc = event.target.closest("[data-inc]");
  const remove = event.target.closest("[data-remove]");
  if (dec) changeQuantity(Number(dec.dataset.dec), -1);
  if (inc) changeQuantity(Number(inc.dataset.inc), 1);
  if (remove) {
    state.cart.delete(Number(remove.dataset.remove));
    renderCart();
    renderBar();
  }
});

goIdle();
