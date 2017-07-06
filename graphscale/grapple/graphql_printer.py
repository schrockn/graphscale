from graphscale import check
from .code_writer import CodeWriter
from .parser import TypeRefVarietal, GrappleDocument, GrappleTypeRef, GrappleTypeDef, GrappleField

from .pent_printer import get_mutation_classes, get_required_arg


def print_graphql_file(document_ast: GrappleDocument, module_name: str) -> str:
    return grapple_graphql_header(module_name) + '\n' + print_graphql_defs(document_ast)


def print_graphql_defs(document_ast: GrappleDocument) -> str:
    writer = CodeWriter()
    for object_type in document_ast.object_types():
        print_graphql_object_type(writer, document_ast, object_type)
    for input_type in document_ast.input_types():
        print_graphql_input_type(writer, input_type)
    for enum_type in document_ast.enum_types():
        print_graphql_enum_type(writer, enum_type)

    return writer.result()


def grapple_graphql_header(module_name: str) -> str:
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
    GraphQLPythonEnumType,
    define_default_resolver,
    define_default_gen_resolver,
    define_pent_mutation_resolver,
)

import {module_name}.pent as module_pents
""".format(module_name=module_name)


def print_graphql_input_type(writer: CodeWriter, grapple_type: GrappleTypeDef) -> None:
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


def print_graphql_enum_type(writer: CodeWriter, grapple_type: GrappleTypeDef) -> None:
    writer.line(
        'GraphQL{name} = GraphQLPythonEnumType(module_pents.{name})'.format(name=grapple_type.name)
    )
    writer.blank_line()


def print_graphql_object_type(
    writer: CodeWriter, document_ast: GrappleDocument, grapple_type: GrappleTypeDef
) -> None:
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


def print_graphql_field(
    writer: CodeWriter, _document_ast: GrappleDocument, grapple_field: GrappleField
) -> None:
    type_ref_str = type_ref_string(grapple_field.type_ref)

    writer.line("'%s': GraphQLField(" % grapple_field.name)
    writer.increase_indent()  # begin args to GraphQLField .ctor
    writer.line('type=%s, # type: ignore' % type_ref_str)

    if grapple_field.args:
        writer.line('args={')
        writer.increase_indent()  # begin entries in args dictionary
        for grapple_arg in grapple_field.args:
            arg_type_ref_str = type_ref_string(grapple_arg.type_ref)
            if grapple_arg.default_value is None:
                writer.line(
                    "'%s': GraphQLArgument(type=%s), # type: ignore" %
                    (grapple_arg.name, arg_type_ref_str)
                )
            else:
                writer.line(
                    "'%s': GraphQLArgument(type=%s, default_value=%s), # type: ignore" %
                    (grapple_arg.name, arg_type_ref_str, grapple_arg.default_value)
                )

        writer.decrease_indent()  # end entries in args dictionary
        writer.line('},')  # close args dictionary

    python_name = grapple_field.python_name
    if grapple_field.field_varietal.is_mutation:
        data_arg = None
        for arg in grapple_field.args:
            if arg.name == 'data':
                data_arg = arg
                break

        check.invariant(data_arg, 'mutations must have an arg named data')
        check.invariant(data_arg.name == 'data', 'mutation argument name must be data')
        check.invariant(
            data_arg.type_ref.varietal == TypeRefVarietal.NONNULL, 'data argument must be required'
        )

        data_cls = data_arg.type_ref.inner_type.python_typename
        writer.line("resolver=define_pent_mutation_resolver('%s', '%s')," % (python_name, data_cls))
    elif grapple_field.field_varietal.is_gen_varietal:
        writer.line("resolver=define_default_gen_resolver('%s')," % python_name)
    else:
        writer.line("resolver=define_default_resolver('%s')," % python_name)

    writer.decrease_indent()  # end args to GraphQLField .ctor
    writer.line('),')  # close GraphQLField .ctor


def print_graphql_input_field(writer: CodeWriter, grapple_field: GrappleField) -> None:
    type_ref_str = type_ref_string(grapple_field.type_ref)
    writer.line("'%s': GraphQLInputObjectField(type=%s)," % (grapple_field.name, type_ref_str))


def type_instantiation(type_string: str) -> str:
    lookup = {
        'String': 'GraphQLString',
        'Int': 'GraphQLInt',
        'ID': 'GraphQLID',
        'Boolean': 'GraphQLBoolean',
    }
    if type_string in lookup:
        return lookup[type_string]

    return 'GraphQL%s' % type_string


def type_ref_string(type_ref: GrappleTypeRef) -> str:
    if type_ref.varietal == TypeRefVarietal.LIST:
        return 'list_of(%s)' % type_ref_string(type_ref.inner_type)
    elif type_ref.varietal == TypeRefVarietal.NONNULL:
        return 'req(%s)' % type_ref_string(type_ref.inner_type)

    return type_instantiation(type_ref.graphql_typename)


def print_create_pent_field(
    writer: CodeWriter, document_ast: GrappleDocument, field: GrappleField
) -> None:
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


def print_read_pent_field(writer: CodeWriter, field: GrappleField) -> None:
    writer.line('async def %s(self, obj_id):' % field.python_name)
    writer.increase_indent()  # begin implemenation
    writer.line(
        "return await gen_pent_dynamic(self.context, '%s', obj_id)" % field.type_ref.python_typename
    )
    writer.decrease_indent()  # end implemenation
    writer.blank_line()


def print_vanilla_field(writer: CodeWriter, field: GrappleField) -> None:
    writer.line('@property')
    writer.line('def %s(self):' % field.python_name)
    writer.increase_indent()  # begin property implemenation
    if not field.type_ref.varietal == TypeRefVarietal.NONNULL:
        writer.line("return self._data.get('%s')" % field.python_name)
    else:
        writer.line("return self._data['%s']" % field.python_name)
    writer.decrease_indent()  # end property definition
    writer.blank_line()


def get_data_arg_in_pent(field: GrappleField) -> str:
    data_arg = get_required_arg(field.args, 'data')
    check.invariant(
        data_arg.type_ref.varietal == TypeRefVarietal.NONNULL, 'data argument must be non null'
    )

    return data_arg.type_ref.inner_type.python_typename
