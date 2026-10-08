import { api, reais, esc } from "./api.js";

const CATEGORIAS = ["Lanches", "Crepes", "Bebidas", "Sobremesas"];
const INATIVIDADE_MS = 30000;
const CONFIRMACAO_MS = 8000;

const raiz = document.getElementById("tela");
const estado = {
  tela: "inicio",
  produtos: [],
  categoria: CATEGORIAS[0],
  carrinho: new Map(),
  enviando: false,
  erro: null,
  numero: null,
};
let temporizador = null;

const itensCarrinho = () => [...estado.carrinho.entries()];
const totalItens = () => itensCarrinho().reduce((soma, [, q]) => soma + q, 0);
const total = () =>
  itensCarrinho().reduce((soma, [id, q]) => {
    const produto = estado.produtos.find((p) => p.id === id);
    return soma + (produto ? produto.preco_centavos * q : 0);
  }, 0);

function agendarRetorno(ms) {
  clearTimeout(temporizador);
  temporizador = setTimeout(voltarAoInicio, ms);
}

function voltarAoInicio() {
  clearTimeout(temporizador);
  estado.tela = "inicio";
  estado.carrinho.clear();
  estado.categoria = CATEGORIAS[0];
  estado.erro = null;
  estado.enviando = false;
  desenhar();
}

function ativar() {
  if (estado.tela === "cardapio" || estado.tela === "revisao") agendarRetorno(INATIVIDADE_MS);
}

function telaInicio() {
  return `
    <section class="flex flex-1 flex-col items-center justify-center gap-[var(--espaco-5)] p-[var(--espaco-5)] text-center">
      <div class="text-[160px]" aria-hidden="true">🍔</div>
      <h1 class="titulo text-laranja">Faça seu pedido</h1>
      <p class="suave">Escolha seus produtos e retire no balcão.</p>
      <button class="btn btn-primario w-full" data-acao="comecar">Toque para começar</button>
    </section>`;
}

function cartaoProduto(produto) {
  return `
    <article class="cartao flex min-h-[360px] min-w-[440px] flex-col items-center justify-between gap-[var(--espaco-2)] p-[var(--espaco-3)] text-center">
      <div class="text-[96px] leading-none" aria-hidden="true">${esc(produto.icone)}</div>
      <h2 class="produto-nome">${esc(produto.nome)}</h2>
      <p class="preco">${reais(produto.preco_centavos)}</p>
      <button class="btn btn-primario w-full" data-acao="adicionar" data-id="${produto.id}">Adicionar</button>
    </article>`;
}

function linhaRevisao([id, quantidade]) {
  const produto = estado.produtos.find((p) => p.id === id);
  return `
    <li class="cartao flex items-center gap-[var(--espaco-2)] p-[var(--espaco-2)]">
      <span class="text-[64px] leading-none" aria-hidden="true">${esc(produto.icone)}</span>
      <div class="flex-1">
        <div class="produto-nome">${esc(produto.nome)}</div>
        <div class="preco">${reais(produto.preco_centavos * quantidade)}</div>
      </div>
      <button class="btn btn-secundario !min-h-[80px] !w-[80px] !px-0" data-acao="menos" data-id="${id}" aria-label="Diminuir ${esc(produto.nome)}">−</button>
      <span class="numero-pedido w-[56px] text-center produto-nome">${quantidade}</span>
      <button class="btn btn-secundario !min-h-[80px] !w-[80px] !px-0" data-acao="mais" data-id="${id}" aria-label="Aumentar ${esc(produto.nome)}">+</button>
      <button class="btn btn-perigo" data-acao="remover" data-id="${id}">Remover</button>
    </li>`;
}

function telaCardapio() {
  const abas = CATEGORIAS.map(
    (c) =>
      `<button class="aba flex-1" role="tab" aria-selected="${c === estado.categoria}" data-acao="categoria" data-categoria="${c}">${c}</button>`
  ).join("");
  const produtos = estado.produtos
    .filter((p) => p.categoria === estado.categoria)
    .map(cartaoProduto)
    .join("");
  const vazio = totalItens() === 0;

  return `
    <header class="sticky top-0 z-10 flex gap-[var(--espaco-2)] bg-preto p-[var(--espaco-2)]" role="tablist">${abas}</header>
    <section class="grid flex-1 grid-cols-2 content-start gap-[var(--espaco-3)] p-[var(--espaco-3)]">${produtos}</section>
    <footer class="sticky bottom-0 z-10 flex items-center gap-[var(--espaco-3)] border-t-2 border-borda bg-superficie p-[var(--espaco-3)]">
      <div class="flex-1">
        <div class="suave">${totalItens()} ${totalItens() === 1 ? "item" : "itens"}</div>
        <div class="preco">${reais(total())}</div>
      </div>
      <button class="btn btn-primario" data-acao="revisar" ${vazio ? "disabled" : ""}>Revisar pedido</button>
    </footer>`;
}

const MENSAGENS_ERRO = {
  rede: "Não foi possível enviar o pedido. Toque em Tentar de novo.",
  cheio: "Não há senhas disponíveis agora. Chame um atendente.",
};

function telaRevisao() {
  const linhas = itensCarrinho().map(linhaRevisao).join("");
  const erro = estado.erro
    ? `<div class="erro mb-[var(--espaco-2)]" role="alert"><span aria-hidden="true">⚠</span><span class="flex-1">${MENSAGENS_ERRO[estado.erro]}</span></div>`
    : "";
  const rotulo = estado.enviando ? "Aguarde…" : estado.erro === "rede" ? "Tentar de novo" : "Finalizar pedido";
  return `
    <header class="p-[var(--espaco-4)] pb-[var(--espaco-2)]">
      <h1 class="titulo text-laranja">Revise seu pedido</h1>
    </header>
    <ul class="m-0 flex flex-1 list-none flex-col content-start gap-[var(--espaco-2)] overflow-y-auto p-[var(--espaco-3)] pt-[var(--espaco-1)]">${linhas}</ul>
    <footer class="sticky bottom-0 z-10 border-t-2 border-borda bg-superficie p-[var(--espaco-3)]">
      ${erro}
      <div class="mb-[var(--espaco-2)] flex items-baseline justify-between">
        <span class="suave">${totalItens()} ${totalItens() === 1 ? "item" : "itens"}</span>
        <span class="preco">Total ${reais(total())}</span>
      </div>
      <div class="grid grid-cols-2 gap-[var(--espaco-2)]">
        <button class="btn btn-secundario" data-acao="voltar" ${estado.enviando ? "disabled" : ""}>Voltar ao cardápio</button>
        <button class="btn btn-primario" data-acao="finalizar" ${estado.enviando || estado.erro === "cheio" ? "disabled" : ""}>${rotulo}</button>
      </div>
    </footer>`;
}

function telaConfirmacao() {
  return `
    <section class="flex flex-1 flex-col items-center justify-center gap-[var(--espaco-4)] p-[var(--espaco-5)] text-center">
      <p class="titulo text-laranja">Pedido recebido!</p>
      <p class="produto-nome suave">Sua senha</p>
      <p class="numero-pedido text-amarelo" style="font-size: var(--fonte-pedido-totem); font-weight: 900; line-height: 1;">${estado.numero}</p>
      <p class="produto-nome">Retire no balcão quando o painel chamar</p>
    </section>`;
}

function desenhar() {
  const telas = { inicio: telaInicio, cardapio: telaCardapio, revisao: telaRevisao, confirmacao: telaConfirmacao };
  const rolagem = window.scrollY;
  raiz.innerHTML = telas[estado.tela]();
  window.scrollTo(0, rolagem);
}

async function finalizar() {
  if (estado.enviando || totalItens() === 0) return;
  estado.enviando = true;
  desenhar();
  try {
    const itens = itensCarrinho().map(([produto_id, quantidade]) => ({ produto_id, quantidade }));
    const pedido = await api("/pedidos", { method: "POST", body: JSON.stringify({ itens }) });
    estado.numero = pedido.numero;
    estado.carrinho.clear();
    estado.erro = null;
    estado.tela = "confirmacao";
    agendarRetorno(CONFIRMACAO_MS);
  } catch (erro) {
    console.warn(erro);
    estado.erro = erro.status === 503 ? "cheio" : "rede";
  } finally {
    estado.enviando = false;
    desenhar();
  }
}

const ACOES = {
  comecar() {
    estado.tela = "cardapio";
    agendarRetorno(INATIVIDADE_MS);
  },
  revisar() {
    estado.tela = "revisao";
  },
  voltar() {
    estado.tela = "cardapio";
  },
  categoria(alvo) {
    estado.categoria = alvo.dataset.categoria;
  },
  adicionar(alvo) {
    const id = Number(alvo.dataset.id);
    estado.carrinho.set(id, Math.min((estado.carrinho.get(id) || 0) + 1, 20));
  },
  mais(alvo) {
    ACOES.adicionar(alvo);
  },
  menos(alvo) {
    const id = Number(alvo.dataset.id);
    const novo = (estado.carrinho.get(id) || 0) - 1;
    if (novo <= 0) estado.carrinho.delete(id);
    else estado.carrinho.set(id, novo);
  },
  remover(alvo) {
    estado.carrinho.delete(Number(alvo.dataset.id));
  },
};

raiz.addEventListener("click", (evento) => {
  const alvo = evento.target.closest("[data-acao]");
  if (!alvo || alvo.disabled) return;
  if (alvo.dataset.acao === "finalizar") {
    finalizar();
    return;
  }
  ACOES[alvo.dataset.acao]?.(alvo);
  if (alvo.dataset.acao !== "comecar") estado.erro = null;
  if (estado.tela === "revisao" && totalItens() === 0) estado.tela = "cardapio";
  desenhar();
});

document.addEventListener("pointerdown", ativar);

async function iniciar() {
  desenhar();
  try {
    estado.produtos = await api("/produtos");
  } catch (erro) {
    console.warn(erro);
    raiz.innerHTML = `<div class="erro m-[var(--espaco-4)]" role="alert"><span aria-hidden="true">⚠</span><span>Não foi possível carregar o cardápio. Chame um atendente.</span></div>`;
  }
}

iniciar();
