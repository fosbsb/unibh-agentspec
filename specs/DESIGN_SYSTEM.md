# Design System: Totem de Autoatendimento

Fonte única de verdade do visual do totem. Toda tela, componente e estilo do projeto segue este documento. Os tokens daqui viram variáveis CSS em `app/static/css/tokens.css`.

**Versão:** 1.1.0

---

## 1. Contexto de uso

| Tela | Dispositivo | Quem usa | Como usa |
|---|---|---|---|
| `/totem` | Totem 1080x1920, retrato | Cliente, em pé, às vezes com pressa | Só toque, sem teclado e sem mouse |
| `/painel` | TV 1920x1080, paisagem | Clientes aguardando, a até 5 metros | Só leitura |
| `/cozinha` | Desktop ou tablet | Atendente e cozinha | Mouse ou toque |

## 2. Princípios

1. **Grande e claro.** Se precisa de zoom para ler ou de precisão para tocar, está errado.
2. **Uma ação principal por tela.** O botão mais importante é sempre laranja e sempre o maior.
3. **Cor nunca é o único sinal.** Todo estado também tem texto ou ícone.
4. **Contraste alto.** O fundo é preto. O texto é branco ou amarelo.
5. **Texto curto, em português do Brasil.** Verbos no imperativo nos botões: "Adicionar", "Revisar pedido", "Confirmar pedido".

---

## 3. Cores

### 3.1 Paleta principal

| Token | Valor | Papel |
|---|---|---|
| `--cor-preto` | `#0D0D0D` | Fundo das telas |
| `--cor-laranja` | `#FF7A00` | Cor da marca, ação principal, botões |
| `--cor-amarelo` | `#FFC20E` | Destaque: preços, número do pedido, pedido pronto |
| `--cor-vermelho` | `#D62828` | Cancelar, remover, erro |

### 3.2 Neutros de apoio

| Token | Valor | Papel |
|---|---|---|
| `--cor-superficie` | `#1C1C1C` | Cartões e painéis sobre o fundo preto |
| `--cor-superficie-alta` | `#2A2A2A` | Item selecionado e linhas em destaque |
| `--cor-borda` | `#3D3D3D` | Divisores e bordas |
| `--cor-texto` | `#FFFFFF` | Texto principal |
| `--cor-texto-suave` | `#BDBDBD` | Texto secundário |
| `--cor-vermelho-claro` | `#FF5A5A` | Texto e ícone de erro sobre fundo escuro |

### 3.3 Regras de uso

| Combinação | Use para | Contraste |
|---|---|---|
| Texto branco sobre preto | Texto corrido | 19:1 |
| Texto amarelo sobre preto | Preço, número do pedido | 12:1 |
| Texto laranja sobre preto | Rótulos e títulos de destaque | 7:1 |
| Texto **preto** sobre laranja | Texto dos botões principais | 7:1 |
| Texto **preto** sobre amarelo | Selo "Pronto", etiqueta de destaque | 12:1 |
| Texto branco sobre vermelho | Botão "Cancelar" e "Remover" | 5:1 |
| Texto vermelho-claro sobre preto | Mensagem de erro | 6:1 |

Proibido:
- Texto **branco** sobre laranja ou amarelo (contraste insuficiente).
- Texto vermelho (`--cor-vermelho`) direto sobre preto. Use `--cor-vermelho-claro`.
- Cores fora desta tabela. Se faltar uma cor, atualize este documento antes.

### 3.4 Cores por estado do pedido

| Estado | Fundo | Texto | Ícone | Rótulo |
|---|---|---|---|---|
| Recebido | `--cor-superficie-alta` | branco | 🕒 | Recebido |
| Preparando | `--cor-laranja` | preto | 🔥 | Preparando |
| Pronto | `--cor-amarelo` | preto | ✅ | Pronto |
| Cancelado | `--cor-vermelho` | branco | ✖ | Cancelado |

---

## 4. Tipografia

| Token | Valor | Uso |
|---|---|---|
| `--fonte-familia` | `"Inter", "Segoe UI", system-ui, sans-serif` | Todo o texto |
| `--fonte-base-totem` | `24px` | Texto corrido no totem |
| `--fonte-base-cozinha` | `16px` | Texto corrido na cozinha |
| `--fonte-titulo` | `48px`, peso 800 | Título da tela |
| `--fonte-produto` | `28px`, peso 700 | Nome do produto |
| `--fonte-preco` | `32px`, peso 800 | Preço |
| `--fonte-pedido-totem` | `160px`, peso 900 | Número do pedido na confirmação |
| `--fonte-pedido-painel` | `192px`, peso 900 | Pedido pronto em destaque no painel |
| `--fonte-pedido-lista` | `72px`, peso 800 | Pedidos nas listas do painel |

Regras:
- Números do pedido usam `font-variant-numeric: tabular-nums`.
- Nada abaixo de 24px no totem e no painel.

---

## 5. Espaçamento, forma e movimento

| Token | Valor |
|---|---|
| `--espaco-1` | `8px` |
| `--espaco-2` | `16px` |
| `--espaco-3` | `24px` |
| `--espaco-4` | `32px` |
| `--espaco-5` | `48px` |
| `--raio-botao` | `20px` |
| `--raio-cartao` | `28px` |
| `--sombra-cartao` | `0 8px 24px rgba(0, 0, 0, 0.5)` |
| `--toque-minimo` | `80px` (altura mínima dos alvos de toque no totem) |
| `--movimento-rapido` | `150ms ease-out` |
| `--movimento-normal` | `300ms ease-out` |

Regra de movimento: todas as animações param quando o sistema tem `prefers-reduced-motion: reduce`.

---

## 6. Componentes

### 6.1 Cartão de produto (totem)

| Parte | Regra |
|---|---|
| Fundo | `--cor-superficie`, raio `--raio-cartao` |
| Ícone | Emoji grande (96px) no topo |
| Nome | `--fonte-produto`, branco |
| Preço | `--fonte-preco`, amarelo, formato `R$ 24,90` |
| Botão | "Adicionar", laranja, texto preto, altura mínima 80px |
| Tamanho | Mínimo de 440px de largura e 360px de altura. Duas colunas no totem |

### 6.2 Botão

| Variante | Fundo | Texto | Uso |
|---|---|---|---|
| Primário | `--cor-laranja` | preto | Ação principal da tela |
| Secundário | transparente, borda laranja de 3px | laranja | Ação de apoio |
| Perigo | `--cor-vermelho` | branco | Cancelar, remover item |
| Desabilitado | `--cor-superficie-alta` | `--cor-texto-suave` | Ação indisponível |

Todos: altura mínima 80px no totem (44px na cozinha), raio `--raio-botao`, texto 28px peso 700.

Estados:
- **Pressionado:** escala 0,97 e fundo 10% mais escuro.
- **Foco:** contorno amarelo de 4px.
- **Carregando:** texto "Aguarde…" e botão desabilitado.

### 6.3 Abas de categoria (totem)

Faixa fixa no topo com as categorias: Lanches, Crepes, Bebidas e Sobremesas. A aba ativa tem fundo laranja e texto preto, e as demais têm fundo `--cor-superficie` e texto branco. Altura mínima 80px.

### 6.4 Carrinho (totem)

Barra fixa no rodapé com a quantidade de itens, o total em amarelo e o botão primário "Revisar pedido", que abre a tela de revisão (6.10). Cada linha do carrinho tem os botões "−" e "+" (80x80px) e o botão perigo "Remover".

### 6.5 Confirmação do pedido (totem)

Tela cheia com o número do pedido em `--fonte-pedido-totem`, amarelo, centralizado, e a frase "Retire no balcão quando o painel chamar". Volta sozinha à tela inicial após 8 segundos.

### 6.6 Selo de estado do pedido

Cápsula com ícone e rótulo, nas cores da seção 3.4.

### 6.7 Painel de pedidos (TV)

| Área | Regra |
|---|---|
| Esquerda: "Preparando" | Título laranja. Lista de pedidos em `--fonte-pedido-lista`, branco |
| Direita: "Pronto" | Título amarelo. Lista de pedidos em `--fonte-pedido-lista`, amarelo |
| Pedido recém-pronto | Destaque em tela cheia por 6 segundos: fundo amarelo, número em preto com `--fonte-pedido-painel`, e a voz fala "Pedido 12, pronto" |
| Rodapé | Tempo médio de preparo, `--cor-texto-suave`, 32px |

### 6.8 Fila da cozinha

Cartões de pedido em ordem de chegada, com número, itens, horário e selo de estado. Botões: "Iniciar" (primário), "Marcar pronto" (primário), "Entregar" (secundário) e "Cancelar" (perigo).

### 6.9 Mensagem de erro

Faixa com fundo `--cor-superficie`, borda esquerda vermelha de 8px, ícone ⚠ e texto em `--cor-vermelho-claro`. Diz o que aconteceu e o que fazer: "Não foi possível enviar o pedido. Toque em Tentar de novo."

### 6.10 Revisão do pedido (totem)

Tela cheia, só de leitura, entre o carrinho e a confirmação. O pedido só é enviado quando o cliente toca em "Confirmar pedido".

| Parte | Regra |
|---|---|
| Título | "Revise seu pedido", `--fonte-titulo`, laranja |
| Linhas | Um cartão por item: emoji, quantidade e nome (`--fonte-produto`), preço unitário em `--cor-texto-suave` e subtotal da linha em `--fonte-preco`, amarelo |
| Total | Cartão com "Total" e o valor em `--fonte-preco`, amarelo |
| Voltar e editar | Botão secundário. Volta ao cardápio com o carrinho intacto |
| Confirmar pedido | Botão primário, mesmo tamanho do "Voltar e editar". Envia o pedido e mostra "Aguarde…" enquanto envia |
| Erro de envio | Faixa da seção 6.9 acima dos botões. O cliente permanece na revisão e o carrinho é mantido |

A edição de quantidades continua só no carrinho do cardápio. O relógio de 30 segundos de inatividade vale também nesta tela.

---

## 7. Acessibilidade

- Contraste mínimo de 4,5:1 em todo texto, e 7:1 no painel.
- Alvos de toque de no mínimo 80px no totem, com 16px de espaço entre eles.
- Nenhuma ação depende de hover, de duplo toque ou de arrastar.
- Todo estado tem texto ou ícone, além da cor.
- Foco visível: contorno amarelo de 4px.
- O totem volta à tela inicial após 30 segundos sem toque.
- Respeitar `prefers-reduced-motion`.

---

## 8. Cardápio de exemplo

Os 10 produtos usados na demonstração. O ícone é um emoji, sem arquivos de imagem.

| Categoria | Produto | Ícone | Preço |
|---|---|---|---|
| Lanches | Hambúrguer clássico | 🍔 | R$ 24,90 |
| Lanches | X-Bacon | 🥓 | R$ 29,90 |
| Lanches | Cachorro-quente | 🌭 | R$ 16,90 |
| Lanches | Batata frita | 🍟 | R$ 14,90 |
| Crepes | Crepe de queijo e presunto | 🥞 | R$ 19,90 |
| Crepes | Crepe de chocolate com morango | 🍓 | R$ 21,90 |
| Bebidas | Suco de laranja | 🍊 | R$ 9,90 |
| Bebidas | Suco de abacaxi com hortelã | 🍍 | R$ 10,90 |
| Bebidas | Milk shake de chocolate | 🥤 | R$ 18,90 |
| Sobremesas | Sundae de morango | 🍦 | R$ 12,90 |

---

## 9. Como os tokens chegam ao código

```css
:root {
  --cor-preto: #0D0D0D;
  --cor-laranja: #FF7A00;
  --cor-amarelo: #FFC20E;
  --cor-vermelho: #D62828;
  --cor-superficie: #1C1C1C;
  --cor-superficie-alta: #2A2A2A;
  --cor-borda: #3D3D3D;
  --cor-texto: #FFFFFF;
  --cor-texto-suave: #BDBDBD;
  --cor-vermelho-claro: #FF5A5A;
}
```

- Os tokens ficam em `app/static/css/tokens.css`.
- As telas usam as variáveis (`var(--cor-laranja)`), nunca o valor hexadecimal direto.
- Se usar Tailwind via CDN, a configuração mapeia as classes para essas variáveis.

---

## 10. Histórico

| Versão | Mudança |
|---|---|
| 1.0.0 | Versão inicial: paleta preto, laranja, amarelo e vermelho, e cardápio de exemplo |
| 1.1.0 | Tela de revisão do pedido (6.10). O botão da barra do carrinho passa de "Finalizar pedido" para "Revisar pedido" |
