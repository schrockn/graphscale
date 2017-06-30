from graphscale import check
from .code_writer import CodeWriter


def print_graphql_file(document_ast):
    return grapple_graphql_header() + '\n' + print_graphql_defs(document_ast)


def print_graphql_defs(document_ast):
    writer = CodeWriter()
    for object_type in document_ast.object_types():
        print_graphql_object_type(writer, document_ast, object_type)
    for input_type in document_ast.input_types():
        print_graphql_input_type(writer, input_type)
    for enum_type in document_ast.enum_types():
        print_graphql_enum_type(writer, enum_type)

    return writer.result()


def is_single_dim_enum(document_ast, type_ref):
    if type_ref.is_list:
        return False
    if type_ref.is_nonnull:
        return is_single_dim_enum(document_ast, type_ref.inner_type)
    return document_ast.is_enum(type_ref.graphql_typename)


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
    req,
    list_of,
    GraphQLDate,
    GraphQLUUID,
    define_default_resolver,
    define_default_gen_resolver,
    define_pent_mutation_resolver,
)
"""


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
    elif grapple_field.field_varietal.is_gen_varietal:
        writer.line("resolver=define_default_gen_resolver('%s')," % python_name)
    else:
        writer.line("resolver=define_default_resolver('%s')," % python_name)

    writer.decrease_indent()  # end args to GraphQLField .ctor
    writer.line('),')  # close GraphQLField .ctor


def print_graphql_input_field(writer, grapple_field):
    type_ref_str = type_ref_string(grapple_field.type_ref)
    writer.line("'%s': GraphQLInputObjectField(type=%s)," % (grapple_field.name, type_ref_str))


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
