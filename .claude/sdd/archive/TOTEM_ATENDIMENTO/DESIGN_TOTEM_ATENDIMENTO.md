# DESIGN: Totem de Autoatendimento

> Arquitetura e especificação técnica (Fase 2)

**Feature:** TOTEM_ATENDIMENTO
**Data:** 2026-10-07
**Origem:** `.claude/sdd/features/DEFINE_TOTEM_ATENDIMENTO.md`
**Visual:** `specs/DESIGN_SYSTEM.md` v1.0.0
**Status:** ✅ Shipped

---

## 1. Visão geral

```text
                     docker compose up
        ┌──────────────────────────────────────────────┐
        │                                              │
  Totem │   ┌───────────────────────┐   ┌───────────┐  │
 /totem ├──►│  app (FastAPI, 1 wkr) │──►│ db        │  │
        │   │                       │   │ PG 16     │  │
Cozinha │   │  /api/*   JSON        │   │ vol:pgdata│  │
/cozinha├──►│  /totem /cozinha      │   └───────────┘  │
        │   │  /painel  /  (HTML)   │    healthcheck   │
  Painel│   │  /static/*  css, js   │◄── service_healthy
 /painel├──►│                       │                  │
        │   └───────────────────────┘                  │
        └──────────────────────────────────────────────┘
   Navegadores: HTML + Tailwind (CDN) + JavaScript puro, polling de 2 s
```

### 1.1 Componentes

| Componente | Responsabilidade |
|---|---|
| `domain.py` | Estados do pedido, mapa de transições e exceções de domínio. Sem I/O |
| `models.py` | Tabelas SQLAlchemy: `products`, `orders`, `order_items`, `daily_counters` |
| `services.py` | Regras de negócio: criar pedido, numerar, avançar, cancelar, listar, painel |
| `api.py` | Rotas `/api/*`; converte exceções de domínio em códigos HTTP |
| `pages.py` | Rotas das páginas HTML (`/`, `/totem`, `/cozinha`, `/painel`) |
| `seed.py` | Carga idempotente dos 10 produtos |
| `main.py` | Criação do app, `lifespan` (create_all e seed), montagem de `/static` |
| `static/` | Telas, tokens e componentes visuais, JavaScript das três telas |

### 1.2 Fluxo de dados

```text
Cliente toca "Revisar pedido" (tela de revisão, sem chamada à API)
Cliente toca "Confirmar pedido"
  └► POST /api/pedidos {items:[{product_id, quantity}]}
       1. carrega produtos (preço vem do banco)
       2. upsert em daily_counters(day) → número do dia (trava a linha)
       3. insere orders + order_items, calcula total_cents
       4. commit (solta a trava do contador)
  ◄─ 201 {number:"007", ...}

Atendente toca "Iniciar"
  └► POST /api/pedidos/7/avancar {from_state:"recebido"}
       1. SELECT ... FOR UPDATE SKIP LOCKED (linha travada → 409)
       2. status != from_state → 409
       3. aplica a próxima transição, commit
  ◄─ 200 {status:"preparando", ...}

Painel a cada 2 s
  └► GET /api/painel → {preparing, ready, avg_prep_seconds}
       novo id em "ready" → destaque 6 s + voz "Pedido 7, pronto"
```

### 1.3 Rastreabilidade

| Requisitos | Onde são atendidos |
|---|---|
| RF-01 a RF-06, RF-17, RF-18 | `totem.html`, `totem.js` |
| RF-07, RF-08 | `services.next_daily_number`, tabela `daily_counters` |
| RF-09, RF-11, RF-12, RF-13 | `domain.py`, `services.advance_order`, `services.cancel_order` |
| RF-10, RF-16 | `GET /api/pedidos`, `cozinha.js` |
| RF-14, RF-15, RF-16 | `GET /api/painel`, `painel.js` |
| RF-19 | `main.lifespan`, `seed.py` |
| RF-20 | `services.create_order` |
| RNF-01 a RNF-03 | `docker-compose.yml`, `Dockerfile` |
| RNF-05 a RNF-07 | `static/`, `tailwind-config.js`, `tokens.css`, `test_design_tokens.py` |
| RNF-08, RNF-09 | `models.py`, `main.lifespan` |
| RNF-10 | `tests/` |

### 1.4 Ajustes em relação ao DEFINE

O design incorpora itens do `specs/DESIGN_SYSTEM.md` que o DEFINE não detalhava, e uma correção de concorrência. Se quiser manter o DEFINE em sincronia, use `/tecspec:workflow:iterate`.

| Ajuste | Origem | Efeito |
|---|---|---|
| Destaque em tela cheia por 6 s para pedido recém-pronto | DS 6.7 | Complementa RF-15 |
| Rodapé do painel com tempo médio de preparo | DS 6.7 | Novo campo `avg_prep_seconds` e coluna `ready_at` |
| Avançar exige `from_state` no corpo | Correção de concorrência | Duas requisições em sequência não pulam dois estados (AT-12) |
| Lista de itens do carrinho sempre visível quando há itens | DS 6.4 e 7 (sem ações escondidas) | Detalha RF-04 e RF-05 |
| Página `/` com links para as três telas | Conveniência na oficina | Uma rota e um arquivo pequenos |
| Quantidade por item entre 1 e 20 | Proteção contra erro de toque | Validação no schema |

---

## 2. Decisões de arquitetura

### D-01: Monólito FastAPI servindo HTML estático

| Atributo | Valor |
|---|---|
| **Status** | Aceita |
| **Data** | 2026-10-07 |

**Contexto:** a demo precisa de um único `docker compose up` e de código fácil de explicar.
**Escolha:** um serviço `app` serve `/api` (JSON), as páginas e `/static`. Segundo serviço: `db`.
**Alternativas rejeitadas:**
1. nginx separado: mais um container e configuração de proxy, sem ganho.
2. SPA única: três telas com dispositivos diferentes ficariam acopladas.

**Consequências:** simples de subir. O polling gera requisições repetidas, aceitável na demo.

### D-02: SQLAlchemy 2.0 síncrono com psycopg 3

| Atributo | Valor |
|---|---|
| **Status** | Aceita |

**Contexto:** a concorrência depende de bloqueios de linha curtos e previsíveis.
**Escolha:** rotas `def` (FastAPI as executa em threads), `Session` síncrona, driver `postgresql+psycopg`.
**Alternativas rejeitadas:**
1. `asyncio` com `asyncpg`: mais conceitos para explicar e nenhum ganho com a carga da demo.
2. `psycopg2`: driver legado.

**Consequências:** código mais direto. Testes de concorrência usam threads com sessões próprias.

### D-03: Número do dia por upsert em `daily_counters`

| Atributo | Valor |
|---|---|
| **Status** | Aceita |

**Contexto:** RF-07 e RF-08 pedem números 001, 002… por dia, sem repetição sob concorrência.
**Escolha:** `INSERT ... ON CONFLICT (day) DO UPDATE SET last_number = last_number + 1 RETURNING last_number`. O `ON CONFLICT DO UPDATE` trava a linha do dia até o commit.
**Alternativas rejeitadas:**
1. `SELECT ... FOR UPDATE` no contador: no primeiro pedido do dia não existe linha para travar, então dois pedidos simultâneos poderiam receber o mesmo número ou falhar na criação.
2. `MAX(daily_number) + 1`: corrida clássica.
3. Sequence do PostgreSQL com reset diário: exige tarefa agendada.

**Consequências:**
- A criação de pedidos é serializada pelo contador. Irrelevante na escala da demo.
- Se a transação falhar, o número não é consumido, então não há buracos.
- `UNIQUE (order_date, daily_number)` é a segunda barreira.
- Depois do 999 o rótulo passa a 4 dígitos. Aceito na demo.

### D-04: Avançar com `SKIP LOCKED` e estado esperado

| Atributo | Valor |
|---|---|
| **Status** | Aceita |

**Contexto:** RF-13 e AT-12. Dois cliques no mesmo pedido não podem avançar dois estados.
**Escolha:** duas camadas.
1. `SELECT ... FOR UPDATE SKIP LOCKED` na linha do pedido. Se outra transação a segura, a resposta é 409 na hora, sem esperar.
2. O corpo traz `from_state` (o estado que o atendente está vendo). Se o estado atual for diferente, 409.

**Por que as duas:** só a camada 1 não basta. Se a requisição B chegar depois do commit de A, não há bloqueio, e B avançaria de Preparando para Pronto. A camada 2 cobre esse caso.
**Alternativas rejeitadas:**
1. `FOR UPDATE` sem `SKIP LOCKED`: a segunda requisição esperaria. O pedido original pediu `SKIP LOCKED`.
2. Coluna `version` com bloqueio otimista: mais código para o mesmo efeito.

**Consequências:** o cliente (cozinha) sempre manda o estado que mostra. A mensagem de 409 diz para atualizar a lista.

### D-05: "Ordem de chegada" é `id` crescente

| Atributo | Valor |
|---|---|
| **Status** | Aceita |

**Contexto:** ordenar por horário (`created_at`) pode contradizer o número do pedido quando duas transações iniciam quase juntas.
**Escolha:** ordenar por `orders.id`. O `id` é gerado no `INSERT`, que ocorre depois de travar o contador do dia, então `id` e `daily_number` crescem juntos.
**Consequências:** a fila da cozinha nunca mostra 008 antes de 007. `created_at` serve só para exibir o horário e calcular o tempo de preparo.

### D-06: Nomes em inglês no código e no JSON; URLs, valores de estado e textos em português

| Atributo | Valor |
|---|---|
| **Status** | Aceita |

**Contexto:** RNF-08 manda `price_cents`; as URLs do contrato são em português (`/api/pedidos`).
**Escolha:** identificadores Python, colunas e campos JSON em inglês (`status`, `total_cents`). Rotas, parâmetro `estado`, valores de estado (`recebido`, `preparando`, `pronto`, `entregue`, `cancelado`) e todo texto de tela em português.
**Consequências:** a fronteira fica explícita. O frontend traduz estado em rótulo com um mapa único em `common.js`.

### D-07: Polling com `setTimeout` encadeado e aviso detectado no cliente

| Atributo | Valor |
|---|---|
| **Status** | Aceita |

**Escolha:** cada tela agenda a próxima consulta 2 s depois do fim da anterior, sem sobreposição. O painel guarda em memória os ids já anunciados. Na primeira carga, os pedidos já prontos entram nesse conjunto sem serem anunciados.
**Alternativas rejeitadas:** `setInterval` (consultas podem se acumular com rede lenta); WebSocket e SSE (fora do escopo).
**Consequências:** recarregar o painel não repete avisos. Um pedido que fique Pronto e seja Entregue dentro de um único ciclo de 2 s não é anunciado; aceito.

### D-08: Testes em PostgreSQL real, dentro do container `app`

| Atributo | Valor |
|---|---|
| **Status** | Aceita |

**Escolha:** `docker compose run --rm app pytest`. O `conftest.py` deriva o banco `totem_test` da `DATABASE_URL` e o cria se faltar. Antes de qualquer `drop_all` ou `TRUNCATE`, o teste confere que o nome do banco termina em `_test`.
**Alternativa rejeitada:** SQLite, que não tem `SKIP LOCKED`.
**Consequências:** um único `requirements.txt` (aplicação e testes) e uma única imagem. Aceito pela simplicidade; numa produção real seriam separados.

### D-09: Um worker do uvicorn

| Atributo | Valor |
|---|---|
| **Status** | Aceita |

**Contexto:** `create_all` e a carga do cardápio rodam na subida.
**Escolha:** `uvicorn` com um único processo. O seed ainda usa `ON CONFLICT DO NOTHING`, então é seguro mesmo se alguém subir mais workers.

### D-10: Tailwind via CDN só para layout; tokens e componentes em CSS próprio

| Atributo | Valor |
|---|---|
| **Status** | Aceita |

**Contexto:** o design system manda usar `var(--cor-*)` e nunca hexadecimal (DS seção 9).
**Escolha:** `tailwind-config.js` mapeia cores, raios e alturas para as variáveis. Componentes do DS (botão, cartão, selo, faixa de erro) ficam em `components.css`, com tamanhos de fonte vindos dos tokens.
**Cuidados:**
- Modificadores de opacidade do Tailwind (`bg-laranja/50`) não funcionam com `var()`. Não usar.
- O CDN observa o DOM, então classes geradas por JavaScript funcionam.
- A fonte Inter não é baixada; vale a pilha de fallback do DS.

---

## 3. Modelo de dados

```text
products                    orders                         order_items
────────                    ──────                         ───────────
id            PK            id            PK               id               PK
category      varchar       order_date    date             order_id         FK → orders
name          varchar  UQ   daily_number  int              product_id       FK → products
icon          varchar       status        varchar (CHECK)  quantity         int  CHECK > 0
price_cents   int           total_cents   int              unit_price_cents int  (cópia do preço)
position      int           created_at    timestamptz
                            updated_at    timestamptz      daily_counters
                            ready_at      timestamptz null ──────────────
                            UQ(order_date, daily_number)   day          date PK
                            IX(status, id)                 last_number  int
```

- `status` é `VARCHAR` com `CHECK` (`Enum(native_enum=False)`), o que dispensa `CREATE TYPE` e funciona com `create_all`.
- `unit_price_cents` copia o preço no momento da compra.
- `ready_at` é preenchido ao entrar em Pronto. Alimenta `avg_prep_seconds`.
- `position` define a ordem do cardápio e das abas (Lanches, Crepes, Bebidas, Sobremesas).

---

## 4. Contrato da API

### 4.1 Rotas

| Método e rota | Corpo | Sucesso | Erros |
|---|---|---|---|
| `GET /api/produtos` | — | 200 `list[ProductOut]` ordenada por `position` | — |
| `POST /api/pedidos` | `OrderCreate` | 201 `OrderOut` | 422 |
| `GET /api/pedidos` | `?estado=` repetível | 200 `list[OrderOut]` por `id` crescente | 422 |
| `POST /api/pedidos/{id}/avancar` | `{"from_state": "..."}` | 200 `OrderOut` | 404, 409, 422 |
| `POST /api/pedidos/{id}/cancelar` | — | 200 `OrderOut` | 404, 409 |
| `GET /api/painel` | — | 200 `PanelOut` | — |

Sem `estado`, `GET /api/pedidos` devolve os ativos: `recebido`, `preparando` e `pronto`.

### 4.2 Schemas

```text
ProductOut   {id, category, name, icon, price_cents}
OrderCreate  {items: [{product_id: int, quantity: int 1..20}]}   # items: mínimo 1
OrderOut     {id, number: "007", status, total_cents, created_at, ready_at|null,
              items: [{product_id, name, icon, quantity, unit_price_cents}]}
PanelOut     {preparing: [{id, number}],            # por id crescente
              ready:     [{id, number, ready_at}],  # por ready_at decrescente
              avg_prep_seconds: int | null}
```

- O corpo de `OrderCreate` ignora campos extras (por exemplo, um `total` enviado pelo cliente). O total é sempre calculado no servidor (AT-18).
- Itens repetidos do mesmo produto são somados.
- `avg_prep_seconds` é a média de `ready_at - created_at` dos pedidos do dia que chegaram a Pronto. `null` se não houver nenhum.

### 4.3 Erros

| Situação | Código | `detail` (em português) |
|---|---|---|
| Pedido sem itens, quantidade fora de 1..20 | 422 | gerado pelo Pydantic |
| `product_id` inexistente | 422 | `Produto não encontrado: {id}.` |
| Pedido inexistente | 404 | `Pedido não encontrado.` |
| Linha travada por outra requisição | 409 | `Outro atendente está mudando este pedido. Atualize a lista.` |
| `from_state` diferente do estado atual | 409 | `O pedido já mudou de estado. Atualize a lista.` |
| Transição inválida (avançar de Entregue ou Cancelado) | 409 | `Este pedido não pode avançar.` |
| Cancelar fora de Recebido e Preparando | 409 | `Este pedido não pode mais ser cancelado.` |

### 4.4 Transições

```text
recebido ──► preparando ──► pronto ──► entregue
   │             │
   └──► cancelado ◄┘            (entregue e cancelado são finais)
```

---

## 5. Telas

### 5.1 Totem (`/totem`, 1080x1920)

```text
estados:  idle ──toque──► menu ──Revisar──► review ──Confirmar──► submitting ──ok──► confirmation ──8 s──► idle
                           ▲  │                 │  ▲                   │ erro
                           │  └─────────────────┘  └─ "Tentar de novo" ◄┘
                           │      "Voltar e editar"
                    menu e review: 30 s sem toque ──► idle (carrinho descartado)
```

| Área (de cima para baixo) | Conteúdo |
|---|---|
| Título | "Monte seu pedido" |
| Abas (80 px) | Lanches, Crepes, Bebidas, Sobremesas; ativa em laranja |
| Grade de produtos | 2 colunas de cartões (DS 6.1); rola na vertical |
| Itens do carrinho | Aparece com 1 item ou mais; cada linha com "−", quantidade, "+" e "Remover" (80x80 px); rola se passar de 40% da altura |
| Barra do rodapé | Quantidade de itens, total em amarelo, botão primário "Revisar pedido" |

- **idle:** tela cheia, "Toque para começar".
- **Quantidade:** "−" em 1 remove a linha. "+" respeita o máximo de 20.
- **Revisar pedido:** desabilitado com carrinho vazio. Abre a tela de revisão (DS 6.10), só de leitura, sem chamada à API.
- **Revisão:** um cartão por item (emoji, quantidade, nome, preço unitário e subtotal), cartão com o total e dois botões: "Voltar e editar" (secundário, volta ao cardápio com o carrinho intacto) e "Confirmar pedido" (primário, envia o pedido).
- **Confirmar pedido:** durante o envio mostra "Aguarde…" e os dois botões ficam desabilitados (evita pedido duplicado).
- **Erro:** faixa do DS 6.9 na tela de revisão, com "Não foi possível enviar o pedido. Toque em Tentar de novo." O cliente permanece na revisão e o carrinho é mantido.
- **confirmation:** número em `--fonte-pedido-totem`, amarelo, e "Retire no balcão quando o painel chamar".
- **Inatividade:** qualquer `pointerdown` no cardápio ou na revisão reinicia o relógio de 30 s. Durante `submitting` o relógio fica parado.
- **Quiosque:** `user-select: none` e `touch-action: manipulation`.

### 5.2 Cozinha (`/cozinha`)

- Grade de cartões (`auto-fill`, mínimo de 320 px), por `id` crescente.
- Cada cartão: número, selo de estado, horário (`HH:MM`), itens com quantidade.
- Botões (altura mínima 44 px):

| Estado | Botões |
|---|---|
| Recebido | "Iniciar" (primário), "Cancelar" (perigo) |
| Preparando | "Marcar pronto" (primário), "Cancelar" (perigo) |
| Pronto | "Entregar" (secundário) |

- Cada botão envia o `from_state` do cartão e fica em "Aguarde…" até a resposta. Em 409, mostra a faixa de erro com o `detail` e busca a lista de novo.
- Se a consulta falhar, aparece "Sem conexão com o servidor. Tentando de novo…" e o polling continua.
- Entregue e Cancelado saem da lista.

### 5.3 Painel (`/painel`, 1920x1080)

| Área | Conteúdo |
|---|---|
| Esquerda | "Preparando", título laranja, números em `--fonte-pedido-lista`, brancos |
| Direita | "Pronto", título amarelo, números em `--fonte-pedido-lista`, amarelos |
| Rodapé | "Tempo médio de preparo: N min" (ou oculto sem dados), `--cor-texto-suave`, 32 px |
| Destaque | Fundo amarelo em tela cheia por 6 s, número preto em `--fonte-pedido-painel`, texto "Pedido pronto" |

- Os ids novos em `ready` entram numa fila de destaques; cada um dura 6 s e dispara a voz `Pedido {N}, pronto` (`N` sem zeros à esquerda, `lang = 'pt-BR'`).
- **Áudio:** ao abrir, aparece "Toque para ativar o som". Enquanto ninguém tocar, o destaque visual funciona e a voz fica muda. Alternativa para TV sem toque: abrir o Chrome com `--autoplay-policy=no-user-gesture-required`.
- As listas usam `aria-live="polite"`.
- Todas as animações param com `prefers-reduced-motion: reduce`.

### 5.4 Constantes

`static/js/config.js` reúne `POLL_MS = 2000`, `IDLE_MS = 30000`, `CONFIRM_MS = 8000`, `HIGHLIGHT_MS = 6000` e `MAX_QTY = 20`.

---

## 6. Manifesto de arquivos

| # | Arquivo | Ação | Finalidade | Depende de |
|---|---|---|---|---|
| 1 | `requirements.txt` | Criar | fastapi, uvicorn, sqlalchemy 2, psycopg[binary] 3, tzdata, pytest, httpx | — |
| 2 | `.gitignore` | Criar | `__pycache__`, `.pytest_cache`, `.venv` | — |
| 3 | `.dockerignore` | Criar | Exclui `.git`, `.claude`, `roteiro`, `specs`, `.playwright-mcp`, caches | — |
| 4 | `Dockerfile` | Criar | Imagem `python:3.12-slim` com `requirements.txt` e o código | 1 |
| 5 | `docker-compose.yml` | Criar | Serviços `db` e `app`, healthcheck, volume | 4 |
| 6 | `pytest.ini` | Criar | `testpaths = tests`, `pythonpath = .` | — |
| 7 | `app/__init__.py` | Criar | Pacote | — |
| 8 | `app/config.py` | Criar | `DATABASE_URL`, `APP_TIMEZONE`, `today()` | — |
| 9 | `app/domain.py` | Criar | `OrderStatus`, `NEXT`, `CANCELABLE`, exceções | — |
| 10 | `app/database.py` | Criar | Engine, `SessionLocal`, `Base`, `get_db` | 8 |
| 11 | `app/models.py` | Criar | Tabelas | 9, 10 |
| 12 | `app/schemas.py` | Criar | Schemas Pydantic | 9 |
| 13 | `app/seed.py` | Criar | Carga idempotente do cardápio | 11 |
| 14 | `app/services.py` | Criar | Regras de negócio | 9, 11 |
| 15 | `app/api.py` | Criar | Rotas `/api` | 12, 14 |
| 16 | `app/pages.py` | Criar | Rotas das páginas | 17 a 28 |
| 17 | `app/main.py` | Criar | App, `lifespan`, montagem | 13, 15, 16 |
| 18 | `app/static/css/tokens.css` | Criar | Variáveis do DS (seção 9 do DS) | — |
| 19 | `app/static/css/components.css` | Criar | Botão, cartão, selo, faixa de erro, tipografia | 18 |
| 20 | `app/static/js/tailwind-config.js` | Criar | Cores, raios e alturas via `var()` | 18 |
| 21 | `app/static/js/config.js` | Criar | Constantes de tempo | — |
| 22 | `app/static/js/common.js` | Criar | `api()`, `formatBRL`, mapa de estados, `showError` | 21 |
| 23 | `app/static/js/totem.js` | Criar | Máquina de estados do totem | 22 |
| 24 | `app/static/js/cozinha.js` | Criar | Fila e ações da cozinha | 22 |
| 25 | `app/static/js/painel.js` | Criar | Painel, fila de destaques e voz | 22 |
| 26 | `app/static/totem.html` | Criar | Tela do totem | 18 a 20, 23 |
| 27 | `app/static/cozinha.html` | Criar | Tela da cozinha | 18 a 20, 24 |
| 28 | `app/static/painel.html` | Criar | Tela do painel | 18 a 20, 25 |
| 29 | `app/static/index.html` | Criar | Links para as três telas | 18 a 20 |
| 30 | `tests/conftest.py` | Criar | Banco de teste, fixtures, `client` | 10, 11, 13, 17 |
| 31 | `tests/test_seed.py` | Criar | AT-17, CS-06, preços | 30 |
| 32 | `tests/test_menu_api.py` | Criar | Cardápio e ordem das categorias | 30 |
| 33 | `tests/test_order_creation.py` | Criar | AT-02, AT-05, AT-07, AT-18 | 30 |
| 34 | `tests/test_daily_number.py` | Criar | AT-06 e CS-04 | 30 |
| 35 | `tests/test_order_flow.py` | Criar | AT-08 a AT-11, 404 | 30 |
| 36 | `tests/test_concurrency.py` | Criar | AT-12, CS-05 | 30 |
| 37 | `tests/test_panel_api.py` | Criar | AT-13 e `avg_prep_seconds` | 30 |
| 38 | `tests/test_pages.py` | Criar | CS-01 (rotas devolvem 200 e HTML) | 30 |
| 39 | `tests/test_design_tokens.py` | Criar | RNF-06 e RNF-07 | 18 a 29 |

Nenhum ciclo de dependência: `domain` e `config` não importam nada do projeto; `models` e `services` dependem só deles; `api` e `pages` ficam no topo.

---

## 7. Padrões de código

### 7.1 `docker-compose.yml`

```yaml
services:
  db:
    image: postgres:16
    environment:
      POSTGRES_USER: totem
      POSTGRES_PASSWORD: totem
      POSTGRES_DB: totem
    volumes:
      - pgdata:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U totem -d totem"]
      interval: 3s
      timeout: 3s
      retries: 15

  app:
    build: .
    environment:
      DATABASE_URL: postgresql+psycopg://totem:totem@db:5432/totem
      APP_TIMEZONE: America/Sao_Paulo
    ports:
      - "8000:8000"
    depends_on:
      db:
        condition: service_healthy

volumes:
  pgdata:
```

A porta do banco não é publicada, para não colidir com um PostgreSQL local. As credenciais são só para a demo.

### 7.2 `Dockerfile`

```dockerfile
FROM python:3.12-slim
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1
WORKDIR /code
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 7.3 Estados e transições (`domain.py`)

```python
from enum import Enum


class OrderStatus(str, Enum):
    RECEBIDO = "recebido"
    PREPARANDO = "preparando"
    PRONTO = "pronto"
    ENTREGUE = "entregue"
    CANCELADO = "cancelado"


NEXT = {
    OrderStatus.RECEBIDO: OrderStatus.PREPARANDO,
    OrderStatus.PREPARANDO: OrderStatus.PRONTO,
    OrderStatus.PRONTO: OrderStatus.ENTREGUE,
}
CANCELABLE = {OrderStatus.RECEBIDO, OrderStatus.PREPARANDO}
ACTIVE = (OrderStatus.RECEBIDO, OrderStatus.PREPARANDO, OrderStatus.PRONTO)


class OrderNotFound(Exception): ...
class ProductNotFound(Exception): ...
class OrderLocked(Exception): ...        # linha em uso por outra transação
class StaleState(Exception): ...         # from_state diferente do atual
class InvalidTransition(Exception): ...  # avançar ou cancelar fora das regras
```

### 7.4 Modelos (`models.py`)

```python
class Order(Base):
    __tablename__ = "orders"
    __table_args__ = (
        UniqueConstraint("order_date", "daily_number"),
        Index("ix_orders_status_id", "status", "id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    order_date: Mapped[date]
    daily_number: Mapped[int]
    status: Mapped[OrderStatus] = mapped_column(
        Enum(OrderStatus, native_enum=False, length=20,
             values_callable=lambda e: [m.value for m in e])
    )
    total_cents: Mapped[int]
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    ready_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # selectin: um SELECT ... FOR UPDATE com JOIN externo falha no PostgreSQL
    items: Mapped[list["OrderItem"]] = relationship(
        lazy="selectin", order_by="OrderItem.id"
    )

    @property
    def number(self) -> str:
        return f"{self.daily_number:03d}"
```

`OrderItem` guarda `unit_price_cents` e tem `relationship(lazy="joined")` para `Product` (nome e ícone na resposta). O `Session` é criado com `expire_on_commit=False`.

### 7.5 Número do dia e criação (`services.py`)

```python
from sqlalchemy.dialects.postgresql import insert as pg_insert


def next_daily_number(db: Session, day: date) -> int:
    stmt = (
        pg_insert(DailyCounter)
        .values(day=day, last_number=1)
        .on_conflict_do_update(
            index_elements=[DailyCounter.day],
            set_={"last_number": DailyCounter.last_number + 1},
        )
        .returning(DailyCounter.last_number)
    )
    return db.execute(stmt).scalar_one()


def create_order(db: Session, items: list[tuple[int, int]], day: date) -> Order:
    wanted: dict[int, int] = {}
    for product_id, qty in items:                      # soma itens repetidos
        wanted[product_id] = wanted.get(product_id, 0) + qty

    products = {
        p.id: p
        for p in db.scalars(select(Product).where(Product.id.in_(wanted)))
    }
    missing = set(wanted) - set(products)
    if missing:
        raise ProductNotFound(min(missing))

    number = next_daily_number(db, day)                # trava a linha do dia
    now = utcnow()
    order = Order(
        order_date=day, daily_number=number, status=OrderStatus.RECEBIDO,
        total_cents=sum(products[i].price_cents * q for i, q in wanted.items()),
        created_at=now, updated_at=now,
    )
    order.items = [
        OrderItem(product_id=i, quantity=q, unit_price_cents=products[i].price_cents)
        for i, q in wanted.items()
    ]
    db.add(order)
    db.commit()                                        # solta o contador
    return order
```

### 7.6 Avançar e cancelar (`services.py`)

```python
def _lock_order(db: Session, order_id: int) -> Order:
    order = db.execute(
        select(Order).where(Order.id == order_id).with_for_update(skip_locked=True)
    ).scalar_one_or_none()
    if order is None:
        if db.scalar(select(Order.id).where(Order.id == order_id)) is None:
            raise OrderNotFound(order_id)
        raise OrderLocked(order_id)        # existe, mas outra transação a segura
    return order


def advance_order(db: Session, order_id: int, from_state: OrderStatus) -> Order:
    order = _lock_order(db, order_id)
    if order.status != from_state:
        raise StaleState(order_id)
    target = NEXT.get(order.status)
    if target is None:
        raise InvalidTransition(order_id)
    now = utcnow()
    order.status, order.updated_at = target, now
    if target is OrderStatus.PRONTO:
        order.ready_at = now
    db.commit()
    return order
```

`cancel_order` segue o mesmo molde: `_lock_order`, confere `order.status in CANCELABLE` (senão `InvalidTransition`) e grava `CANCELADO`. Se `_lock_order` lançar exceção, a sessão é encerrada pelo `get_db` e o bloqueio some com ela.

### 7.7 Carga do cardápio (`seed.py`)

```python
MENU = [
    ("Lanches", "Hambúrguer clássico", "🍔", 2490),
    ("Lanches", "X-Bacon", "🥓", 2990),
    ("Lanches", "Cachorro-quente", "🌭", 1690),
    ("Lanches", "Batata frita", "🍟", 1490),
    ("Crepes", "Crepe de queijo e presunto", "🥞", 1990),
    ("Crepes", "Crepe de chocolate com morango", "🍓", 2190),
    ("Bebidas", "Suco de laranja", "🍊", 990),
    ("Bebidas", "Suco de abacaxi com hortelã", "🍍", 1090),
    ("Bebidas", "Milk shake de chocolate", "🥤", 1890),
    ("Sobremesas", "Sundae de morango", "🍦", 1290),
]


def seed_products(db: Session) -> None:
    rows = [
        {"category": c, "name": n, "icon": i, "price_cents": p, "position": pos}
        for pos, (c, n, i, p) in enumerate(MENU)
    ]
    db.execute(pg_insert(Product).values(rows).on_conflict_do_nothing(index_elements=["name"]))
    db.commit()
```

`main.py` chama `Base.metadata.create_all(engine)` e `seed_products` dentro do `lifespan`.

### 7.8 Rotas (`api.py`)

```python
@router.post("/pedidos/{order_id}/avancar", response_model=OrderOut)
def advance(order_id: int, body: AdvanceIn, db: Session = Depends(get_db)):
    try:
        return services.advance_order(db, order_id, body.from_state)
    except OrderNotFound:
        raise HTTPException(404, "Pedido não encontrado.")
    except OrderLocked:
        raise HTTPException(409, "Outro atendente está mudando este pedido. Atualize a lista.")
    except StaleState:
        raise HTTPException(409, "O pedido já mudou de estado. Atualize a lista.")
    except InvalidTransition:
        raise HTTPException(409, "Este pedido não pode avançar.")
```

As rotas são `def` e não `async def`, para rodarem em threads (D-02).

### 7.9 Tailwind e tokens (`tailwind-config.js`)

```js
tailwind.config = {
  theme: {
    extend: {
      colors: {
        preto: "var(--cor-preto)",
        laranja: "var(--cor-laranja)",
        amarelo: "var(--cor-amarelo)",
        vermelho: "var(--cor-vermelho)",
        superficie: "var(--cor-superficie)",
        "superficie-alta": "var(--cor-superficie-alta)",
        borda: "var(--cor-borda)",
        suave: "var(--cor-texto-suave)",
        "vermelho-claro": "var(--cor-vermelho-claro)",
      },
      borderRadius: { botao: "var(--raio-botao)", cartao: "var(--raio-cartao)" },
      minHeight: { toque: "var(--toque-minimo)" },
    },
  },
};
```

Cada página carrega, nesta ordem: `tokens.css`, `components.css`, o script do CDN do Tailwind e depois `tailwind-config.js`.

### 7.10 Consulta encadeada (`common.js`)

```js
export function poll(fn, ms = POLL_MS) {
  const tick = async () => {
    try { await fn(); } catch (e) { /* a tela mostra a faixa de conexão */ }
    setTimeout(tick, ms);
  };
  tick();
}

export async function api(path, options = {}) {
  const res = await fetch(`/api${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw Object.assign(new Error(body.detail || "Erro inesperado."), { status: res.status });
  }
  return res.json();
}

const brl = new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" });
export const formatBRL = (cents) => brl.format(cents / 100);
```

### 7.11 Detecção de pedido pronto (`painel.js`)

```js
const announced = new Set();
let firstLoad = true;
const queue = [];

async function refresh() {
  const panel = await api("/painel");
  render(panel);
  for (const o of panel.ready) {
    if (!announced.has(o.id)) {
      announced.add(o.id);
      if (!firstLoad) queue.push(o);        // na 1ª carga só marca como visto
    }
  }
  firstLoad = false;
  playNext();                               // um destaque por vez, 6 s cada
}

function speak(number) {
  if (!soundEnabled) return;
  const u = new SpeechSynthesisUtterance(`Pedido ${Number(number)}, pronto`);
  u.lang = "pt-BR";
  speechSynthesis.speak(u);
}
```

---

## 8. Estratégia de testes

Todos os testes de API e de serviço rodam em PostgreSQL real (D-08), com `TRUNCATE ... RESTART IDENTITY CASCADE` entre os testes e o cardápio recarregado pela fixture. O `client` usa `TestClient(app)` **sem** `with`, para o `lifespan` não tocar o banco real.

| Tipo | Escopo | Ferramenta |
|---|---|---|
| Unitário | `domain.py`: mapa `NEXT` e `CANCELABLE` | pytest |
| Serviço | Numeração, total, avanço, cancelamento, painel | pytest + sessão real |
| API | Rotas, códigos HTTP, mensagens | pytest + `TestClient` |
| Concorrência | Threads com sessões próprias e `Barrier` | pytest |
| Estático | Páginas devolvem 200; ausência de hexadecimal fora de `tokens.css` | pytest |
| Interface | Fluxos de tela e temporizadores | Manual ou Playwright no `/build` |

### 8.1 Cobertura dos testes de aceitação

| Teste | Onde é verificado |
|---|---|
| AT-01 | Backend: `test_menu_api` (4 lanches, ordem das categorias). Tela: Playwright |
| AT-02 | `test_order_creation` (total 5970 centavos). Tela: Playwright |
| AT-03 | Playwright |
| AT-04 | `test_order_creation` (201, número, estado). Tela: Playwright |
| AT-05, AT-06 | `test_daily_number` (datas explícitas, sem esperar a virada) |
| AT-07 | `test_order_creation` (422 com lista vazia). Botão desabilitado: Playwright |
| AT-08 | `test_order_flow` |
| AT-09, AT-10, AT-11 | `test_order_flow` |
| AT-12 | `test_concurrency`: duas threads com `Barrier`; e uma sessão segurando a linha enquanto outra tenta avançar (409 imediato, sem bloquear) |
| AT-13 | `test_panel_api` |
| AT-14 | Playwright, com um pedido avançado pela API (a voz é verificada pelo destaque na tela e por um espião em `speechSynthesis.speak`) |
| AT-15, AT-16 | Playwright, aguardando 30 s e 8 s |
| AT-17 | `test_seed` |
| AT-18 | `test_order_creation` (corpo com `total` falso é ignorado) |
| AT-19 | Playwright (rótulo e ícone presentes em cada estado) |
| CS-01 | `test_pages` e `docker compose up` do zero no `/build` |
| CS-02 | Playwright (contagem de toques) |
| CS-03 | Playwright (cozinha avança e painel muda em até 4 s) |
| CS-04 | `test_daily_number`: 20 threads, números 1 a 20 sem repetição |
| CS-05 | `test_concurrency` |
| CS-06 | `test_seed` (seed executado duas vezes) |
| CS-07 | Suíte inteira verde |

### 8.2 Casos extras

- Itens repetidos do mesmo produto são somados.
- Quantidade 0 e 21 recebem 422.
- `product_id` inexistente recebe 422.
- `from_state` desatualizado recebe 409 e o estado não muda.
- Segunda chamada de `avancar` após commit (sem corrida) recebe 409.
- Pedido Cancelado e Entregue fora das listas padrão.
- `avg_prep_seconds` nulo sem pedidos prontos e calculado com `ready_at` conhecido.

---

## 9. Verificação do DESIGN

```text
[x] Diagrama de arquitetura claro
[x] Decisões com contexto, escolha e alternativas (D-01 a D-10)
[x] Manifesto completo (39 arquivos) e sem ciclos
[x] Padrões de código prontos para copiar
[x] Estratégia de testes cobre todos os AT e CS do DEFINE
[x] Ajustes ao DEFINE listados na seção 1.4
```

## 10. Próximo passo

```bash
/tecspec:workflow:build .claude/sdd/features/DESIGN_TOTEM_ATENDIMENTO.md
```

---

**Revisão:** shipped e arquivado em 2026-10-07.
