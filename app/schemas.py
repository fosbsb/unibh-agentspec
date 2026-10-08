from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.estados import EstadoPedido


class ProdutoOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nome: str
    categoria: str
    icone: str
    preco_centavos: int


class ItemIn(BaseModel):
    produto_id: int
    quantidade: int = Field(ge=1, le=20)


class PedidoIn(BaseModel):
    itens: list[ItemIn] = Field(min_length=1, max_length=30)


class ItemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    produto_id: int
    nome: str
    preco_centavos: int
    quantidade: int


class PedidoOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    numero: int
    estado: EstadoPedido
    total_centavos: int
    criado_em: datetime
    itens: list[ItemOut]


class EstadoIn(BaseModel):
    estado: EstadoPedido


class PedidoResumo(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    numero: int


class PainelOut(BaseModel):
    preparando: list[PedidoResumo]
    pronto: list[PedidoResumo]
    tempo_medio_segundos: int | None
