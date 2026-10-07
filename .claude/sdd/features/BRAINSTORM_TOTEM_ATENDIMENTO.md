# BRAINSTORM: Totem de Atendimento

> Exploração da ideia antes da captura de requisitos (Fase 0)

## Metadados

| Atributo | Valor |
|---|---|
| **Feature** | TOTEM_ATENDIMENTO |
| **Data** | 2026-10-07 |
| **Autor** | brainstorm-agent |
| **Status** | Pronto para /define |

---

## Ideia inicial

**Pedido original:** totem de autoatendimento para uma lanchonete. O cliente escolhe produtos no cardápio, monta o pedido e recebe o número. Uma tela de cozinha mostra os pedidos em ordem de chegada e o atendente muda o estado. Uma TV mostra os pedidos em preparo e os prontos.

**Contexto:** demonstração para uma oficina. Precisa subir com um único `docker compose up`, sem login e sem etapa de build no frontend.

**Stack fixada:** FastAPI, SQLAlchemy, PostgreSQL 16 (serviço `db`), HTML com Tailwind via CDN e JavaScript puro, pytest.

**Visual:** segue `specs/DESIGN_SYSTEM.md` (preto, laranja, amarelo e vermelho).

**Cardápio (10 produtos, carregados na subida):** Lanches (Hambúrguer clássico R$ 24,90; X-Bacon R$ 29,90; Cachorro-quente R$ 16,90; Batata frita R$ 14,90), Crepes (queijo e presunto R$ 19,90; chocolate com morango R$ 21,90), Bebidas (Suco de laranja R$ 9,90; Suco de abacaxi com hortelã R$ 10,90; Milk shake de chocolate R$ 18,90) e Sobremesas (Sundae de morango R$ 12,90).

---

## Contexto do projeto

| Aspecto | Observação |
|---|---|
| **Estado do repositório** | Só documentação (README, roteiro, design system). Sem código |
| **Design system** | `specs/DESIGN_SYSTEM.md` v1.0.0 define telas, tokens, componentes e o cardápio com emojis |
| **Template** | `.claude/sdd/templates/BRAINSTORM_TEMPLATE.md` não existe. Estrutura padrão do comando |
| **Telas** | `/totem` (1080x1920, toque), `/painel` (TV 1920x1080, leitura), `/cozinha` (desktop ou tablet) |

---

## Perguntas e respostas

| # | Pergunta | Resposta | Impacto |
|---|---|---|---|
| 1 | Fluxo do cliente no totem | Tela inicial "Toque para começar" → cardápio com abas → carrinho → **tela de revisão** → "Finalizar pedido" → confirmação (8 s). Volta ao início após 30 s sem toque | Adiciona a tela de revisão, que o design system não descreve |
| 2 | Numeração dos pedidos | Sequencial de 3 dígitos (001, 002…), reinicia todo dia | Número único por data. Geração dentro da transação |
| 3 | Estados e cancelamento | Quatro estados: Recebido → Preparando → Pronto → Entregue. **Sem cancelamento** | Remove o estado Cancelado e o botão "Cancelar" do design system |
| 4 | Amostras para ancorar a solução | Nenhuma. Referências: cardápio e design system | Sem dados de ground truth |
| 5 | Atualização das telas | Aprovada a Abordagem A: polling a cada 2 s | Sem SSE nem WebSocket |
| 6 | Escopo (YAGNI) | Confirmado | Ver seção "YAGNI" |
| 7 | Modelo de dados, API e regras | Confirmados | Ver seção "Design resumido" |

---

## Amostras coletadas

Nenhuma amostra externa. As referências do projeto são o cardápio de 10 produtos e o `specs/DESIGN_SYSTEM.md`.

---

## Abordagens exploradas

### Abordagem A: Polling a cada 2 s ⭐ Selecionada

**Por quê:** é o mais simples. Cozinha e painel chamam `GET /api/pedidos` a cada 2 segundos com `fetch`. Não há conexão aberta para gerenciar, uma queda de rede se recupera no próximo ciclo e o código é fácil de explicar e testar com pytest.

**Prós:** simplicidade, robustez, testes diretos, funciona atrás de qualquer proxy.

**Contras:** latência de até 2 s e requisições repetidas sem mudança. Para três telas numa demonstração, isso não pesa.

### Abordagem B: SSE

**Por que não:** a atualização é quase instantânea, mas exige um canal de eventos no backend. Com vários workers precisa de um broker (por exemplo, `LISTEN/NOTIFY` do PostgreSQL). Os testes ficam mais difíceis e a conexão pode cair sem aviso.

### Abordagem C: WebSocket

**Por que não:** é o mais complexo, e a comunicação bidirecional não é necessária. As telas só leem, e o envio de pedido já é por POST.

---

## YAGNI: o que ficou de fora

| Item removido | Motivo | Pode voltar? |
|---|---|---|
| Pagamento | O pedido é só registrado, sem cobrança | Sim |
| Impressão e estoque | Fora do foco da demonstração | Sim |
| Login e perfis | Pedido explícito: sem login | Não, para esta demo |
| Cancelamento de pedido | Decisão da pergunta 3 | Sim |
| Relatórios e múltiplas lojas | Não ajudam a mostrar o fluxo | Sim |
| Personalização de itens | Cada produto entra como está | Sim |
| Observações no pedido | Não foi pedido | Sim |
| Imagens de produto | Emoji como ícone, sem arquivos | Sim |
| Migrations (Alembic) | Tabelas criadas na subida da aplicação | Sim |
| SSE e WebSocket | Polling resolve | Sim |

**Mantidos por já estarem no design system:** tempo médio de preparo no rodapé do painel (6.7) e voz "Pedido 12, pronto" pela Web Speech API.

---

## Design resumido

### Telas

| Tela | Comportamento |
|---|---|
| `/totem` | Início → cardápio com abas (Lanches, Crepes, Bebidas, Sobremesas) → carrinho com − / + / Remover → revisão → confirmação com o número por 8 s → início. Volta ao início após 30 s sem toque. Erro de envio mostra a mensagem 6.9 com "Tentar de novo" e mantém o carrinho |
| `/cozinha` | Fila em ordem de chegada com número, itens, horário e selo de estado. Botões "Iniciar" (Recebido→Preparando), "Marcar pronto" (Preparando→Pronto) e "Entregar" (Pronto→Entregue) |
| `/painel` | "Preparando" à esquerda, "Pronto" à direita. Pedido recém-pronto em destaque por 6 s com voz. Rodapé com o tempo médio de preparo |

### Modelo de dados

| Tabela | Campos principais |
|---|---|
| `produtos` | id, nome (único), categoria, ícone (emoji), preço em centavos |
| `pedidos` | id, número (3 dígitos), data do pedido, estado, criado_em, iniciado_em, pronto_em, entregue_em. Data + número é único |
| `itens_pedido` | id, pedido, produto, quantidade, preço unitário (copiado na criação) |

Os campos `iniciado_em` e `pronto_em` permitem calcular o tempo médio de preparo (regra 4).

### API

| Rota | Função |
|---|---|
| `GET /api/produtos` | Cardápio agrupado por categoria |
| `POST /api/pedidos` | Cria o pedido e devolve o número |
| `GET /api/pedidos` | Fila para cozinha e painel |
| `POST /api/pedidos/{id}/avancar` | Avança o estado, na ordem fixa |

### Regras

1. O pedido tem pelo menos 1 item, e a quantidade por item fica entre 1 e 99. O total é calculado no servidor.
2. `avancar` aceita só a transição seguinte. Se o estado já mudou, devolve 409 e a tela recarrega.
3. A cozinha lista Recebido, Preparando e Pronto em ordem de chegada. Os Entregues saem da fila.
4. O tempo médio de preparo é a média entre `iniciado_em` e `pronto_em`, calculada no servidor.
5. O número do pedido é gerado dentro da transação, com reinício diário.
6. Dois atendentes nunca pegam o mesmo pedido: bloqueio de linha com `SELECT ... FOR UPDATE SKIP LOCKED`.
7. A carga do cardápio na subida não duplica produtos existentes.

---

## Requisitos rascunhados (para o /define)

### Funcionais

| ID | Requisito | Prioridade |
|---|---|---|
| RF-01 | O totem mostra tela inicial, cardápio com abas, carrinho, revisão e confirmação com o número do pedido | Must |
| RF-02 | O cliente adiciona, aumenta, diminui e remove itens no carrinho | Must |
| RF-03 | O sistema cria o pedido com número sequencial de 3 dígitos que reinicia todo dia | Must |
| RF-04 | A cozinha lista os pedidos em ordem de chegada e o atendente avança o estado na ordem fixa | Must |
| RF-05 | O painel mostra os pedidos em preparo e prontos, com atualização a cada 2 s | Must |
| RF-06 | O painel destaca por 6 s o pedido recém-pronto e fala "Pedido N, pronto" | Should |
| RF-07 | O painel mostra o tempo médio de preparo no rodapé | Should |
| RF-08 | O cardápio de 10 produtos é carregado na subida, sem duplicar | Must |
| RF-09 | O totem volta ao início após 30 s sem toque, e a confirmação some após 8 s | Must |
| RF-10 | Falha no envio mostra erro e mantém o carrinho | Should |

### Não funcionais

| ID | Requisito |
|---|---|
| RNF-01 | Sobe com um único `docker compose up`, com serviços `app` e `db` (PostgreSQL 16, com volume) |
| RNF-02 | Frontend sem etapa de build: HTML, Tailwind via CDN e JavaScript puro |
| RNF-03 | Sem login |
| RNF-04 | Visual conforme `specs/DESIGN_SYSTEM.md`, com tokens em `app/static/css/tokens.css` |
| RNF-05 | Testes com pytest cobrindo criação de pedido, numeração diária, transições de estado, conflito e carga do cardápio |
| RNF-06 | Concorrência: transições seguras com bloqueio de linha |

### Ajustes no design system (a fazer antes ou durante o /design)

1. Adicionar a **tela de revisão do pedido** no totem (nova seção de componente).
2. Remover o estado **Cancelado** (seção 3.4) e o botão "Cancelar" da fila da cozinha (seção 6.8).
3. Manter o vermelho em "Remover" item e nas mensagens de erro.
4. Registrar a mudança no histórico (nova versão do documento).

### Fora do escopo

Pagamento, impressão, estoque, login, relatórios, múltiplas lojas, personalização de itens, cancelamento, WebSocket e SSE.

---

## Riscos e pontos de atenção

| Risco | Mitigação |
|---|---|
| Voz do navegador exige interação prévia do usuário (política de autoplay) | O painel pede um toque inicial para habilitar o áudio |
| Race condition na numeração diária | Gerar o número dentro da transação, com restrição única de data + número |
| Fuso horário no reinício diário | Definir o fuso (America/Sao_Paulo) no `/define` |
| Design system fora de sincronia com as decisões | Aplicar os ajustes listados antes do `/design` |
| PostgreSQL ainda não pronto quando o app sobe | Healthcheck no `db` e `depends_on` com condição saudável |

---

## Qualidade

- [x] Pelo menos 3 perguntas de descoberta (7 feitas)
- [x] Pergunta sobre amostras
- [x] Pelo menos 2 abordagens exploradas (3)
- [x] YAGNI aplicado
- [x] Pelo menos 2 validações (escopo e arquitetura; modelo, API e regras)
- [x] Abordagem confirmada pelo usuário
- [x] Requisitos rascunhados

---

## Próximo passo

```bash
/define .claude/sdd/features/BRAINSTORM_TOTEM_ATENDIMENTO.md
```
