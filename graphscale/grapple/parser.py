from collections import namedtuple
from datetime import datetime
from enum import Enum, auto
from uuid import UUID

from graphql.language.ast import (
    EnumTypeDefinition, InputObjectTypeDefinition, ListType, NamedType, NonNullType,
    ObjectTypeDefinition, IntValue, StringValue, EnumValue, FloatValue, BooleanValue
)
from graphql.language.parser import parse
from graphql.language.source import Source

import graphscale.check as check
from graphscale.utils import is_camel_case, to_snake_case


def parse_grapple(grapple_string):
    ast = parse(Source(grapple_string))
    grapple_types = []
    for type_node in ast.definitions:
        grapple_types.append(create_grapple_type_definition(type_node))
    return GrappleDocument(types=grapple_types)


def has_directive(type_ast, name):
    return name in [dir_node.name.value for dir_node in type_ast.directives]


def get_directive(type_ast, name):
    for dir_node in type_ast.directives:
        if dir_node.name.value == name:
            return dir_node
    return None


def to_python_typename(graphql_type):
    check.str_param(graphql_type, 'graphql_type')
    scalars = {
        'ID': UUID,
        'Int': int,
        'Float': float,
        'String': str,
        'Boolean': bool,
        'DateTime': datetime,
    }
    if graphql_type in scalars:
        return scalars[graphql_type].__name__
    return graphql_type


class TypeVarietal(Enum):
    OBJECT = auto()
    INPUT = auto()
    ENUM = auto()


class GrappleDocument:
    def __init__(self, *, types):
        self._types = types

    def pents(self):
        return [obj_type for obj_type in self.object_types() if obj_type.is_pent]

    def pent_mutation_datas(self):
        return [in_type for in_type in self.input_types() if in_type.is_pent_mutation_data]

    def pent_payloads(self):
        return [obj_type for obj_type in self.object_types() if obj_type.is_pent_payload]

    def mutation_type(self):
        for obj_type in self.object_types():
            if obj_type.name == 'Mutation':
                return obj_type

    def query_type(self):
        for obj_type in self.object_types():
            if obj_type.name == 'Query':
                return obj_type

    def object_types(self):
        return [t for t in self._types if t.type_varietal == TypeVarietal.OBJECT]

    def input_types(self):
        return [t for t in self._types if t.type_varietal == TypeVarietal.INPUT]

    def enum_types(self):
        return [t for t in self._types if t.type_varietal == TypeVarietal.ENUM]

    def is_enum(self, name):
        ttype = self.type_named(name)
        return ttype and ttype.type_varietal == TypeVarietal.ENUM

    def type_named(self, name):
        for ttype in self._types:
            if ttype.name == name:
                return ttype


def create_grapple_type_definition(type_ast):
    if isinstance(type_ast, ObjectTypeDefinition):
        return create_grapple_object_type(type_ast)
    elif isinstance(type_ast, InputObjectTypeDefinition):
        return create_grapple_input_type(type_ast)
    elif isinstance(type_ast, EnumTypeDefinition):
        return create_grapple_enum_type(type_ast)
    else:
        check.violation('node not supported: ' + str(type_ast))


def create_grapple_enum_type(enum_type_ast):
    grapple_type_name = enum_type_ast.name.value

    values = [value_ast.name.value for value_ast in enum_type_ast.values]
    return GrappleTypeDefinition.enum_type(
        name=grapple_type_name,
        values=values,
    )


def create_grapple_input_type(input_type_ast):
    grapple_type_name = input_type_ast.name.value
    grapple_fields = [create_grapple_input_field(field) for field in input_type_ast.fields]
    input_directive = get_directive(input_type_ast, 'pentMutationData')
    return GrappleTypeDefinition.input_type(
        name=grapple_type_name,
        fields=grapple_fields,
        is_pent_mutation_data=input_directive is not None
    )


def req_int_argument(directive_ast, name):
    for argument in directive_ast.arguments:
        if argument.name.value == name:
            if not isinstance(argument.value, IntValue):
                raise Exception('must be int')
            return int(argument.value.value)

    raise Exception('argument required')


def req_string_argument(directive_ast, name):
    for argument in directive_ast.arguments:
        if argument.name.value == name:
            if not isinstance(argument.value, StringValue):
                raise Exception('must be str')
            return str(argument.value.value)

    raise Exception('argument required')


def create_grapple_object_type(object_type_ast):
    grapple_type_name = object_type_ast.name.value
    grapple_fields = [create_grapple_field(field) for field in object_type_ast.fields]
    pent_directive = get_directive(object_type_ast, 'pent')
    type_id = req_int_argument(pent_directive, 'type_id') if pent_directive else None
    pent_payload_directive = get_directive(object_type_ast, 'pentMutationPayload')

    return GrappleTypeDefinition.object_type(
        name=grapple_type_name,
        fields=grapple_fields,
        is_pent=pent_directive is not None,
        type_id=type_id,
        is_pent_payload=pent_payload_directive is not None
    )


GrappleTypeDefData = namedtuple(
    'GrappleTypeDefData',
    'name fields type_varietal values type_id is_pent is_pent_mutation_data, is_pent_payload'
)


class GrappleTypeDefinition(GrappleTypeDefData):
    @staticmethod
    def object_type(*, name, fields, is_pent, type_id, is_pent_payload):
        check.str_param(name, 'name')
        check.list_param(fields, 'fields')
        check.bool_param(is_pent, 'is_pent')
        check.opt_int_param(type_id, 'type_id')
        check.bool_param(is_pent_payload, 'is_pent_payload')

        return GrappleTypeDefinition(
            name=name,
            fields=fields,
            type_varietal=TypeVarietal.OBJECT,
            values=None,
            type_id=type_id,
            is_pent=is_pent,
            is_pent_mutation_data=False,
            is_pent_payload=is_pent_payload,
        )

    @staticmethod
    def input_type(*, name, fields, is_pent_mutation_data):
        check.str_param(name, 'name')
        check.list_param(fields, 'fields')
        check.bool_param(is_pent_mutation_data, 'is_pent_mutation_data')

        return GrappleTypeDefinition(
            name=name,
            fields=fields,
            type_varietal=TypeVarietal.INPUT,
            values=None,
            type_id=None,
            is_pent=False,
            is_pent_mutation_data=is_pent_mutation_data,
            is_pent_payload=False,
        )

    @staticmethod
    def enum_type(*, name, values):
        check.str_param(name, 'name')
        check.list_param(values, 'values')

        return GrappleTypeDefinition(
            name=name,
            fields=[],
            values=values,
            type_varietal=TypeVarietal.ENUM,
            type_id=None,
            is_pent=False,
            is_pent_mutation_data=False,
            is_pent_payload=False,
        )

    def has_field(self, name):
        return name in [field.name for field in self.fields]


GrappleFieldArgument = namedtuple('GrappleFieldArgument', 'name type_ref, default_value')


def value_from_ast(ast):
    if not ast:
        return None
    if isinstance(ast, IntValue):
        return ast.value
    if isinstance(ast, StringValue):
        return '"' + ast.value + '"'
    if isinstance(ast, BooleanValue):
        return "True" if ast.value else "False"

    check.violation('Unsupported ast value: ' + repr(ast))


def create_grapple_field_arg(graphql_arg):
    return GrappleFieldArgument(
        name=graphql_arg.name.value,
        type_ref=create_type_ref(graphql_arg.type),
        default_value=value_from_ast(graphql_arg.default_value),
    )


def create_grapple_input_field(graphql_field):
    return construct_field(
        name=graphql_field.name.value,
        type_ref=create_type_ref(graphql_field.type),
        args=[],
    )


class FieldVarietal(Enum):
    VANILLA = auto()
    CUSTOM = auto()
    CUSTOM_GEN = auto()
    READ_PENT = auto()
    CREATE_PENT = auto()
    DELETE_PENT = auto()
    CUSTOM_MUTATION = auto()
    UPDATE_PENT = auto()
    BROWSE_PENTS = auto()
    GEN_FROM_STORED_ID = auto()
    EDGE_TO_STORED_ID = auto()

    @property
    def is_gen_varietal(self):
        return self in [
            FieldVarietal.CUSTOM_GEN,
            FieldVarietal.READ_PENT,
            FieldVarietal.CREATE_PENT,
            FieldVarietal.DELETE_PENT,
            FieldVarietal.CUSTOM_MUTATION,
            FieldVarietal.UPDATE_PENT,
            FieldVarietal.BROWSE_PENTS,
            FieldVarietal.GEN_FROM_STORED_ID,
            FieldVarietal.EDGE_TO_STORED_ID,
        ]

    @property
    def is_mutation(self):
        return self in [
            FieldVarietal.CREATE_PENT, FieldVarietal.CUSTOM_MUTATION, FieldVarietal.UPDATE_PENT
        ]

    @property
    def is_custom_impl(self):
        return self in [
            FieldVarietal.CUSTOM, FieldVarietal.CUSTOM_MUTATION, FieldVarietal.CUSTOM_GEN
        ]


FIELD_VARIETAL_MAPPING = {
    'custom': FieldVarietal.CUSTOM,
    'customGen': FieldVarietal.CUSTOM_GEN,
    'customMutation': FieldVarietal.CUSTOM_MUTATION,
    'readPent': FieldVarietal.READ_PENT,
    'createPent': FieldVarietal.CREATE_PENT,
    'deletePent': FieldVarietal.DELETE_PENT,
    'updatePent': FieldVarietal.UPDATE_PENT,
    'browsePents': FieldVarietal.BROWSE_PENTS,
    'genFromStoredId': FieldVarietal.GEN_FROM_STORED_ID,
    'edgeToStoredId': FieldVarietal.EDGE_TO_STORED_ID,
}


def get_field_varietal(graphql_field):
    for directive_name, varietal_enum in FIELD_VARIETAL_MAPPING.items():
        if has_directive(graphql_field, directive_name):
            return varietal_enum

    return FieldVarietal.VANILLA


EdgeToStoredIdData = namedtuple('EdgeToStoredIdData', 'edge_name edge_id field')
DeletePentData = namedtuple('DeletePentData', 'type')


def get_field_varietal_data(graphql_field, field_varietal):
    if field_varietal == FieldVarietal.EDGE_TO_STORED_ID:
        dir_ast = get_directive(graphql_field, 'edgeToStoredId')
        return EdgeToStoredIdData(
            edge_name=req_string_argument(dir_ast, 'edgeName'),
            edge_id=req_int_argument(dir_ast, 'edgeId'),
            field=req_string_argument(dir_ast, 'field'),
        )
    elif field_varietal == FieldVarietal.DELETE_PENT:
        dir_ast = get_directive(graphql_field, 'deletePent')
        return DeletePentData(type=req_string_argument(dir_ast, 'type'))
    else:
        return None


def create_grapple_field(graphql_field):
    field_varietal = get_field_varietal(graphql_field)
    return construct_field(
        name=graphql_field.name.value,
        type_ref=create_type_ref(graphql_field.type),
        args=[create_grapple_field_arg(graphql_arg) for graphql_arg in graphql_field.arguments],
        field_varietal=field_varietal,
        field_varietal_data=get_field_varietal_data(graphql_field, field_varietal),
    )


TypeContainerData = namedtuple('TypeContainerData', 'inner_type')


class NonNullTypeRef(TypeContainerData):
    is_named = False
    is_list = False
    is_nonnull = True


class ListTypeRef(TypeContainerData):
    is_named = False
    is_list = True
    is_nonnull = False


CoreTypeData = namedtuple('CoreTypeData', 'graphql_typename python_typename')


class CoreTypeRef(CoreTypeData):
    is_named = True
    is_list = False
    is_nonnull = False


def create_type_ref(graphql_type_ast):
    if isinstance(graphql_type_ast, NamedType):
        graphql_typename = graphql_type_ast.name.value
        return CoreTypeRef(
            graphql_typename=graphql_typename, python_typename=to_python_typename(graphql_typename)
        )
    elif isinstance(graphql_type_ast, NonNullType):
        return NonNullTypeRef(inner_type=create_type_ref(graphql_type_ast.type))
    elif isinstance(graphql_type_ast, ListType):
        return ListTypeRef(inner_type=create_type_ref(graphql_type_ast.type))

    check.violation('unsupported ast: ' + repr(graphql_type_ast))


GrappleFieldData = namedtuple(
    'GrappleFieldData',
    'name type_ref args field_varietal, field_varietal_data',
)


class GrappleField(GrappleFieldData):
    @property
    def is_custom_field(self):
        return self.field_varietal == FieldVarietal.CUSTOM

    @property
    def python_name(self):
        if self.name == 'id':
            return 'obj_id'
        name = self.name
        if is_camel_case(name):
            name = to_snake_case(name)
        if self.field_varietal.is_gen_varietal:
            name = 'gen_' + name
        return name


def construct_field(
    *, name, type_ref, args, field_varietal=FieldVarietal.VANILLA, field_varietal_data=None
):
    return GrappleField(name, type_ref, args, field_varietal, field_varietal_data)
