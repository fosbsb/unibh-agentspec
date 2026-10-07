import { enviarJSON, h, poll, requisitar, selo } from '/static/js/api.js';

const ACAO = {
  recebido: { rotulo: 'Iniciar', classe: 'btn-primario' },
  preparando: { rotulo: 'Marcar pronto', classe: 'btn-primario' },
  pronto: { rotulo: 'Entregar', classe: 'btn-secundario' },
};

const $ = (id) => document.getElementById(id);
let ultimoRetrato = '';
let timerAviso;

function avisar(texto) {
  $('aviso-texto').textContent = texto;
  $('aviso').hidden = false;
  clearTimeout(timerAviso);
  timerAviso = setTimeout(() => { $('aviso').hidden = true; }, 5_000);
}

const horario = (iso) =>
  new Date(iso).toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit', timeZone: 'America/Sao_Paulo' });

async function avancar(pedido, botao) {
  botao.disabled = true;
  botao.textContent = 'Aguarde…';
  try {
    await enviarJSON(`/api/pedidos/${pedido.id}/avancar`, { estado_atual: pedido.estado });
  } catch (erro) {
    avisar(erro.status === 409
      ? 'O pedido mudou de estado. A fila foi atualizada.'
      : 'Não foi possível atualizar o pedido. Tente de novo.');
  }
  await carregarFila(true);
}

function cartao(pedido) {
  const acao = ACAO[pedido.estado];
  const botao = h('button', { className: `btn ${acao.classe} w-full`, type: 'button' }, acao.rotulo);
  botao.addEventListener('click', () => avancar(pedido, botao));
  return h('article', { className: 'cartao p-4 flex flex-col gap-3' },
    h('div', { className: 'flex items-center justify-between' },
      h('span', { className: 'text-[40px] font-black num-pedido text-amarelo' }, pedido.numero),
      selo(pedido.estado)),
    h('div', { className: 'text-suave' }, `Chegada às ${horario(pedido.criado_em)}`),
    h('ul', { className: 'flex flex-col gap-1 text-[18px]' },
      ...pedido.itens.map((i) => h('li', {}, `${i.quantidade}× ${i.icone}  ${i.nome}`))),
    botao);
}

async function carregarFila(forcar = false) {
  const { pedidos } = await requisitar('/api/pedidos');
  const retrato = JSON.stringify(pedidos);
  if (!forcar && retrato === ultimoRetrato) return;
  ultimoRetrato = retrato;
  $('fila').replaceChildren(...pedidos.map(cartao));
  $('vazio').hidden = pedidos.length > 0;
  $('contagem').textContent = `${pedidos.length} ${pedidos.length === 1 ? 'pedido' : 'pedidos'} na fila`;
}

poll(carregarFila);
