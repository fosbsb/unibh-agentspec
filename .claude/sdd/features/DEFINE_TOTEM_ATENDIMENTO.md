# DEFINE: Totem de Atendimento

> Requisitos capturados e validados (Fase 1)

## Metadados

| Atributo | Valor |
|---|---|
| **Feature** | TOTEM_ATENDIMENTO |
| **Data** | 2026-10-07 |
| **Origem** | `.claude/sdd/features/BRAINSTORM_TOTEM_ATENDIMENTO.md` |
| **Tipo de entrada** | brainstorm_document |
| **Clarity Score** | 14/15 |
| **Status** | Pronto para /design |

---

## Problema

Uma lanchonete simulada precisa de um fluxo de autoatendimento: o cliente monta o pedido sozinho, a cozinha enxerga a fila em ordem de chegada e os clientes que aguardam sabem quando o pedido fica pronto. O projeto é uma **demonstração para uma oficina** de desenvolvimento com agentes, então precisa subir com um único comando, sem login e sem etapa de build no frontend.

## Usuários

| Usuário | Dispositivo | Necessidade | Dor a evitar |
|---|---|---|---|
| **Cliente** | Totem 1080x1920, só toque | Escolher produtos, revisar e receber o número do pedido | Tela confusa, alvos pequenos, perder o carrinho num erro |
| **Atendente / cozinha** | Desktop ou tablet | Ver os pedidos em ordem de chegada e mudar o estado | Dois atendentes pegarem o mesmo pedido, estado incoerente |
| **Cliente aguardando** | TV 1920x1080, a até 5 m | Saber quando o pedido está em preparo e quando está pronto | Não ouvir nem ver o próprio número |
| **Participante da oficina** | Terminal | Subir o sistema com um comando e ver o fluxo funcionando | Etapas de instalação e build |

## Objetivos

1. O cliente conclui um pedido no totem e recebe um número de 3 dígitos.
2. A cozinha vê o pedido em até 2 s e avança o estado na ordem fixa.
3. O painel mostra os pedidos em preparo e prontos, e chama o pedido recém-pronto por voz.
4. O sistema inteiro sobe com `docker compose up`.

## Critérios de sucesso

| ID | Critério | Como medir |
|---|---|---|
| CS-01 | `docker compose up` em máquina limpa deixa as 3 telas acessíveis e o cardápio com 10 produtos | Teste manual e de integração |
| CS-02 | Um pedido criado no totem aparece na cozinha em até 2 s (um ciclo de polling) | Teste manual |
| CS-03 | Números de pedido são únicos por dia, sequenciais e reiniciam à meia-noite (America/Sao_Paulo) | pytest |
| CS-04 | Duas tentativas simultâneas de avançar o mesmo pedido resultam em uma transição e um 409 | pytest |
| CS-05 | Reiniciar a aplicação não duplica produtos | pytest |
| CS-06 | O total do pedido é calculado no servidor e nunca vem do cliente | pytest |
| CS-07 | Nenhum texto no totem ou painel abaixo de 24 px, e nenhum alvo de toque abaixo de 80 px | Inspeção visual |

---

## Requisitos funcionais

| ID | Requisito | Prioridade |
|---|---|---|
| RF-01 | O totem mostra, em ordem: tela inicial ("Toque para começar"), cardápio com abas de categoria, carrinho, **tela de revisão**, confirmação com o número | Must |
| RF-02 | O cliente adiciona produtos e usa "−", "+" e "Remover" no carrinho. A quantidade por item vai de 1 a 99 | Must |
| RF-03 | "Finalizar pedido" na revisão cria o pedido e mostra o número em destaque por 8 s, depois volta à tela inicial | Must |
| RF-04 | O totem volta à tela inicial após 30 s sem toque | Must |
| RF-05 | Falha no envio mostra a mensagem de erro do design system (6.9) com "Tentar de novo" e mantém o carrinho | Should |
| RF-06 | O número do pedido tem 3 dígitos (001, 002…), é sequencial e reinicia todo dia no fuso America/Sao_Paulo | Must |
| RF-07 | O pedido tem pelo menos 1 item. O servidor calcula o total e copia o preço unitário de cada produto na criação | Must |
| RF-08 | A cozinha lista pedidos em Recebido, Preparando e Pronto em ordem de chegada. Entregues saem da fila | Must |
| RF-09 | O atendente avança o estado com "Iniciar", "Marcar pronto" e "Entregar". Só a transição seguinte é aceita, sem voltar nem pular | Must |
| RF-10 | Se o estado já mudou, `avancar` devolve 409 e a tela recarrega a fila | Must |
| RF-11 | Dois atendentes nunca pegam o mesmo pedido: bloqueio de linha com `SELECT ... FOR UPDATE SKIP LOCKED` | Must |
| RF-12 | O painel mostra "Preparando" à esquerda e "Pronto" à direita, atualizando a cada 2 s por polling | Must |
| RF-13 | O pedido recém-pronto aparece em destaque por 6 s e a voz fala "Pedido N, pronto" (Web Speech API) | Should |
| RF-14 | O painel pede um toque inicial para habilitar o áudio (política de autoplay dos navegadores) | Should |
| RF-15 | O rodapé do painel mostra o tempo médio de preparo, média entre `iniciado_em` e `pronto_em`, calculada no servidor | Should |
| RF-16 | Na subida, o sistema cria as tabelas e carrega os 10 produtos sem duplicar (nome único) | Must |

## Requisitos não funcionais

| ID | Requisito |
|---|---|
| RNF-01 | Sobe com um único `docker compose up`, com os serviços `app` (FastAPI) e `db` (PostgreSQL 16, com volume) |
| RNF-02 | O `app` só inicia depois que o `db` estiver saudável (healthcheck + `depends_on` com condição) |
| RNF-03 | Frontend sem build: HTML estático, Tailwind via CDN e JavaScript puro |
| RNF-04 | Sem login nem autenticação |
| RNF-05 | Sem migrations: `create_all` na subida |
| RNF-06 | Visual conforme `specs/DESIGN_SYSTEM.md`, com tokens em `app/static/css/tokens.css` e Tailwind mapeado para as variáveis |
| RNF-07 | Preços guardados em centavos (inteiros) e exibidos como `R$ 24,90` |
| RNF-08 | Testes com pytest cobrindo criação de pedido, numeração diária, transições, conflito e carga do cardápio |
| RNF-09 | Respeita `prefers-reduced-motion` |

---

## Testes de aceitação

| ID | Cenário | Dado | Quando | Então |
|---|---|---|---|---|
| AT-001 | Criar pedido | Cardápio carregado | `POST /api/pedidos` com 2 itens válidos | 201, número "001" no primeiro pedido do dia, total igual à soma no servidor |
| AT-002 | Numeração diária | Pedidos 001 e 002 criados ontem | Cria o primeiro pedido de hoje | O número é "001" |
| AT-003 | Pedido vazio | Qualquer estado | `POST /api/pedidos` sem itens | 422, nenhum pedido criado |
| AT-004 | Quantidade inválida | Qualquer estado | Item com quantidade 0 ou 100 | 422 |
| AT-005 | Total do cliente ignorado | Qualquer estado | Envia total falso no corpo | O total gravado é o calculado no servidor |
| AT-006 | Avançar na ordem | Pedido em Recebido | `avancar` três vezes | Preparando, Pronto, Entregue, nessa ordem |
| AT-007 | Não avançar além do fim | Pedido em Entregue | `avancar` | 409, estado inalterado |
| AT-008 | Concorrência | Pedido em Recebido | Duas chamadas simultâneas de `avancar` | Uma retorna 200, a outra 409, e o pedido fica em Preparando |
| AT-009 | Ordem da fila | 3 pedidos criados em sequência | `GET /api/pedidos` | Ordem de chegada, sem Entregues |
| AT-010 | Carga idempotente | Cardápio já carregado | A aplicação reinicia | Continuam 10 produtos |
| AT-011 | Cardápio agrupado | Cardápio carregado | `GET /api/produtos` | 4 categorias, 10 produtos, preços corretos |
| AT-012 | Tempo médio de preparo | 2 pedidos prontos com 4 e 6 min de preparo | `GET /api/pedidos` | Tempo médio de 5 min |
| AT-013 | Inatividade (manual) | Totem no cardápio | 30 s sem toque | Volta à tela inicial |
| AT-014 | Confirmação (manual) | Pedido finalizado | 8 s | Volta à tela inicial |
| AT-015 | Voz do painel (manual) | Áudio habilitado, pedido 012 em Preparando | O atendente marca pronto | O painel destaca 6 s e fala "Pedido 12, pronto" |
| AT-016 | Erro de envio (manual) | API fora do ar | "Finalizar pedido" | Mensagem de erro com "Tentar de novo", carrinho preservado |

---

## Restrições

| Tipo | Restrição |
|---|---|
| Stack | FastAPI, SQLAlchemy, PostgreSQL 16, HTML + Tailwind CDN + JS puro, pytest |
| Entrega | Um único `docker compose up` |
| Design | `specs/DESIGN_SYSTEM.md`, com os ajustes abaixo |
| Atualização | Polling de 2 s. Sem SSE nem WebSocket |
| Fuso | America/Sao_Paulo para o reinício diário |
| Rede | Tailwind via CDN exige internet na primeira carga das telas |

## Ajustes obrigatórios no design system

Devem ser feitos antes ou no início do `/design`, e o documento ganha uma nova versão no histórico:

1. Adicionar o componente **tela de revisão do pedido** no totem (itens, quantidades, total, "Finalizar pedido" primário e "Voltar" secundário).
2. Remover o estado **Cancelado** (seção 3.4) e o botão "Cancelar" da fila da cozinha (seção 6.8).
3. Manter o vermelho em "Remover" item e nas mensagens de erro.

---

## Fora do escopo

Pagamento, impressão, estoque, login e perfis, relatórios, múltiplas lojas, personalização de itens, observações no pedido, cancelamento de pedido, imagens de produto, migrations, SSE e WebSocket.

---

## Suposições

| Suposição | Se estiver errada |
|---|---|
| Os participantes têm Docker e Docker Compose | Documentar o pré-requisito no README |
| A máquina tem internet para o CDN do Tailwind | Vendorizar o Tailwind em arquivo local (muda RNF-03) |
| O navegador do painel suporta Web Speech API | A voz não toca. O destaque visual continua funcionando |
| Uma única loja e um único painel | Fora do escopo |

## Riscos

| Risco | Mitigação |
|---|---|
| Autoplay bloqueia a voz | Toque inicial no painel (RF-14) |
| Corrida na numeração diária | Gerar o número na transação, com restrição única de data + número |
| App sobe antes do banco | Healthcheck e `depends_on` (RNF-02) |
| Design system fora de sincronia | Aplicar os ajustes obrigatórios antes do `/design` |

---

## Registro de clareza

| Elemento | Nota | Observação |
|---|---|---|
| Problema | 2 | Contexto de demonstração, sem métrica de negócio |
| Usuários | 3 | Quatro perfis com dispositivo e dor |
| Objetivos | 3 | Quatro objetivos verificáveis |
| Sucesso | 3 | Sete critérios, a maioria automatizável |
| Escopo | 3 | Lista explícita do que fica fora |
| **Total** | **14/15** | Mínimo de 12 atingido |

---

## Próximo passo

```bash
/design .claude/sdd/features/DEFINE_TOTEM_ATENDIMENTO.md
```
