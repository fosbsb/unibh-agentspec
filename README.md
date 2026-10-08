<div align="center">

# Oficina de Desenvolvimento com Agentes da UniBH - Tecnisys

**Spec-Driven Development: construindo software com o TecSpec e o Claude Code**

![Oficina](https://img.shields.io/badge/oficina-UniBH%202026-1e3a8a?style=flat-square)
![Nível](https://img.shields.io/badge/n%C3%ADvel-iniciante%20a%20intermedi%C3%A1rio-64748b?style=flat-square)
![Licença MIT](https://img.shields.io/badge/licen%C3%A7a-MIT-22c55e?style=flat-square)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-fosbsb-0A66C2?style=flat-square)](https://www.linkedin.com/in/fosbsb/)

**Ferramentas**

![Claude Code](https://img.shields.io/badge/Claude%20Code-CLI%20%2B%20VS%20Code-d97757?style=flat-square)
![TecSpec](https://img.shields.io/badge/TecSpec-plugin%202.1.0-7c3aed?style=flat-square)
![Agentes](https://img.shields.io/badge/agentes-78-0ea5e9?style=flat-square)
![KB](https://img.shields.io/badge/KB-71%20dom%C3%ADnios-16a34a?style=flat-square)
![SDD](https://img.shields.io/badge/workflow-SDD%205%20fases-f59e0b?style=flat-square)
![MCP](https://img.shields.io/badge/MCP-context7%20%2B%20exa%20%2B%20Ref-db2777?style=flat-square)

</div>

---

Nesta oficina, você aprende a construir software **a partir de uma especificação**, com o Claude Code e o plugin **TecSpec** trabalhando como uma equipe de especialistas. Em vez de pedir "faz um app" e torcer, você passa por fases (ideia, requisitos, arquitetura, código e entrega), e cada fase deixa um documento que a próxima lê.

O foco não é digitar menos código. É **decidir antes de codar** e deixar a IA executar com contexto, critérios de aceite e rastreabilidade.

> [!NOTE]
> **Projeto de exemplo.** Ao longo da oficina construímos um totem de autoatendimento de lanchonete. O passo a passo está no [roteiro](roteiro/ROTEIRO.md) e o design system em [specs/DESIGN_SYSTEM.md](specs/DESIGN_SYSTEM.md).

| Parte | O que você faz | Conceito |
|---|---|---|
| 0. Setup | Instala o Claude Code e o plugin TecSpec | Plugin, marketplace, MCP |
| 1. Conhecer o TecSpec | Explora agentes, KB e comandos | Especialistas, base de conhecimento |
| 2. Ideia e requisitos | `/tecspec:workflow:brainstorm` e `/tecspec:workflow:define` | Escopo, critérios de aceite |
| 3. Arquitetura | `/tecspec:workflow:design` | Decisões técnicas, plano de arquivos |
| 4. Código | `/tecspec:workflow:build` | Execução com verificação |
| 5. Entrega | `/tecspec:workflow:ship` | Arquivamento e lições aprendidas |
| 6. Projeto de exemplo | Totem de autoatendimento ([roteiro](roteiro/ROTEIRO.md)) | Tudo junto |

---

## Como o TecSpec funciona

```text
┌─────────────────────────┐         ┌─────────────────────────┐         ┌─────────────────────────┐
│ VOCÊ                    │         │ CLAUDE CODE             │         │ PLUGIN TECSPEC          │
│                         │  prompt │                         │  chama  │                         │
│ descreve a ideia e      │  ────►  │ lê o seu projeto,       │  ────►  │ 78 agentes, 71 domínios │
│ aprova cada fase        │         │ conversa e edita        │         │ de KB e 35 comandos     │
│ no VS Code              │         │ arquivos                │         │ instalado uma vez       │
└─────────────────────────┘         └─────────────────────────┘         └─────────────────────────┘
                                                 │
                                  ┌──────────────┴─────────────────┐
                                  ▼                                ▼
                     ┌─────────────────────────┐      ┌─────────────────────────┐
                     │ .claude/ (seu projeto)  │      │ MCP SERVERS             │
                     │                         │      │                         │
                     │ sdd/features/           │      │ context7, exa e Ref     │
                     │ agents/ (overrides)     │      │ docs e busca atuais     │
                     └─────────────────────────┘      └─────────────────────────┘
```

| Caixa | O que faz | Onde roda |
|---|---|---|
| **Você** | Descreve o que quer, responde às perguntas e aprova cada fase | Seu computador |
| **Claude Code** | Executa os comandos, lê e edita os arquivos do projeto | Terminal ou extensão do VS Code |
| **Plugin TecSpec** | Fornece agentes, base de conhecimento, comandos e hooks | Instalado no seu usuário |
| **`.claude/` do projeto** | Guarda os documentos de cada fase e os agentes customizados | Pasta do projeto |
| **MCP servers** | Trazem documentação atual de bibliotecas e busca na web | Serviços externos |

---

## Pré-requisitos

- [Claude Code](https://claude.com/claude-code) instalado (`claude --version`)
- VS Code (opcional, mas recomendado)
- [Git](https://git-scm.com/downloads)
- Python 3 (usado pelos scripts do plugin)
- Chaves gratuitas para os MCPs **context7**, **exa** e **Ref** (opcionais, mas os agentes rendem mais com elas)
- *(Opcional)* `OPENROUTER_API_KEY`, só para a segunda opinião de outro modelo (`/tecspec:review:judge`)

### Baixe o projeto

```bash
git clone https://github.com/fosbsb/unibh-agentspec.git
cd unibh-agentspec
```

Abra a **pasta do projeto** no VS Code (*File > Open Folder*) e use o terminal dessa pasta.

---

## Parte 0: Instalar o TecSpec

O TecSpec é um plugin do Claude Code. Você instala uma vez e ele fica disponível em todos os projetos.

```bash
claude plugin marketplace add https://gitlab.tecnisys.com.br/publico/claude-code-toolkit.git
claude plugin install tecspec
```

Para atualizar depois:

```bash
claude plugin update tecspec
```

### Registre os MCPs

Os agentes usam três servidores MCP. Registre uma vez, no escopo do usuário:

```bash
claude mcp add --scope user context7 -- npx -y @upstash/context7-mcp --api-key SUA_CHAVE
claude mcp add --scope user --transport http exa "https://mcp.exa.ai/mcp?exaApiKey=SUA_CHAVE"
claude mcp add --scope user --transport http Ref https://api.ref.tools/mcp --header "x-ref-api-key: SUA_CHAVE"
```

### Como verificar

1. Rode `claude plugin list` e confirme que `tecspec` aparece.
2. Abra o Claude Code na pasta do projeto e rode `/mcp`: os três servidores devem estar conectados.
3. Ao iniciar a sessão, o TecSpec detecta a stack do projeto e grava `.detected-stack*.md`. Se o arquivo apareceu, os hooks funcionaram.

---

## Parte 1: Conhecer o TecSpec

### O que vem no plugin

| Peça | Quantidade | Para que serve |
|---|---|---|
| **Agentes** | 78, em 14 categorias | Especialistas que recebem uma tarefa focada (FastAPI, PostgreSQL, React, dbt, Spark, Docker…) |
| **Knowledge base** | 71 domínios | Referência técnica curta e atual, que os agentes consultam em vez de adivinhar |
| **Comandos** | 35 | Atalhos como `/tecspec:workflow:define`, `/tecspec:workflow:build`, `/tecspec:review:review`, `/tecspec:git:commit` |
| **Skills** | 5 | Roteamento automático de tarefas para o agente certo |
| **Hooks** | 2 | Detectam a stack do projeto ao iniciar a sessão |

### Categorias de agentes

| Categoria | Exemplos |
|---|---|
| `architect` | `the-planner`, `schema-designer`, `pipeline-architect` |
| `backend` | `fastapi-architect`, `sqlalchemy-specialist`, `celery-worker-builder` |
| `frontend` | `react-ui-developer`, `shadcn-ui-specialist`, `web-design-specialist` |
| `database` | `postgresql-analyst`, `postgresql-dba`, `postgis-specialist` |
| `infra` | `docker-ops`, `devops-engineer` |
| `cloud` | `aws-lambda-architect`, `gcp-data-architect`, `supabase-specialist` |
| `data-engineering` | `dbt-specialist`, `spark-specialist`, `airflow-specialist` |
| `python` | `python-developer`, `code-reviewer`, `code-cleaner` |
| `test` | `test-generator`, `data-quality-analyst` |
| `dev` | `commit-crafter`, `codebase-explorer`, `prompt-crafter` |
| `workflow` | `brainstorm-agent`, `define-agent`, `design-agent`, `build-agent`, `ship-agent`, `iterate-agent` |

Você não precisa escolher o agente na mão: o roteador do TecSpec escolhe pelo tipo de arquivo e pela intenção da tarefa. Quando quiser chamar um específico, cite o nome no pedido.

### Experimente

Dentro do Claude Code, na pasta do projeto:

```text
Explore este repositório e me diga o que existe nele.
```

O agente `codebase-explorer` devolve um resumo executivo e um mergulho nos detalhes.

---

## Os dois fluxos de trabalho

| Fluxo | Quando usar | Comandos |
|---|---|---|
| **Dev Loop** | Tarefa de 1 a 4 horas, escopo claro | `/tecspec:dev:dev` |
| **SDD (5 fases)** | Feature com várias partes, que precisa de rastreabilidade | `/tecspec:workflow:brainstorm`, `/tecspec:workflow:define`, `/tecspec:workflow:design`, `/tecspec:workflow:build`, `/tecspec:workflow:ship` |

Esta oficina usa o **SDD**.

### As 5 fases

```text
brainstorm  →  define  →  design  →  build  →  ship
  (ideia)    (requisitos) (arquitetura) (código) (entrega)
```

Os comandos usam o prefixo do plugin: `/tecspec:workflow:<fase>`.

| Fase | Comando | Entrada | Saída |
|---|---|---|---|
| 0. Brainstorm | `/tecspec:workflow:brainstorm` | Sua ideia crua | `.claude/sdd/features/BRAINSTORM_{FEATURE}.md` |
| 1. Define | `/tecspec:workflow:define` | O brainstorm ou um texto livre | `.claude/sdd/features/DEFINE_{FEATURE}.md` |
| 2. Design | `/tecspec:workflow:design` | O `DEFINE_*.md` | `.claude/sdd/features/DESIGN_{FEATURE}.md` |
| 3. Build | `/tecspec:workflow:build` | O `DESIGN_*.md` | Código e `.claude/sdd/reports/BUILD_REPORT_{FEATURE}.md` |
| 4. Ship | `/tecspec:workflow:ship` | O `DEFINE_*.md` | `.claude/sdd/archive/{FEATURE}/SHIPPED_{DATA}.md` |

A fase 0 é opcional. Se os requisitos mudarem no meio do caminho, use `/tecspec:workflow:iterate` para atualizar o documento certo, e o TecSpec avisa o que precisa ser refeito nas fases seguintes.

> [!TIP]
> Cada fase tem um **quality gate**. Por exemplo, o `/tecspec:workflow:define` só avança com clareza de pelo menos 12/15. Se o documento não passar, o comando mostra o que falta.

---

## Parte 2: Ideia e requisitos (`/tecspec:workflow:brainstorm` e `/tecspec:workflow:define`)

### Por que usar a spec aqui

Pedir "faz um sistema de X" deixa a IA decidir tudo por você. Escrever o problema, quem usa e o que significa "pronto" antes de codar faz o resto da oficina render.

### Passo a passo

1. **Explore a ideia:**
   ```text
   /tecspec:workflow:brainstorm "descreva aqui a sua ideia"
   ```
   O agente conversa com você, compara abordagens e registra a decisão em `BRAINSTORM_{FEATURE}.md`.
2. **Capture os requisitos:**
   ```text
   /tecspec:workflow:define .claude/sdd/features/BRAINSTORM_{FEATURE}.md
   ```
   Saem o problema, os usuários, as metas, o que fica fora do escopo e os **critérios de aceite**.

### Como verificar

1. O arquivo `DEFINE_{FEATURE}.md` existe em `.claude/sdd/features/`.
2. Ele tem critérios de aceite que você consegue testar (e não frases como "deve ser rápido").
3. Você leu o documento inteiro e concorda com ele.

### Se der erro

| Sintoma | Causa provável | O que fazer |
|---|---|---|
| Comando `/tecspec:workflow:define` não existe | Plugin não instalado ou sessão antiga | Rode `claude plugin list` e reinicie o Claude Code |
| Clareza abaixo de 12/15 | Requisitos vagos | Responda às perguntas do agente com mais detalhe |
| O agente inventa requisitos | Pedido muito aberto | Corrija no documento e rode `/tecspec:workflow:iterate` |

---

## Parte 3: Arquitetura (`/tecspec:workflow:design`)

### Por que usar a spec aqui

O design transforma "o que" em "como": componentes, decisões técnicas, lista de arquivos e quais agentes vão construir cada parte.

### Passo a passo

```text
/tecspec:workflow:design .claude/sdd/features/DEFINE_{FEATURE}.md
```

### Como verificar

1. `DESIGN_{FEATURE}.md` existe e cita os arquivos que serão criados.
2. Cada decisão tem um motivo escrito.
3. Cada critério de aceite do `DEFINE` aparece coberto no design.

---

## Parte 4: Código (`/tecspec:workflow:build`)

### Por que usar a spec aqui

O `/tecspec:workflow:build` lê o design e delega cada arquivo ao agente especialista certo, verificando o resultado conforme avança.

### Passo a passo

```text
/tecspec:workflow:build .claude/sdd/features/DESIGN_{FEATURE}.md
```

### Como verificar

1. O código foi criado nos caminhos listados no design.
2. Os testes e o lint do projeto passam.
3. `BUILD_REPORT_{FEATURE}.md` registra o que foi feito e o que ficou pendente.

---

## Parte 5: Entrega (`/tecspec:workflow:ship`)

Quando o build estiver pronto e aprovado por você:

```text
/tecspec:workflow:ship .claude/sdd/features/DEFINE_{FEATURE}.md
```

Os documentos da feature são arquivados em `.claude/sdd/archive/{FEATURE}/`, junto com um `SHIPPED_{DATA}.md` com as lições aprendidas.

---

## Comandos úteis no dia a dia

| Comando | Para que serve |
|---|---|
| `/tecspec:dev:dev "tarefa"` | Dev Loop: monta um `PROMPT_*.md` e executa com verificação |
| `/tecspec:workflow:iterate` | Atualiza qualquer fase quando algo muda |
| `/tecspec:review:review` | Revisão de código dupla (CodeRabbit + Claude) |
| `/tecspec:review:judge` | Segunda opinião de outro modelo (precisa de `OPENROUTER_API_KEY`) |
| `/tecspec:git:commit` | Mensagem de commit no padrão Conventional Commits |
| `/tecspec:workflow:create-pr` | Pull request com descrição estruturada |
| `/tecspec:core:status` | Relatório de saúde do projeto |
| `/tecspec:core:readme-maker` | Gera um README a partir do código |
| `/tecspec:visual-explainer:generate-web-diagram` | Diagrama HTML para explicar uma ideia |

As fases do SDD aceitam `--judge` para pedir a segunda opinião do outro modelo (`--judge=strict` bloqueia em caso de reprovação).

---

## Personalize: agentes locais

Agentes em `.claude/agents/` do projeto **têm prioridade** sobre os do plugin que tenham o mesmo `name:`. Veja o [guia da pasta](.claude/agents/README.md).

| Pasta | Para que serve |
|---|---|
| `.claude/agents/workflow/` | Sobrescrever os agentes das fases do SDD |
| `.claude/agents/custom/` | Criar agentes novos, só deste projeto |

---

## Estrutura do repositório

```text
unibh-agentspec/
├── .claude/
│   ├── agents/              # overrides e agentes próprios (veja o README da pasta)
│   └── sdd/                 # documentos de cada fase, criados pelos comandos
├── roteiro/                 # passo a passo da oficina (ROTEIRO.md)
├── specs/                   # DESIGN_SYSTEM.md do projeto de exemplo
└── README.md
```

---

## Projeto de exemplo

O **totem de autoatendimento** é construído passo a passo com as cinco fases acima. O [roteiro](roteiro/ROTEIRO.md) traz o prompt de cada etapa, o que esperar e como verificar.

### Executar a demonstração

```bash
docker compose up --build
```

| Tela | Endereço | Dispositivo |
|---|---|---|
| Totem | http://localhost:8000/totem | Cliente, 1080x1920, só toque |
| Cozinha | http://localhost:8000/cozinha | Atendente, desktop ou tablet |
| Painel | http://localhost:8000/painel | TV 1920x1080 |

- Sem login e sem build de frontend. O Tailwind vem do CDN, então a máquina precisa de internet.
- Na TV, toque em **Ativar som** para liberar a voz do navegador.
- `docker compose down` apaga os pedidos, e o próximo `up` recomeça só com o cardápio.
- Ao atualizar uma versão antiga, rode `docker compose down` antes do `up`: o banco não tem volume e o `create_all` não altera tabelas existentes.
- A senha do pedido tem 3 dígitos (100 a 199) e é reaproveitada depois que o pedido é entregue.
- A demo não tem autenticação. Não a exponha na internet.

**Testes** (sem Docker para o banco, com SQLite em memória; exige Python 3.10 ou superior):

```bash
pip install -r requirements.txt
pytest
```

---

## Documentação

| Assunto | Onde |
|---|---|
| Plugin TecSpec | [gitlab.tecnisys.com.br/publico/claude-code-toolkit](https://gitlab.tecnisys.com.br/publico/claude-code-toolkit) |
| Agentes locais | [.claude/agents/README.md](.claude/agents/README.md) |
| Claude Code | [claude.com/claude-code](https://claude.com/claude-code) |
| Projeto AgentSpec (origem do fluxo SDD) | [github.com/luanmorenommaciel/agentspec](https://github.com/luanmorenommaciel/agentspec) |
| Roteiro da oficina | [roteiro/ROTEIRO.md](roteiro/ROTEIRO.md) |
| Spec-Driven Development | Comandos `/tecspec:workflow:brainstorm`, `/tecspec:workflow:define`, `/tecspec:workflow:design`, `/tecspec:workflow:build` e `/tecspec:workflow:ship` |

---

## Créditos

O fluxo de Spec-Driven Development usado nesta oficina (brainstorm, define, design, build e ship) e a ideia de agentes especialistas com base de conhecimento vêm do projeto **AgentSpec**, de Luan Moreno M. Maciel: [github.com/luanmorenommaciel/agentspec](https://github.com/luanmorenommaciel/agentspec). O plugin TecSpec, usado aqui, é a versão distribuída pela Tecnisys.

---

## Licença

[MIT](LICENSE) © 2026 Flaviano O. Silva. Material didático, sem fins comerciais.
