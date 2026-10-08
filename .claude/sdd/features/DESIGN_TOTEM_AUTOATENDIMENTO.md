# DESIGN: Totem de Autoatendimento

> Arquitetura e especificação técnica (Fase 2)

## Metadados

| Atributo | Valor |
|---|---|
| **Feature** | TOTEM_AUTOATENDIMENTO |
| **Data** | 2026-10-08 |
| **Origem** | `.claude/sdd/features/DEFINE_TOTEM_AUTOATENDIMENTO.md` |
| **Status** | Pronto para /build |

---

## 1. Visão geral

```text
   Totem (1080x1920)      Cozinha (desktop/tablet)       TV (1920x1080)
   /totem                 /cozinha                       /painel
   totem.js               cozinha.js (poll 2s)           painel.js (poll 2s)
        │                        │                             │
        └──────────── fetch JSON (mesma origem) ───────────────┘
                                 │
                    ┌────────────▼─────────────┐
                    │  app  (FastAPI/uvicorn)  │
                    │  ├─ routers/produtos.py  │   GET  /api/produtos
                    │  ├─ routers/pedidos.py   │   POST /api/pedidos
                    │  │                       │   GET  /api/pedidos
                    │  │                       │   PATCH /api/pedidos/{id}/estado
                    │  ├─ routers/painel.py    │   GET  /api/painel
                    │  ├─ main.py (páginas +   │   GET  /totem /cozinha /painel
                    │  │   /static + lifespan) │
                    │  └─ seed.py              │
                    └────────────┬─────────────┘
                                 │ SQLAlchemy 2.x (psycopg 3)
                    ┌────────────▼─────────────┐
                    │  db  (postgres:16)       │
                    └──────────────────────────┘
```

**Componentes**

| Componente | Responsabilidade |
|---|---|
| `main.py` | Cria o app, registra routers, serve as páginas e `/static`, roda `create_all` + seed no lifespan |
| `database.py` | Engine, `SessionLocal`, dependência `get_db`, espera o banco responder |
| `models.py` | `Produto`, `Pedido`, `ItemPedido` |
| `schemas.py` | Contratos Pydantic de entrada e saída |
| `estados.py` | Enum `EstadoPedido` e regra de transição (função pura, testável sem banco) |
| `seed.py` | Carrega os 10 produtos se a tabela estiver vazia |
| `routers/` | Endpoints finos; a regra de negócio fica em `servicos.py` |
| `servicos.py` | Criar pedido (total, número), avançar estado, tempo médio |
| `static/` | Três páginas HTML, `tokens.css` e JS puro por tela |

**Fluxo principal**

```text
Cliente toca "Finalizar" → POST /api/pedidos {itens}
  → servidor valida, busca preços no banco, calcula total, gera número, grava (estado=recebido)
  → totem mostra número por 8 s
Cozinha (poll 2s) vê o pedido → "Iniciar"  → PATCH {estado:"preparando"}
                              → "Marcar pronto" → PATCH {estado:"pronto"}
Painel (poll 2s) detecta o id novo em "pronto" → destaque 6 s + voz
Cozinha → "Entregar" → PATCH {estado:"entregue"} → sai das duas telas
```

---

## 2. Decisões (ADRs inline)

### D1: Número do pedido com restrição única e nova tentativa

> **Substituída em 2026-10-08** (dev loop `PROMPT_SENHA_E_REVISAO`). A senha agora tem 3 dígitos, de 100 a 199. O serviço lê o número do último pedido criado e avança em círculo, pulando as senhas de pedidos não entregues (`proxima_senha`). A coluna `numero` deixou de ser `UNIQUE` global e ganhou o índice único parcial `ix_pedidos_numero_ativo` (`estado != 'entregue'`), que funciona em PostgreSQL e SQLite. Com as 100 em uso, o POST devolve 503. A nova tentativa em `IntegrityError` foi mantida. O texto abaixo é o histórico da decisão original.

| Atributo | Valor |
|---|---|
| **Status** | Substituída |
| **Data** | 2026-10-08 |

**Contexto:** o número precisa ser sequencial, legível e único, mesmo com dois totens enviando ao mesmo tempo. Os testes rodam em SQLite, que não tem `SEQUENCE`.

**Escolha:** coluna `numero` com `UNIQUE`. Ao criar, o serviço calcula `max(numero) + 1` e grava. Se der `IntegrityError` (corrida), refaz a transação, até 5 tentativas. Sem reinício diário.

**Justificativa:** funciona igual em PostgreSQL e SQLite, sem DDL específico, e a garantia vem do banco, não do código.

**Alternativas rejeitadas**
1. `SEQUENCE` do PostgreSQL: não existe no SQLite dos testes e exigiria um caminho de código por dialeto.
2. Contador em tabela com `SELECT … FOR UPDATE`: o SQLite ignora o bloqueio e não ganha nada em relação à restrição única.
3. Reinício diário: precisa de data de negócio e regra de virada; não é pedido na demo.

**Consequências:** sob concorrência rara há uma nova tentativa invisível ao cliente. O número cresce sem limite, e a demo nunca chega perto de 4 dígitos.

### D2: Tailwind via CDN mapeado para os tokens, sem fallback offline

| Atributo | Valor |
|---|---|
| **Status** | Aceita |
| **Data** | 2026-10-08 |

**Contexto:** o design system manda usar `var(--cor-…)` e nunca hexadecimal. O DEFINE assume internet na oficina.

**Escolha:** cada página carrega `tokens.css` e o script do Tailwind CDN, e um `tailwind.config` inline (em `static/js/tailwind-config.js`) mapeia as cores e os raios para as variáveis CSS. Sem fallback offline.

**Justificativa:** mantém uma única fonte de cores (`tokens.css`) e o frontend sem build. O fallback exigiria baixar o Tailwind para o repositório, o que quebra o "sem etapa de build" na prática de manutenção.

**Alternativas rejeitadas**
1. Hexadecimal nas classes (`bg-[#FF7A00]`): viola a seção 9 do design system.
2. Copiar o Tailwind compilado para `static/`: aumenta o repositório e cria um artefato gerado.

**Consequências:** a demo depende de rede para o Tailwind. Registrado como premissa no README.

### D3: Endpoint de estado recebe o estado de destino

| Atributo | Valor |
|---|---|
| **Status** | Aceita |
| **Data** | 2026-10-08 |

**Contexto:** o DEFINE diz que `PATCH` "avança uma etapa". A cozinha usa tablet e toque, e duplo clique é comum.

**Escolha:** `PATCH /api/pedidos/{id}/estado` com corpo `{"estado": "preparando"}`. O servidor aceita só o destino que é exatamente o próximo da sequência; qualquer outro devolve 409.

**Justificativa:** com um endpoint do tipo "avançar", um duplo clique em "Iniciar" levaria o pedido a `pronto` sem querer. Com o destino explícito, o segundo clique recebe 409 e a tela só atualiza.

**Alternativas rejeitadas**
1. `POST /avancar` sem corpo: não é idempotente em cliques repetidos.
2. Aceitar qualquer destino a frente: contradiz AT-07.

**Consequências:** o front precisa tratar 409 como "já mudou" e recarregar a fila, sem mostrar erro.

### D4: Testes com SQLite em memória e tempos tratados em Python

| Atributo | Valor |
|---|---|
| **Status** | Aceita |
| **Data** | 2026-10-08 |

**Contexto:** RNF-08 pede pytest sem Docker. SQLite devolve `datetime` sem fuso mesmo com `DateTime(timezone=True)`.

**Escolha:** o engine de teste usa `sqlite://` com `StaticPool` e `check_same_thread=False`, e o `get_db` é substituído por `dependency_overrides`. O tempo médio é calculado em Python, normalizando datas sem fuso para UTC. Horários são gravados em UTC.

**Justificativa:** evita SQL específico de dialeto (`EXTRACT(EPOCH …)`), o que mantém a mesma lógica nos dois bancos.

**Alternativas rejeitadas**
1. Testcontainers/PostgreSQL nos testes: exige Docker e deixa a suíte lenta.
2. Média em SQL: precisa de função diferente por dialeto.

**Consequências:** o PostgreSQL real só é exercitado no smoke test do compose (checklist da seção 7).

### D5: Um endpoint agregado para o painel

| Atributo | Valor |
|---|---|
| **Status** | Aceita |
| **Data** | 2026-10-08 |

**Escolha:** `GET /api/painel` devolve `{preparando: [...], pronto: [...], tempo_medio_segundos}` em uma chamada.

**Justificativa:** a TV faz uma única requisição a cada 2 s e recebe um retrato consistente dos dois estados, sem a corrida de duas chamadas separadas. É um acréscimo à lista de endpoints do DEFINE (RF-20 a RF-24 continuam valendo).

**Alternativa rejeitada:** chamar `/api/pedidos` duas vezes e calcular a média no cliente, o que duplica a lógica.

### D6: Destaque do recém-pronto detectado no cliente

| Atributo | Valor |
|---|---|
| **Status** | Aceita |
| **Data** | 2026-10-08 |

**Escolha:** o `painel.js` guarda o conjunto de ids em `pronto` da resposta anterior. Ids novos entram em uma fila de destaques (6 s cada, um por vez). A primeira resposta após abrir a página só preenche o conjunto, sem disparar destaque.

**Justificativa:** não exige estado extra no servidor nem campo "visto". Abrir ou recarregar a TV não repete anúncios antigos.

**Consequências:** se a TV for fechada e reaberta, perde os destaques em curso. É aceitável na demo.

### D7: Banco sem volume nomeado

| Atributo | Valor |
|---|---|
| **Status** | Aceita |
| **Data** | 2026-10-08 |

**Escolha:** o serviço `db` não declara volume nomeado. `docker compose down` remove o contêiner e os pedidos de teste; o próximo `up` recomeça do seed.

**Justificativa:** a oficina repete a demo várias vezes, e pedidos antigos poluiriam o painel. O RF-02 (seed idempotente) continua valendo para `restart`, que preserva o contêiner.

---

## 3. Contrato da API

Valores em **centavos** (inteiro). Estados em minúsculas sem acento: `recebido`, `preparando`, `pronto`, `entregue`.

| Método e rota | Entrada | Saída | Erros |
|---|---|---|---|
| `GET /api/produtos` | — | `[{id, nome, categoria, icone, preco_centavos}]` ordenado por categoria (Lanches, Crepes, Bebidas, Sobremesas) e id | — |
| `POST /api/pedidos` | `{itens:[{produto_id, quantidade}]}` | 201 `Pedido` | 404 produto inexistente; 422 lista vazia, quantidade fora de 1..20, mais de 30 linhas |
| `GET /api/pedidos?estado=a&estado=b` | filtro opcional repetível | `[Pedido]` em ordem de chegada (id crescente) | 422 estado desconhecido |
| `PATCH /api/pedidos/{id}/estado` | `{estado}` | `Pedido` | 404 pedido; 409 transição inválida; 422 estado desconhecido |
| `GET /api/painel` | — | `{preparando:[PedidoResumo], pronto:[PedidoResumo], tempo_medio_segundos: int \| null}` | — |

```text
Pedido        = {id, numero, estado, total_centavos, criado_em,
                 itens:[{produto_id, nome, preco_centavos, quantidade}]}
PedidoResumo  = {id, numero}
```

Regras:
- Linhas com o mesmo `produto_id` são somadas antes de validar a quantidade.
- O total é a soma de `preco_centavos × quantidade` com os preços do banco (RF-11).
- Tempo médio: média de `pronto_em − preparando_em` sobre os 20 pedidos mais recentes que têm os dois horários. Sem dados, `null`.
- `GET /api/painel` não devolve pedidos `recebido` nem `entregue`.

---

## 4. Modelo de dados

```text
produtos                        pedidos                           itens_pedido
├─ id            PK             ├─ id              PK             ├─ id            PK
├─ nome          str            ├─ numero          int UNIQUE     ├─ pedido_id     FK pedidos
├─ categoria     str            ├─ estado          str            ├─ produto_id    FK produtos
├─ icone         str            ├─ total_centavos  int            ├─ nome          str (cópia)
└─ preco_centavos int           ├─ criado_em       tz UTC         ├─ preco_centavos int (cópia)
                                ├─ preparando_em   tz UTC null    └─ quantidade    int
                                ├─ pronto_em       tz UTC null
                                └─ entregue_em     tz UTC null
```

Índices: `pedidos.numero` (único) e `pedidos.estado`.

---

## 5. Manifesto de arquivos

| # | Arquivo | Ação | Propósito | Depende de |
|---|---|---|---|---|
| 1 | `requirements.txt` | Criar | Dependências | — |
| 2 | `Dockerfile` | Criar | Imagem do app | 1 |
| 3 | `docker-compose.yml` | Criar | Serviços `app` e `db` com healthcheck | 2 |
| 4 | `.dockerignore` | Criar | Reduz o contexto de build | — |
| 5 | `app/__init__.py` | Criar | Pacote | — |
| 6 | `app/estados.py` | Criar | Enum e regra de transição | — |
| 7 | `app/database.py` | Criar | Engine, sessão, `get_db`, espera do banco | — |
| 8 | `app/models.py` | Criar | Tabelas | 7 |
| 9 | `app/schemas.py` | Criar | Contratos Pydantic | 6 |
| 10 | `app/seed.py` | Criar | Carga dos 10 produtos | 8 |
| 11 | `app/servicos.py` | Criar | Criar pedido, avançar estado, tempo médio | 6, 8, 9 |
| 12 | `app/routers/__init__.py` | Criar | Pacote | — |
| 13 | `app/routers/produtos.py` | Criar | `GET /api/produtos` | 7, 8, 9 |
| 14 | `app/routers/pedidos.py` | Criar | Rotas de pedidos | 7, 9, 11 |
| 15 | `app/routers/painel.py` | Criar | `GET /api/painel` | 7, 11 |
| 16 | `app/main.py` | Criar | App, lifespan, páginas, estáticos | 7 a 15 |
| 17 | `app/static/css/tokens.css` | Criar | Tokens do design system e utilitários | — |
| 18 | `app/static/js/tailwind-config.js` | Criar | Mapeia o Tailwind para os tokens | 17 |
| 19 | `app/static/js/api.js` | Criar | `fetch` comum, formatação `R$` | — |
| 20 | `app/static/totem.html` + `js/totem.js` | Criar | Tela do totem | 17 a 19 |
| 21 | `app/static/cozinha.html` + `js/cozinha.js` | Criar | Fila da cozinha | 17 a 19 |
| 22 | `app/static/painel.html` + `js/painel.js` | Criar | Painel da TV | 17 a 19 |
| 23 | `tests/conftest.py` | Criar | Engine SQLite, `client`, fábrica de dados | 7, 8, 16 |
| 24 | `tests/test_estados.py` | Criar | Regra de transição pura | 6 |
| 25 | `tests/test_seed.py` | Criar | AT-01, AT-02 | 10, 23 |
| 26 | `tests/test_pedidos.py` | Criar | AT-03 a AT-09 | 14, 23 |
| 27 | `tests/test_painel.py` | Criar | Painel e tempo médio | 15, 23 |
| 28 | `pytest.ini` | Criar | `testpaths`, `pythonpath` | — |
| 29 | `specs/DESIGN_SYSTEM.md` | Modificar | v1.1.0: sem "Cancelado", com "Entregue" | — |
| 30 | `README.md` (raiz) | Modificar | Como subir e testar a demo | 3 |

**Ordem de build:** 1–4 → 5–10 → 11–16 → 23–28 (testes antes do front) → 17–22 → 29–30.

---

## 6. Padrões de código

### 6.1 Regra de transição (`app/estados.py`)

```python
from enum import Enum


class EstadoPedido(str, Enum):
    RECEBIDO = "recebido"
    PREPARANDO = "preparando"
    PRONTO = "pronto"
    ENTREGUE = "entregue"


SEQUENCIA = list(EstadoPedido)


def proximo_estado(atual: EstadoPedido) -> EstadoPedido | None:
    i = SEQUENCIA.index(atual)
    return SEQUENCIA[i + 1] if i + 1 < len(SEQUENCIA) else None


def transicao_valida(atual: EstadoPedido, destino: EstadoPedido) -> bool:
    return proximo_estado(atual) == destino
```

### 6.2 Banco e dependência (`app/database.py`)

```python
import os
import time

from sqlalchemy import create_engine, text
from sqlalchemy.orm import DeclarativeBase, sessionmaker

DATABASE_URL = os.getenv(
    "DATABASE_URL", "postgresql+psycopg://totem:totem@db:5432/totem"
)

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def esperar_banco(tentativas: int = 30, intervalo: float = 1.0) -> None:
    for i in range(tentativas):
        try:
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            return
        except Exception:
            if i == tentativas - 1:
                raise
            time.sleep(intervalo)
```

### 6.3 Modelos (`app/models.py`)

```python
from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


def agora() -> datetime:
    return datetime.now(timezone.utc)


class Produto(Base):
    __tablename__ = "produtos"
    id: Mapped[int] = mapped_column(primary_key=True)
    nome: Mapped[str] = mapped_column(String(80))
    categoria: Mapped[str] = mapped_column(String(30))
    icone: Mapped[str] = mapped_column(String(8))
    preco_centavos: Mapped[int] = mapped_column(Integer)


class Pedido(Base):
    __tablename__ = "pedidos"
    id: Mapped[int] = mapped_column(primary_key=True)
    numero: Mapped[int] = mapped_column(Integer, unique=True)
    estado: Mapped[str] = mapped_column(String(15), default="recebido", index=True)
    total_centavos: Mapped[int] = mapped_column(Integer)
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=agora)
    preparando_em: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    pronto_em: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    entregue_em: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    itens: Mapped[list["ItemPedido"]] = relationship(
        back_populates="pedido", cascade="all, delete-orphan", lazy="selectin"
    )


class ItemPedido(Base):
    __tablename__ = "itens_pedido"
    id: Mapped[int] = mapped_column(primary_key=True)
    pedido_id: Mapped[int] = mapped_column(ForeignKey("pedidos.id"))
    produto_id: Mapped[int] = mapped_column(ForeignKey("produtos.id"))
    nome: Mapped[str] = mapped_column(String(80))
    preco_centavos: Mapped[int] = mapped_column(Integer)
    quantidade: Mapped[int] = mapped_column(Integer)
    pedido: Mapped[Pedido] = relationship(back_populates="itens")
```

### 6.3.1 Seed (`app/seed.py`)

```python
CARDAPIO = [
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


def carregar_cardapio(db) -> int:
    if db.query(Produto).first() is not None:
        return 0
    db.add_all(
        Produto(categoria=c, nome=n, icone=i, preco_centavos=p) for c, n, i, p in CARDAPIO
    )
    db.commit()
    return len(CARDAPIO)
```

### 6.4 Criar pedido com nova tentativa (`app/servicos.py`)

```python
from collections import defaultdict

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError

from app.estados import EstadoPedido, transicao_valida
from app.models import ItemPedido, Pedido, Produto, agora

MAX_TENTATIVAS = 5


def criar_pedido(db, itens_in) -> Pedido:
    quantidades: dict[int, int] = defaultdict(int)
    for item in itens_in:
        quantidades[item.produto_id] += item.quantidade
    if any(q > 20 for q in quantidades.values()):
        raise HTTPException(422, "Quantidade máxima por produto é 20")

    produtos = {
        p.id: p
        for p in db.scalars(select(Produto).where(Produto.id.in_(quantidades)))
    }
    faltando = set(quantidades) - set(produtos)
    if faltando:
        raise HTTPException(404, f"Produto inexistente: {sorted(faltando)}")

    total = sum(produtos[i].preco_centavos * q for i, q in quantidades.items())

    for _ in range(MAX_TENTATIVAS):
        numero = (db.scalar(select(func.max(Pedido.numero))) or 0) + 1
        pedido = Pedido(numero=numero, total_centavos=total, estado=EstadoPedido.RECEBIDO.value)
        pedido.itens = [
            ItemPedido(
                produto_id=i, nome=produtos[i].nome,
                preco_centavos=produtos[i].preco_centavos, quantidade=q,
            )
            for i, q in quantidades.items()
        ]
        db.add(pedido)
        try:
            db.commit()
            return pedido
        except IntegrityError:
            db.rollback()
    raise HTTPException(503, "Não foi possível gerar o número do pedido")


def mudar_estado(db, pedido_id: int, destino: EstadoPedido) -> Pedido:
    pedido = db.get(Pedido, pedido_id)
    if pedido is None:
        raise HTTPException(404, "Pedido não encontrado")
    atual = EstadoPedido(pedido.estado)
    if not transicao_valida(atual, destino):
        raise HTTPException(409, f"Transição inválida: {atual.value} → {destino.value}")
    pedido.estado = destino.value
    setattr(pedido, {"preparando": "preparando_em", "pronto": "pronto_em",
                     "entregue": "entregue_em"}[destino.value], agora())
    db.commit()
    return pedido
```

### 6.5 Tempo médio (`app/servicos.py`)

```python
from datetime import timezone


def _utc(dt):
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


def tempo_medio_segundos(db) -> int | None:
    pedidos = db.scalars(
        select(Pedido)
        .where(Pedido.preparando_em.is_not(None), Pedido.pronto_em.is_not(None))
        .order_by(Pedido.id.desc())
        .limit(20)
    ).all()
    if not pedidos:
        return None
    total = sum((_utc(p.pronto_em) - _utc(p.preparando_em)).total_seconds() for p in pedidos)
    return round(total / len(pedidos))
```

### 6.6 Lifespan e páginas (`app/main.py`)

```python
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app import database, models  # noqa: F401  (registra as tabelas)
from app.routers import painel, pedidos, produtos
from app.seed import carregar_cardapio

STATIC = Path(__file__).parent / "static"


@asynccontextmanager
async def lifespan(app: FastAPI):
    database.esperar_banco()
    database.Base.metadata.create_all(database.engine)
    with database.SessionLocal() as db:
        carregar_cardapio(db)
    yield


app = FastAPI(title="Totem de Autoatendimento", lifespan=lifespan)
app.include_router(produtos.router, prefix="/api")
app.include_router(pedidos.router, prefix="/api")
app.include_router(painel.router, prefix="/api")
app.mount("/static", StaticFiles(directory=STATIC), name="static")


def _pagina(nome: str):
    return lambda: FileResponse(STATIC / f"{nome}.html")


for _nome in ("totem", "cozinha", "painel"):
    app.add_api_route(f"/{_nome}", _pagina(_nome), include_in_schema=False)
```

> Nos testes, o `lifespan` não deve rodar contra o Postgres. O `conftest.py` usa `TestClient(app)` **sem** o gerenciador de contexto (sem `with`), e cria as tabelas e o seed no engine SQLite por conta própria.

### 6.7 Tailwind mapeado para os tokens (`static/js/tailwind-config.js`)

```js
tailwind.config = {
  theme: {
    extend: {
      colors: {
        preto: "var(--cor-preto)",
        laranja: "var(--cor-laranja)",
        amarelo: "var(--cor-amarelo)",
        vermelho: "var(--cor-vermelho)",
        "vermelho-claro": "var(--cor-vermelho-claro)",
        superficie: "var(--cor-superficie)",
        "superficie-alta": "var(--cor-superficie-alta)",
        borda: "var(--cor-borda)",
        suave: "var(--cor-texto-suave)",
      },
      borderRadius: { botao: "var(--raio-botao)", cartao: "var(--raio-cartao)" },
    },
  },
};
```

Cada página carrega, nesta ordem: `tokens.css`, o script `https://cdn.tailwindcss.com` e `tailwind-config.js`. O `tailwind-config.js` precisa vir **depois** do CDN, porque é o CDN que define o global `tailwind` (corrigido no /build: a ordem inversa dava `ReferenceError: tailwind is not defined`).

### 6.8 Polling e formatação (`static/js/api.js`)

```js
export const reais = (centavos) =>
  new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" }).format(centavos / 100);

export async function api(caminho, opcoes = {}) {
  const resp = await fetch(`/api${caminho}`, {
    headers: { "Content-Type": "application/json" },
    ...opcoes,
  });
  if (!resp.ok) {
    const erro = new Error(`HTTP ${resp.status}`);
    erro.status = resp.status;
    throw erro;
  }
  return resp.json();
}

export function repetir(fn, ms = 2000) {
  let ativo = true;
  const volta = async () => {
    if (!ativo) return;
    try { await fn(); } catch (e) { console.warn(e); }
    setTimeout(volta, ms);
  };
  volta();
  return () => { ativo = false; };
}
```

`repetir` agenda a próxima chamada só depois da anterior terminar, para não empilhar requisições se o servidor demorar.

### 6.9 Detecção de recém-pronto (`static/js/painel.js`)

```js
let vistos = null;      // null = primeira resposta ainda não chegou
const fila = [];
let mostrando = false;

function atualizar(dados) {
  const ids = new Set(dados.pronto.map((p) => p.id));
  if (vistos !== null) {
    dados.pronto.filter((p) => !vistos.has(p.id)).forEach((p) => fila.push(p));
  }
  vistos = ids;
  desenharListas(dados);
  tocarProximo();
}

function tocarProximo() {
  if (mostrando || fila.length === 0) return;
  const pedido = fila.shift();
  mostrando = true;
  mostrarDestaque(pedido.numero);
  falar(`Pedido ${pedido.numero}, pronto`);
  setTimeout(() => { esconderDestaque(); mostrando = false; tocarProximo(); }, 6000);
}

function falar(texto) {
  if (!somAtivo || !("speechSynthesis" in window)) return;
  const fala = new SpeechSynthesisUtterance(texto);
  fala.lang = "pt-BR";
  speechSynthesis.speak(fala);
}
```

`somAtivo` passa a `true` no toque do botão "Ativar som", que também fala uma frase curta de teste para liberar o áudio.

### 6.10 Cozinha: ação por estado e tratamento de 409

```js
const ACOES = {
  recebido:   { rotulo: "Iniciar",       destino: "preparando", classe: "primario" },
  preparando: { rotulo: "Marcar pronto", destino: "pronto",     classe: "primario" },
  pronto:     { rotulo: "Entregar",      destino: "entregue",   classe: "secundario" },
};

async function mudar(id, destino) {
  try {
    await api(`/pedidos/${id}/estado`, { method: "PATCH", body: JSON.stringify({ estado: destino }) });
  } catch (e) {
    if (e.status !== 409) mostrarErro("Não foi possível atualizar o pedido. Toque de novo.");
  }
  await carregar();   // 409 significa "alguém já mudou": só recarrega
}
```

Os botões mostram "Aguarde…" e ficam desabilitados enquanto a chamada está em curso (seção 6.2 do design system).

### 6.11 Docker

```yaml
# docker-compose.yml
services:
  db:
    image: postgres:16
    environment:
      POSTGRES_USER: totem
      POSTGRES_PASSWORD: totem
      POSTGRES_DB: totem
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U totem -d totem"]
      interval: 3s
      timeout: 3s
      retries: 15

  app:
    build: .
    environment:
      DATABASE_URL: postgresql+psycopg://totem:totem@db:5432/totem
    depends_on:
      db:
        condition: service_healthy
    ports:
      - "8000:8000"
```

```dockerfile
# Dockerfile
FROM python:3.12-slim
WORKDIR /srv
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app app
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

```text
# requirements.txt
fastapi>=0.115,<1
uvicorn[standard]>=0.30,<1
sqlalchemy>=2.0,<3
psycopg[binary]>=3.2,<4
pytest>=8,<9
httpx>=0.27,<1
```

> O `build` do Compose é a imagem do backend, e não uma etapa de build de frontend. Isso é compatível com o RNF-02. As versões acima são faixas; o `/build` deve confirmar que instalam e fixar as exatas.

### 6.12 Conftest (`tests/conftest.py`)

```python
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app import models  # noqa: F401
from app.database import Base, get_db
from app.main import app
from app.seed import carregar_cardapio


@pytest.fixture
def db_session():
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(engine)
    Sessao = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    with Sessao() as db:
        carregar_cardapio(db)
        yield db


@pytest.fixture
def client(db_session):
    app.dependency_overrides[get_db] = lambda: db_session
    yield TestClient(app)          # sem "with": não dispara o lifespan do Postgres
    app.dependency_overrides.clear()
```

---

## 7. Estratégia de testes

| Tipo | Escopo | Ferramenta | Cobre |
|---|---|---|---|
| Unitário | `estados.py`: sequência, transição válida e inválida, fim da linha | pytest | RF-15, AT-06 a AT-08 |
| Unitário | `servicos.tempo_medio_segundos`: sem dados, com dados, datas sem fuso | pytest | RF-23 |
| API | Seed: 10 produtos, 4 categorias, idempotência | pytest + `TestClient` | AT-01, AT-02, CS-05 |
| API | Criar pedido: total, ignora total do cliente, itens repetidos somados, 404, 422, número crescente | pytest + `TestClient` | AT-03, AT-04, AT-05, CS-04 |
| API | Estados: avanço correto, pulo, volta, pedido `entregue`, duplo envio, 404 | pytest + `TestClient` | AT-06 a AT-08, CS-03 |
| API | Listagem em ordem de chegada e filtro de estado repetido | pytest + `TestClient` | AT-09, RF-14 |
| API | Painel: só `preparando` e `pronto`, entregue some, tempo médio | pytest + `TestClient` | AT-13 (lado servidor), AT-14, RF-24 |
| Concorrência | Dois `criar_pedido` com número já usado forçam nova tentativa | pytest (força `IntegrityError` com um número pré-existente via monkeypatch) | D1 |
| Smoke manual | `docker compose up` em máquina limpa; três telas abrem; pedido percorre o ciclo | Checklist | CS-01, CS-02 |
| Manual de tela | AT-10, AT-11, AT-12, AT-13 (lado visual e voz) | Checklist com navegador | RF-04 a RF-09, RF-21, RF-22 |

**Checklist do smoke test (executado no `/build`)**
1. `docker compose up --build` sem erros e `app` inicia após o `db` ficar saudável.
2. `GET /api/produtos` devolve 10 itens.
3. Abrir `/totem`, `/cozinha` e `/painel` em abas separadas.
4. Fazer um pedido no totem e ver o número; vê-lo na cozinha em até 2 s.
5. Iniciar → Marcar pronto: o painel mostra o destaque e o pedido na coluna "Pronto".
6. Entregar: o pedido some da cozinha e do painel.
7. `docker compose restart app` e confirmar que continuam 10 produtos.

---

## 8. Tratamento de erros

| Situação | Backend | Frontend |
|---|---|---|
| Produto inexistente | 404 com mensagem | Totem mostra erro padronizado (6.9) e mantém o carrinho |
| Corpo inválido | 422 (Pydantic) | Idem |
| Transição inválida | 409 | Cozinha recarrega a fila sem mostrar erro |
| Banco fora do ar | 500 | Totem: erro com "Tentar de novo". Cozinha e painel mantêm a última tela e tentam no próximo ciclo |
| Falha de rede no polling | — | `repetir` registra no console e continua |
| Voz indisponível | — | Só o destaque visual |

---

## 9. Segurança e limites (escopo de demo)

- Sem autenticação por decisão do brief. A rede da oficina é confiável, e o README deve avisar que a demo não é para exposição pública.
- Credenciais do banco (`totem/totem`) ficam só no Compose, e a porta do `db` não é publicada no host.
- O servidor valida quantidades (1..20), número de linhas (máx. 30) e recalcula preços.
- O front insere texto com `textContent` ou escape, mesmo vindo do seed.

---

## 10. Rastreabilidade

| Requisito | Onde é atendido |
|---|---|
| RF-01 a RF-03 | `seed.py`, `routers/produtos.py`, `test_seed.py` |
| RF-04 a RF-09 | `totem.html`, `totem.js`, seção 6.8 |
| RF-10 a RF-16 | `servicos.py`, `routers/pedidos.py`, `estados.py`, D1, D3 |
| RF-17 a RF-19 | `cozinha.html`, `cozinha.js`, seção 6.10 |
| RF-20 a RF-24 | `painel.html`, `painel.js`, `routers/painel.py`, D5, D6 |
| RNF-01, RNF-03 | `docker-compose.yml`, `esperar_banco`, D7 |
| RNF-02, RNF-04 | `tokens.css`, `tailwind-config.js`, D2 |
| RNF-05 a RNF-07 | `tokens.css` e as três páginas (conferir no checklist de tela) |
| RNF-08 | `conftest.py`, D4 |

---

## 11. Ajuste no design system (arquivo 29)

| Mudança | Detalhe |
|---|---|
| Remover | Estado "Cancelado" (seção 3.4), botão "Cancelar" da fila da cozinha (6.8) |
| Incluir | Estado "Entregue": fundo `--cor-superficie`, texto `--cor-texto-suave`, ícone 📦, rótulo "Entregue", sem token novo |
| Manter | Variante "Perigo" do botão (usada em "Remover" item do carrinho) e a cor vermelha |
| Versão | 1.1.0 e nova linha no histórico |

---

## Próximo passo

```bash
/tecspec:workflow:build .claude/sdd/features/DESIGN_TOTEM_AUTOATENDIMENTO.md
```
