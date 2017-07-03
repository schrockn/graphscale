from graphscale import safecheck

from .code_writer import CodeWriter
from .parser import (
    EdgeToStoredIdData, FieldVarietal, GrappleDocument, GrappleField, TypeRefVarietal
)

GRAPPLE_KVETCH_HEADER = """#W0661: unused imports lint
#C0301: line too long
#pylint: disable=W0661, C0301

from graphscale.kvetch import define_object, define_stored_id_edge
"""


def print_kvetch_decls(document_ast: GrappleDocument) -> str:

    writer = CodeWriter()
    writer.line(GRAPPLE_KVETCH_HEADER)

    writer.line("def generated_objects():")
    writer.increase_indent()
    writer.line('return [')
    writer.increase_indent()
    for pent_type in document_ast.pents():
        writer.line(
            "define_object(type_name='%s', type_id=%s)," % (pent_type.name, pent_type.type_id)
        )
    writer.decrease_indent()
    writer.line(']')
    writer.decrease_indent()
    writer.blank_line()

    print_kvetch_generated_edges(writer, document_ast)

    writer.line("def generated_indexes():")
    writer.increase_indent()
    writer.line('return []')
    writer.decrease_indent()
    writer.blank_line()

    return writer.result()


def get_stored_on_type(field: GrappleField) -> str:
    safecheck.invariant(field.type_ref.varietal == TypeRefVarietal.NONNULL, 'outer non null')
    safecheck.invariant(field.type_ref.inner_type.varietal == TypeRefVarietal.LIST, 'then list')
    safecheck.invariant(
        field.type_ref.inner_type.inner_type.varietal == TypeRefVarietal.NONNULL, 'then nonnull'
    )
    safecheck.invariant(
        field.type_ref.inner_type.inner_type.inner_type.varietal == TypeRefVarietal.NAMED,
        'then named'
    )
    return field.type_ref.inner_type.inner_type.inner_type.python_typename


def define_edge_code(field: GrappleField) -> str:
    data = field.field_varietal_data

    if not isinstance(data, EdgeToStoredIdData):
        safecheck.failed('must be EdgeToStoredIdData')

    stored_on_type = get_stored_on_type(field)

    return (
        "define_stored_id_edge(edge_name='{edge_name}', edge_id={edge_id}"
        ", stored_id_attr='{stored_id_attr}', stored_on_type='{stored_on_type}'),"
    ).format(
        edge_name=data.edge_name,
        edge_id=data.edge_id,
        stored_id_attr=data.field + '_id',
        stored_on_type=stored_on_type
    )


def print_kvetch_generated_edges(writer: CodeWriter, document_ast: GrappleDocument) -> None:
    writer.line("def generated_edges():")
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
