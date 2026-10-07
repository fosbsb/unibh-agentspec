# BUILD REPORT: Totem de Autoatendimento

**Feature:** TOTEM_ATENDIMENTO
**Data:** 2026-10-07
**Origem:** `.claude/sdd/features/DESIGN_TOTEM_ATENDIMENTO.md`
**Status:** Concluído, com ressalvas listadas na seção 6

---

## 1. Resumo

| Item | Resultado |
|---|---|
| Arquivos do manifesto | 39 de 39 criados, mais 1 extra (`tests/test_domain.py`) |
| Subida do zero (`docker compose down -v` e `up`) | OK: `/`, `/totem`, `/cozinha`, `/painel`, `/api/produtos`, `/api/painel` respondem 200 |
| Testes pytest (PostgreSQL real) | **64 passaram**, 0 falharam |
| Verificação de interface (Chromium isolado) | **30 de 30** verificações passaram, com capturas de tela |
| Teste de mutação | 2 de 2 quebras propositais foram detectadas |
| `ruff` e `mypy` | Não executados (ver seção 6) |
| TODO ou comentários no código | Nenhum |

## 2. Como rodar

```bash
docker compose up                      # sobe db e app; telas em http://localhost:8000
docker compose run --rm app pytest     # roda a suíte no banco totem_test
```

| Tela | URL |
|---|---|
| Menu das telas | http://localhost:8000/ |
| Totem | http://localhost:8000/totem |
| Cozinha | http://localhost:8000/cozinha |
| Painel (TV) | http://localhost:8000/painel |

O Tailwind vem de CDN, então o navegador precisa de internet.

## 3. Arquivos criados

| Grupo | Arquivos |
|---|---|
| Infraestrutura | `requirements.txt`, `.gitignore`, `.dockerignore`, `Dockerfile`, `docker-compose.yml`, `pytest.ini` |
| Backend (`app/`) | `config.py`, `domain.py`, `database.py`, `models.py`, `schemas.py`, `seed.py`, `services.py`, `api.py`, `pages.py`, `main.py` |
| CSS | `static/css/tokens.css`, `static/css/components.css` |
| JavaScript | `static/js/tailwind-config.js`, `config.js`, `common.js`, `totem.js`, `cozinha.js`, `painel.js` |
| HTML | `static/index.html`, `totem.html`, `cozinha.html`, `painel.html` |
| Testes (`tests/`) | `conftest.py`, `test_domain.py`, `test_seed.py`, `test_menu_api.py`, `test_order_creation.py`, `test_daily_number.py`, `test_order_flow.py`, `test_concurrency.py`, `test_panel_api.py`, `test_pages.py`, `test_design_tokens.py` |

## 4. Desvios do DESIGN

| Desvio | Motivo |
|---|---|
| `tests/test_domain.py` adicionado | O DESIGN previa teste unitário de `domain.py` na estratégia, mas não o listava no manifesto |
| `<link rel="icon" href="data:,">` nas 4 páginas | Sem ele, o navegador pedia `/favicon.ico` e o log mostrava 404 |
| `conftest.py` aponta `DATABASE_URL` para `totem_test` antes de importar o app | Mais simples que sobrescrever dependências. Toda a aplicação, inclusive o `lifespan`, usa o banco de teste na suíte |

Nenhuma decisão D-01 a D-10 foi alterada.

## 5. Evidências

### 5.1 Cobertura dos testes de aceitação

| ID | Verificado por | Resultado |
|---|---|---|
| AT-01 | pytest (`test_menu_api`) e interface | OK |
| AT-02 | pytest (total 5970 centavos) e interface (R$ 59,70) | OK |
| AT-03 | Interface | OK |
| AT-04 | pytest e interface (número `001`) | OK |
| AT-05, AT-06 | pytest (`test_daily_number`, datas explícitas) | OK |
| AT-07 | pytest (422 com lista vazia) e interface (botão desabilitado) | OK |
| AT-08 | pytest | OK |
| AT-09, AT-10, AT-11 | pytest | OK |
| AT-12 | pytest: duas threads com `Barrier`; linha travada devolve 409 sem esperar; sequência de duas chamadas não pula estado | OK |
| AT-13 | pytest | OK |
| AT-14 | Interface, com espião em `speechSynthesis.speak`: fala `Pedido 1, pronto` em `pt-BR`, uma única vez, e não repete nos ciclos seguintes nem após recarregar | OK |
| AT-15 | Interface: 30,5 s até a tela inicial, carrinho descartado | OK |
| AT-16 | Interface: 8,3 s | OK |
| AT-17 | pytest (`test_seed`, seed duas vezes) | OK |
| AT-18 | pytest (`total_cents` e `unit_price_cents` falsos ignorados) | OK |
| AT-19 | Interface: selo com ícone e rótulo | OK |

| ID | Verificado por | Resultado |
|---|---|---|
| CS-01 | `docker compose down -v` e `up`; `test_pages` | OK |
| CS-02 | Interface (fluxo com 2 itens em menos de 10 toques) | OK, não cronometrado |
| CS-03 | Interface: pedido aparece no painel em até 4 s | OK |
| CS-04 | pytest: 20 threads, números 1 a 20 sem repetição | OK |
| CS-05 | pytest | OK |
| CS-06 | pytest | OK |
| CS-07 | 64 de 64 | OK |

### 5.2 Medidas contra o design system

| Verificação | Medido |
|---|---|
| Cartão de produto (mínimo 440x360) | 504x362 |
| Botão "Adicionar" (mínimo 80 px) | 80 px |
| Botões "−" e "+" (80x80) | 80x80 |
| Botão da cozinha (mínimo 44 px) | 48 px |
| Nenhuma cor hexadecimal fora de `tokens.css` | Verificado por `test_design_tokens` |
| Toda `var(--...)` usada está definida em `tokens.css` | Verificado por `test_design_tokens` |

### 5.3 Teste de mutação

Para confirmar que a suíte não passa por acaso, o código foi quebrado de propósito e restaurado em seguida.

| Quebra | Resultado |
|---|---|
| Remover a checagem de `from_state` em `advance_order` | `test_two_simultaneous_advances_move_the_order_once` falhou |
| Fazer o total ignorar a quantidade | `test_order_total_is_sum_of_items` e `test_repeated_product_lines_are_merged` falharam |

Depois de restaurar, a suíte voltou a 64 de 64.

## 6. Problemas e ressalvas

### 6.1 Encontrados e corrigidos durante o build

| Problema | Correção |
|---|---|
| 3 das 4 primeiras falhas da verificação de interface eram do roteiro de teste: o espião de voz contava o enunciado silencioso que o painel fala para destravar o áudio | Espião passou a ignorar texto vazio. Não era erro da aplicação |
| 404 em `/favicon.ico` aparecia como erro de console | Ícone vazio embutido nas páginas |
| Teste frágil: `"001" in str(panel)` podia casar com um timestamp | Trocado por comparação de ids |

### 6.2 Ressalvas que permanecem

| Ressalva | Detalhe |
|---|---|
| `ruff` e `mypy` não rodaram | Não estão no `requirements.txt` nem no DESIGN. O código foi validado só por testes e pela execução real |
| Cozinha: botões quebram de linha | Em cartões de 320 px, "Marcar pronto" e "Cancelar" ficam um sobre o outro. Segue o texto de 28 px do design system. Legível, mas ocupa mais altura |
| Voz depende de um toque inicial | O painel mostra "Toque para ativar o som". Em TV sem toque, abrir o Chrome com `--autoplay-policy=no-user-gesture-required` |
| Internet necessária | Tailwind via CDN. Sem rede, o layout perde os utilitários (cores e componentes próprios continuam) |
| Pedido duplicado em falha de rede | Se a resposta se perder depois de o servidor gravar o pedido, "Tentar de novo" cria outro. O botão fica desabilitado durante o envio, mas não há chave de idempotência. Aceito na demo |
| Pedido que fica Pronto e vira Entregue em menos de 2 s | Não é anunciado no painel (D-07) |
| Rótulo com 4 dígitos depois do pedido 999 | Aceito (D-03) |
| Verificação de interface fora do repositório | O roteiro Playwright ficou no diretório temporário da sessão e **não** foi incluído no projeto, porque o manifesto não previa testes de interface. Se quiser mantê-lo, vale um `/tecspec:workflow:iterate` para incluí-lo |
| Navegador do Playwright MCP indisponível | Outra instância do Chrome segurava o perfil. Em vez de encerrá-la, usei um Chromium isolado com o `playwright-core` já instalado na máquina |

## 7. Qualidade do build

```text
[x] Todos os arquivos do manifesto criados
[x] Testes passam (64 de 64)
[x] Subida do zero verificada
[x] Interface verificada em navegador (30 de 30)
[x] Sem TODO e sem comentários no código
[x] Relatório gerado
[ ] Lint (ruff) e tipos (mypy): não executados
```

## 8. Próximo passo

```bash
/tecspec:workflow:ship .claude/sdd/features/DEFINE_TOTEM_ATENDIMENTO.md
```
