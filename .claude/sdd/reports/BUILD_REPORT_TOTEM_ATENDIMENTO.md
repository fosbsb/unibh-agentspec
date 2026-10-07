# BUILD REPORT: Totem de Atendimento

## Metadados

| Atributo | Valor |
|---|---|
| **Feature** | TOTEM_ATENDIMENTO |
| **Data** | 2026-10-07 |
| **DESIGN** | `.claude/sdd/features/DESIGN_TOTEM_ATENDIMENTO.md` |
| **Resultado** | Concluído, com verificações manuais pendentes (ver "Não verificado") |

## Resumo da verificação

| Verificação | Resultado |
|---|---|
| `pytest` (no container, PostgreSQL 16 real) | 24 passaram, 0 falharam |
| `ruff check app tests` | Sem erros |
| `docker compose up` a partir de ambiente limpo (`down -v`) | Sobe. 10 produtos em 4 categorias |
| Reinício do `app` | Continuam 10 produtos (sem duplicar) |
| Totem no navegador (1080x1920) | Fluxo completo até a confirmação. Volta ao início em 8 s |
| Cozinha no navegador | Mostra pedido com horário e itens. "Iniciar" avança para Preparando |
| Painel no navegador (1920x1080) | Destaque de 6 s e voz "Pedido 1, pronto" em pt-BR (síntese espionada) |

## Arquivos do manifesto

| # | Arquivo | Estado |
|---|---|---|
| 1–5 | `requirements.txt`, `Dockerfile`, `docker-compose.yml`, `.dockerignore`, `pytest.ini` | Criados |
| 6–18 | `app/` (`config`, `relogio`, `database`, `models`, `schemas`, `seed`, `services/pedidos`, `routers/produtos`, `routers/pedidos`, `main`) | Criados |
| 19–27 | `app/static/` (`css/tokens.css`, `js/tailwind-config.js`, `js/api.js`, `totem`, `cozinha`, `painel`: HTML e JS) | Criados |
| 28–32 | `tests/` (`conftest`, `test_cardapio`, `test_pedidos`, `test_estados`, `test_fila`) | Criados |
| 33 | `specs/DESIGN_SYSTEM.md` | Atualizado para 1.1.0 na fase de design, com um complemento no build |
| 34 | `README.md` | Seção "Rodando o totem" e linha do projeto de exemplo atualizada |
| extra | `.gitignore` | Criado (fora do manifesto) |

## Cobertura dos testes de aceitação

| Aceitação | Situação | Onde |
|---|---|---|
| AT-001 a AT-005 | Automatizado, passou | `test_pedidos.py` |
| AT-006, AT-007 | Automatizado, passou | `test_estados.py` |
| AT-008 | Automatizado, passou (linha bloqueada e corrida de duas threads) | `test_estados.py` |
| AT-009, AT-012 | Automatizado, passou | `test_fila.py` |
| AT-010, AT-011 | Automatizado, passou | `test_cardapio.py` |
| AT-014 (confirmação 8 s) | Verificado manualmente no navegador | — |
| AT-015 (destaque e voz) | Verificado no navegador. A fala foi capturada por um espião de `speechSynthesis`, sem ouvir o áudio | — |
| AT-013 (30 s de inatividade) | **Não verificado** | — |
| AT-016 (erro de envio) | **Não verificado** | — |

## Desvios do DESIGN

| Desvio | Motivo |
|---|---|
| `SessaoDep = Annotated[Session, Depends(get_session)]` em `database.py` | Evita o aviso B008 do ruff com o padrão `Depends` em argumento padrão. Comportamento idêntico |
| Linhas do carrinho com "−", "+" e "Remover" ficam na tela de revisão, e a barra do cardápio só resume | O DESIGN não dizia onde ficavam. O design system 6.4 e 6.5.1 foi ajustado para refletir isso |
| O painel lista pedidos **Recebido e Preparando** na coluna "Preparando" | O design system não definia onde o cliente vê um pedido recém-criado |
| `<link rel="icon" href="data:,">` nas três telas | Evita o 404 de `/favicon.ico` no console |
| O `Dockerfile` copia `tests/` e `pytest.ini` para a imagem | Permite `docker compose run --rm app pytest` |

## Não verificado

1. **Ociosidade de 30 s no totem (AT-013)**: o timer está implementado, mas não esperei os 30 s no navegador.
2. **Erro de envio (AT-016)**: o caminho de erro com "Tentar de novo" e a preservação do carrinho não foi exercitado.
3. **Conflito na cozinha com duas abas (passo 6 do roteiro)**: o 409 está coberto por pytest, mas a mensagem na interface não foi vista.
4. **CS-07 (tamanhos mínimos)**: o texto base e os botões usam os tokens do design system, mas não medi cada elemento. Os títulos "Carrinho vazio" e o texto dos seletores foram vistos só nas capturas.
5. **`prefers-reduced-motion`**: regra presente em `tokens.css`, sem teste visual.
6. **Áudio real**: não ouvi a voz. Só confirmei a chamada com texto "Pedido 1, pronto" e idioma pt-BR.
7. **Primeira carga sem internet**: o Tailwind via CDN foi carregado com rede disponível. Sem rede, as telas ficam sem estilo (suposição já registrada no DEFINE).

## Observações

- O teste de corrida (`test_corrida_entre_dois_atendentes`) usa duas threads com uma barreira. O resultado esperado (um 200 e um 409) é garantido pelo `estado_atual` mesmo quando o `SKIP LOCKED` não dispara, então o teste é estável. O caso do bloqueio em si é coberto pelo teste determinístico `test_linha_bloqueada_por_outro_atendente_e_conflito`.
- Os dados da demonstração criados durante a verificação foram apagados com `docker compose down -v`.
- O estado "Entregue" tem um selo definido em `api.js` (ícone 📦), embora entregues nunca apareçam nas telas. O design system não define esse selo.

## Próximo passo

```bash
/ship .claude/sdd/features/DEFINE_TOTEM_ATENDIMENTO.md
```
