from graphscale import check
from graphscale.utils import to_snake_case

from .code_writer import CodeWriter
from .parser import (
    EdgeToStoredIdData, FieldVarietal, GrappleDocument, GrappleField, TypeRefVarietal
)

GRAPPLE_KVETCH_HEADER = """#W0611: unused imports lint
#C0301: line too long
#pylint: disable=W0611, C0301

from typing import List
from graphscale.kvetch import ObjectDefinition, StoredIdEdgeDefinition, IndexDefinition
"""


def print_kvetch_decls(document_ast: GrappleDocument) -> str:

    writer = CodeWriter()
    writer.line(GRAPPLE_KVETCH_HEADER)

    writer.line("def generated_objects() -> List[ObjectDefinition]:")
    writer.increase_indent()
    writer.line('return [')
    writer.increase_indent()
    for pent_type in document_ast.pents():
        writer.line(
            "ObjectDefinition(type_name='%s', type_id=%s)," % (pent_type.name, pent_type.type_id)
        )
    writer.decrease_indent()
    writer.line(']')
    writer.decrease_indent()
    writer.blank_line()

    print_kvetch_generated_edges(writer, document_ast)

    writer.line("def generated_indexes() -> List[IndexDefinition]:")
    writer.increase_indent()
    writer.line('return []')
    writer.decrease_indent()
    writer.blank_line()

    return writer.result()


def get_stored_on_type(field: GrappleField) -> str:
    check.invariant(field.type_ref.varietal == TypeRefVarietal.NONNULL, 'outer non null')
    check.invariant(field.type_ref.inner_type.varietal == TypeRefVarietal.LIST, 'then list')
    check.invariant(
        field.type_ref.inner_type.inner_type.varietal == TypeRefVarietal.NONNULL, 'then nonnull'
    )
    check.invariant(
        field.type_ref.inner_type.inner_type.inner_type.varietal == TypeRefVarietal.NAMED,
        'then named'
    )
    return field.type_ref.inner_type.inner_type.inner_type.python_typename


def define_edge_code(field: GrappleField) -> str:
    data = field.field_varietal_data

    if not isinstance(data, EdgeToStoredIdData):
        check.failed('must be EdgeToStoredIdData')

    stored_on_type = get_stored_on_type(field)

    return (
        "StoredIdEdgeDefinition(edge_name='{edge_name}', edge_id={edge_id}"
        ", stored_id_attr='{stored_id_attr}', stored_on_type='{stored_on_type}'),"
    ).format(
        edge_name=data.edge_name,
        edge_id=data.edge_id,
        stored_id_attr=to_snake_case(data.field) + '_id',
        stored_on_type=stored_on_type
    )


def print_kvetch_generated_edges(writer: CodeWriter, document_ast: GrappleDocument) -> None:
    writer.line("def generated_edges() -> List[StoredIdEdgeDefinition]:")
    writer.increase_indent()
    writer.line('return [')
    writer.increase_indent()
    for pent_type in document_ast.pents():
        for field in pent_type.fields:
            if field.field_varietal == FieldVarietal.EDGE_TO_STORED_ID:
                writer.line(define_edge_code(field))
    writer.decrease_indent()
    writer.line(']')
    writer.decrease_indent()
    writer.blank_line()
