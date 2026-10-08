export const reais = (centavos) =>
  new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" }).format(
    centavos / 100
  );

export const esc = (texto) =>
  String(texto).replace(
    /[&<>"']/g,
    (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[c]
  );

export async function api(caminho, opcoes = {}) {
  const resposta = await fetch(`/api${caminho}`, {
    headers: { "Content-Type": "application/json" },
    ...opcoes,
  });
  if (!resposta.ok) {
    const erro = new Error(`HTTP ${resposta.status}`);
    erro.status = resposta.status;
    throw erro;
  }
  return resposta.json();
}

export function repetir(fn, ms = 2000) {
  let ativo = true;
  const volta = async () => {
    if (!ativo) return;
    try {
      await fn();
    } catch (erro) {
      console.warn(erro);
    }
    if (ativo) setTimeout(volta, ms);
  };
  volta();
  return () => {
    ativo = false;
  };
}

export const SELOS = {
  recebido: { icone: "🕒", rotulo: "Recebido" },
  preparando: { icone: "🔥", rotulo: "Preparando" },
  pronto: { icone: "✅", rotulo: "Pronto" },
  entregue: { icone: "📦", rotulo: "Entregue" },
};

export const selo = (estado) =>
  `<span class="selo selo-${estado}"><span aria-hidden="true">${SELOS[estado].icone}</span>${SELOS[estado].rotulo}</span>`;
