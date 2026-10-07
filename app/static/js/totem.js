import { enviarJSON, formatarPreco, h, requisitar } from '/static/js/api.js';

const TELAS = ['inicio', 'cardapio', 'revisao', 'confirmacao'];
const OCIOSIDADE_MS = 30_000;
const CONFIRMACAO_MS = 8_000;

const $ = (id) => document.getElementById(id);
const carrinho = new Map();
let categorias = [];
let categoriaAtiva = 0;
let tela = 'inicio';
let timerOciosidade;
let timerConfirmacao;

function irPara(nova) {
  tela = nova;
  TELAS.forEach((nome) => { $(nome).hidden = nome !== nova; });
  window.scrollTo(0, 0);
  armarOciosidade();
}

function reiniciar() {
  clearTimeout(timerConfirmacao);
  carrinho.clear();
  atualizarBarra();
  esconderErro();
  irPara('inicio');
}

function armarOciosidade() {
  clearTimeout(timerOciosidade);
  if (tela === 'cardapio' || tela === 'revisao') {
    timerOciosidade = setTimeout(reiniciar, OCIOSIDADE_MS);
  }
}

document.addEventListener('pointerdown', armarOciosidade);

const totalCentavos = () =>
  [...carrinho.values()].reduce((soma, i) => soma + i.quantidade * i.produto.preco_centavos, 0);
const totalItens = () => [...carrinho.values()].reduce((soma, i) => soma + i.quantidade, 0);

function atualizarBarra() {
  const itens = totalItens();
  $('barra-itens').textContent = itens === 0
    ? 'Carrinho vazio'
    : `${itens} ${itens === 1 ? 'item' : 'itens'}`;
  $('barra-total').textContent = formatarPreco(totalCentavos());
  $('revisar').disabled = itens === 0;
}

function adicionar(produto) {
  const atual = carrinho.get(produto.id);
  if (atual) atual.quantidade = Math.min(99, atual.quantidade + 1);
  else carrinho.set(produto.id, { produto, quantidade: 1 });
  atualizarBarra();
}

function desenharAbas() {
  $('abas').replaceChildren(...categorias.map((categoria, indice) => {
    const aba = h('button', { className: 'aba', type: 'button', role: 'tab' }, categoria.nome);
    aba.setAttribute('aria-selected', String(indice === categoriaAtiva));
    aba.addEventListener('click', () => { categoriaAtiva = indice; desenharAbas(); desenharProdutos(); });
    return aba;
  }));
}

function desenharProdutos() {
  const { produtos } = categorias[categoriaAtiva];
  $('produtos').replaceChildren(...produtos.map((produto) => {
    const botao = h('button', { className: 'btn btn-primario w-full', type: 'button' }, 'Adicionar');
    botao.addEventListener('click', () => adicionar(produto));
    return h('article', { className: 'cartao p-6 flex flex-col items-center gap-3 min-h-[360px] min-w-[440px] justify-between text-center' },
      h('div', { className: 'text-[96px] leading-none', ariaHidden: 'true' }, produto.icone),
      h('h2', { className: 'fonte-produto' }, produto.nome),
      h('div', { className: 'fonte-preco' }, formatarPreco(produto.preco_centavos)),
      botao);
  }));
}

function desenharRevisao() {
  const linhas = [...carrinho.values()].map(({ produto, quantidade }) => {
    const mudar = (delta) => () => {
      const item = carrinho.get(produto.id);
      item.quantidade = Math.max(1, Math.min(99, item.quantidade + delta));
      atualizarBarra();
      desenharRevisao();
    };
    const remover = () => {
      carrinho.delete(produto.id);
      atualizarBarra();
      if (carrinho.size === 0) irPara('cardapio');
      else desenharRevisao();
    };
    const botaoQuadrado = (texto, rotulo, acao) => {
      const b = h('button', { className: 'btn btn-secundario !w-[80px] !px-0', type: 'button' }, texto);
      b.setAttribute('aria-label', rotulo);
      b.addEventListener('click', acao);
      return b;
    };
    const botaoRemover = h('button', { className: 'btn btn-perigo', type: 'button' }, 'Remover');
    botaoRemover.addEventListener('click', remover);
    return h('div', { className: 'cartao p-4 flex items-center gap-4' },
      h('span', { className: 'text-[64px] leading-none', ariaHidden: 'true' }, produto.icone),
      h('div', { className: 'flex-1' },
        h('div', { className: 'fonte-produto' }, produto.nome),
        h('div', { className: 'fonte-preco' }, formatarPreco(quantidade * produto.preco_centavos))),
      botaoQuadrado('−', `Diminuir ${produto.nome}`, mudar(-1)),
      h('span', { className: 'fonte-produto w-[56px] text-center num-pedido' }, String(quantidade)),
      botaoQuadrado('+', `Aumentar ${produto.nome}`, mudar(1)),
      botaoRemover);
  });
  $('linhas').replaceChildren(...linhas);
  $('revisao-total').textContent = formatarPreco(totalCentavos());
}

function mostrarErro(texto) {
  $('erro-texto').textContent = texto;
  $('erro').hidden = false;
}
function esconderErro() { $('erro').hidden = true; }

async function finalizar() {
  const botao = $('finalizar');
  botao.disabled = true;
  botao.textContent = 'Aguarde…';
  esconderErro();
  try {
    const itens = [...carrinho.values()].map((i) => ({ produto_id: i.produto.id, quantidade: i.quantidade }));
    const pedido = await enviarJSON('/api/pedidos', { itens });
    carrinho.clear();
    atualizarBarra();
    $('numero-pedido').textContent = pedido.numero;
    botao.textContent = 'Finalizar pedido';
    irPara('confirmacao');
    timerConfirmacao = setTimeout(reiniciar, CONFIRMACAO_MS);
  } catch {
    mostrarErro('Não foi possível enviar o pedido. Toque em Tentar de novo.');
    botao.textContent = 'Tentar de novo';
  } finally {
    botao.disabled = false;
  }
}

async function carregarCardapio() {
  try {
    ({ categorias } = await requisitar('/api/produtos'));
    categoriaAtiva = 0;
    desenharAbas();
    desenharProdutos();
    return true;
  } catch {
    return false;
  }
}

$('comecar').addEventListener('click', async () => {
  if (categorias.length === 0 && !(await carregarCardapio())) return;
  irPara('cardapio');
});
$('revisar').addEventListener('click', () => { desenharRevisao(); irPara('revisao'); });
$('voltar').addEventListener('click', () => { esconderErro(); irPara('cardapio'); });
$('finalizar').addEventListener('click', finalizar);

carregarCardapio();
atualizarBarra();
