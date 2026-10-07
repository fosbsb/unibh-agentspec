import { api, esc, poll, seloHTML, showError } from "./common.js";

const el = {
  queue: document.getElementById("queue"),
  empty: document.getElementById("empty"),
  summary: document.getElementById("summary"),
  error: document.getElementById("error"),
};

const ACTIONS = {
  recebido: [
    { action: "advance", label: "Iniciar", style: "btn-primario" },
    { action: "cancel", label: "Cancelar", style: "btn-perigo" },
  ],
  preparando: [
    { action: "advance", label: "Marcar pronto", style: "btn-primario" },
    { action: "cancel", label: "Cancelar", style: "btn-perigo" },
  ],
  pronto: [{ action: "advance", label: "Entregar", style: "btn-secundario" }],
};

const timeFormat = new Intl.DateTimeFormat("pt-BR", { hour: "2-digit", minute: "2-digit" });

let orders = [];
let lastSignature = "";
const busy = new Set();

function cardHTML(order) {
  const items = order.items
    .map((i) => `<li>${i.quantity}× ${esc(i.icon)} ${esc(i.name)}</li>`)
    .join("");
  const disabled = busy.has(order.id);
  const buttons = ACTIONS[order.status]
    .map(
      (a) =>
        `<button class="btn btn-cozinha ${a.style}" data-action="${a.action}" data-id="${order.id}" data-from="${order.status}" ${disabled ? "disabled" : ""}>${disabled ? "Aguarde…" : a.label}</button>`,
    )
    .join("");
  return `
    <article class="cartao p-4 flex flex-col gap-3">
      <div class="flex items-center justify-between gap-2">
        <span class="pedido-numero pedido-numero-lista text-amarelo">${esc(order.number)}</span>
        ${seloHTML(order.status)}
      </div>
      <div class="text-suave">Pedido às ${timeFormat.format(new Date(order.created_at))}</div>
      <ul class="m-0 pl-5 flex flex-col gap-1 flex-1">${items}</ul>
      <div class="flex gap-3 flex-wrap">${buttons}</div>
    </article>`;
}

function render() {
  const signature = JSON.stringify([orders, [...busy]]);
  if (signature === lastSignature) return;
  lastSignature = signature;
  el.queue.innerHTML = orders.map(cardHTML).join("");
  el.empty.classList.toggle("hidden", orders.length > 0);
  el.summary.textContent =
    orders.length === 1 ? "1 pedido na fila" : `${orders.length} pedidos na fila`;
}

async function refresh() {
  orders = await api("/pedidos");
  render();
}

async function act(button) {
  const id = Number(button.dataset.id);
  const { action, from } = button.dataset;
  busy.add(id);
  showError(el.error, null);
  render();
  try {
    if (action === "advance") {
      await api(`/pedidos/${id}/avancar`, {
        method: "POST",
        body: JSON.stringify({ from_state: from }),
      });
    } else {
      await api(`/pedidos/${id}/cancelar`, { method: "POST" });
    }
  } catch (error) {
    showError(el.error, error.message);
  } finally {
    busy.delete(id);
  }
  try {
    await refresh();
  } catch {
    render();
  }
}

el.queue.addEventListener("click", (event) => {
  const button = event.target.closest("button[data-action]");
  if (button && !button.disabled) act(button);
});

let connectionLost = false;

poll(refresh, (error) => {
  if (error) {
    connectionLost = true;
    showError(el.error, "Sem conexão com o servidor. Tentando de novo…");
  } else if (connectionLost) {
    connectionLost = false;
    showError(el.error, null);
  }
});
