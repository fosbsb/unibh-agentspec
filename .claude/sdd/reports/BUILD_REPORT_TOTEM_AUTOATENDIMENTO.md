# BUILD REPORT: Totem de Autoatendimento

| Atributo | Valor |
|---|---|
| **Feature** | TOTEM_AUTOATENDIMENTO |
| **Data** | 2026-10-08 |
| **Design** | `.claude/sdd/features/DESIGN_TOTEM_AUTOATENDIMENTO.md` |
| **Resultado** | Concluído; 30 de 30 itens do manifesto entregues |

## Resumo da validação

| Verificação | Resultado |
|---|---|
| `pytest` (Python 3.12, em contêiner) | 44 passaram, 0 falharam |
| `pyflakes app tests` | Só 2 avisos de import intencional (`app.models`, registra as tabelas; já marcados com `noqa`) |
| `docker compose up --build` | `db` saudável, `app` sobe depois dele, sem erros nos logs |
| Smoke test na API contra PostgreSQL 16 | 10 produtos; pedido de R$ 64,70; pulo de estado devolve 409; ciclo até `entregue`; painel correto; 10 produtos após `restart` |
| Telas no navegador (Playwright) | Totem, cozinha e painel funcionando; 0 erros de console (só o aviso padrão do Tailwind CDN) |
| `ruff` e `mypy` | Não executados: não estão instalados |

## Arquivos entregues

| # | Arquivo | Situação |
|---|---|---|
| 1-4 | `requirements.txt`, `Dockerfile`, `docker-compose.yml`, `.dockerignore` | Criados |
| 5-10 | `app/{__init__,estados,database,models,schemas,seed}.py` | Criados |
| 11 | `app/servicos.py` | Criado |
| 12-15 | `app/routers/{__init__,produtos,pedidos,painel}.py` | Criados |
| 16 | `app/main.py` | Criado |
| 17-19 | `app/static/css/tokens.css`, `js/tailwind-config.js`, `js/api.js` | Criados |
| 20-22 | `totem`, `cozinha` e `painel` (`.html` + `.js`) | Criados |
| 23-28 | `tests/{conftest,test_estados,test_seed,test_pedidos,test_painel}.py`, `pytest.ini` | Criados |
| 29 | `specs/DESIGN_SYSTEM.md` | Atualizado para 1.1.0 |
| 30 | `README.md` | Seção "Executar a demonstração" |
| extra | `.gitignore` | Criado (`__pycache__`, `.pytest_cache`) |

## Cobertura dos testes de aceitação

| Teste | Como foi verificado |
|---|---|
| AT-01, AT-02 | `test_seed.py` e restart no compose |
| AT-03, AT-04, AT-05 | `test_pedidos.py` |
| AT-06, AT-07, AT-08 | `test_pedidos.py`, `test_estados.py`, smoke test (409) |
| AT-09 | `test_pedidos.py::test_numeros_crescentes_e_ordem_de_chegada` |
| AT-10 | Botão desabilitado com carrinho vazio, conferido no código; não exercitado no navegador |
| AT-11 | Temporizador de 8 s implementado; **não** cronometrado no navegador |
| AT-12 | Erro padronizado e carrinho mantido implementados; **não** simulado no navegador |
| AT-13 | Verificado no navegador: destaque com o número, some após 6 s, pedido na coluna "Pronto" |
| AT-14 | `test_painel.py` e smoke test (painel vazio após a entrega) |
| CS-01, CS-02 | Verificados no smoke test e no navegador |

## Desvios do DESIGN

| Item | Desvio | Motivo |
|---|---|---|
| Ordem dos scripts (D2, seção 6.7) | O `tailwind-config.js` carrega **depois** do CDN | O DESIGN dizia o contrário e dava `ReferenceError: tailwind is not defined`. O DESIGN foi corrigido |
| Favicon | `<link rel="icon" href="data:,">` nas três páginas | Evita 404 no console |
| Tela inicial do totem | Tela "Faça seu pedido" com botão "Toque para começar" | O DESIGN falava em "tela inicial" sem defini-la. É o destino do retorno de 8 s e de 30 s |
| `GET /api/produtos` | Ordem de categorias por `CASE` em SQL | O DESIGN pedia essa ordem e não indicava como obtê-la |

## Pendências e riscos

- **Voz (RF-22):** a lógica está implementada, mas o áudio não foi ouvido. O ambiente de teste não permite verificar a Web Speech API. Testar na TV real, depois de tocar em "Ativar som".
- **Cronometragem no navegador:** os 8 s de confirmação, os 30 s de inatividade e a mensagem de erro de rede (AT-11, AT-12) estão implementados, mas não foram cronometrados nem simulados.
- **Tailwind via CDN:** exige internet. O CDN emite o aviso "should not be used in production", esperado em uma demonstração.
- **Tempo médio de preparo:** mostra no mínimo "1 min", mesmo com tempos menores (arredondamento para cima na tela).
- **Python local 3.9:** o código usa `X | None` e exige Python 3.10 ou superior fora do Docker. Está no README.
- **Aviso de depreciação:** o `TestClient` avisa para usar `httpx2` no lugar de `httpx`. Não afeta os testes. Revisar ao fixar versões.
- **Versões:** `requirements.txt` usa faixas. Fixar as versões exatas antes de distribuir para a turma.
- **Concorrência (D1):** a nova tentativa de número foi testada com `IntegrityError` simulado, mas não com requisições simultâneas reais no PostgreSQL.
- **Sem commits:** nada foi commitado.
