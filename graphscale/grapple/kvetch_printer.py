from .code_writer import CodeWriter


def print_kvetch_decls(document_ast):

    writer = CodeWriter()
    writer.line('from graphscale.kvetch import define_object, define_edge')
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


def define_edge_code(data):
    return "define_edge(edge_name='{edge_name}', edge_id={edge_id}, from_id_attr='{from_id_attr}'),".format(
        edge_name=data.edge_name, edge_id=data.edge_id, from_id_attr=data.field + '_id'
    )


def print_kvetch_generated_edges(writer, document_ast):
    writer.line("def generated_edges():")
    writer.increase_indent()
    writer.line('return [')
    writer.increase_indent()
    for pent_type in document_ast.pents():
        for field in pent_type.fields:
            if field.field_varietal == FieldVarietal.EDGE_TO_STORED_ID:
                writer.line(define_edge_code(field.field_varietal_data))
    writer.decrease_indent()
    writer.line(']')
    writer.decrease_indent()
    writer.blank_line()
