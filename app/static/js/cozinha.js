import { api, repetir, esc, selo } from "./api.js";

const ACOES = {
  recebido: { rotulo: "Iniciar", destino: "preparando", classe: "btn-primario" },
  preparando: { rotulo: "Marcar pronto", destino: "pronto", classe: "btn-primario" },
  pronto: { rotulo: "Entregar", destino: "entregue", classe: "btn-secundario" },
};

const fila = document.getElementById("fila");
const contador = document.getElementById("contador");
const faixaErro = document.getElementById("erro");
const pendentes = new Set();
let pedidos = [];

const hora = (iso) =>
  new Date(iso).toLocaleTimeString("pt-BR", { hour: "2-digit", minute: "2-digit" });

function mostrarErro(texto) {
  faixaErro.innerHTML = `<span aria-hidden="true">⚠</span><span>${esc(texto)}</span>`;
  faixaErro.hidden = false;
}

function cartao(pedido) {
  const acao = ACOES[pedido.estado];
  const ocupado = pendentes.has(pedido.id);
  const itens = pedido.itens
    .map((i) => `<li>${i.quantidade}× ${esc(i.nome)}</li>`)
    .join("");
  const botao = acao
    ? `<button class="btn ${acao.classe} w-full" data-id="${pedido.id}" data-destino="${acao.destino}" ${ocupado ? "disabled" : ""}>${ocupado ? "Aguarde…" : acao.rotulo}</button>`
    : "";
  return `
    <article class="cartao flex flex-col gap-[var(--espaco-2)] p-[var(--espaco-3)]">
      <div class="flex items-center justify-between">
        <span class="numero-pedido text-[40px] font-extrabold text-amarelo">#${pedido.numero}</span>
        ${selo(pedido.estado)}
      </div>
      <div class="suave">Chegou às ${hora(pedido.criado_em)}</div>
      <ul class="m-0 list-none p-0 text-[18px]">${itens}</ul>
      ${botao}
    </article>`;
}

function desenhar() {
  contador.textContent = `${pedidos.length} ${pedidos.length === 1 ? "pedido" : "pedidos"} na fila`;
  fila.innerHTML = pedidos.length
    ? pedidos.map(cartao).join("")
    : `<p class="suave text-[20px]">Nenhum pedido na fila.</p>`;
}

async function carregar() {
  pedidos = await api("/pedidos?estado=recebido&estado=preparando&estado=pronto");
  faixaErro.hidden = true;
  desenhar();
}

async function mudar(id, destino) {
  pendentes.add(id);
  desenhar();
  try {
    await api(`/pedidos/${id}/estado`, {
      method: "PATCH",
      body: JSON.stringify({ estado: destino }),
    });
  } catch (erro) {
    if (erro.status !== 409) mostrarErro("Não foi possível atualizar o pedido. Toque de novo.");
  } finally {
    pendentes.delete(id);
  }
  try {
    await carregar();
  } catch (erro) {
    console.warn(erro);
    desenhar();
  }
}

fila.addEventListener("click", (evento) => {
  const botao = evento.target.closest("button[data-id]");
  if (!botao || botao.disabled) return;
  mudar(Number(botao.dataset.id), botao.dataset.destino);
});

repetir(async () => {
  try {
    await carregar();
  } catch (erro) {
    mostrarErro("Sem conexão com o servidor. Tentando de novo…");
    throw erro;
  }
});
