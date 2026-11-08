"""Operadores SQL sobre colunas JSON com semântica idêntica entre SQLite e PostgreSQL.

`Column.contains()` em uma coluna JSON genérica compila para `LIKE '%valor%'`: no SQLite isso é
um teste de substring sobre o texto serializado (``patient.read`` casaria com
``["patient.read.extra"]``) e no PostgreSQL falha com ``operator does not exist: json ~~ text``.
Escopos de autorização precisam de pertencimento exato a um array JSON de strings, a mesma
semântica de ``valor in set(lista)`` usada na checagem por objeto.
"""

from __future__ import annotations

from typing import Any

from sqlalchemy import String, literal
from sqlalchemy.exc import CompileError
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.sql.elements import ColumnElement
from sqlalchemy.sql.functions import FunctionElement
from sqlalchemy.types import Boolean


class json_array_contains(FunctionElement[bool]):  # noqa: N801 - convenção de construto SQL
    """Verdadeiro somente se a coluna for um array JSON contendo exatamente a string dada."""

    type = Boolean()
    inherit_cache = True
    name = "json_array_contains"

    def __init__(self, column: ColumnElement[Any], value: str) -> None:
        super().__init__(column, literal(value, String()))


def _parts(element: json_array_contains, compiler: Any, **kw: Any) -> tuple[str, str]:
    column, value = list(element.clauses)
    return compiler.process(column, **kw), compiler.process(value, **kw)


@compiles(json_array_contains, "postgresql")
def _compile_postgresql(element: json_array_contains, compiler: Any, **kw: Any) -> str:
    column, value = _parts(element, compiler, **kw)
    return (
        f"(jsonb_typeof(CAST({column} AS JSONB)) = 'array' "
        f"AND CAST({column} AS JSONB) @> jsonb_build_array(CAST({value} AS TEXT)))"
    )


@compiles(json_array_contains, "sqlite")
def _compile_sqlite(element: json_array_contains, compiler: Any, **kw: Any) -> str:
    column, value = _parts(element, compiler, **kw)
    return (
        f"(json_type({column}) = 'array' AND EXISTS (SELECT 1 FROM json_each({column}) "
        f"WHERE json_each.type = 'text' AND json_each.value = {value}))"
    )


@compiles(json_array_contains)
def _compile_unsupported(element: json_array_contains, compiler: Any, **kw: Any) -> str:
    raise CompileError(
        f"json_array_contains não suporta o dialeto {compiler.dialect.name}; "
        "falhando fechado para não ampliar escopo de autorização."
    )
