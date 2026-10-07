# Roteiro: Totem de Atendimento com o TecSpec

Passo a passo para construir o totem. Siga a ordem: cada passo traz o **prompt**, o **que esperar** e **como verificar**.

**Resultado final:** um totem de autoatendimento de lanchonete com PostgreSQL e um design system próprio (preto, laranja, amarelo e vermelho), feito do zero com o fluxo SDD (`/brainstorm → /define → /design → /build → /ship`).

| Tela | Quem usa | O que faz |
|---|---|---|
| `/totem` | Cliente | Escolhe produtos no cardápio, monta o pedido e recebe o número |
| `/cozinha` | Atendente e cozinha | Vê os pedidos em ordem, inicia o preparo, marca como pronto e entrega |
| `/painel` | TV da sala de espera | Mostra os pedidos em preparo e os prontos, e fala o número do pedido pronto |

**Cardápio simulado** (10 produtos, carregados no banco quando a aplicação sobe):

| Categoria | Produto | Preço |
|---|---|---|
| Lanches | 🍔 Hambúrguer clássico | R$ 24,90 |
| Lanches | 🥓 X-Bacon | R$ 29,90 |
| Lanches | 🌭 Cachorro-quente | R$ 16,90 |
| Lanches | 🍟 Batata frita | R$ 14,90 |
| Crepes | 🥞 Crepe de queijo e presunto | R$ 19,90 |
| Crepes | 🍓 Crepe de chocolate com morango | R$ 21,90 |
| Bebidas | 🍊 Suco de laranja | R$ 9,90 |
| Bebidas | 🍍 Suco de abacaxi com hortelã | R$ 10,90 |
| Bebidas | 🥤 Milk shake de chocolate | R$ 18,90 |
| Sobremesas | 🍦 Sundae de morango | R$ 12,90 |

**Stack escolhida** (simples de rodar, sem etapa de build no frontend):

| Camada | Tecnologia |
|---|---|
| API | Python 3.12 + FastAPI |
| Banco | PostgreSQL 16, acessado com SQLAlchemy |
| Telas | HTML + Tailwind (CDN) + JavaScript puro, servidas pelo próprio FastAPI |
| Estilo | [specs/DESIGN_SYSTEM.md](../specs/DESIGN_SYSTEM.md) + tokens CSS em `app/static/css/tokens.css` |
| Testes | pytest |
| Execução | Docker Compose, com os serviços `app` e `db` |

> [!NOTE]
> Os prompts abaixo já trazem as decisões da stack. Isso evita que o agente gaste tempo perguntando o que já está decidido.

---

## Passo 0: Preparação

### Checklist

- [ ] Claude Code instalado (`claude --version`)
- [ ] Plugin TecSpec instalado (`claude plugin list` mostra `tecspec`)
- [ ] MCPs `context7`, `exa` e `Ref` conectados (rode `/mcp` dentro do Claude Code)
- [ ] Docker e Docker Compose funcionando (`docker compose version`)
- [ ] Imagem do Postgres já baixada: `docker pull postgres:16`
- [ ] Porta `8000` livre
- [ ] O arquivo `specs/DESIGN_SYSTEM.md` existe no projeto

### Comandos

```bash
cd ~/git/unibh-agentspec
git status
claude
```

### O que esperar

- O Claude Code abre na pasta do projeto.
- Ao iniciar a sessão, o TecSpec detecta a stack e cria `.detected-stack*.md`. No projeto vazio, a detecção encontra pouca coisa, e isso é normal.
- Dentro do Claude Code, o `/` mostra `/brainstorm`, `/define`, `/design`, `/build` e `/ship` na lista.

---

## Passo 1: `/brainstorm` (explorar a ideia)

### Prompt

```text
/brainstorm "Quero um totem de autoatendimento para uma lanchonete. O cliente toca na tela do totem, escolhe produtos do cardápio, monta o pedido e recebe o número do pedido. Uma tela de cozinha mostra os pedidos em ordem de chegada, e o atendente muda o estado do pedido (recebido, preparando, pronto, entregue). Uma TV mostra os pedidos em preparo e os prontos. É uma demonstração para uma oficina: precisa subir com um único docker compose up, sem login e sem etapa de build no frontend. Stack: FastAPI, SQLAlchemy com PostgreSQL 16 (container db no docker compose), telas em HTML, Tailwind via CDN e JavaScript puro, testes com pytest. O visual segue o design system já definido em specs/DESIGN_SYSTEM.md (preto, laranja, amarelo e vermelho). O cardápio tem 10 produtos simulados, carregados no banco na subida da aplicação: Hambúrguer clássico (R$ 24,90), X-Bacon (R$ 29,90), Cachorro-quente (R$ 16,90) e Batata frita (R$ 14,90) em Lanches; Crepe de queijo e presunto (R$ 19,90) e Crepe de chocolate com morango (R$ 21,90) em Crepes; Suco de laranja (R$ 9,90), Suco de abacaxi com hortelã (R$ 10,90) e Milk shake de chocolate (R$ 18,90) em Bebidas; Sundae de morango (R$ 12,90) em Sobremesas."
```

### O que esperar

- O agente faz **uma pergunta por vez**, no mínimo três, e oferece opções de resposta.
- Pode perguntar se você tem amostras ou exemplos. Responda que não tem.
- Depois propõe **2 ou 3 abordagens** com prós e contras e recomenda uma.
- Ao final grava `.claude/sdd/features/BRAINSTORM_{FEATURE}.md` (o nome vem da ideia, algo como `BRAINSTORM_TOTEM_ATENDIMENTO.md`).

### Respostas sugeridas para as perguntas

As perguntas variam. Use estas respostas conforme o tema que aparecer:

| Se o agente perguntar sobre… | Responda |
|---|---|
| Fluxo do cliente | `Tela inicial "Toque para começar", cardápio com abas de categoria, carrinho com mais e menos, "Finalizar pedido" e tela de confirmação com o número do pedido.` |
| Numeração dos pedidos | `Número sequencial de 3 dígitos (001, 002…), que reinicia todo dia.` |
| Estados do pedido | `Recebido, Preparando, Pronto, Entregue e Cancelado.` |
| Pagamento | `Fora do escopo. O pedido é só registrado, sem cobrança.` |
| Banco de dados | `PostgreSQL 16 em um container separado (serviço db), com volume para os dados. Tabelas de produtos, pedidos e itens do pedido. Sem migrations: as tabelas são criadas na subida da aplicação.` |
| Carga do cardápio | `Os 10 produtos são inseridos na subida da aplicação, sem duplicar se já existirem.` |
| Dois atendentes iniciando ao mesmo tempo | `Nunca podem pegar o mesmo pedido. Usar bloqueio de linha no PostgreSQL (SELECT ... FOR UPDATE SKIP LOCKED).` |
| Atualização do painel | `Atualização a cada 2 segundos por polling. Sem WebSocket, para manter simples.` |
| Aviso sonoro | `Quando um pedido fica pronto, o painel fala "Pedido 12, pronto", usando a voz do navegador (Web Speech API).` |
| Autenticação | `Sem login. É demonstração.` |
| Inatividade do totem | `Volta à tela inicial após 30 segundos sem toque. A confirmação do pedido some após 8 segundos.` |
| Imagens dos produtos | `Sem arquivos de imagem. Cada produto usa um emoji como ícone.` |
| Visual e acessibilidade | `Segue o specs/DESIGN_SYSTEM.md, com alto contraste, botões grandes para toque e leitura à distância no painel.` |
| Fora do escopo | `Pagamento, impressão, estoque, login, relatórios, múltiplas lojas e personalização de itens.` |
| Amostras de dados | `Não temos.` |

### Como verificar

1. O arquivo `BRAINSTORM_*.md` existe:
   ```bash
   ls .claude/sdd/features/
   ```
2. Ele traz a abordagem escolhida e o que ficou fora do escopo (YAGNI).

> [!IMPORTANT]
> Anote o nome exato do arquivo gerado. Os próximos prompts usam esse nome.

---

## Passo 2: `/define` (requisitos e critérios de aceite)

### Prompt

Troque o nome do arquivo pelo que o passo 1 gerou:

```text
/define .claude/sdd/features/BRAINSTORM_TOTEM_ATENDIMENTO.md
```

### O que esperar

- Como o brainstorm já respondeu quase tudo, o `/define` faz poucas ou nenhuma pergunta.
- O agente calcula a **nota de clareza** (problema, usuários, metas, sucesso e escopo, de 0 a 3 cada). O comando só avança com 12 de 15 ou mais.
- Se a nota ficar abaixo de 12, ele pergunta mais. Responda com detalhe.
- Grava `.claude/sdd/features/DEFINE_{FEATURE}.md` com problema, usuários, metas, requisitos e **critérios de aceite**.

### Como verificar

1. O arquivo `DEFINE_*.md` existe.
2. Os critérios de aceite são testáveis, por exemplo: "ao finalizar um pedido com 2 itens, o sistema gera o próximo número do dia e o pedido aparece na cozinha com o estado Recebido".
3. Os 10 produtos do cardápio estão listados.
4. A nota de clareza é 12/15 ou mais.

### Se algo vier errado

Se um requisito estiver errado ou faltando, corrija sem editar o arquivo à mão:

```text
/iterate .claude/sdd/features/DEFINE_TOTEM_ATENDIMENTO.md "Ajuste: a tela da cozinha deve mostrar quantos pedidos estão aguardando em cada estado."
```

---

## Passo 3: Design system do totem

O design system já está definido em [specs/DESIGN_SYSTEM.md](../specs/DESIGN_SYSTEM.md). Este passo transforma o documento em código: os tokens CSS e uma página de amostra. Ele vem **antes** do `/design` porque a arquitetura precisa saber onde ficam os tokens e os componentes. Quem executa é o agente `web-design-specialist`.

**Paleta definida no documento:**

| Cor | Valor | Papel |
|---|---|---|
| Preto | `#0D0D0D` | Fundo das telas |
| Laranja | `#FF7A00` | Marca, ação principal e botões |
| Amarelo | `#FFC20E` | Preços, número do pedido, pedido pronto |
| Vermelho | `#D62828` | Cancelar, remover e erro |

### Prompt

```text
Use o agente web-design-specialist. Leia o specs/DESIGN_SYSTEM.md, que já está definido (paleta preto, laranja, amarelo e vermelho), e, sem alterar esse documento, crie:

1. app/static/css/tokens.css, com todos os tokens do documento como variáveis CSS em :root, com os mesmos nomes.
2. app/static/design-system.html, uma página de amostra que abre direto no navegador, usando Tailwind via CDN e o tokens.css, com: a paleta, a tipografia, os botões em todas as variantes e estados, as abas de categoria, os 10 produtos do cardápio como cartões de produto, o carrinho, a confirmação do pedido, os quatro selos de estado do pedido, o painel de pedidos e a mensagem de erro.

Use apenas as variáveis dos tokens, nunca valores de cor escritos direto. Não crie as telas do sistema nem o backend agora.
```

### O que esperar

- O agente lê o documento e pergunta pouco ou nada.
- Cria dois arquivos: `app/static/css/tokens.css` e `app/static/design-system.html`. O documento `specs/DESIGN_SYSTEM.md` não muda.
- A amostra mostra fundo preto, botões laranja com texto preto, preços e números de pedido em amarelo, e vermelho nas ações de cancelar e remover.

### Como verificar

1. Os arquivos existem:
   ```bash
   ls specs/ app/static/css/
   ```
2. Abra a amostra no navegador:
   ```bash
   open app/static/design-system.html
   ```
3. Confira:
   - os 10 produtos aparecem com ícone, nome e preço;
   - os quatro estados do pedido se distinguem por ícone e texto, e não só pela cor;
   - o texto sobre laranja e amarelo é preto;
   - os nomes das variáveis em `tokens.css` são os mesmos do documento.
4. Se algo não agradar, peça o ajuste em uma frase, por exemplo: `Aumente o raio dos cartões de produto e deixe o preço maior. Atualize o tokens.css e a página de amostra.`

---

## Passo 4: `/design` (arquitetura)

### Prompt

```text
/design .claude/sdd/features/DEFINE_TOTEM_ATENDIMENTO.md "Toda a interface deve seguir specs/DESIGN_SYSTEM.md e usar os tokens de app/static/css/tokens.css. O banco é PostgreSQL 16 no serviço db do docker compose. Os 10 produtos do cardápio são carregados na subida da aplicação."
```

### O que esperar

- O `design-agent` lê o `DEFINE` e propõe a arquitetura.
- O documento traz um **manifesto de arquivos**, com o agente responsável por cada um (por exemplo `fastapi-architect`, `sqlalchemy-specialist`, `postgresql-analyst`, `web-design-specialist`, `docker-ops`, `test-generator`).
- Grava `.claude/sdd/features/DESIGN_{FEATURE}.md`.

Estrutura que o design deve propor (confira, e corrija se vier muito diferente):

```text
app/
├── main.py              # FastAPI, rotas e arquivos estáticos
├── database.py          # engine e sessão (PostgreSQL via DATABASE_URL)
├── models.py            # Produto, Pedido e ItemPedido
├── schemas.py           # Pydantic
├── seed.py              # carga dos 10 produtos
├── services/pedidos.py  # número do dia, estados e bloqueio de linha
├── routers/             # cardápio, pedidos, cozinha e painel
└── static/
    ├── css/tokens.css   # tokens do design system
    ├── totem.html, cozinha.html, painel.html
    └── js/
specs/DESIGN_SYSTEM.md
tests/                   # pytest
Dockerfile
docker-compose.yml       # serviços app e db
.env.example             # POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_DB, DATABASE_URL
requirements.txt
```

### Como verificar

1. O arquivo `DESIGN_*.md` existe.
2. Cada critério de aceite do `DEFINE` aparece coberto no design.
3. Cada decisão técnica tem um motivo escrito.
4. O compose tem os serviços `app` e `db`, com **healthcheck** no `db` e o `app` esperando o banco ficar saudável.
5. "Iniciar o próximo pedido" usa `FOR UPDATE SKIP LOCKED`, para dois atendentes nunca pegarem o mesmo pedido.
6. A carga dos produtos não duplica registros quando a aplicação reinicia.
7. As telas citam o `DESIGN_SYSTEM.md` e os tokens.

---

## Passo 5: `/build` (o código é gerado)

### Prompt

```text
/build .claude/sdd/features/DESIGN_TOTEM_ATENDIMENTO.md
```

### O que esperar

- O Claude Code pede **permissão** para criar arquivos e rodar comandos. Aprove conforme aparecer.
- Os arquivos do manifesto são criados em ordem, um a um, com verificação (sintaxe, lint, testes).
- O fim da execução traz um resumo e grava `.claude/sdd/reports/BUILD_REPORT_{FEATURE}.md`.
- Leva alguns minutos.

### Como verificar

```bash
ls app app/static tests
cat .claude/sdd/reports/BUILD_REPORT_TOTEM_ATENDIMENTO.md
```

O relatório deve listar os arquivos criados, os testes executados e o que ficou pendente.

### Se der erro

| Sintoma | O que fazer |
|---|---|
| O build para pedindo uma decisão | Responda à pergunta e peça para continuar |
| Um teste falha | Cole o erro no Claude Code e peça: `Corrija o teste que falhou e rode a suíte de novo.` |

---

## Passo 6: Rodar e testar o totem

### Prompt

```text
Prepare o .env a partir do .env.example, suba a aplicação com docker compose e confirme que o banco está saudável, que os 10 produtos foram carregados e que as três telas respondem. Me diga as URLs e rode a suíte de testes.
```

Ou, na mão, em outro terminal:

```bash
cp .env.example .env
docker compose up -d --build
docker compose ps
docker compose exec app pytest
```

### O que esperar

- `docker compose ps` mostra `db` como `healthy` e `app` como `running`.
- A aplicação sobe em http://localhost:8000.
- `pytest` termina com `N passed`.

### Roteiro de teste

Abra as três telas em **janelas lado a lado**. O celular pode servir como totem.

| # | Onde | Ação | Resultado esperado |
|---|---|---|---|
| 1 | `/totem` | Toque em **Toque para começar** | Cardápio com as abas Lanches, Crepes, Bebidas e Sobremesas |
| 2 | `/totem` | Em **Lanches**, adicione **Hambúrguer clássico** duas vezes e **Batata frita** | Carrinho com 3 itens e total `R$ 64,70` |
| 3 | `/totem` | Em **Bebidas**, adicione **Milk shake de chocolate** | Carrinho com 4 itens e total `R$ 83,60` |
| 4 | `/totem` | Toque em **Finalizar pedido** | Tela de confirmação com o número `001` em amarelo, que some após 8 segundos |
| 5 | `/totem` | Faça um segundo pedido: **Crepe de chocolate com morango** e **Sundae de morango** | Pedido `002`, total `R$ 34,80` |
| 6 | `/cozinha` | Veja a fila | Pedidos `001` e `002` com o estado **Recebido**, nessa ordem |
| 7 | `/cozinha` | Clique em **Iniciar** | O pedido `001` passa para **Preparando** |
| 8 | `/painel` | Observe, em até 2 segundos | `001` na coluna **Preparando** |
| 9 | `/cozinha` | Clique em **Marcar pronto** no `001` | O pedido `001` passa para **Pronto** |
| 10 | `/painel` | Observe, em até 2 segundos | Destaque em amarelo com `001`, a voz fala "Pedido 1, pronto", e o `001` vai para a coluna **Pronto** |
| 11 | `/cozinha` | Clique em **Entregar** no `001` | O pedido `001` sai do painel |

### Confira os dados no PostgreSQL

Confirme que os dados estão no banco:

```bash
docker compose exec db psql -U totem -d totem -c "SELECT nome, categoria, preco FROM produtos ORDER BY id;"
docker compose exec db psql -U totem -d totem -c "SELECT numero, status, total FROM pedidos ORDER BY id;"
```

A primeira consulta devolve os 10 produtos. A segunda devolve os pedidos feitos no teste.

> [!NOTE]
> Usuário, banco e nomes de tabela e coluna dependem do que o agente gerou. Confira no `.env` e no `models.py`, e ajuste os comandos.

Para conferir que os dados **persistem**, reinicie só a aplicação e recarregue o painel. Os pedidos continuam lá e os produtos não duplicam:

```bash
docker compose restart app
```

### Como verificar pela API (opcional)

```bash
curl -s http://localhost:8000/docs | head -5
```

A página `/docs` do FastAPI lista todas as rotas criadas.

### Se der erro

| Sintoma | Causa provável | O que fazer |
|---|---|---|
| Porta 8000 ocupada | Outro processo | `docker compose down` ou `lsof -i :8000` |
| `app` reinicia com erro de conexão | O banco ainda não estava pronto, ou o `DATABASE_URL` está errado | `docker compose logs db app` e confira o `.env` |
| `db` fica `unhealthy` | Usuário ou senha diferentes de um volume antigo | `docker compose down -v` apaga o volume. Suba de novo |
| Cardápio vazio | A carga dos produtos não rodou | `docker compose logs app` e confira o `seed.py` |
| Painel não fala | Navegador bloqueia áudio sem interação | Clique uma vez na página do painel antes de marcar o pedido como pronto |
| Tela em branco | Erro de JavaScript | Abra o console do navegador (F12) e cole o erro no Claude Code |

---

## Passo 7: `/iterate` (o requisito mudou)

### Prompt

```text
/iterate .claude/sdd/features/DEFINE_TOTEM_ATENDIMENTO.md "Novo requisito: o painel deve mostrar o tempo médio de preparo do dia, calculado entre a criação do pedido e o momento em que ele fica pronto. Mostre em minutos, no rodapé do painel, usando os tokens do design system."
```

### O que esperar

- O `iterate-agent` atualiza o `DEFINE` com o novo requisito e critério de aceite.
- Ele avisa, com **cascata**, que o `DESIGN` e o código também precisam mudar.
- Pergunta se deve atualizar o `DESIGN`. Responda que sim.

Depois, aplique a mudança no código:

```text
/build .claude/sdd/features/DESIGN_TOTEM_ATENDIMENTO.md
```

### Como verificar

1. Faça um pedido no totem, inicie e marque como pronto na cozinha.
2. O rodapé do painel mostra o tempo médio de preparo, no estilo do resto do painel.
3. `docker compose exec app pytest` continua passando, agora com um teste novo.

---

## Passo 8: Revisão, design system, commit e entrega

### 8.1 Revisão de código

```text
/review
```

**Esperado:** relatório com achados por gravidade (segurança, bugs, estilo). Se a ferramenta CodeRabbit não estiver instalada, a revisão do Claude ainda roda. Para corrigir o que fizer sentido:

```text
Corrija os achados críticos e importantes do review e rode os testes de novo.
```

### 8.2 Auditoria do design system

O agente `design-system-auditor` confere se as telas obedecem ao documento do passo 3:

```text
Use o agente design-system-auditor para auditar app/static/totem.html, cozinha.html e painel.html contra specs/DESIGN_SYSTEM.md. Liste os desvios (cores fora dos tokens, texto branco sobre laranja ou amarelo, alvos de toque menores que 80px no totem, fonte abaixo de 24px no totem e no painel, textos fora do padrão) e corrija os que encontrar.
```

**Esperado:**
- Uma lista de desvios por tela, por exemplo uma cor escrita direto no HTML em vez do token.
- As correções aplicadas nos arquivos.
- O aviso final de que as telas estão em conformidade com o documento.

### 8.3 Commit

```text
/commit
```

**Esperado:** uma mensagem no padrão Conventional Commits, por exemplo `feat: adiciona totem de autoatendimento com cozinha e painel`. Confirme o commit.

> [!IMPORTANT]
> Confirme que o `.env` **não** entrou no commit. Só o `.env.example` deve ir para o Git.

### 8.4 Entrega

```text
/ship .claude/sdd/features/DEFINE_TOTEM_ATENDIMENTO.md
```

**Esperado:**
- Os documentos da feature vão para `.claude/sdd/archive/{FEATURE}/`.
- É criado um `SHIPPED_{DATA}.md` com o que foi entregue e as **lições aprendidas**.

### Como verificar

```bash
ls .claude/sdd/archive/*/
git log --oneline
```

---

## Resumo do que ficou no repositório

Ao final, o repositório tem `.claude/sdd/archive/` e `specs/DESIGN_SYSTEM.md`:

| Fase | Documento que ficou |
|---|---|
| Brainstorm | A ideia, as alternativas e o que ficou fora |
| Define | Requisitos e critérios de aceite |
| Design system | Regras visuais, tokens e componentes |
| Design | Arquitetura e manifesto de arquivos |
| Build | Código e relatório |
| Ship | Lições aprendidas |

---

## Apêndice: prompts de apoio

Use quando precisar sair do trilho sem perder tempo.

**Explicar um arquivo**
```text
Explique o arquivo app/services/pedidos.py em linguagem simples.
```

**Explicar o bloqueio de linha do PostgreSQL**
```text
Explique, com um exemplo de dois atendentes clicando em Iniciar ao mesmo tempo, por que usamos FOR UPDATE SKIP LOCKED ao iniciar o próximo pedido.
```

**Entender o estado do projeto**
```text
/status
```

**Gerar um diagrama da arquitetura**
```text
/generate-web-diagram "Arquitetura do totem de autoatendimento: totem, cozinha e painel conversando com a API FastAPI e o PostgreSQL, tudo em docker compose"
```

**Segunda opinião de outro modelo** (precisa de `OPENROUTER_API_KEY`)
```text
/judge .claude/sdd/features/DESIGN_TOTEM_ATENDIMENTO.md
```

**Recomeçar do zero**
```bash
docker compose down -v
git restore . && git clean -fd app tests Dockerfile docker-compose.yml requirements.txt .env.example .claude/sdd
```

> [!WARNING]
> O comando de recomeçar apaga os dados do banco (`-v`) e os arquivos não commitados. Ele **não** apaga `specs/DESIGN_SYSTEM.md`.
