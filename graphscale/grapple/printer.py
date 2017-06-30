from graphscale import check
from graphscale.utils import to_snake_case
from .parser import FieldVarietal, NonNullTypeRef


def grapple_graphql_header():
    return """#W0661: unused imports lint
#C0301: line too long
#C0103: disable invalid constant name
#pylint: disable=W0611,C0301,C0103

from graphql import (
    GraphQLSchema,
    GraphQLObjectType,
    GraphQLField,
    GraphQLString,
    GraphQLArgument,
    GraphQLList,
    GraphQLInt,
    GraphQLInputObjectType,
    GraphQLInputObjectField,
    GraphQLNonNull,
    GraphQLID,
    GraphQLEnumType,
    GraphQLBoolean,
)

from graphql.type import GraphQLEnumValue

from graphscale.grapple import (
    GrappleType,
    id_field,
    req,
    list_of,
    GraphQLDate,
    GraphQLUUID,
    define_default_resolver,
    define_pent_mutation_resolver,
)
"""


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


def print_grapple_classes(document_ast):
    writer = CodeWriter()
    if document_ast.query_type():
        print_root_class(writer, document_ast, document_ast.query_type())
    if document_ast.mutation_type():
        print_root_class(writer, document_ast, document_ast.mutation_type())
    for pent_type in document_ast.pents():
        print_generated_pent(writer, document_ast, pent_type)

    for pent_mutation_data in document_ast.pent_mutation_datas():
        print_generated_pent_mutation_data(writer, document_ast, pent_mutation_data)

    writer.blank_line()
    return writer.result()


def print_generated_pent_mutation_data(writer, document_ast, grapple_type):
    writer.line('class %sGenerated(PentMutationData):' % grapple_type.name)
    writer.increase_indent()  # begin class implementation

    writer.line('def __init__(self, *,')
    writer.increase_indent()  # begin arg list
    for field in grapple_type.fields:
        if field.type_ref.is_nonnull:
            writer.line('{name},'.format(name=field.python_name))
        else:
            writer.line('{name}=None,'.format(name=field.python_name))
    writer.decrease_indent()  # end arg list
    writer.line('):')
    writer.increase_indent()  # begin __init__ impl

    writer.line('self._data = locals()')
    writer.line("del self._data['self']")

    writer.decrease_indent()  # end __init__ impl
    writer.blank_line()
    print_generated_fields(writer, document_ast, grapple_type.fields)
    writer.decrease_indent()  # end class definition


def print_graphql_defs(document_ast):
    writer = CodeWriter()
    for object_type in document_ast.object_types():
        print_graphql_object_type(writer, document_ast, object_type)
    for input_type in document_ast.input_types():
        print_graphql_input_type(writer, input_type)
    for enum_type in document_ast.enum_types():
        print_graphql_enum_type(writer, enum_type)

    return writer.result()


def uncapitalized(string):
    return string[0].lower() + string[1:]


def capitalize(string):
    return string[0].upper() + string[1:]


def print_graphql_input_type(writer, grapple_type):
    writer.line('GraphQL%s = GraphQLInputObjectType(' % grapple_type.name)
    writer.increase_indent()  # begin GraphQLInputObjectType .ctor args
    writer.line("name='%s'," % grapple_type.name)
    writer.line('fields=lambda: {')
    writer.increase_indent()  # begin field declarations
    for field in grapple_type.fields:
        print_graphql_input_field(writer, field)
    writer.decrease_indent()  # end field declarations
    writer.line('},')
    writer.decrease_indent()  # end GraphQLInputObjectType .ctor args
    writer.line(')')
    writer.blank_line()


def print_graphql_enum_type(writer, grapple_type):
    writer.line('GraphQL%s = GraphQLEnumType(' % grapple_type.name)
    writer.increase_indent()  # begin GraphQLEnumType .ctor args
    writer.line("name='%s'," % grapple_type.name)
    writer.line('values={')
    writer.increase_indent()  # begin value declarations
    for value in grapple_type.values:
        writer.line("'%s': GraphQLEnumValue()," % value)
    writer.decrease_indent()  # end value declarations
    writer.line('},')
    writer.decrease_indent()  # end GraphQLEnumType.ctor args
    writer.line(')')
    writer.blank_line()


def print_graphql_object_type(writer, document_ast, grapple_type):
    writer.line('GraphQL%s = GraphQLObjectType(' % grapple_type.name)
    writer.increase_indent()  # begin GraphQLObjectType .ctor args
    writer.line("name='%s'," % grapple_type.name)
    writer.line('fields=lambda: {')
    writer.increase_indent()  # begin field declarations
    for field in grapple_type.fields:
        print_graphql_field(writer, document_ast, field)
    writer.decrease_indent()  # end field declarations
    writer.line('},')
    writer.decrease_indent()  # end GraphQLObjectType .ctor args
    writer.line(')')
    writer.blank_line()


def type_instantiation(type_string):
    lookup = {
        'String': 'GraphQLString',
        'Int': 'GraphQLInt',
        'ID': 'GraphQLID',
        'Boolean': 'GraphQLBoolean',
    }
    if type_string in lookup:
        return lookup[type_string]
    else:
        return 'GraphQL%s' % type_string


def type_ref_string(type_ref):
    if type_ref.is_list:
        return 'list_of(%s)' % type_ref_string(type_ref.inner_type)
    elif type_ref.is_nonnull:
        return 'req(%s)' % type_ref_string(type_ref.inner_type)
    else:
        return type_instantiation(type_ref.graphql_typename)


def graphql_type_string(type_ref):
    if type_ref.is_list:
        return '[%s]' % graphql_type_string(type_ref.inner_type)
    elif type_ref.is_nonnull:
        return '%s!' % graphql_type_string(type_ref.inner_type)
    else:
        return type_ref.graphql_typename


def is_single_dim_enum(document_ast, type_ref):
    if type_ref.is_list:
        return False
    if type_ref.is_nonnull:
        return is_single_dim_enum(document_ast, type_ref.inner_type)
    return document_ast.is_enum(type_ref.graphql_typename)


def print_graphql_field(writer, document_ast, grapple_field):
    type_ref_str = type_ref_string(grapple_field.type_ref)
    is_enum = is_single_dim_enum(document_ast, grapple_field.type_ref)

    writer.line("'%s': GraphQLField(" % grapple_field.name)
    writer.increase_indent()  # begin args to GraphQLField .ctor
    writer.line('type=%s,' % type_ref_str)

    if grapple_field.args:
        writer.line('args={')
        writer.increase_indent()  # begin entries in args dictionary
        for grapple_arg in grapple_field.args:
            arg_type_ref_str = type_ref_string(grapple_arg.type_ref)
            if grapple_arg.default_value is None:
                writer.line(
                    "'%s': GraphQLArgument(type=%s)," % (grapple_arg.name, arg_type_ref_str)
                )
            else:
                writer.line(
                    "'%s': GraphQLArgument(type=%s, default_value=%s)," %
                    (grapple_arg.name, arg_type_ref_str, grapple_arg.default_value)
                )

        writer.decrease_indent()  # end entries in args dictionary
        writer.line('},')  # close args dictionary

    python_name = grapple_field.python_name
    if is_enum:
        writer.line(
            'resolver=lambda obj, args, *_: obj.%s(*args).name if obj.%s(*args) else None,' %
            (python_name, python_name)
        )
    elif grapple_field.field_varietal.is_mutation:
        data_arg = None
        for arg in grapple_field.args:
            if arg.name == 'data':
                data_arg = arg
                break

        check.invariant(data_arg, 'mutations must have an arg named data')
        check.invariant(data_arg.name == 'data', 'mutation argument name must be data')
        check.invariant(data_arg.type_ref.is_nonnull, 'data argument must be required')

        data_cls = data_arg.type_ref.inner_type.python_typename
        writer.line("resolver=define_pent_mutation_resolver('%s', '%s')," % (python_name, data_cls))
    else:
        writer.line("resolver=define_default_resolver('%s')," % python_name)

    writer.decrease_indent()  # end args to GraphQLField .ctor
    writer.line('),')  # close GraphQLField .ctor


def print_graphql_input_field(writer, grapple_field):
    type_ref_str = type_ref_string(grapple_field.type_ref)
    writer.line("'%s': GraphQLInputObjectField(type=%s)," % (grapple_field.name, type_ref_str))


def filter_nodes(nodes, ast_cls):
    return filter(lambda node: isinstance(node, ast_cls), nodes)


class CodeWriter:
    def __init__(self):
        self.lines = []
        self.indent = 0

    def line(self, text):
        self.lines.append((" " * self.indent) + text)

    def blank_line(self):
        self.lines.append("")

    def increase_indent(self):
        self.indent += 4

    def decrease_indent(self):
        if self.indent <= 0:
            raise Exception('indent cannot be negative')
        self.indent -= 4

    def result(self):
        return "\n".join(self.lines)


def print_root_class(writer, document_ast, grapple_type):
    writer.line('class %sGenerated:' % grapple_type.name)
    writer.increase_indent()  # begin class implementation
    writer.line('@property')
    writer.line('def context(self):')
    writer.increase_indent()  # begin context impl
    writer.line("raise Exception('must implement in Root')")
    writer.decrease_indent()  # endcontext impl
    writer.blank_line()
    print_generated_fields(writer, document_ast, grapple_type.fields)
    writer.blank_line()
    writer.decrease_indent()  # end class definition


def print_generated_pent(writer, document_ast, grapple_type):
    writer.line('class %sGenerated(Pent):' % grapple_type.name)
    writer.increase_indent()  # begin class implementation
    print_generated_fields(writer, document_ast, grapple_type.fields)
    writer.decrease_indent()  # end class definition


def print_if_return_false(writer, if_line):
    writer.line(if_line)
    writer.increase_indent()
    writer.line('return False')
    writer.decrease_indent()


def print_required_data_check(writer, field):
    python_typename = field.type_ref.python_typename
    graphql_type = graphql_type_string(field.type_ref)
    print_if_return_false(
        writer, "if req_data_elem_invalid(data, '%s', %s): # %s: %s" %
        (field.python_name, python_typename, field.name, graphql_type)
    )


def print_optional_data_check(writer, field):
    python_typename = field.type_ref.python_typename
    graphql_type = graphql_type_string(field.type_ref)
    print_if_return_false(
        writer, "if opt_data_elem_invalid(data, '%s', %s): # %s: %s" %
        (field.name, python_typename, field.name, graphql_type)
    )


def get_required_arg(args, name):
    for arg in args:
        if arg.name == name:
            return arg

    check.failed('arg with name %s could not be found' % name)


def print_generated_fields(writer, document_ast, fields):
    wrote_once = False
    for field in fields:
        if field.field_varietal.is_custom_impl:
            continue
        elif field.field_varietal == FieldVarietal.VANILLA:
            print_vanilla_field(writer, field)
        elif field.field_varietal == FieldVarietal.READ_PENT:
            print_read_pent_field(writer, field)
        elif field.field_varietal == FieldVarietal.CREATE_PENT:
            print_create_pent_field(writer, document_ast, field)
        elif field.field_varietal == FieldVarietal.DELETE_PENT:
            print_delete_pent_field(writer, field)
        elif field.field_varietal == FieldVarietal.UPDATE_PENT:
            print_update_pent_field(writer, document_ast, field)
        elif field.field_varietal == FieldVarietal.BROWSE_PENTS:
            print_browse_pents_field(writer, field)
        elif field.field_varietal == FieldVarietal.GEN_FROM_STORED_ID:
            print_gen_from_stored_id_field(writer, field)
        elif field.field_varietal == FieldVarietal.EDGE_TO_STORED_ID:
            print_edge_to_stored_id_field(writer, field)
        else:
            raise Exception('unsupported varietal')

        wrote_once = True

    if not wrote_once:
        writer.line('pass')


def print_edge_to_stored_id_field(writer, field):
    first_arg, after_arg, target_type = get_first_after_args(field)
    writer.line('async def %s(self, first, after=None):' % field.python_name)
    writer.increase_indent()  # begin implemenation
    writer.line(
        "return await self.gen_associated_pents_dynamic"
        "('{target_type}', '{edge_name}', after, first)".format(
            target_type=target_type, edge_name=field.field_varietal_data.edge_name
        )
    )
    writer.decrease_indent()  # end implementation
    writer.blank_line()


def print_gen_from_stored_id_field(writer, field):
    check.invariant(len(field.args) == 0, 'genFromStoredId should have no args')
    check.invariant(field.type_ref.is_named, 'only supports bare types for now')

    cls_name = field.type_ref.python_typename
    # very hard coded for now. should be configurable via argument to directive optionally
    prop = to_snake_case(field.name) + '_id'

    writer.line('async def %s(self):' % field.python_name)
    writer.increase_indent()  # begin implemenation
    writer.line(
        "return await self.gen_from_stored_id_dynamic"
        "('{cls_name}', '{prop}')".format(cls_name=cls_name, prop=prop)
    )
    writer.decrease_indent()  # end implementation
    writer.blank_line()


def get_first_after_args(field):
    check.invariant(len(field.args) == 2, 'browse/conn should have 2 args')
    first_arg = get_required_arg(field.args, 'first')
    check.invariant(first_arg.default_value, 'must have default value')

    after_arg = get_required_arg(field.args, 'after')
    check.invariant(after_arg.type_ref.graphql_typename == 'UUID', 'arg must be UUID')

    check.invariant(field.type_ref.is_nonnull, 'outer non null')
    check.invariant(field.type_ref.inner_type.is_list, 'then list')
    check.invariant(field.type_ref.inner_type.inner_type.is_nonnull, 'then nonnull')
    check.invariant(field.type_ref.inner_type.inner_type.inner_type.is_named, 'then named')
    target_type = field.type_ref.inner_type.inner_type.inner_type.python_typename
    return (first_arg, after_arg, target_type)


def print_browse_pents_field(writer, field):
    first_arg, after_arg, browse_type = get_first_after_args(field)

    writer.line('async def %s(self, first, after=None):' % field.python_name)
    writer.increase_indent()  # begin implemenation
    writer.line(
        "return await gen_browse_pents_dynamic(self.context, after, first, '%s')" % browse_type
    )
    writer.decrease_indent()  # end implementation
    writer.blank_line()


def print_update_pent_field(writer, document_ast, field):
    check.invariant(len(field.args) == 2, 'updatePent should have 2 args')
    check_required_id_arg(field)
    pent_cls, data_cls, payload_cls = get_mutation_classes(document_ast, field)

    writer.line('async def %s(self, obj_id, data):' % field.python_name)
    writer.increase_indent()  # begin implemenation
    writer.line(
        "return await gen_update_pent_dynamic"
        "(self.context, obj_id, '{pent_cls}', '{data_cls}', '{payload_cls}', data)".format(
            pent_cls=pent_cls, data_cls=data_cls, payload_cls=payload_cls
        )
    )
    writer.decrease_indent()  # end implementation
    writer.blank_line()


def print_delete_pent_field(writer, field):
    check.invariant(len(field.args) == 1, 'deletePent should only have 1 arg')
    check_required_id_arg(field)
    payload_cls = field.type_ref.python_typename
    pent_cls = field.field_varietal_data.type

    writer.line('async def %s(self, obj_id):' % field.python_name)
    writer.increase_indent()  # begin implemenation
    writer.line(
        "return await gen_delete_pent_dynamic(self.context, '{pent_cls}', '{payload_cls}', obj_id)".
        format(pent_cls=pent_cls, payload_cls=payload_cls)
    )
    writer.decrease_indent()  # end implementation
    writer.blank_line()


def get_mutation_classes(document_ast, field):
    data_cls = get_data_arg_in_pent(field)
    payload_cls = field.type_ref.python_typename

    payload_type = document_ast.type_named(payload_cls)
    check.invariant(
        len(payload_type.fields) == 1, 'payload class for vanilla crud should only have one field'
    )
    data_field = payload_type.fields[0]
    pent_cls = data_field.type_ref.python_typename
    return (pent_cls, data_cls, payload_cls)


def print_create_pent_field(writer, document_ast, field):
    check.invariant(len(field.args) == 1, 'createPent should only have 1 arg')

    pent_cls, data_cls, payload_cls = get_mutation_classes(document_ast, field)

    writer.line('async def %s(self, data):' % field.python_name)
    writer.increase_indent()  # begin implemenation
    writer.line(
        "return await gen_create_pent_dynamic"
        "(self.context, '{pent_cls}', '{data_cls}', '{payload_cls}', data)".format(
            pent_cls=pent_cls, data_cls=data_cls, payload_cls=payload_cls
        )
    )
    writer.decrease_indent()  # end implemenation
    writer.blank_line()


def print_read_pent_field(writer, field):
    writer.line('async def %s(self, obj_id):' % field.python_name)
    writer.increase_indent()  # begin implemenation
    writer.line(
        "return await gen_pent_dynamic(self.context, '%s', obj_id)" % field.type_ref.python_typename
    )
    writer.decrease_indent()  # end implemenation
    writer.blank_line()


def print_vanilla_field(writer, field):
    writer.line('@property')
    writer.line('def %s(self):' % field.python_name)
    writer.increase_indent()  # begin property implemenation
    if not field.type_ref.is_nonnull:
        writer.line("return self._data.get('%s')" % field.python_name)
    else:
        writer.line("return self._data['%s']" % field.python_name)
    writer.decrease_indent()  # end property definition
    writer.blank_line()


def get_data_arg_in_pent(field):
    data_arg = get_required_arg(field.args, 'data')
    check.invariant(
        isinstance(data_arg.type_ref, NonNullTypeRef), 'input argument must be non null'
    )

    return data_arg.type_ref.inner_type.python_typename


def check_required_id_arg(field):
    id_arg = get_required_arg(field.args, 'id')
    check.invariant(id_arg.type_ref.is_nonnull, 'arg must be non null')
    check.invariant(id_arg.type_ref.inner_type.graphql_typename == 'UUID', 'arg must be UUID')
