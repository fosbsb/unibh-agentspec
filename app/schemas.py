from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, computed_field

Estado = Literal["recebido", "preparando", "pronto", "entregue"]


class ItemEntrada(BaseModel):
    produto_id: int
    quantidade: int = Field(ge=1, le=99)


class PedidoEntrada(BaseModel):
    itens: list[ItemEntrada] = Field(min_length=1)


class AvancarEntrada(BaseModel):
    estado_atual: Estado


class ProdutoSaida(BaseModel):
    id: int
    nome: str
    icone: str
    preco_centavos: int


class CategoriaSaida(BaseModel):
    nome: str
    produtos: list[ProdutoSaida]


class CardapioSaida(BaseModel):
    categorias: list[CategoriaSaida]


class ItemSaida(BaseModel):
    produto_id: int
    nome: str
    icone: str
    quantidade: int
    preco_unitario_centavos: int

    @computed_field
    @property
    def subtotal_centavos(self) -> int:
        return self.quantidade * self.preco_unitario_centavos


class PedidoSaida(BaseModel):
    id: int
    numero: str
    estado: Estado
    criado_em: datetime
    iniciado_em: datetime | None
    pronto_em: datetime | None
    itens: list[ItemSaida]

    @computed_field
    @property
    def total_centavos(self) -> int:
        return sum(i.subtotal_centavos for i in self.itens)


class FilaSaida(BaseModel):
    pedidos: list[PedidoSaida]
    tempo_medio_preparo_segundos: int | None
