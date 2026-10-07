# DEFINE: Totem de Autoatendimento

> Requisitos capturados e validados (Fase 1)

**Feature:** TOTEM_ATENDIMENTO
**Data:** 2026-10-07
**Origem:** `.claude/sdd/features/BRAINSTORM_TOTEM_ATENDIMENTO.md` (tipo: `brainstorm_document`)
**Status:** Pronto para /design
**Clarity Score:** 15/15

---

## 1. Problema

Uma lanchonete precisa que o cliente faça o pedido sozinho, sem fila no balcão, e que a cozinha e o cliente saibam em que ponto o pedido está. Hoje não existe um fluxo que ligue o toque do cliente, a produção na cozinha e o aviso de "pedido pronto".

Este projeto é uma **demonstração para uma oficina**: precisa ser simples de subir (`docker compose up`), sem login e sem etapa de build no frontend.

## 2. Usuários

| Persona | Dispositivo | Necessidade | Dor atual |
|---|---|---|---|
| **Cliente** | Totem 1080x1920, retrato, só toque | Escolher produtos, montar o pedido e receber o número, rápido | Fila e pressa; sem teclado nem mouse |
| **Atendente / cozinha** | Desktop ou tablet, mouse ou toque | Ver pedidos em ordem de chegada e mudar o estado | Não saber o que entrou primeiro; dois atendentes pegarem o mesmo pedido |
| **Cliente aguardando** | TV 1920x1080, a até 5 m | Saber se o pedido está em preparo ou pronto | Não ouvir nem ver o chamado |
| **Participante da oficina** | Terminal | Subir tudo com um comando e rodar os testes | Setup longo e etapas de build |

## 3. Objetivos

| Prioridade | Objetivo |
|---|---|
| Must | Cliente faz um pedido completo no totem e recebe um número de 3 dígitos |
| Must | Cozinha vê os pedidos em ordem de chegada e muda o estado com um clique |
| Must | Painel mostra pedidos em preparo e prontos, atualizando sozinho |
| Must | Subir tudo com um único `docker compose up`, sem login e sem build de frontend |
| Should | Totem volta sozinho à tela inicial quando fica ocioso |
| Should | Painel avisa por voz quando um pedido fica pronto |

## 4. Requisitos

### 4.1 Funcionais

| ID | Requisito |
|---|---|
| RF-01 | O totem exibe a tela inicial "Toque para começar". |
| RF-02 | O totem exibe o cardápio com abas por categoria (Lanches, Crepes, Bebidas, Sobremesas). |
| RF-03 | Cada produto mostra emoji, nome e preço em reais (formato `R$ 24,90`). |
| RF-04 | O cliente adiciona produtos ao carrinho e ajusta a quantidade com botões de mais e menos. Quantidade zero remove o item. |
| RF-05 | O carrinho mostra os itens, o subtotal por item e o total do pedido. |
| RF-06 | "Revisar pedido" abre uma tela de revisão só de leitura, com itens, quantidades, subtotais e total. "Confirmar pedido" cria o pedido e exibe a tela de confirmação com o número do pedido. "Voltar e editar" retorna ao cardápio com o carrinho intacto. Nenhum pedido é criado antes da confirmação. |
| RF-07 | O número do pedido tem 3 dígitos (001, 002…) e reinicia todo dia. |
| RF-08 | Números nunca se repetem no mesmo dia, mesmo com pedidos simultâneos. |
| RF-09 | O pedido nasce no estado Recebido. |
| RF-10 | A tela de cozinha lista os pedidos ativos (Recebido, Preparando, Pronto) em ordem de chegada, do mais antigo ao mais novo. |
| RF-11 | O atendente avança o pedido com um clique: Recebido → Preparando → Pronto → Entregue. |
| RF-12 | O atendente cancela um pedido em Recebido ou Preparando. Entregue e Cancelado são estados finais. |
| RF-13 | Duas tentativas simultâneas de avançar o mesmo pedido resultam em uma transição só; a outra recebe resposta de conflito. |
| RF-14 | O painel (TV) mostra duas colunas: Preparando e Pronto, com o número do pedido bem grande. |
| RF-15 | Quando um pedido passa a Pronto, o painel fala "Pedido N, pronto" pela voz do navegador (Web Speech API), uma vez por pedido. |
| RF-16 | Cozinha e painel se atualizam por polling a cada 2 segundos. |
| RF-17 | O totem volta à tela inicial após 30 s sem toque e descarta o carrinho. |
| RF-18 | A confirmação do pedido some sozinha após 8 s e o totem volta à tela inicial. |
| RF-19 | A aplicação cria as tabelas e carrega os 10 produtos na subida, sem duplicar se já existirem. |
| RF-20 | O total do pedido é calculado no servidor a partir dos preços do banco. |

### 4.2 Não funcionais

| ID | Requisito |
|---|---|
| RNF-01 | `docker compose up` sobe `db` e `app` e deixa as três telas acessíveis, sem passos adicionais. |
| RNF-02 | O `app` só inicia depois que o `db` está saudável (`healthcheck` e `depends_on: condition: service_healthy`). |
| RNF-03 | Os dados do PostgreSQL ficam em volume nomeado. |
| RNF-04 | Nenhum login, nenhuma autenticação. |
| RNF-05 | Frontend sem etapa de build: HTML, Tailwind via CDN e JavaScript puro. |
| RNF-06 | O visual segue `specs/DESIGN_SYSTEM.md`: paleta preto, laranja, amarelo e vermelho; cor nunca é o único sinal de estado; texto em português do Brasil. |
| RNF-07 | Tokens do design system ficam em `app/static/css/tokens.css`. |
| RNF-08 | Preços guardados em centavos inteiros (`price_cents`). |
| RNF-09 | Sem migrations. As tabelas são criadas na subida. |
| RNF-10 | Testes automatizados com pytest, executados contra PostgreSQL real em banco de teste separado. |

### 4.3 Restrições

| Restrição | Detalhe |
|---|---|
| Stack | FastAPI, SQLAlchemy, PostgreSQL 16, pytest |
| Banco | Serviço `db` no docker compose |
| Concorrência | Bloqueio de linha com `SELECT ... FOR UPDATE SKIP LOCKED` no avanço de estado; contador diário travado com `FOR UPDATE` |
| Telas | `/totem`, `/painel` e `/cozinha` |
| Imagens | Sem arquivos de imagem; emoji como ícone |

## 5. Cardápio (carga inicial)

| Categoria | Produto | Preço | `price_cents` |
|---|---|---|---|
| Lanches | Hambúrguer clássico | R$ 24,90 | 2490 |
| Lanches | X-Bacon | R$ 29,90 | 2990 |
| Lanches | Cachorro-quente | R$ 16,90 | 1690 |
| Lanches | Batata frita | R$ 14,90 | 1490 |
| Crepes | Crepe de queijo e presunto | R$ 19,90 | 1990 |
| Crepes | Crepe de chocolate com morango | R$ 21,90 | 2190 |
| Bebidas | Suco de laranja | R$ 9,90 | 990 |
| Bebidas | Suco de abacaxi com hortelã | R$ 10,90 | 1090 |
| Bebidas | Milk shake de chocolate | R$ 18,90 | 1890 |
| Sobremesas | Sundae de morango | R$ 12,90 | 1290 |

## 6. Estados do pedido

| Estado | Rótulo e ícone | Fundo (design system) | Próximos estados |
|---|---|---|---|
| Recebido | 🕒 Recebido | `--cor-superficie-alta` | Preparando, Cancelado |
| Preparando | 🔥 Preparando | `--cor-laranja` | Pronto, Cancelado |
| Pronto | ✅ Pronto | `--cor-amarelo` | Entregue |
| Entregue | Entregue | neutro | (final) |
| Cancelado | ✖ Cancelado | `--cor-vermelho` | (final) |

## 7. Interface de API (contrato de alto nível)

| Método e rota | Função |
|---|---|
| `GET /api/produtos` | Lista o cardápio por categoria |
| `POST /api/pedidos` | Cria o pedido (itens e quantidades) e devolve o número do dia |
| `GET /api/pedidos?estado=...` | Lista pedidos por estado, em ordem de chegada |
| `POST /api/pedidos/{id}/avancar` | Avança para o próximo estado |
| `POST /api/pedidos/{id}/cancelar` | Cancela o pedido |
| `GET /api/painel` | Pedidos em preparo e prontos |

O detalhamento de payloads e códigos de erro fica para o `/design`.

## 8. Critérios de sucesso

| ID | Critério mensurável |
|---|---|
| CS-01 | `docker compose up` em máquina limpa deixa `/totem`, `/cozinha` e `/painel` respondendo 200, sem nenhum comando adicional. |
| CS-02 | Um pedido completo (início, escolha, carrinho, finalizar) leva menos de 10 toques para 2 itens. |
| CS-03 | Uma mudança de estado na cozinha aparece no painel em até 4 s (2 ciclos de polling). |
| CS-04 | Com 20 pedidos criados em paralelo, os números do dia são únicos e contínuos. |
| CS-05 | Com 2 requisições simultâneas de avançar o mesmo pedido, exatamente uma tem sucesso. |
| CS-06 | Reiniciar a aplicação duas vezes mantém exatamente 10 produtos. |
| CS-07 | A suíte pytest passa inteira contra PostgreSQL real. |

## 9. Testes de aceitação

| ID | Cenário |
|---|---|
| AT-01 | **Dado** o totem na tela inicial, **quando** o cliente toca na tela, **então** vê o cardápio com a aba Lanches e 4 produtos. |
| AT-02 | **Dado** o cardápio, **quando** o cliente adiciona 2 Hambúrgueres clássicos e 1 Suco de laranja, **então** o carrinho mostra total de R$ 59,70. |
| AT-03 | **Dado** um item com quantidade 1 no carrinho, **quando** o cliente toca em menos, **então** o item é removido. |
| AT-04 | **Dado** um carrinho com itens, **quando** o cliente toca em "Revisar pedido", **então** vê a tela de revisão com os itens e o total, e nenhum pedido foi criado ainda. |
| AT-04b | **Dado** a tela de revisão, **quando** o cliente toca em "Voltar e editar", **então** volta ao cardápio com o carrinho intacto; **quando** toca em "Confirmar pedido", **então** vê o número do pedido (ex.: 001) e o pedido existe no estado Recebido. |
| AT-05 | **Dado** o primeiro pedido do dia, **quando** ele é criado, **então** recebe o número 001; o segundo recebe 002. |
| AT-06 | **Dado** pedidos do dia anterior, **quando** o primeiro pedido do novo dia é criado, **então** recebe o número 001. |
| AT-07 | **Dado** carrinho vazio, **quando** o cliente tenta finalizar, **então** a API rejeita o pedido e o totem não avança. |
| AT-08 | **Dado** 3 pedidos criados em ordem, **quando** a cozinha abre, **então** os vê do mais antigo ao mais novo. |
| AT-09 | **Dado** um pedido Recebido, **quando** o atendente avança 3 vezes, **então** o pedido passa por Preparando, Pronto e Entregue. |
| AT-10 | **Dado** um pedido Pronto, **quando** o atendente tenta cancelar, **então** a API recusa e o estado não muda. |
| AT-11 | **Dado** um pedido Entregue, **quando** o atendente tenta avançar, **então** a API recusa. |
| AT-12 | **Dado** um pedido Recebido, **quando** duas requisições de avançar chegam ao mesmo tempo, **então** o pedido fica em Preparando (não em Pronto) e uma das requisições recebe conflito. |
| AT-13 | **Dado** pedidos em Preparando e Pronto, **quando** o painel carrega, **então** mostra cada pedido na coluna do seu estado e não mostra Recebido, Entregue nem Cancelado. |
| AT-14 | **Dado** o painel aberto, **quando** um pedido passa a Pronto, **então** o painel fala "Pedido N, pronto" uma única vez. |
| AT-15 | **Dado** o totem com itens no carrinho, **quando** passam 30 s sem toque, **então** volta à tela inicial e o carrinho é descartado. |
| AT-16 | **Dado** a tela de confirmação, **quando** passam 8 s, **então** o totem volta à tela inicial. |
| AT-17 | **Dado** o banco já com os 10 produtos, **quando** a aplicação reinicia, **então** continuam 10 produtos. |
| AT-18 | **Dado** um cliente que envia um total no corpo do pedido, **quando** a API cria o pedido, **então** ignora esse total e usa o valor calculado no servidor. |
| AT-19 | **Dado** cada estado na cozinha e no painel, **quando** renderizado, **então** exibe rótulo em texto e ícone, além da cor. |

## 10. Fora do escopo

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
| Cancelamento em Pronto ou volta de estado | Transições são só para frente |

## 11. Premissas e riscos

| Tipo | Item | Mitigação |
|---|---|---|
| Premissa | O dia do contador é o dia local do servidor (fuso configurável por variável de ambiente, padrão `America/Sao_Paulo`) | Decidir no `/design` |
| Premissa | Cliente e atendente usam navegador moderno com suporte a Web Speech API na TV | Aviso visual sempre presente |
| Risco | `app` sobe antes do `db` aceitar conexões | Healthcheck e `service_healthy` |
| Risco | Navegador bloqueia fala antes de interação | Toque inicial na TV para liberar o áudio |
| Risco | Número duplicado sob concorrência | Contador por data com bloqueio de linha e teste dedicado |
| Risco | Tailwind via CDN exige internet na oficina | Registrar no README; fallback fica fora do MVP |

## 12. Clarity Score

| Elemento | Nota | Justificativa |
|---|---|---|
| Problema | 3/3 | Específico e com contexto de demo |
| Usuários | 3/3 | 4 personas com dispositivo, necessidade e dor |
| Objetivos | 3/3 | Priorizados em Must e Should |
| Sucesso | 3/3 | 7 critérios mensuráveis |
| Escopo | 3/3 | Dentro e fora explícitos |
| **Total** | **15/15** | Acima do mínimo de 12 |

## 13. Qualidade do define

```text
[x] Problema claro e específico
[x] Ao menos uma persona identificada (4)
[x] Critérios de sucesso mensuráveis
[x] Testes de aceitação testáveis (19)
[x] Fora do escopo explícito
[x] Clarity Score >= 12/15 (15/15)
```

## 14. Próximo passo

```bash
/tecspec:workflow:design .claude/sdd/features/DEFINE_TOTEM_ATENDIMENTO.md
```
