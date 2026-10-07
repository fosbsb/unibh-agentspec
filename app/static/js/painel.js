import { h, poll, requisitar } from '/static/js/api.js';

const DESTAQUE_MS = 6_000;
const $ = (id) => document.getElementById(id);

const vistos = new Set();
const filaDeDestaques = [];
let primeiraCarga = true;
let exibindo = false;
let audioAtivo = false;

$('ativar-som').addEventListener('click', () => {
  audioAtivo = true;
  $('ativar-som').hidden = true;
  if ('speechSynthesis' in window) speechSynthesis.speak(new SpeechSynthesisUtterance(''));
});

function falar(pedido) {
  if (!audioAtivo || !('speechSynthesis' in window)) return;
  const fala = new SpeechSynthesisUtterance(`Pedido ${Number(pedido.numero)}, pronto`);
  fala.lang = 'pt-BR';
  speechSynthesis.speak(fala);
}

function proximoDestaque() {
  const pedido = filaDeDestaques.shift();
  if (!pedido) {
    exibindo = false;
    $('destaque').hidden = true;
    return;
  }
  exibindo = true;
  $('destaque-numero').textContent = pedido.numero;
  $('destaque').hidden = false;
  falar(pedido);
  setTimeout(proximoDestaque, DESTAQUE_MS);
}

function detectarProntos(pedidos) {
  for (const pedido of pedidos.filter((p) => p.estado === 'pronto')) {
    if (vistos.has(pedido.id)) continue;
    vistos.add(pedido.id);
    if (!primeiraCarga) filaDeDestaques.push(pedido);
  }
  primeiraCarga = false;
  if (!exibindo) proximoDestaque();
}

function desenharLista(id, pedidos) {
  $(id).replaceChildren(...pedidos.map((p) => h('li', {}, p.numero)));
}

function textoTempoMedio(segundos) {
  if (segundos === null) return 'Tempo médio de preparo: —';
  const minutos = Math.round(segundos / 60);
  return minutos < 1
    ? 'Tempo médio de preparo: menos de 1 min'
    : `Tempo médio de preparo: ${minutos} min`;
}

async function atualizar() {
  const { pedidos, tempo_medio_preparo_segundos: media } = await requisitar('/api/pedidos');
  desenharLista('preparando', pedidos.filter((p) => p.estado === 'recebido' || p.estado === 'preparando'));
  desenharLista('pronto', pedidos.filter((p) => p.estado === 'pronto'));
  $('rodape').textContent = textoTempoMedio(media);
  detectarProntos(pedidos);
}

poll(atualizar);
