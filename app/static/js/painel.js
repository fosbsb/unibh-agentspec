import { api, repetir } from "./api.js";

const DESTAQUE_MS = 6000;

const listaPreparando = document.getElementById("preparando");
const listaPronto = document.getElementById("pronto");
const rodape = document.getElementById("tempo");
const botaoSom = document.getElementById("som");
const destaque = document.getElementById("destaque");
const destaqueNumero = document.getElementById("destaque-numero");

let vistos = null;
let somAtivo = false;
let mostrando = false;
const fila = [];

function numeros(lista, classe, fonte) {
  return lista
    .map(
      (p) =>
        `<li class="numero-pedido ${classe}" style="font-size: var(${fonte}); font-weight: 800; line-height: 1.15;">${p.numero}</li>`
    )
    .join("");
}

function textoTempo(segundos) {
  if (segundos === null || segundos === undefined) return "Tempo médio de preparo: —";
  const minutos = Math.max(1, Math.round(segundos / 60));
  return `Tempo médio de preparo: ${minutos} min`;
}

function desenhar(dados) {
  listaPreparando.innerHTML = numeros(dados.preparando, "text-white", "--fonte-pedido-lista");
  listaPronto.innerHTML = numeros(dados.pronto, "text-preto", "--fonte-pedido-pronto");
  rodape.textContent = textoTempo(dados.tempo_medio_segundos);
}

function falar(texto) {
  if (!somAtivo || !("speechSynthesis" in window)) return;
  const fala = new SpeechSynthesisUtterance(texto);
  fala.lang = "pt-BR";
  speechSynthesis.speak(fala);
}

function tocarProximo() {
  if (mostrando || fila.length === 0) return;
  const pedido = fila.shift();
  mostrando = true;
  destaqueNumero.textContent = pedido.numero;
  destaque.hidden = false;
  falar(`Senha ${pedido.numero}, pronta`);
  setTimeout(() => {
    destaque.hidden = true;
    mostrando = false;
    tocarProximo();
  }, DESTAQUE_MS);
}

function atualizar(dados) {
  const ids = new Set(dados.pronto.map((p) => p.id));
  if (vistos !== null) {
    dados.pronto.filter((p) => !vistos.has(p.id)).forEach((p) => fila.push(p));
  }
  vistos = ids;
  desenhar(dados);
  tocarProximo();
}

botaoSom.addEventListener("click", () => {
  somAtivo = true;
  botaoSom.textContent = "Som ativado";
  botaoSom.disabled = true;
  falar("Som ativado");
});

if (!("speechSynthesis" in window)) botaoSom.hidden = true;

repetir(async () => atualizar(await api("/painel")));
