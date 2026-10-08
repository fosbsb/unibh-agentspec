# PROMPT: Senha de 3 dígitos e tela de revisão

> Dev Loop (Level 2). Alteração sobre o totem já construído (SDD: `.claude/sdd/features/*_TOTEM_AUTOATENDIMENTO.md`).

## Objetivo

1. A **senha** do pedido (hoje o campo `numero`) passa a ter **3 dígitos e começar com 1**: faixa de 100 a 199.
2. Antes de enviar o pedido, o totem mostra uma **tela de revisão** com itens, quantidades e total, onde o cliente ainda pode ajustar ou voltar.

## Modo e limites

| Item | Valor |
|---|---|
| Modo | hitl |
| Máximo de iterações | 20 |
| Linguagem | Textos de interface em português do Brasil; código e testes seguem o padrão existente |
| Execução de Python | Em contêiner: `docker run --rm -v "$PWD":/srv -w /srv python:3.12-slim ...` (o Python local é 3.9 e o código exige 3.10+) |

## Decisões já tomadas (não reabrir)

| Tema | Decisão |
|---|---|
| Faixa | `NUMERO_MIN = 100`, `NUMERO_MAX = 199` |
| Depois da 199 | Volta para 100 e **pula senhas em uso** (pedidos com estado diferente de `entregue`) |
| Todas em uso | `POST /api/pedidos` devolve **503** com a mensagem "Todas as senhas estão em uso. Chame um atendente." |
| Unicidade | A coluna `numero` deixa de ser `UNIQUE` global. Passa a haver índice único **parcial** só para pedidos ativos (`estado != 'entregue'`) |
| Revisão | Tela cheia com itens, quantidades e total, **com edição** (−, +, Remover). Botões: "Finalizar pedido" (primário) e "Voltar ao cardápio" (secundário) |
| Rodapé do cardápio | Só resumo (itens e total) e o botão "Revisar pedido". As linhas do carrinho saem do rodapé |
| Vocabulário | Para o cliente, o número do pedido se chama **senha** (totem e TV, incluindo a voz). A cozinha continua com `#123` |

## Contexto do código atual

| Arquivo | Estado atual |
|---|---|
| `app/models.py` | `Pedido.numero` é `Integer, unique=True` |
| `app/servicos.py` | `criar_pedido` calcula `max(numero) + 1`, com até 5 tentativas em `IntegrityError` |
| `app/static/js/totem.js` | Telas `inicio`, `cardapio`, `confirmacao`. O rodapé do cardápio tem as linhas do carrinho e o botão "Finalizar pedido", que já envia o pedido. A tela de erro e o "Tentar de novo" ficam no rodapé |
| `app/static/js/painel.js` | Destaque "Pedido pronto" e voz "Pedido N, pronto" |
| `tests/` | `test_pedidos.py` assume números 1, 2, 3. `test_painel.py` compara números de forma relativa |
| Banco | **Sem volume.** O `db` em execução tem a tabela antiga (com `UNIQUE`). O `create_all` não altera tabelas existentes, então é obrigatório rodar `docker compose down` antes do próximo `up` |

## Tarefas

### 🔴 T1: Alocação da senha e índice único parcial

**Agente:** @sqlalchemy-specialist

- Em `app/models.py`: remover `unique=True` de `numero`; adicionar em `Pedido.__table_args__` um `Index("ix_pedidos_numero_ativo", "numero", unique=True, postgresql_where=text("estado != 'entregue'"), sqlite_where=text("estado != 'entregue'"))`.
- Em `app/servicos.py`:
  - constantes `NUMERO_MIN = 100` e `NUMERO_MAX = 199`;
  - função `proxima_senha(db)`: lê o `numero` do pedido de maior `id` (o último criado) e o conjunto de números dos pedidos ativos; o candidato inicial é `ultimo + 1` (ou `NUMERO_MIN` se não houver pedidos, ou se `ultimo` for `NUMERO_MAX`); percorre até 100 candidatos, voltando de 199 para 100, e devolve o primeiro que não está em uso;
  - se nenhum estiver livre, `raise HTTPException(503, "Todas as senhas estão em uso. Chame um atendente.")`;
  - `criar_pedido` usa `proxima_senha` dentro do laço de tentativas existente (o `IntegrityError` de corrida continua refazendo a tentativa).
- Não mexer na regra de transição de estados.

**Verificação:** `docker run ... python -c "import app.models, app.servicos"` sem erro, e T2 passando.

### 🔴 T2: Testes da senha

**Agente:** @test-generator

- Atualizar `tests/test_pedidos.py`: a primeira senha é 100; a sequência é `[100, 101, 102]`; a listagem volta nessa ordem.
- Acrescentar testes em `tests/test_pedidos.py`:
  1. senha sempre entre 100 e 199 e com 3 dígitos;
  2. depois da 199 volta para 100 (criar um pedido direto no banco com `numero=199` e estado `entregue`, e checar que o próximo é 100);
  3. pula senha em uso (pedidos ativos com 100 e 101 → próximo é 102 quando o último foi 199, ou o primeiro livre);
  4. senha de pedido `entregue` pode ser reutilizada;
  5. com as 100 senhas em uso, o POST devolve 503 e não cria pedido;
  6. o índice parcial impede dois pedidos ativos com o mesmo número (insert direto levanta `IntegrityError`) e permite um ativo e um entregue com o mesmo número.
- Manter os testes de nova tentativa por `IntegrityError` funcionando.

**Verificação:** `docker run ... python -m pytest -q` com tudo verde e nenhum teste removido sem substituição.

### 🟡 T3: Tela de revisão no totem

**Agente:** @web-design-specialist (seguir `specs/DESIGN_SYSTEM.md`, só tokens)

Em `app/static/js/totem.js`:
- nova tela `revisao`; o botão do rodapé do cardápio passa a se chamar "Revisar pedido" e só leva à revisão (não envia);
- o rodapé do cardápio mostra apenas "N itens", o total em amarelo e "Revisar pedido" (desabilitado com carrinho vazio); remover as linhas do carrinho do rodapé;
- a revisão mostra o título "Revise seu pedido", a lista (ícone, nome, `−`, quantidade, `+`, "Remover", subtotal da linha), o total em amarelo e os botões "Finalizar pedido" (primário) e "Voltar ao cardápio" (secundário);
- "Finalizar pedido" envia o pedido (lógica de `finalizar` atual). Mostrar "Aguarde…" e desabilitar durante o envio;
- a mensagem de erro padronizada (seção 6.9 do design system) e o botão "Tentar de novo" passam a viver na revisão e mantêm o carrinho; para 503, o texto é "Não há senhas disponíveis agora. Chame um atendente.";
- se o cliente remover o último item na revisão, volta ao cardápio;
- o temporizador de 30 s de inatividade também vale na revisão;
- alvos de toque de 80 px e 16 px de espaço entre eles; todas as cores via variáveis.

**Verificação:** `node --check app/static/js/totem.js` sem erro; depois T5.

### 🟡 T4: Vocabulário "senha" para o cliente

**Agente:** @web-design-specialist

- `totem.js` (confirmação): título "Pedido recebido!", rótulo "Sua senha" acima do número e a frase "Retire no balcão quando o painel chamar" mantida.
- `painel.html` e `painel.js`: sobreposição "Senha pronta" no lugar de "Pedido pronto"; voz `Senha ${numero}, pronta`.
- Não alterar a cozinha nem os nomes de campos da API (`numero`).

**Verificação:** `grep -rn "Pedido pronto\|Pedido \${" app/static` sem ocorrências.

### 🟡 T5: Verificação no navegador e no compose

**Agente:** nenhum (executar e conferir)

1. `docker compose down` e depois `docker compose up --build -d` (obrigatório por causa do banco sem volume).
2. `GET /api/produtos` devolve 10 itens.
3. Pedido pela API: a senha é 100; o segundo é 101.
4. No totem (viewport 1080x1920 no Playwright): iniciar → adicionar itens → "Revisar pedido" → ajustar com `+` e `−` → "Voltar ao cardápio" mantém o carrinho → "Revisar pedido" → "Finalizar pedido" → a confirmação mostra "Sua senha" com 3 dígitos começando com 1.
5. Remover o último item na revisão volta ao cardápio.
6. Console sem erros (o aviso do Tailwind CDN é esperado).
7. No painel, passar a senha para "pronto" pela API e conferir "Senha pronta" no destaque.
8. Medir os botões da revisão (≥ 80 px).
9. Ao final, **deixar o projeto no ar** (`docker compose up -d`) para o usuário testar.

### 🟢 T6: Documentação

**Agente:** @design-system-auditor para o design system; edição direta para o restante

- `specs/DESIGN_SYSTEM.md`: **manter a versão em 1.1.0** (decisão do usuário: só muda quando ele decidir). Atualizar a seção 6.4 (rodapé com "Revisar pedido"), criar a seção "Tela de revisão (totem)", atualizar a 6.5 (rótulo "Sua senha", faixa 100–199) e a 6.7 ("Senha pronta"). Não acrescentar linha nova no histórico.
- `.claude/sdd/features/DEFINE_TOTEM_AUTOATENDIMENTO.md`: RF-05 a RF-09 (revisão), RF-13 (senha de 100 a 199, volta e reaproveita), RF-22 (voz "Senha N, pronta"), AT-03 (primeiro pedido com senha 100); incluir RF novo para o 503.
- `.claude/sdd/features/DESIGN_TOTEM_AUTOATENDIMENTO.md`: nota em D1 informando que a decisão foi **substituída** (índice parcial, faixa 100–199, volta e pula em uso), com data 2026-10-08.
- `README.md`: avisar que, ao atualizar uma versão antiga, é preciso `docker compose down` antes do `up`.
- Não commitar.

**Verificação:** `grep -n "1.1.0" specs/DESIGN_SYSTEM.md` mostra a versão inalterada e `grep -n "100" .claude/sdd/features/DEFINE_TOTEM_AUTOATENDIMENTO.md`.

## Portões de qualidade

```text
[ ] pytest verde em contêiner Python 3.12 (nenhum teste removido sem substituto)
[ ] Primeira senha é 100; nenhuma senha fora de 100 a 199
[ ] Volta de 199 para 100 e reaproveitamento após entrega testados
[ ] 503 com as 100 senhas em uso testado
[ ] Revisão permite ajustar, voltar e finalizar; erro mantém o carrinho
[ ] Nenhuma cor em hexadecimal nas telas; alvos de toque >= 80 px
[ ] Design system **continua em 1.1.0**, e ele, o DEFINE e o DESIGN estão coerentes com o código
[ ] Projeto no ar no final
```

## Fora do escopo

- Reiniciar a senha por dia ou por turno.
- Mais de 100 senhas simultâneas ou outras faixas configuráveis.
- Mudar a cozinha (continua `#123`) e os nomes de campo da API.
- Migrações de banco (Alembic): o banco da demo é recriado com `down`/`up`.
- Commits.

## Saída esperada

`EXIT_COMPLETE` quando todos os portões acima estiverem marcados, com um resumo do que foi alterado e do que não foi verificado (por exemplo, a voz na TV real).
