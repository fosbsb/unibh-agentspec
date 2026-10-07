const moeda = new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' });

export const formatarPreco = (centavos) => moeda.format(centavos / 100).replace(/\s/g, ' ');

export async function requisitar(url, opcoes) {
  const resposta = await fetch(url, opcoes);
  const corpo = await resposta.json().catch(() => ({}));
  if (!resposta.ok) {
    throw Object.assign(new Error(corpo.detail || 'Erro na requisição'), { status: resposta.status });
  }
  return corpo;
}

export function enviarJSON(url, dados) {
  return requisitar(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(dados),
  });
}

export function poll(funcao, ms = 2000) {
  let parar = false;
  (async function ciclo() {
    try {
      await funcao();
    } catch (erro) {
      console.warn(erro);
    }
    if (!parar) setTimeout(ciclo, ms);
  })();
  return () => { parar = true; };
}

export function h(tag, atributos = {}, ...filhos) {
  const elemento = Object.assign(document.createElement(tag), atributos);
  elemento.append(...filhos);
  return elemento;
}

export const ESTADOS = {
  recebido: { icone: '🕒', rotulo: 'Recebido' },
  preparando: { icone: '🔥', rotulo: 'Preparando' },
  pronto: { icone: '✅', rotulo: 'Pronto' },
  entregue: { icone: '📦', rotulo: 'Entregue' },
};

export function selo(estado) {
  const { icone, rotulo } = ESTADOS[estado];
  return h('span', { className: `selo selo-${estado}` },
    h('span', { ariaHidden: 'true' }, icone), h('span', {}, rotulo));
}
