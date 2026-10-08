# DEFINE: Totem de Autoatendimento

> Requisitos validados para a demonstração da oficina (Fase 1)

## Metadados

| Atributo | Valor |
|---|---|
| **Feature** | TOTEM_AUTOATENDIMENTO |
| **Data** | 2026-10-08 |
| **Origem** | `.claude/sdd/features/BRAINSTORM_TOTEM_AUTOATENDIMENTO.md` |
| **Tipo de entrada** | brainstorm_document |
| **Clarity Score** | 14/15 |
| **Status** | Pronto para /design |

---

## Problema

Em uma lanchonete, o pedido feito no balcão depende de um atendente para anotar, e o cliente não sabe quando o pedido fica pronto. A oficina precisa de uma **demonstração funcional e reproduzível** que mostre o ciclo completo: o cliente pede sozinho, a cozinha acompanha a fila e a TV avisa quando o pedido está pronto. Tudo precisa subir em qualquer máquina com um único comando.

## Usuários

| Usuário | Dispositivo | Necessidade | Dor atual |
|---|---|---|---|
| Cliente | Totem 1080x1920, só toque | Escolher produtos, montar o pedido e receber o número | Fila no balcão e pedido anotado por terceiros |
| Atendente / cozinha | Desktop ou tablet | Ver os pedidos em ordem de chegada e avançar o estado | Sem fila visível e sem controle de estado |
| Clientes aguardando | TV 1920x1080, a até 5 m | Saber se o pedido está em preparo ou pronto | Não sabem quando retirar |
| Aluno da oficina | Terminal | Subir a demo com um comando e ler o código | Setup longo e build de frontend |

## Objetivos

| Prioridade | Objetivo |
|---|---|
| MUST | Ciclo completo: pedido no totem, fila na cozinha, estado na TV |
| MUST | `docker compose up` sobe a demo inteira, sem login e sem build de frontend |
| MUST | Visual conforme `specs/DESIGN_SYSTEM.md` |
| MUST | Cardápio de 10 produtos carregado na subida |
| SHOULD | Tempo médio de preparo exibido na TV |
| SHOULD | Mensagem de erro padronizada com "Tentar de novo" |
| COULD | Voz "Pedido N, pronto" na TV (Web Speech API) |

---

## Requisitos funcionais

### Cardápio
- **RF-01.** Na subida, a aplicação cria as tabelas e carrega 10 produtos em 4 categorias (Lanches, Crepes, Bebidas, Sobremesas), com nome, ícone (emoji) e preço, conforme a seção 8 do design system.
- **RF-02.** O seed só insere produtos se a tabela estiver vazia. Reiniciar não duplica.
- **RF-03.** `GET /api/produtos` devolve os produtos com id, nome, categoria, ícone e preço em centavos.

### Totem (`/totem`)
- **RF-04.** Mostrar abas de categoria e cartões de produto em 2 colunas, com botão "Adicionar".
- **RF-05.** O rodapé do cardápio mostra a quantidade de itens, o total e o botão "Revisar pedido". As linhas do carrinho ficam na tela de revisão.
- **RF-06.** "Revisar pedido" só fica habilitado com pelo menos 1 item.
- **RF-06a.** A tela de revisão lista itens, quantidades, subtotais e o total, e permite "−", "+" e "Remover". Tem os botões "Voltar ao cardápio" (mantém o carrinho) e "Finalizar pedido". Remover o último item volta ao cardápio.
- **RF-07.** Ao tocar em "Finalizar pedido" na revisão, enviar `POST /api/pedidos` e exibir em tela cheia "Sua senha" com o número, e a frase "Retire no balcão quando o painel chamar".
- **RF-08.** A confirmação volta sozinha à tela inicial em 8 s. Após 30 s sem toque (no cardápio ou na revisão), o totem volta ao início e limpa o carrinho.
- **RF-09.** Se o envio falhar, mostrar a mensagem de erro padronizada na revisão, com "Tentar de novo", e manter o carrinho. Se não houver senha livre (503), mostrar "Não há senhas disponíveis agora. Chame um atendente."

### Pedidos (API)
- **RF-10.** `POST /api/pedidos` recebe itens (produto_id, quantidade), cria o pedido no estado `recebido` e devolve id, número, estado e total.
- **RF-11.** O servidor calcula o total a partir dos preços do banco e ignora qualquer valor enviado pelo cliente.
- **RF-12.** Cada item do pedido guarda cópia do nome e do preço no momento da criação.
- **RF-13.** O número do pedido, chamado de **senha** para o cliente, tem 3 dígitos e começa com 1: faixa de 100 a 199. É sequencial a partir do último pedido criado e distinto do id interno. Depois da 199 volta para 100 e pula as senhas em uso (pedidos com estado diferente de `entregue`). A unicidade vale só entre pedidos ativos, e a senha de um pedido entregue pode ser reutilizada.
- **RF-13a.** Se as 100 senhas estiverem em uso, `POST /api/pedidos` devolve 503 com a mensagem "Todas as senhas estão em uso. Chame um atendente." e não cria o pedido.
- **RF-14.** `GET /api/pedidos` lista pedidos em ordem de chegada, com filtro opcional por estado.
- **RF-15.** `PATCH /api/pedidos/{id}/estado` avança o pedido uma etapa. A ordem é `recebido → preparando → pronto → entregue`. Transição inválida devolve 409. Pedido inexistente devolve 404.
- **RF-16.** O pedido registra o horário de cada transição.

### Cozinha (`/cozinha`)
- **RF-17.** Mostrar os pedidos não entregues em ordem de chegada, com número, itens, horário e selo de estado.
- **RF-18.** Mostrar o botão da próxima ação conforme o estado: "Iniciar" (recebido), "Marcar pronto" (preparando), "Entregar" (pronto).
- **RF-19.** A tela atualiza por polling a cada 2 s. Pedidos entregues saem da fila.

### Painel (`/painel`)
- **RF-20.** Mostrar duas colunas: "Preparando" e "Pronto", com os números dos pedidos.
- **RF-21.** Quando um pedido passa a `pronto`, mostrar destaque "Senha pronta" em tela cheia por 6 s (fundo amarelo, número em preto).
- **RF-22.** Falar "Senha N, pronta" em pt-BR via Web Speech API depois que o usuário toca em "Ativar som". Sem o toque, o destaque visual funciona normalmente.
- **RF-23.** Mostrar no rodapé o tempo médio de preparo, calculado de `preparando` até `pronto`. Sem dados, mostrar "—".
- **RF-24.** A tela atualiza por polling a cada 2 s. Pedidos `entregue` não aparecem.

---

## Requisitos não funcionais

| ID | Requisito |
|---|---|
| RNF-01 | `docker compose up` único sobe `app` e `db` (PostgreSQL 16). Sem login, sem passos manuais |
| RNF-02 | Frontend sem etapa de build: HTML, Tailwind via CDN e JavaScript puro |
| RNF-03 | O `app` só inicia depois que o banco está saudável (healthcheck + `depends_on`) |
| RNF-04 | Tokens do design system em `app/static/css/tokens.css`; telas usam variáveis, nunca hexadecimal direto |
| RNF-05 | Alvos de toque de no mínimo 80 px no totem; nada abaixo de 24 px no totem e no painel |
| RNF-06 | Todo estado tem texto ou ícone além da cor; animações respeitam `prefers-reduced-motion` |
| RNF-07 | Textos de interface em português do Brasil, preços no formato `R$ 24,90` |
| RNF-08 | Testes com pytest, executáveis sem o Docker (SQLite em memória via dependência substituída) |

---

## Critérios de sucesso

| ID | Critério | Como medir |
|---|---|---|
| CS-01 | Em máquina limpa, `docker compose up` deixa `/totem`, `/cozinha` e `/painel` acessíveis | Smoke test manual |
| CS-02 | Um pedido criado no totem aparece na cozinha e no painel em até 2 s de polling | Teste manual |
| CS-03 | Transição fora de ordem é recusada com 409 | Teste pytest |
| CS-04 | O total do pedido vem sempre do preço do banco | Teste pytest |
| CS-05 | Reiniciar o `app` mantém exatamente 10 produtos | Teste pytest |
| CS-06 | `pytest` passa sem Docker | Execução local |

---

## Testes de aceitação

| ID | Dado | Quando | Então |
|---|---|---|---|
| AT-01 | Banco vazio | O app sobe | Existem 10 produtos em 4 categorias |
| AT-02 | Banco com 10 produtos | O app reinicia | Continuam 10 produtos |
| AT-03 | Produtos 1 (R$ 24,90) e 4 (R$ 14,90) | `POST /api/pedidos` com 2 unidades do 1 e 1 do 4 | Total 6470 centavos, estado `recebido`, senha entre 100 e 199 (a primeira é 100) |
| AT-04 | Cliente envia total adulterado | `POST /api/pedidos` | O total devolvido ignora o valor do cliente |
| AT-05 | Quantidade 0 ou negativa, ou produto inexistente | `POST /api/pedidos` | Resposta 422 ou 404, nenhum pedido criado |
| AT-06 | Pedido `recebido` | `PATCH` estado | Passa a `preparando` |
| AT-07 | Pedido `recebido` | Tentar ir direto para `pronto` | 409, estado inalterado |
| AT-08 | Pedido `entregue` | `PATCH` estado | 409 |
| AT-09 | 3 pedidos criados em sequência | `GET /api/pedidos` | Voltam em ordem de chegada, com números crescentes |
| AT-10 | Carrinho vazio no totem | O cliente olha o rodapé | "Revisar pedido" está desabilitado |
| AT-11 | Totem na confirmação | Passam 8 s | Volta à tela inicial |
| AT-12 | Falha de rede no envio | O cliente toca em "Finalizar pedido" na revisão | Aparece a mensagem de erro, o carrinho é mantido e "Tentar de novo" reenvia |
| AT-15 | Carrinho com itens | O cliente toca em "Revisar pedido" e depois em "Voltar ao cardápio" | O carrinho continua com os mesmos itens |
| AT-16 | Pedido ativo com senha 199 como último criado | Novo pedido | A senha é 100, ou a primeira livre depois dela |
| AT-17 | As 100 senhas em uso | `POST /api/pedidos` | 503 e nenhum pedido criado |
| AT-13 | Pedido passa a `pronto` | Painel faz o próximo polling | Destaque de 6 s e o pedido aparece na coluna "Pronto" |
| AT-14 | Pedido passa a `entregue` | Cozinha e painel atualizam | Pedido some das duas telas |

---

## Restrições

| Tipo | Restrição |
|---|---|
| Stack | FastAPI, SQLAlchemy, PostgreSQL 16, HTML + Tailwind CDN + JS puro, pytest |
| Execução | Um único `docker compose up`, sem login e sem build de frontend |
| Visual | `specs/DESIGN_SYSTEM.md` é a fonte única de verdade |
| Premissa | Há internet na oficina para carregar o Tailwind via CDN |
| Banco | Container `db` no Compose; tabelas criadas com `create_all` |

## Fora do escopo

| Item | Motivo |
|---|---|
| Cancelamento de pedido (estado e botão) | Decidido no brainstorm: fluxo linear de 4 estados |
| Login, perfis e pagamento | Brief pede "sem login"; pagamento não foi pedido |
| CRUD de produtos | O cardápio vem do seed |
| Migrações Alembic | `create_all` basta para a demo |
| WebSocket e SSE | Decidido: polling de 2 s |
| Imagens de produto | Ícones em emoji |
| Observações por item e impressão de senha | Fora do fluxo descrito |

---

## Dependências e ajustes em outros documentos

| Item | Ação |
|---|---|
| `specs/DESIGN_SYSTEM.md` | Remover o estado "Cancelado", o botão "Cancelar" (6.8) e o botão Perigo no fluxo da cozinha. Incluir o estado "Entregue" (cor, ícone, rótulo). Subir a versão para 1.1.0 |
| Fonte do tempo médio de preparo | Usar `preparando_em` e `pronto_em` do pedido (RF-16) |

## Decisões deixadas para o /design

| Tema | Pergunta |
|---|---|
| Número do pedido | Sequence do PostgreSQL ou contador transacional? Reinicia por dia? |
| Tailwind via CDN | Configurar o mapeamento para os tokens inline ou só usar `tokens.css`? Há fallback offline? |
| SQLite nos testes | Como lidar com diferenças de dialeto (sequence, timestamps)? |
| Estados | Um endpoint que avança uma etapa, ou recebe o estado de destino e valida? |

---

## Clarity Score

| Elemento | Nota | Observação |
|---|---|---|
| Problema | 3 | Específico, com contexto de oficina |
| Usuários | 3 | Quatro perfis, dispositivo e necessidade |
| Objetivos | 3 | Priorizados em MUST, SHOULD e COULD |
| Sucesso | 3 | Critérios e testes de aceitação verificáveis |
| Escopo | 2 | Fronteiras claras, mas o número do pedido e o tempo médio dependem do /design |
| **Total** | **14/15** | Acima do mínimo de 12 |

---

## Próximo passo

```bash
/tecspec:workflow:design .claude/sdd/features/DEFINE_TOTEM_AUTOATENDIMENTO.md
```
