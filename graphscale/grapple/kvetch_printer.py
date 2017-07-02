from graphscale import check

from .code_writer import CodeWriter
from .parser import FieldVarietal


def print_kvetch_decls(document_ast):

    writer = CodeWriter()
    writer.line('from graphscale.kvetch import define_object, define_stored_id_edge')
    writer.blank_line()

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


def get_stored_on_type(field):
    check.invariant(field.type_ref.is_nonnull, 'outer non null')
    check.invariant(field.type_ref.inner_type.is_list, 'then list')
    check.invariant(field.type_ref.inner_type.inner_type.is_nonnull, 'then nonnull')
    check.invariant(field.type_ref.inner_type.inner_type.inner_type.is_named, 'then named')
    return field.type_ref.inner_type.inner_type.inner_type.python_typename


def define_edge_code(field):
    data = field.field_varietal_data
    stored_on_type = get_stored_on_type(field)

    return "define_stored_id_edge(edge_name='{edge_name}', edge_id={edge_id}, stored_id_attr='{stored_id_attr}', stored_on_type='{stored_on_type}'),".format(
        edge_name=data.edge_name,
        edge_id=data.edge_id,
        stored_id_attr=data.field + '_id',
        stored_on_type=stored_on_type
    )


def print_kvetch_generated_edges(writer, document_ast):
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
