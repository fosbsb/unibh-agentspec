import { HIGHLIGHT_MS } from "./config.js";
import { api, esc, poll } from "./common.js";

const el = {
  preparing: document.getElementById("preparing"),
  ready: document.getElementById("ready"),
  average: document.getElementById("average"),
  highlight: document.getElementById("highlight"),
  highlightNumber: document.getElementById("highlight-number"),
  gate: document.getElementById("sound-gate"),
};

const announced = new Set();
const queue = [];
let firstLoad = true;
let showing = false;
let soundEnabled = false;

function enableSound() {
  soundEnabled = true;
  el.gate.classList.add("hidden");
  if ("speechSynthesis" in window) {
    const unlock = new SpeechSynthesisUtterance(" ");
    unlock.volume = 0;
    speechSynthesis.speak(unlock);
  }
}

el.gate.addEventListener("click", enableSound);
el.gate.addEventListener("keydown", (event) => {
  if (event.key === "Enter" || event.key === " ") enableSound();
});

function speak(number) {
  if (!soundEnabled || !("speechSynthesis" in window)) return;
  const utterance = new SpeechSynthesisUtterance(`Pedido ${Number(number)}, pronto`);
  utterance.lang = "pt-BR";
  speechSynthesis.speak(utterance);
}

function playNext() {
  if (showing || queue.length === 0) return;
  const order = queue.shift();
  showing = true;
  el.highlightNumber.textContent = order.number;
  el.highlight.classList.remove("hidden");
  speak(order.number);
  setTimeout(() => {
    el.highlight.classList.add("hidden");
    showing = false;
    playNext();
  }, HIGHLIGHT_MS);
}

function numbersHTML(orders) {
  return orders
    .map((o) => `<div class="pedido-numero pedido-numero-lista">${esc(o.number)}</div>`)
    .join("");
}

function averageText(seconds) {
  if (seconds === null) return "";
  const minutes = Math.round(seconds / 60);
  return `Tempo médio de preparo: ${minutes < 1 ? "menos de 1 min" : `${minutes} min`}`;
}

async function refresh() {
  const panel = await api("/painel");
  el.preparing.innerHTML = numbersHTML(panel.preparing);
  el.ready.innerHTML = numbersHTML(panel.ready);
  el.average.textContent = averageText(panel.avg_prep_seconds);

  for (const order of [...panel.ready].reverse()) {
    if (announced.has(order.id)) continue;
    announced.add(order.id);
    if (!firstLoad) queue.push(order);
  }
  firstLoad = false;
  playNext();
}

poll(refresh);
