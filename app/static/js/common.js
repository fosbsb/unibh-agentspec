import { POLL_MS } from "./config.js";

export const STATUS = {
  recebido: { icon: "🕒", label: "Recebido" },
  preparando: { icon: "🔥", label: "Preparando" },
  pronto: { icon: "✅", label: "Pronto" },
  entregue: { icon: "📦", label: "Entregue" },
  cancelado: { icon: "✖", label: "Cancelado" },
};

const brl = new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" });

export const formatBRL = (cents) => brl.format(cents / 100);

export function esc(value) {
  const node = document.createElement("span");
  node.textContent = String(value);
  return node.innerHTML;
}

export function seloHTML(status) {
  const { icon, label } = STATUS[status];
  return `<span class="selo selo-${status}"><span aria-hidden="true">${icon}</span>${label}</span>`;
}

export async function api(path, options = {}) {
  const response = await fetch(`/api${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    const detail = typeof body.detail === "string" ? body.detail : null;
    throw Object.assign(new Error(detail || "Erro inesperado."), {
      status: response.status,
    });
  }
  return response.json();
}

export function poll(task, onError = () => {}, ms = POLL_MS) {
  const tick = async () => {
    try {
      await task();
      onError(null);
    } catch (error) {
      onError(error);
    }
    setTimeout(tick, ms);
  };
  tick();
}

export function showError(element, message, actionLabel, onAction) {
  if (!message) {
    element.classList.add("hidden");
    element.replaceChildren();
    return;
  }
  element.classList.remove("hidden");
  element.innerHTML = `<span aria-hidden="true">⚠</span><span class="flex-1">${esc(message)}</span>`;
  if (actionLabel) {
    const button = document.createElement("button");
    button.className = "btn btn-primario";
    button.textContent = actionLabel;
    button.addEventListener("click", onAction);
    element.append(button);
  }
}
