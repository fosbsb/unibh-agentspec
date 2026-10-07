# DESIGN: Totem de Atendimento

> Arquitetura e especificação técnica (Fase 2)

## Metadados

| Atributo | Valor |
|---|---|
| **Feature** | TOTEM_ATENDIMENTO |
| **Data** | 2026-10-07 |
| **Origem** | `.claude/sdd/features/DEFINE_TOTEM_ATENDIMENTO.md` |
| **Status** | Pronto para /build |

---

## 1. Visão geral

Uma aplicação FastAPI de processo único serve a API REST e as três telas estáticas. O PostgreSQL 16 roda em um container separado. Nenhuma tela tem build: cada uma é um HTML com Tailwind via CDN e módulos JavaScript nativos.

```text
                    docker compose up
      ┌──────────────────────────────────────────────┐
      │                                              │
      │   ┌─────────── app (FastAPI, :8000) ───────┐ │
      │   │                                        │ │
Totem ─────▶ GET /totem ─┐   routers/              │ │
(toque)   │             ├─▶ ├─ produtos.py          │ │
Cozinha ───▶ GET /cozinha┤   └─ pedidos.py          │ │
(mouse)   │             │        │                  │ │
Painel ────▶ GET /painel ┘        ▼                  │ │
(TV)      │   StaticFiles     services/pedidos.py   │ │
          │   /static/*       (regras de negócio)   │ │
          │                        │                 │ │
          │                        ▼  SQLAlchemy     │ │
          │                   models.py / seed.py    │ │
          │   └────────────────────┬─────────────────┘ │
          │                        │ psycopg 3         │
          │   ┌────────────────────▼───────────────┐   │
          │   │ db (PostgreSQL 16) + volume pgdata │   │
          │   └────────────────────────────────────┘   │
          └──────────────────────────────────────────────┘
```

### Componentes

| Componente | Responsabilidade |
|---|---|
| `routers/` | Valida entrada, traduz exceções de domínio em HTTP, não contém regra de negócio |
| `services/pedidos.py` | Criar pedido, numeração diária, avançar estado, listar fila, tempo médio |
| `models.py` | Tabelas `produtos`, `pedidos`, `itens_pedido`, `contador_dia` |
| `seed.py` | Carga idempotente dos 10 produtos |
| `relogio.py` | Única fonte de "hoje" e "agora" (fuso America/Sao_Paulo), substituível nos testes |
| `static/js/api.js` | `fetch` com tratamento de erro, formatação de preço, polling |
| `static/*.html` + `js/*.js` | Uma tela por arquivo, sem estado compartilhado entre telas |

### Fluxo de dados

```text
Totem:    cardápio ──GET /api/produtos──▶ carrinho (memória) ──POST /api/pedidos──▶ número
Cozinha:  loop 2 s ──GET /api/pedidos──▶ fila ──POST /api/pedidos/{id}/avancar──▶ novo estado
Painel:   loop 2 s ──GET /api/pedidos──▶ listas Preparando / Pronto + detecção de "recém-pronto"
```

---

## 2. Decisões de arquitetura

### ADR-01: Polling de 2 s para atualizar cozinha e painel

| | |
|---|---|
| **Status** | Aceita (herdada do BRAINSTORM) |
| **Escolha** | `GET /api/pedidos` a cada 2 s, com o próximo ciclo agendado **depois** que o anterior termina (`setTimeout` encadeado, não `setInterval`) |
| **Motivo** | Simplicidade e recuperação automática de falhas de rede. O encadeamento evita requisições empilhadas se o servidor ficar lento |
| **Rejeitadas** | SSE e WebSocket: complexidade sem ganho para três telas |
| **Consequência** | Latência de até 2 s. Requisições repetidas sem mudança |

### ADR-02: Concorrência no avanço de estado

| | |
|---|---|
| **Status** | Aceita |
| **Contexto** | RF-10 e RF-11. Dois atendentes podem tocar no mesmo botão. Só bloquear a linha não basta: se o atendente A avança Recebido→Preparando e o atendente B, com a tela desatualizada, toca em "Iniciar" depois, o servidor avançaria Preparando→Pronto sem que ninguém tenha preparado o pedido |
| **Escolha** | O cliente envia o estado que viu (`estado_atual`). O servidor bloqueia a linha com `SELECT ... FOR UPDATE SKIP LOCKED` e só avança se o estado gravado for igual ao enviado. Caso contrário, devolve 409 |
| **Linha bloqueada por outra transação** | `SKIP LOCKED` não devolve a linha. O serviço distingue "não existe" (404) de "existe e está em uso" (409) com uma segunda consulta simples |
| **Rejeitadas** | (a) Só `FOR UPDATE` sem `estado_atual`: o problema acima. (b) Controle otimista com coluna `versao`: mais campos para o mesmo efeito |
| **Consequência** | O contrato de `avancar` ganha o campo `estado_atual` (refinamento de RF-09/RF-10, ver seção 10) |

### ADR-03: Numeração diária por contador atômico

| | |
|---|---|
| **Status** | Aceita |
| **Escolha** | Tabela `contador_dia (data PK, ultimo)` com `INSERT ... ON CONFLICT (data) DO UPDATE SET ultimo = ultimo + 1 RETURNING ultimo`, na mesma transação que cria o pedido |
| **Motivo** | O upsert é atômico e a linha fica bloqueada até o commit, o que serializa criações simultâneas sem tentativas repetidas. Se a criação falhar, o rollback desfaz o contador e não sobram buracos na sequência |
| **Rejeitadas** | `MAX(numero)+1` com retry na violação da restrição única (mais código e corrida visível). Sequence do PostgreSQL (não reinicia por dia sem tarefa agendada) |
| **Consequência** | Quarta tabela, além das três do DEFINE. O número é guardado como inteiro e formatado com `zfill(3)`. Acima de 999 o número ganha o 4º dígito, sem erro (improvável numa demonstração) |

### ADR-04: SQLAlchemy síncrono, psycopg 3 e um único worker

| | |
|---|---|
| **Status** | Aceita |
| **Escolha** | SQLAlchemy 2.0 síncrono com `psycopg[binary]`, rotas `def` (FastAPI executa em threadpool). `uvicorn` com 1 worker. Tabelas por `create_all` na subida |
| **Motivo** | Menos conceitos para a oficina, e o volume é de uma lanchonete. Um worker evita corrida entre `create_all` e a carga do cardápio na subida |
| **Rejeitadas** | `asyncpg` e sessão assíncrona (mais conceitos sem ganho). Alembic (já excluído no escopo) |
| **Consequência** | A carga do cardápio ainda usa `ON CONFLICT DO NOTHING`, então reinícios e réplicas futuras não duplicam |

### ADR-05: Testes contra PostgreSQL real, em banco separado

| | |
|---|---|
| **Status** | Aceita |
| **Motivo** | `SKIP LOCKED`, o upsert do contador e `AVG(pronto_em - iniciado_em)` são recursos do PostgreSQL. SQLite daria falso positivo |
| **Escolha** | O `conftest.py` cria o banco `totem_test` no mesmo servidor `db` e limpa as tabelas entre testes. O banco de demonstração nunca é tocado |
| **Execução** | `docker compose run --rm app pytest` |
| **Consequência** | Os testes exigem o serviço `db` de pé |

### ADR-06: Preço em centavos, com cópia no item

| | |
|---|---|
| **Status** | Aceita |
| **Escolha** | `preco_centavos` inteiro. `itens_pedido.preco_unitario_centavos` copia o preço na criação. O total é `sum(qtd × preço)` calculado no servidor (RF-07, CS-06) |
| **Motivo** | Evita erro de ponto flutuante e mantém pedidos antigos estáveis se o cardápio mudar |
| **Formatação** | Só no frontend: `Intl.NumberFormat('pt-BR', {style:'currency', currency:'BRL'})` |

### ADR-07: Frontend sem build, Tailwind mapeado para os tokens

| | |
|---|---|
| **Status** | Aceita |
| **Escolha** | Cada tela é um HTML com `<script src="https://cdn.tailwindcss.com">`, seguido de `tailwind-config.js`, que mapeia as cores para `var(--cor-*)`. O JavaScript usa módulos ES (`<script type="module">`). O DOM é montado com `createElement` e `textContent`, nunca com `innerHTML` de dados do servidor |
| **Motivo** | Cumpre RNF-03 e a regra 9 do design system (telas nunca usam hexadecimal direto). `textContent` elimina injeção de HTML sem esforço |
| **Rejeitadas** | Framework com build (viola o requisito). Tailwind vendorizado em arquivo (a suposição de internet foi aceita; vira plano B) |
| **Consequência** | Primeira carga exige internet para o CDN. A fonte Inter não é carregada: vale o fallback `"Segoe UI", system-ui` do design system |

### ADR-08: "Recém-pronto" detectado no painel

| | |
|---|---|
| **Status** | Aceita |
| **Escolha** | O painel guarda os ids de pedidos Prontos já vistos. Um id Pronto novo, depois da primeira carga, entra numa fila de destaques exibidos um por vez (6 s cada) com voz |
| **Motivo** | Não exige campo nem rota extra. A primeira carga é ignorada para o painel não anunciar pedidos antigos ao abrir |
| **Consequência** | Um pedido que passa de Preparando a Entregue dentro de um mesmo ciclo de 2 s nunca é anunciado (aceitável) |

### ADR-09: Ordem de chegada por `(data_pedido, numero)`

| | |
|---|---|
| **Status** | Aceita |
| **Motivo** | O número nasce de um contador serializado, então é monotônico dentro do dia. Ordenar por ele é determinístico, ao contrário de `criado_em`, que em transações simultâneas pode empatar |

---

## 3. Modelo de dados

```text
produtos            pedidos                      itens_pedido
─────────           ──────────────────           ───────────────────────────
id PK               id PK                        id PK
nome UNIQUE         numero INT                   pedido_id FK → pedidos
categoria           data_pedido DATE             produto_id FK → produtos
icone               estado                       quantidade (1..99)
preco_centavos      criado_em TIMESTAMPTZ        preco_unitario_centavos
                    iniciado_em TIMESTAMPTZ ∅
contador_dia        pronto_em TIMESTAMPTZ ∅
────────────        entregue_em TIMESTAMPTZ ∅
data DATE PK        UNIQUE (data_pedido, numero)
ultimo INT          CHECK estado IN (recebido, preparando, pronto, entregue)
```

`produtos.preco_centavos > 0` e `itens_pedido.quantidade BETWEEN 1 AND 99` também têm `CHECK`.

### Máquina de estados

```text
 recebido ──"Iniciar"──▶ preparando ──"Marcar pronto"──▶ pronto ──"Entregar"──▶ entregue
              │                           │                         │
         iniciado_em                  pronto_em                 entregue_em
```

Sem retorno, sem salto e sem cancelamento.

---

## 4. Contrato da API

Todos os textos de erro em português. Corpo de erro: `{"detail": "..."}`.

### `GET /api/produtos` → 200

```json
{"categorias": [
  {"nome": "Lanches", "produtos": [
    {"id": 1, "nome": "Hambúrguer clássico", "icone": "🍔", "preco_centavos": 2490}
  ]}
]}
```

As categorias seguem a ordem do menor id de produto: Lanches, Crepes, Bebidas, Sobremesas.

### `POST /api/pedidos` → 201

```json
// requisição
{"itens": [{"produto_id": 1, "quantidade": 2}, {"produto_id": 7, "quantidade": 1}]}
// resposta (PedidoOut)
{"id": 15, "numero": "001", "estado": "recebido",
 "criado_em": "2026-10-07T12:30:00-03:00",
 "itens": [{"produto_id": 1, "nome": "Hambúrguer clássico", "icone": "🍔",
            "quantidade": 2, "preco_unitario_centavos": 2490, "subtotal_centavos": 4980}],
 "total_centavos": 5970}
```

| Caso | Resposta |
|---|---|
| `itens` vazio, quantidade fora de 1..99, tipo inválido | 422 |
| `produto_id` inexistente | 422 com `detail` "Produto inexistente: 99" |
| Campo extra como `total` | Ignorado |

### `GET /api/pedidos` → 200

```json
{"pedidos": [ /* PedidoOut + iniciado_em, pronto_em; só recebido, preparando e pronto, em ordem de chegada */ ],
 "tempo_medio_preparo_segundos": 300}
```

`tempo_medio_preparo_segundos` é `null` se não houver pedido pronto hoje.

### `POST /api/pedidos/{id}/avancar` → 200

```json
{"estado_atual": "recebido"}
```

| Caso | Resposta |
|---|---|
| Sucesso | 200 com `PedidoOut` no novo estado |
| `estado_atual` diferente do gravado, pedido já Entregue ou linha em uso por outra transação | 409 "O pedido mudou de estado. Atualize a tela." |
| Pedido inexistente | 404 |
| `estado_atual` não é um dos quatro estados | 422 |

### Páginas

| Rota | Retorno |
|---|---|
| `/` | Redireciona para `/totem` |
| `/totem`, `/cozinha`, `/painel` | O HTML correspondente |
| `/static/*` | Arquivos estáticos |

---

## 5. Manifesto de arquivos

| # | Arquivo | Ação | Propósito | Depende de | Agente |
|---|---|---|---|---|---|
| 1 | `requirements.txt` | Criar | fastapi, uvicorn, sqlalchemy, psycopg[binary], tzdata, pytest, httpx | — | docker-ops |
| 2 | `Dockerfile` | Criar | `python:3.12-slim`, instala dependências, `uvicorn` com 1 worker | 1 | docker-ops |
| 3 | `docker-compose.yml` | Criar | Serviços `db` e `app`, volume, healthcheck | 2 | docker-ops |
| 4 | `.dockerignore` | Criar | Exclui `.git`, `.claude`, `specs`, `roteiro` | — | docker-ops |
| 5 | `pytest.ini` | Criar | `testpaths = tests`, `pythonpath = .` | — | test-generator |
| 6 | `app/__init__.py` | Criar | Pacote | — | fastapi-architect |
| 7 | `app/config.py` | Criar | `DATABASE_URL` do ambiente | — | fastapi-architect |
| 8 | `app/relogio.py` | Criar | `agora()` e `hoje()` em America/Sao_Paulo | — | fastapi-architect |
| 9 | `app/database.py` | Criar | Engine, `SessionLocal`, `get_session` | 7 | sqlalchemy-specialist |
| 10 | `app/models.py` | Criar | Quatro tabelas e restrições | 9 | sqlalchemy-specialist |
| 11 | `app/schemas.py` | Criar | Modelos Pydantic de entrada e saída | 10 | fastapi-architect |
| 12 | `app/seed.py` | Criar | Os 10 produtos e `carregar_cardapio` | 10 | sqlalchemy-specialist |
| 13 | `app/services/__init__.py` | Criar | Pacote | — | fastapi-architect |
| 14 | `app/services/pedidos.py` | Criar | Regras: criar, numerar, avançar, listar, média | 8, 10, 11 | sqlalchemy-specialist |
| 15 | `app/routers/__init__.py` | Criar | Pacote | — | fastapi-architect |
| 16 | `app/routers/produtos.py` | Criar | `GET /api/produtos` | 9, 11 | fastapi-architect |
| 17 | `app/routers/pedidos.py` | Criar | Rotas de pedidos e tradução de exceções | 14 | fastapi-architect |
| 18 | `app/main.py` | Criar | App, lifespan (`create_all` + seed), rotas de página, `StaticFiles` | 12, 16, 17 | fastapi-architect |
| 19 | `app/static/css/tokens.css` | Criar | Tokens do design system (seção 9 do documento) e utilitários de movimento | — | design-system-auditor |
| 20 | `app/static/js/tailwind-config.js` | Criar | Mapeia classes Tailwind para `var(--cor-*)` | 19 | web-design-specialist |
| 21 | `app/static/js/api.js` | Criar | `getJSON`, `postJSON`, `formatarPreco`, `poll`, helper `h()` de DOM | — | web-design-specialist |
| 22 | `app/static/totem.html` | Criar | Esqueleto das telas do totem | 19, 20 | web-design-specialist |
| 23 | `app/static/js/totem.js` | Criar | Estados de tela, carrinho, timers de 30 s e 8 s | 21, 22 | web-design-specialist |
| 24 | `app/static/cozinha.html` | Criar | Esqueleto da fila | 19, 20 | web-design-specialist |
| 25 | `app/static/js/cozinha.js` | Criar | Polling, botões, tratamento de 409 | 21, 24 | web-design-specialist |
| 26 | `app/static/painel.html` | Criar | Esqueleto do painel | 19, 20 | web-design-specialist |
| 27 | `app/static/js/painel.js` | Criar | Polling, destaque, voz, toque de ativação do áudio | 21, 26 | web-design-specialist |
| 28 | `tests/conftest.py` | Criar | Banco `totem_test`, limpeza, `client`, relógio falso | 10, 18 | test-generator |
| 29 | `tests/test_cardapio.py` | Criar | AT-010, AT-011 | 28 | test-generator |
| 30 | `tests/test_pedidos.py` | Criar | AT-001 a AT-005 | 28 | test-generator |
| 31 | `tests/test_estados.py` | Criar | AT-006 a AT-008 | 28 | test-generator |
| 32 | `tests/test_fila.py` | Criar | AT-009, AT-012 | 28 | test-generator |
| 33 | `specs/DESIGN_SYSTEM.md` | Modificar | v1.1.0: tela de revisão, sem Cancelado. **Já aplicado nesta fase** | — | design-system-auditor |
| 34 | `README.md` | Modificar | Seção "Como rodar o totem": `docker compose up`, URLs, `pytest` | 3 | code-documenter |

**Ordem de build:** infraestrutura (1–5) → backend (6–18) → testes (28–32, rodando contra o backend) → frontend (19–27) → README.

Não há dependência circular: `routers → services → models → database → config`.

---

## 6. Padrões de código

### 6.1 `docker-compose.yml`

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
      interval: 2s
      timeout: 3s
      retries: 15
  app:
    build: .
    environment:
      DATABASE_URL: postgresql+psycopg://totem:totem@db:5432/totem
    ports:
      - "8000:8000"
    depends_on:
      db:
        condition: service_healthy
volumes:
  pgdata:
```

### 6.2 Modelos (trechos)

```python
class Pedido(Base):
    __tablename__ = "pedidos"
    __table_args__ = (
        UniqueConstraint("data_pedido", "numero"),
        CheckConstraint("estado IN ('recebido','preparando','pronto','entregue')"),
    )
    id: Mapped[int] = mapped_column(primary_key=True)
    numero: Mapped[int]
    data_pedido: Mapped[date]
    estado: Mapped[str] = mapped_column(String(12), default="recebido")
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=relogio.agora)
    iniciado_em: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    pronto_em: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    entregue_em: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    itens: Mapped[list["ItemPedido"]] = relationship(lazy="selectin", order_by="ItemPedido.id")
```

`ItemPedido.produto` usa `lazy="joined"`. `Pedido.itens` não usa `joined` porque `FOR UPDATE` não combina com `LEFT JOIN`.

### 6.3 Numeração (ADR-03)

```python
def proximo_numero(session: Session, dia: date) -> int:
    stmt = (
        pg_insert(ContadorDia)
        .values(data=dia, ultimo=1)
        .on_conflict_do_update(index_elements=[ContadorDia.data],
                               set_={"ultimo": ContadorDia.ultimo + 1})
        .returning(ContadorDia.ultimo)
    )
    return session.execute(stmt).scalar_one()
```

### 6.4 Criar pedido

```python
def criar_pedido(session: Session, itens: list[ItemEntrada]) -> Pedido:
    ids = {i.produto_id for i in itens}
    produtos = {p.id: p for p in session.scalars(select(Produto).where(Produto.id.in_(ids)))}
    faltando = ids - produtos.keys()
    if faltando:
        raise ProdutoInexistente(sorted(faltando)[0])
    hoje = relogio.hoje()
    pedido = Pedido(
        data_pedido=hoje,
        numero=proximo_numero(session, hoje),  # por último: segura o bloqueio o mínimo possível
        itens=[ItemPedido(produto_id=i.produto_id, quantidade=i.quantidade,
                          preco_unitario_centavos=produtos[i.produto_id].preco_centavos)
               for i in itens],
    )
    session.add(pedido)
    session.commit()
    return pedido
```

### 6.5 Avançar estado (ADR-02)

```python
PROXIMO = {"recebido": "preparando", "preparando": "pronto", "pronto": "entregue"}
CARIMBO = {"preparando": "iniciado_em", "pronto": "pronto_em", "entregue": "entregue_em"}

def avancar(session: Session, pedido_id: int, estado_atual: str) -> Pedido:
    pedido = session.scalars(
        select(Pedido).where(Pedido.id == pedido_id).with_for_update(skip_locked=True)
    ).one_or_none()
    if pedido is None:
        existe = session.scalar(select(Pedido.id).where(Pedido.id == pedido_id))
        raise ConflitoEstado() if existe else PedidoNaoEncontrado()
    if pedido.estado != estado_atual or pedido.estado not in PROXIMO:
        raise ConflitoEstado()
    novo = PROXIMO[pedido.estado]
    pedido.estado = novo
    setattr(pedido, CARIMBO[novo], relogio.agora())
    session.commit()
    return pedido
```

O router captura `ConflitoEstado` → 409 e `PedidoNaoEncontrado` → 404. Os dois tipos herdam de uma exceção de domínio própria, sem importar nada do FastAPI no serviço.

### 6.6 Fila e tempo médio

```python
def listar_fila(session: Session) -> list[Pedido]:
    stmt = (select(Pedido).where(Pedido.estado != "entregue")
            .order_by(Pedido.data_pedido, Pedido.numero))
    return list(session.scalars(stmt))

def tempo_medio_preparo(session: Session) -> int | None:
    media = session.scalar(
        select(func.avg(func.extract("epoch", Pedido.pronto_em - Pedido.iniciado_em)))
        .where(Pedido.data_pedido == relogio.hoje(), Pedido.pronto_em.is_not(None))
    )
    return None if media is None else round(media)
```

### 6.7 Carga do cardápio

```python
def carregar_cardapio(session: Session) -> None:
    stmt = pg_insert(Produto).values(CARDAPIO).on_conflict_do_nothing(index_elements=["nome"])
    session.execute(stmt)
    session.commit()
```

`CARDAPIO` é a lista de dicionários com os 10 produtos da seção 8 do design system (nome, categoria, ícone, `preco_centavos`), na ordem da tabela.

### 6.8 Lifespan e páginas

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(engine)
    with SessionLocal() as session:
        carregar_cardapio(session)
    yield

app = FastAPI(lifespan=lifespan)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

@app.get("/", include_in_schema=False)
def raiz():
    return RedirectResponse("/totem")

for nome in ("totem", "cozinha", "painel"):
    app.add_api_route(f"/{nome}", lambda n=nome: FileResponse(STATIC_DIR / f"{n}.html"),
                      include_in_schema=False)
```

### 6.9 Tailwind mapeado para os tokens

```html
<link rel="stylesheet" href="/static/css/tokens.css">
<script src="https://cdn.tailwindcss.com"></script>
<script src="/static/js/tailwind-config.js"></script>
```

```js
// tailwind-config.js
tailwind.config = {
  theme: { extend: { colors: {
    preto: 'var(--cor-preto)', laranja: 'var(--cor-laranja)', amarelo: 'var(--cor-amarelo)',
    vermelho: 'var(--cor-vermelho)', superficie: 'var(--cor-superficie)',
    'superficie-alta': 'var(--cor-superficie-alta)', borda: 'var(--cor-borda)',
    suave: 'var(--cor-texto-suave)', 'vermelho-claro': 'var(--cor-vermelho-claro)',
  }}}
};
```

### 6.10 `api.js`

```js
export const formatarPreco = (c) =>
  new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(c / 100);

export async function requisitar(url, opcoes) {
  const r = await fetch(url, opcoes);
  const corpo = await r.json().catch(() => ({}));
  if (!r.ok) throw Object.assign(new Error(corpo.detail || 'Erro'), { status: r.status });
  return corpo;
}

export function poll(fn, ms = 2000) {
  let parar = false;
  (async function ciclo() {
    try { await fn(); } catch (e) { console.warn(e); }
    if (!parar) setTimeout(ciclo, ms);
  })();
  return () => { parar = true; };
}

export function h(tag, atributos = {}, ...filhos) {
  const el = Object.assign(document.createElement(tag), atributos);
  el.append(...filhos);
  return el;
}
```

### 6.11 Totem: máquina de telas e timers

```js
const TELAS = ['inicio', 'cardapio', 'revisao', 'confirmacao'];
let tela = 'inicio', carrinho = new Map(); // produto_id → {produto, quantidade}
let timerOciosidade, timerConfirmacao;

function irPara(nova) {
  tela = nova;
  TELAS.forEach(t => document.getElementById(t).hidden = t !== nova);
}
function reiniciar() { carrinho.clear(); irPara('inicio'); }

document.addEventListener('pointerdown', () => {
  clearTimeout(timerOciosidade);
  if (tela === 'cardapio' || tela === 'revisao')
    timerOciosidade = setTimeout(reiniciar, 30_000);
});

async function finalizar(botao) {
  botao.disabled = true; botao.textContent = 'Aguarde…';
  try {
    const itens = [...carrinho.values()].map(i => ({ produto_id: i.produto.id, quantidade: i.quantidade }));
    const pedido = await requisitar('/api/pedidos', {
      method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ itens }),
    });
    mostrarConfirmacao(pedido.numero);
    timerConfirmacao = setTimeout(reiniciar, 8_000);
  } catch {
    mostrarErro('Não foi possível enviar o pedido. Toque em Tentar de novo.');
    botao.disabled = false; botao.textContent = 'Tentar de novo';
  }
}
```

O timer de 30 s é armado só nas telas `cardapio` e `revisao`. Na confirmação vale o de 8 s. Os botões mais, menos e remover ficam em linhas do carrinho de pelo menos 80x80 px.

### 6.12 Cozinha: botões por estado

```js
const ACAO = {
  recebido:   { rotulo: 'Iniciar',       classe: 'primario' },
  preparando: { rotulo: 'Marcar pronto', classe: 'primario' },
  pronto:     { rotulo: 'Entregar',      classe: 'secundario' },
};

async function avancar(pedido, botao) {
  botao.disabled = true;
  try {
    await requisitar(`/api/pedidos/${pedido.id}/avancar`, {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ estado_atual: pedido.estado }),
    });
  } catch (e) {
    if (e.status === 409) avisar('O pedido mudou de estado. A fila foi atualizada.');
    else avisar('Não foi possível atualizar. Tente de novo.');
  }
  await carregarFila(); // recarrega sempre, com sucesso ou conflito
}
```

### 6.13 Painel: destaque e voz

```js
const vistos = new Set(); let primeiraCarga = true; const fila = []; let exibindo = false;

function detectarProntos(pedidos) {
  for (const p of pedidos.filter(p => p.estado === 'pronto')) {
    if (!vistos.has(p.id)) { vistos.add(p.id); if (!primeiraCarga) fila.push(p); }
  }
  primeiraCarga = false;
  if (!exibindo) proximoDestaque();
}

function proximoDestaque() {
  const p = fila.shift();
  if (!p) { exibindo = false; esconderDestaque(); return; }
  exibindo = true;
  mostrarDestaque(p.numero);
  if (audioAtivo) {
    const fala = new SpeechSynthesisUtterance(`Pedido ${Number(p.numero)}, pronto`);
    fala.lang = 'pt-BR';
    speechSynthesis.speak(fala);
  }
  setTimeout(proximoDestaque, 6_000);
}
```

`audioAtivo` passa a `true` no primeiro toque do painel (sobreposição "Toque para ativar o som", RF-14). Sem o toque, o destaque visual funciona normalmente.

### 6.14 Fixtures de teste

```python
TEST_DB = "totem_test"

@pytest.fixture(scope="session")
def engine():
    base = make_url(settings.database_url)
    admin = create_engine(base.set(database="postgres"), isolation_level="AUTOCOMMIT")
    with admin.connect() as c:
        if not c.scalar(text("SELECT 1 FROM pg_database WHERE datname = :n"), {"n": TEST_DB}):
            c.execute(text(f"CREATE DATABASE {TEST_DB}"))
    eng = create_engine(base.set(database=TEST_DB))
    Base.metadata.create_all(eng)
    yield eng
    eng.dispose()

@pytest.fixture(autouse=True)
def banco_limpo(engine):
    with engine.begin() as c:
        c.execute(text("TRUNCATE itens_pedido, pedidos, contador_dia, produtos RESTART IDENTITY CASCADE"))
    with Session(engine) as s:
        carregar_cardapio(s)

@pytest.fixture
def client(engine):
    fabrica = sessionmaker(engine, expire_on_commit=False)
    def sessao():
        with fabrica() as s:
            yield s
    app.dependency_overrides[get_session] = sessao
    yield TestClient(app)  # sem `with`: o lifespan não roda
    app.dependency_overrides.clear()

@pytest.fixture
def dia(monkeypatch):
    """Controla 'hoje' nos serviços: dia(date(2026, 10, 8))."""
    def definir(d):
        monkeypatch.setattr(relogio, "hoje", lambda: d)
    return definir
```

Os serviços chamam `relogio.hoje()` pelo módulo (nunca `from app.relogio import hoje`), para o `monkeypatch` funcionar.

---

## 7. Estratégia de testes

| Camada | Escopo | Ferramenta |
|---|---|---|
| API e serviços | Todos os requisitos automatizáveis | pytest + `TestClient` + PostgreSQL real (ADR-05) |
| Concorrência | Corrida entre dois chamadores | `ThreadPoolExecutor` com `Barrier`, e um teste determinístico com a linha bloqueada |
| Frontend | Fluxo completo e timers | Roteiro manual de verificação (abaixo) |

### Mapa de testes automatizados

| Aceitação | Arquivo | Como |
|---|---|---|
| AT-001 | `test_pedidos.py` | Cria pedido com 2 itens. Confere 201, número "001" e total |
| AT-002 | `test_pedidos.py` | `dia()` em ontem, cria 2 pedidos. `dia()` em hoje, cria 1. Número "001" |
| AT-003, AT-004 | `test_pedidos.py` | Parametrizado: itens vazios, quantidade 0, 100, `produto_id` inexistente. 422 e nenhum registro |
| AT-005 | `test_pedidos.py` | Corpo com `total` falso. O total gravado é o calculado |
| AT-006, AT-007 | `test_estados.py` | Avança três vezes, enviando o `estado_atual` correto. Um quarto `avancar` devolve 409 |
| AT-008 | `test_estados.py` | (1) Sessão A segura `FOR UPDATE` e a chamada em B devolve 409. (2) Duas threads com `estado_atual=recebido`: exatamente um 200 e um 409, estado final Preparando |
| AT-009 | `test_fila.py` | Cria 3 pedidos, avança o primeiro até Entregue. A fila traz os outros 2, em ordem |
| AT-010 | `test_cardapio.py` | Chama `carregar_cardapio` duas vezes. Continuam 10 produtos |
| AT-011 | `test_cardapio.py` | 4 categorias na ordem esperada, 10 produtos, preços corretos |
| AT-012 | `test_fila.py` | Grava `iniciado_em`/`pronto_em` com diferenças de 4 e 6 min. Média de 300 s |

Testes adicionais, além do DEFINE: avançar com `estado_atual` defasado devolve 409 e não altera o pedido (ADR-02), `avancar` em pedido inexistente devolve 404, e `tempo_medio_preparo_segundos` é `null` sem pedidos prontos.

### Roteiro manual (AT-013 a AT-016 e CS-07)

| # | Passo | Resultado esperado |
|---|---|---|
| 1 | `docker compose up` em máquina limpa, abrir `/totem`, `/cozinha`, `/painel` | As 3 telas carregam. O cardápio mostra 10 produtos em 4 abas (CS-01) |
| 2 | No totem, montar pedido, revisar e finalizar | Número de 3 dígitos em amarelo. Volta ao início em 8 s (AT-014) |
| 3 | Deixar o totem 30 s no cardápio | Volta ao início e o carrinho esvazia (AT-013) |
| 4 | Parar o `app` e tocar em "Finalizar pedido" | Mensagem de erro com "Tentar de novo", carrinho intacto (AT-016) |
| 5 | Abrir o painel, tocar uma vez, marcar um pedido pronto na cozinha | Destaque de 6 s e voz "Pedido N, pronto" (AT-015) |
| 6 | Abrir a cozinha em duas abas e tocar "Iniciar" nas duas | A segunda mostra o aviso de conflito e a fila atualizada |
| 7 | Reduzir a janela do totem e inspecionar tamanhos | Texto ≥ 24 px, alvos ≥ 80 px (CS-07) |
| 8 | Ativar `prefers-reduced-motion` | Sem animações |

---

## 8. Rastreabilidade

| Requisito | Onde é atendido |
|---|---|
| RF-01 a RF-05 | `totem.html`, `totem.js` (6.11), `DESIGN_SYSTEM.md` 6.5.1 |
| RF-06 | ADR-03, `proximo_numero` (6.3) |
| RF-07 | `criar_pedido` (6.4), ADR-06 |
| RF-08 | `listar_fila` (6.6), ADR-09 |
| RF-09, RF-10, RF-11 | ADR-02, `avancar` (6.5), `cozinha.js` (6.12) |
| RF-12 | `painel.js`, ADR-01 |
| RF-13, RF-14 | ADR-08, `painel.js` (6.13) |
| RF-15 | `tempo_medio_preparo` (6.6) |
| RF-16 | `seed.py` (6.7), lifespan (6.8) |
| RNF-01, RNF-02 | `docker-compose.yml` (6.1) |
| RNF-03, RNF-06 | ADR-07, 6.9 |
| RNF-04, RNF-05 | Sem rotas de autenticação. `create_all` no lifespan |
| RNF-07 | ADR-06 |
| RNF-08 | Seção 7 |
| RNF-09 | Utilitário de movimento em `tokens.css` com `@media (prefers-reduced-motion: reduce)` |

---

## 9. Segurança e robustez

| Ponto | Tratamento |
|---|---|
| Injeção de HTML | O DOM é montado com `textContent` (ADR-07) |
| SQL | Apenas SQLAlchemy com parâmetros |
| Total adulterado | O servidor ignora o total do cliente |
| Credenciais do banco | Valores de demonstração no `docker-compose.yml`. A porta do `db` não é publicada |
| Toque duplo em "Finalizar pedido" | O botão fica desabilitado durante o envio |
| Sem autenticação | Requisito explícito (RNF-04). Não expor a porta 8000 fora da rede da oficina |

**Risco aceito:** se a resposta do `POST /api/pedidos` se perder depois de gravar o pedido, "Tentar de novo" cria um segundo pedido. Chave de idempotência ficou fora do escopo (YAGNI).

---

## 10. Refinamentos ao DEFINE

| Item | Mudança | Motivo |
|---|---|---|
| RF-09 e RF-10 | `avancar` recebe `estado_atual` | ADR-02. Sem ele, um clique atrasado pularia um estado |
| Modelo de dados | Quarta tabela `contador_dia` | ADR-03 |
| RF-06 | O número é guardado como inteiro e formatado com 3 dígitos | Facilita ordenação e a fala "Pedido 12" |
| AT-006 a AT-008 | As chamadas enviam `estado_atual` | Consequência do ADR-02 |

Esses itens podem ser levados ao DEFINE com `/iterate`, ou aceitos como estão: o `/build` segue este DESIGN.

---

## 11. Qualidade

- [x] Diagrama de arquitetura claro
- [x] Decisões documentadas com motivo (9 ADRs)
- [x] Manifesto completo (34 arquivos, com agente por arquivo)
- [x] Padrões de código prontos para copiar
- [x] Estratégia de testes cobre todos os requisitos
- [x] Sem dependências circulares

---

## Próximo passo

```bash
/build .claude/sdd/features/DESIGN_TOTEM_ATENDIMENTO.md
```
