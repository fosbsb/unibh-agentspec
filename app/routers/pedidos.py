from fastapi import APIRouter, HTTPException

from app.database import SessaoDep
from app.schemas import AvancarEntrada, FilaSaida, PedidoEntrada, PedidoSaida
from app.services import pedidos as servico

router = APIRouter(prefix="/api/pedidos")


def _saida(pedido) -> PedidoSaida:
    return PedidoSaida(
        id=pedido.id,
        numero=f"{pedido.numero:03d}",
        estado=pedido.estado,
        criado_em=pedido.criado_em,
        iniciado_em=pedido.iniciado_em,
        pronto_em=pedido.pronto_em,
        itens=[
            {
                "produto_id": i.produto_id,
                "nome": i.produto.nome,
                "icone": i.produto.icone,
                "quantidade": i.quantidade,
                "preco_unitario_centavos": i.preco_unitario_centavos,
            }
            for i in pedido.itens
        ],
    )


@router.post("", response_model=PedidoSaida, status_code=201)
def criar(entrada: PedidoEntrada, session: SessaoDep):
    try:
        return _saida(servico.criar_pedido(session, entrada.itens))
    except servico.ProdutoInexistente as erro:
        raise HTTPException(422, str(erro))


@router.get("", response_model=FilaSaida)
def fila(session: SessaoDep):
    return FilaSaida(
        pedidos=[_saida(p) for p in servico.listar_fila(session)],
        tempo_medio_preparo_segundos=servico.tempo_medio_preparo(session),
    )


@router.post("/{pedido_id}/avancar", response_model=PedidoSaida)
def avancar(pedido_id: int, entrada: AvancarEntrada, session: SessaoDep):
    try:
        return _saida(servico.avancar(session, pedido_id, entrada.estado_atual))
    except servico.PedidoNaoEncontrado:
        raise HTTPException(404, "Pedido não encontrado.")
    except servico.ConflitoEstado:
        raise HTTPException(409, "O pedido mudou de estado. Atualize a tela.")
