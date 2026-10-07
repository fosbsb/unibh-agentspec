# BRAINSTORM: Totem de Autoatendimento

> Exploração colaborativa antes da captura de requisitos (Fase 0)

**Feature:** TOTEM_ATENDIMENTO
**Data:** 2026-10-07
**Autor:** brainstorm-agent
**Status:** ✅ Shipped

---

## 1. Ideia original

Totem de autoatendimento para uma lanchonete. O cliente toca na tela, escolhe produtos do cardápio, monta o pedido e recebe o número do pedido. Uma tela de cozinha mostra os pedidos em ordem de chegada e o atendente muda o estado do pedido. Uma TV mostra os pedidos em preparo e os prontos.

Contexto: demonstração para uma oficina. Precisa subir com um único `docker compose up`, sem login e sem etapa de build no frontend.

## 2. Contexto do projeto

| Item | Situação |
|---|---|
| Código existente | Nenhum. O repositório só tem README, roteiro e design system |
| CLAUDE.md | Não existe |
| Design system | `specs/DESIGN_SYSTEM.md` v1.0.0 (preto, laranja, amarelo, vermelho) |
| Telas definidas pelo design system | `/totem` (1080x1920, toque), `/painel` (TV 1920x1080, leitura), `/cozinha` (desktop ou tablet) |

## 3. Stack (dada)

FastAPI, SQLAlchemy, PostgreSQL 16 (serviço `db` no docker compose), HTML com Tailwind via CDN e JavaScript puro, testes com pytest.

## 4. Perguntas e decisões

| # | Tema | Decisão |
|---|---|---|
| 1 | Fluxo do cliente | Tela "Toque para começar", cardápio com abas de categoria, carrinho com mais e menos, "Finalizar pedido" e confirmação com o número do pedido |
| 2 | Numeração | Sequencial de 3 dígitos (001, 002…), reinicia todo dia |
| 3 | Estados | Recebido, Preparando, Pronto, Entregue e Cancelado. Avanço em um clique; Cancelar separado, em vermelho |
| 4 | Atualização e aviso | Polling a cada 2 s, sem WebSocket. Painel fala "Pedido 12, pronto" via Web Speech API |
| 5 | Amostras | Nenhuma disponível. Cardápio de 10 itens e design system já estão definidos |

### Decisões herdadas do pedido

- Sem login. Sem pagamento.
- Cardápio de 10 produtos carregado na subida da aplicação, sem duplicar.
- Tabelas criadas na subida (sem migrations).

## 5. Dados de amostra

Nenhum arquivo de amostra. O cardápio vem do pedido original:

| Categoria | Produto | Preço |
|---|---|---|
| Lanches | Hambúrguer clássico | R$ 24,90 |
| Lanches | X-Bacon | R$ 29,90 |
| Lanches | Cachorro-quente | R$ 16,90 |
| Lanches | Batata frita | R$ 14,90 |
| Crepes | Crepe de queijo e presunto | R$ 19,90 |
| Crepes | Crepe de chocolate com morango | R$ 21,90 |
| Bebidas | Suco de laranja | R$ 9,90 |
| Bebidas | Suco de abacaxi com hortelã | R$ 10,90 |
| Bebidas | Milk shake de chocolate | R$ 18,90 |
| Sobremesas | Sundae de morango | R$ 12,90 |

## 6. Abordagens exploradas

### Abordagem A: monólito FastAPI que serve HTML estático (recomendada, escolhida)

**Por quê:** um único serviço `app` serve a API JSON em `/api` e as páginas `/totem`, `/painel` e `/cozinha`, mais o serviço `db`. É o caminho mais curto para um `docker compose up` e é fácil de explicar numa oficina.

**Prós:**
- Um container de aplicação, um comando.
- Sem build de frontend: JavaScript puro e Tailwind via CDN.
- Tokens do design system em `app/static/css/tokens.css`.

**Contras:**
- O polling gera requisições repetidas (aceitável numa demo).

### Abordagem B: nginx na frente servindo o estático, com API separada

**Por que não:** adiciona um container e configuração de proxy, contrariando a simplicidade do "um único docker compose up".

### Abordagem C: SPA única com roteamento no cliente

**Por que não:** as três telas têm dispositivos e usos diferentes. Uma SPA única as acopla sem ganho.

## 7. Desenho validado

### 7.1 Arquitetura

```text
docker compose
├── db   (PostgreSQL 16, volume nomeado, healthcheck)
└── app  (FastAPI; depende de db saudável)
         ├── /api/...      JSON
         ├── /totem        cliente
         ├── /cozinha      atendente
         └── /painel       TV
```

### 7.2 Rotas de API

| Método e rota | Função |
|---|---|
| `GET /api/produtos` | Lista o cardápio por categoria |
| `POST /api/pedidos` | Cria o pedido e devolve o número do dia |
| `GET /api/pedidos?estado=...` | Lista pedidos por estado, em ordem de chegada |
| `POST /api/pedidos/{id}/avancar` | Avança para o próximo estado |
| `POST /api/pedidos/{id}/cancelar` | Cancela o pedido |
| `GET /api/painel` | Pedidos em preparo e prontos para a TV |

### 7.3 Regras de negócio

- Transições: `Recebido → Preparando → Pronto → Entregue`. Cancelar vale em Recebido e Preparando. Entregue e Cancelado são estados finais.
- Dois atendentes iniciando ao mesmo tempo nunca pegam o mesmo pedido: bloqueio de linha com `SELECT ... FOR UPDATE SKIP LOCKED`.
- Número do dia: linha de contador por data, travada com `SELECT ... FOR UPDATE`, para não repetir número sob concorrência.
- Preço em centavos inteiros (`price_cents`). O total é calculado no servidor, nunca aceito do cliente.

### 7.4 Dados

Tabelas `products`, `orders` e `order_items`, criadas na subida com `create_all`. Carga do cardápio idempotente. Volume nomeado para os dados do PostgreSQL.

### 7.5 Comportamento das telas

- **Totem:** volta à tela inicial após 30 s sem toque. A confirmação do pedido some após 8 s. Cada produto usa um emoji como ícone.
- **Cozinha:** pedidos em ordem de chegada; botão de avanço grande e botão Cancelar em vermelho.
- **Painel:** duas colunas (Preparando, Pronto), atualização a cada 2 s, voz ao surgir um pedido novo em Pronto.
- **Visual:** segue `specs/DESIGN_SYSTEM.md`, com alto contraste, botões grandes e leitura à distância no painel.

### 7.6 Testes e entrega

- pytest contra PostgreSQL real (o mesmo serviço `db`), em banco de teste separado. SQLite não serve, pois não tem `SKIP LOCKED`.
- O `app` só inicia depois que o `db` fica saudável (`healthcheck` e `depends_on: condition: service_healthy`).
- Testes obrigatórios: regra de transição, numeração diária, concorrência no avanço de estado, carga idempotente do cardápio.

## 8. YAGNI: removido do escopo

| Item | Motivo |
|---|---|
| Pagamento e cobrança | A demo só registra o pedido |
| Impressão de senha | A confirmação já mostra o número |
| Estoque | Não resolve o problema central |
| Login e perfis | Demo sem login |
| Relatórios e múltiplas lojas | Sem necessidade |
| Personalização de itens | Complica o modelo de dados |
| Imagens de produto | Emoji como ícone |
| Migrations (Alembic) | Tabelas criadas na subida |
| WebSocket ou SSE | Polling de 2 s basta |

## 9. Rascunho de requisitos

**Must have**
- Totem: fluxo completo (início, abas de categoria, carrinho, finalizar, confirmação com número).
- Número do pedido de 3 dígitos, reiniciando por dia.
- Cozinha: lista em ordem de chegada, com avanço de estado e cancelamento.
- Painel: pedidos em preparo e prontos, com aviso por voz.
- Cardápio de 10 produtos carregado na subida, sem duplicar.
- `docker compose up` único, sem login e sem build de frontend.
- Visual conforme `specs/DESIGN_SYSTEM.md`.
- Testes pytest em PostgreSQL real.

**Should have**
- Retorno automático do totem à tela inicial após 30 s de inatividade.
- Confirmação que some após 8 s.

**Won't have (agora)**
- Itens da seção 8.

## 10. Riscos e pontos de atenção

| Risco | Mitigação |
|---|---|
| `app` sobe antes do `db` aceitar conexões | `healthcheck` e `depends_on: service_healthy` |
| Web Speech API depende da voz do navegador | Aviso visual sempre presente; voz é reforço |
| Navegadores bloqueiam fala antes de interação do usuário | Botão ou toque inicial na TV para liberar o áudio |
| Número duplicado sob concorrência | Contador por data com bloqueio de linha e teste dedicado |

## 11. Qualidade do brainstorm

```text
[x] Mínimo de 3 perguntas de descoberta (4 feitas)
[x] Pergunta de amostras feita
[x] Ao menos 2 abordagens exploradas (3)
[x] YAGNI aplicado
[x] Mínimo de 2 validações (2 feitas)
[x] Abordagem confirmada pelo usuário
[x] Rascunho de requisitos incluído
```

## 12. Próximo passo

```bash
/tecspec:workflow:define .claude/sdd/features/BRAINSTORM_TOTEM_ATENDIMENTO.md
```

---

**Revisão:** shipped e arquivado em 2026-10-07.
