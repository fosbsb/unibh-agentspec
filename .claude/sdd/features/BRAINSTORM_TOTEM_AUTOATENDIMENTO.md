# BRAINSTORM: Totem de Autoatendimento

> Exploração da ideia antes da captura de requisitos (Fase 0)

## Metadados

| Atributo | Valor |
|---|---|
| **Feature** | TOTEM_AUTOATENDIMENTO |
| **Data** | 2026-10-08 |
| **Autor** | brainstorm (Claude) com Flaviano O. Silva |
| **Status** | Pronto para /define |

---

## Ideia inicial

Totem de autoatendimento para uma lanchonete. O cliente escolhe produtos do cardápio na tela, monta o pedido e recebe o número. Uma tela de cozinha mostra os pedidos em ordem de chegada e o atendente muda o estado (recebido, preparando, pronto, entregue). Uma TV mostra os pedidos em preparo e os prontos.

**Contexto:** demonstração para uma oficina. Sobe com um único `docker compose up`, sem login e sem etapa de build no frontend.

**Stack definida:** FastAPI, SQLAlchemy, PostgreSQL 16 (container `db`), HTML + Tailwind via CDN + JavaScript puro, pytest.

---

## Perguntas e respostas

| # | Pergunta | Resposta | Impacto |
|---|---|---|---|
| 1 | Como cozinha e TV recebem atualizações? | Polling a cada 2s | Sem WebSocket/SSE; API só com REST |
| 2 | O que fazer com o estado "Cancelado" do design system? | Fora do escopo | Fluxo linear de 4 estados; ajustar o design system |
| 3 | Como falar "Pedido N, pronto" na TV? | Web Speech API (pt-BR) | Botão "Ativar som" na TV por causa da política de autoplay |
| 4 | Há amostras para ancorar a solução? | Nenhuma além das existentes | Cardápio e design system são a fonte de verdade |

---

## Amostras

| Tipo | Localização | Uso |
|---|---|---|
| Design system | `specs/DESIGN_SYSTEM.md` | Tokens, componentes, regras de acessibilidade e cardápio de exemplo (seção 8) |
| Cardápio | Descrição do pedido + seção 8 do design system | Seed de 10 produtos, com ícones em emoji |

---

## Abordagens exploradas

### A: Monólito FastAPI com HTML estático e polling (escolhida)

Um serviço `app` serve a API REST e as três telas estáticas. Compose com `app` e `db`.

- **Prós:** caminho mais curto para um `docker compose up` único, sem build de frontend, arquivos fáceis de ler na oficina, testes de API cobrem quase tudo.
- **Contras:** latência de até 2s e tráfego pequeno e constante.

### B: FastAPI com templates Jinja2 (descartada)
Mistura renderização no servidor com atualização dinâmica e acaba pedindo HTMX ou JS de qualquer jeito. O brief pede HTML com JS puro.

### C: API e telas em serviços separados com nginx (descartada)
Mais um container, CORS e configuração. Complexidade desnecessária para a oficina.

---

## Decisões de projeto

| Decisão | Escolha | Motivo |
|---|---|---|
| Arquitetura | Monólito FastAPI + estáticos | Simplicidade e um único `up` |
| Atualização | Polling de 2s | Simples de explicar e de testar |
| Criação de tabelas | `create_all` na subida | Sem Alembic na demo |
| Seed | Na subida, só se a tabela estiver vazia | Reiniciar não duplica produtos |
| Preço | Em centavos (inteiro), total recalculado no servidor | Evita erro de ponto flutuante e valores forjados pelo cliente |
| Itens do pedido | Copiam nome e preço no momento do pedido | O histórico não muda se o produto mudar |
| Número do pedido | Sequencial legível, separado do id interno | Fácil de falar e de ler na TV |
| Estados | `recebido → preparando → pronto → entregue`, só para frente, sem pular | Fluxo previsível; transição inválida devolve 409 |
| Testes de API | `TestClient` com SQLite em memória | Rápidos; o PostgreSQL real é coberto pelo smoke test do compose |

---

## Modelo e API (rascunho)

**Tabelas**
- `produtos`: id, nome, categoria, icone, preco_centavos
- `pedidos`: id, numero, estado, criado_em, preparando_em, pronto_em, entregue_em
- `itens_pedido`: id, pedido_id, produto_id, nome, preco_centavos, quantidade

**Endpoints**
- `GET /api/produtos`
- `POST /api/pedidos` (cria; devolve número e total)
- `GET /api/pedidos?estado=...` (ordem de chegada)
- `PATCH /api/pedidos/{id}/estado` (avança uma etapa)
- Páginas: `/totem`, `/cozinha`, `/painel`

**Estrutura**
```text
docker-compose.yml, Dockerfile, requirements.txt
app/ main.py, database.py, models.py, schemas.py, seed.py, routers/
app/static/ css/tokens.css, js/{api,totem,cozinha,painel}.js, {totem,cozinha,painel}.html
tests/
```

---

## Telas

| Tela | Dispositivo | Comportamento |
|---|---|---|
| `/totem` | 1080x1920 retrato, só toque | Abas de categoria, cartões em 2 colunas, carrinho fixo no rodapé, confirmação com número em 160px, volta ao início em 8s; 30s sem toque volta ao início |
| `/cozinha` | Desktop ou tablet | Fila em ordem de chegada; botões Iniciar, Marcar pronto, Entregar; entregues saem da fila |
| `/painel` | TV 1920x1080 | Colunas Preparando e Pronto; pedido recém-pronto em tela cheia por 6s com voz; rodapé com tempo médio de preparo |

---

## YAGNI: removido do escopo

| Item removido | Motivo | Pode voltar? |
|---|---|---|
| Cancelamento (estado e botão) | Fluxo da demo tem 4 estados | Sim |
| Login, perfis e pagamento | Brief diz "sem login"; pagamento não foi pedido | Sim |
| CRUD de produtos | Cardápio vem do seed | Sim |
| Migrações Alembic | `create_all` basta para a demo | Sim, em produção |
| WebSocket e SSE | Polling decidido | Sim |
| Imagens de produto | Ícones em emoji (design system) | Improvável |
| Observações por item e impressão de senha | Fora do fluxo descrito | Sim |

---

## Requisitos preliminares (para o /define)

**Usuários**

| Usuário | Necessidade |
|---|---|
| Cliente | Escolher produtos, montar o pedido e receber o número, só com toque |
| Atendente/cozinha | Ver a fila em ordem de chegada e avançar o estado |
| Clientes aguardando | Ver na TV o que está em preparo e o que está pronto |

**Must have**
- Seed de 10 produtos em 4 categorias na subida, sem duplicar
- Totem: navegar por categoria, adicionar, alterar quantidade, remover, finalizar e ver o número
- Cozinha: fila em ordem de chegada e avanço de estado
- Painel: listas Preparando e Pronto, destaque do recém-pronto com voz
- `docker compose up` sobe tudo, sem login e sem build de frontend
- Visual conforme `specs/DESIGN_SYSTEM.md`
- Testes pytest para API, transições, seed e total

**Should have**
- Tempo médio de preparo no painel
- Mensagem de erro padronizada (seção 6.9) quando o envio falha, com "Tentar de novo"

**Critérios de sucesso (rascunho)**
- Em máquina limpa, `docker compose up` deixa as três telas acessíveis
- Um pedido feito no totem aparece na cozinha e no painel em até 2s + 2s
- Transição fora de ordem é recusada com 409
- `pytest` passa

---

## Riscos e pontos em aberto

| Item | Tratamento |
|---|---|
| Autoplay de áudio bloqueado na TV | Botão "Ativar som" antes de a voz funcionar |
| App subir antes do banco ficar pronto | `depends_on` com healthcheck no `db` e nova tentativa de conexão |
| Design system desatualizado | Atualizar: remover "Cancelado" e o botão Cancelar; incluir "Entregue" (cor, ícone e selo) |
| Tempo médio de preparo | Definir no /define como medir (de `preparando` a `pronto`) e o que mostrar sem dados |
| Tailwind via CDN exige internet na oficina | Registrar como premissa; avaliar fallback no /design |
| Concorrência no número do pedido | Definir no /design (sequence do PostgreSQL ou contador transacional) |

---

## Próximo passo

```bash
/tecspec:workflow:define .claude/sdd/features/BRAINSTORM_TOTEM_AUTOATENDIMENTO.md
```
