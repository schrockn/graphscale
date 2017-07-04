from datetime import datetime
from enum import Enum, auto
from typing import NamedTuple, List, Any, Union
from uuid import UUID

from graphql.language.ast import (
    EnumTypeDefinition, InputObjectTypeDefinition, ListType, NamedType, NonNullType,
    ObjectTypeDefinition, IntValue, StringValue, BooleanValue, Node, TypeDefinition, Value,
    InputValueDefinition, Directive, FieldDefinition, Type
)
from graphql.language.parser import parse
from graphql.language.source import Source

from graphscale import check

from graphscale.utils import is_camel_case, to_snake_case


class TypeVarietal(Enum):
    OBJECT = auto()
    INPUT = auto()
    ENUM = auto()


class TypeRefVarietal(Enum):
    NAMED = auto()
    LIST = auto()
    NONNULL = auto()


# for some reason named tuple causes a ton of errors the class doesn't recognize the self
# reference for some reason. Therefore the actual instance of GrappleTypeRef is a hand
# coded class.
# class GrappleTypeRef(NamedTuple):
#     varietal: TypeRefVarietal
#     graphql_typename: str = None
#     python_typename: str = None
#     inner_type: 'GrappleTypeRef' = None  # self reference not working in this context
class GrappleTypeRef:
    def __init__(
        self,
        varietal: TypeRefVarietal,
        graphql_typename: str=None,
        python_typename: str=None,
        inner_type: 'GrappleTypeRef'=None
    ) -> None:
        self.__varietal = varietal
        self.__graphql_typename = graphql_typename
        self.__python_typename = python_typename
        self.__inner_type = inner_type

    @property
    def varietal(self) -> TypeRefVarietal:
        return self.__varietal

    @property
    def graphql_typename(self) -> str:
        return self.__graphql_typename

    @property
    def python_typename(self) -> str:
        return self.__python_typename

    @property
    def inner_type(self) -> 'GrappleTypeRef':
        return self.__inner_type


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
    def is_gen_varietal(self) -> bool:
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
    def is_mutation(self) -> bool:
        return self in [
            FieldVarietal.CREATE_PENT, FieldVarietal.CUSTOM_MUTATION, FieldVarietal.UPDATE_PENT
        ]

    @property
    def is_custom_impl(self) -> bool:
        return self in [
            FieldVarietal.CUSTOM, FieldVarietal.CUSTOM_MUTATION, FieldVarietal.CUSTOM_GEN
        ]


class EdgeToStoredIdData(NamedTuple):
    edge_name: str
    edge_id: int
    field: str


class DeletePentData(NamedTuple):
    type: str


FieldVarietalsUnion = Union[EdgeToStoredIdData, DeletePentData]


class GrappleFieldData(NamedTuple):
    name: str
    type_ref: GrappleTypeRef
    args: Any
    field_varietal: FieldVarietal
    field_varietal_data: FieldVarietalsUnion


class GrappleField(GrappleFieldData):
    @property
    def is_custom_field(self) -> bool:
        return self.field_varietal == FieldVarietal.CUSTOM

    @property
    def python_name(self) -> str:
        if self.name == 'id':
            return 'obj_id'
        name = self.name
        if is_camel_case(name):
            name = to_snake_case(name)
        if self.field_varietal.is_gen_varietal:
            name = 'gen_' + name
        return name


class GrappleTypeDef(NamedTuple):
    name: str
    fields: List[GrappleField]
    values: List[Any]
    type_id: int
    is_pent: bool
    is_pent_mutation_data: bool
    is_pent_payload: bool
    type_varietal: TypeVarietal


def create_object_type_def(
    *, name: str, fields: List[GrappleField], is_pent: bool, type_id: int, is_pent_payload: bool
) -> GrappleTypeDef:
    return GrappleTypeDef(
        name=name,
        fields=fields,
        type_varietal=TypeVarietal.OBJECT,
        values=None,
        type_id=type_id,
        is_pent=is_pent,
        is_pent_mutation_data=False,
        is_pent_payload=is_pent_payload,
    )


def create_input_type_def(*, name: str, fields: List[GrappleField],
                          is_pent_mutation_data: bool) -> GrappleTypeDef:
    return GrappleTypeDef(
        name=name,
        fields=fields,
        type_varietal=TypeVarietal.INPUT,
        values=None,
        type_id=None,
        is_pent=False,
        is_pent_mutation_data=is_pent_mutation_data,
        is_pent_payload=False,
    )


def create_enum_type_def(*, name: str, values: List[Any]) -> GrappleTypeDef:
    return GrappleTypeDef(
        name=name,
        fields=[],
        values=values,
        type_varietal=TypeVarietal.ENUM,
        type_id=None,
        is_pent=False,
        is_pent_mutation_data=False,
        is_pent_payload=False,
    )


class GrappleDocument:
    def __init__(self, *, types: List[GrappleTypeDef]) -> None:
        self._types = types

    def pents(self) -> List[GrappleTypeDef]:
        return [obj_type for obj_type in self.object_types() if obj_type.is_pent]

    def pent_mutation_datas(self) -> List[GrappleTypeDef]:
        return [in_type for in_type in self.input_types() if in_type.is_pent_mutation_data]

    def pent_payloads(self) -> List[GrappleTypeDef]:
        return [obj_type for obj_type in self.object_types() if obj_type.is_pent_payload]

    def mutation_type(self) -> GrappleTypeDef:
        for obj_type in self.object_types():
            if obj_type.name == 'Mutation':
                return obj_type
        return None

    def query_type(self) -> GrappleTypeDef:
        for obj_type in self.object_types():
            if obj_type.name == 'Query':
                return obj_type
        return None

    def object_types(self) -> List[GrappleTypeDef]:
        return [t for t in self._types if t.type_varietal == TypeVarietal.OBJECT]

    def input_types(self) -> List[GrappleTypeDef]:
        return [t for t in self._types if t.type_varietal == TypeVarietal.INPUT]

    def enum_types(self) -> List[GrappleTypeDef]:
        return [t for t in self._types if t.type_varietal == TypeVarietal.ENUM]

    def is_enum(self, name: str) -> bool:
        ttype = self.type_named(name)
        return ttype and ttype.type_varietal == TypeVarietal.ENUM

    def type_named(self, name: str) -> GrappleTypeDef:
        for ttype in self._types:
            if ttype.name == name:
                return ttype
        return None


def parse_grapple(grapple_string: str) -> GrappleDocument:
    ast = parse(Source(grapple_string))
    grapple_types = []
    for type_node in ast.definitions:
        grapple_types.append(create_grapple_type_definition(type_node))
    return GrappleDocument(types=grapple_types)


def has_directive(ast: Node, name: str) -> bool:
    return name in [dir_node.name.value for dir_node in ast.directives]


def get_directive(ast: Node, name: str) -> Directive:
    for dir_node in ast.directives:
        if dir_node.name.value == name:
            check.isinst(dir_node, Directive)
            return dir_node
    return None


def to_python_typename(graphql_type: str) -> str:
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


def create_grapple_type_definition(type_ast: TypeDefinition) -> GrappleTypeDef:
    check.isinst(type_ast, TypeDefinition)
    if isinstance(type_ast, ObjectTypeDefinition):
        return create_grapple_object_type(type_ast)
    elif isinstance(type_ast, InputObjectTypeDefinition):
        return create_grapple_input_type(type_ast)
    elif isinstance(type_ast, EnumTypeDefinition):
        return create_grapple_enum_type(type_ast)
    check.invariant(False, 'node not supported: ' + str(type_ast))
    return None


def create_grapple_enum_type(enum_type_ast: EnumTypeDefinition) -> GrappleTypeDef:
    check.isinst(enum_type_ast, EnumTypeDefinition)
    grapple_type_name = enum_type_ast.name.value

    values = [value_ast.name.value for value_ast in enum_type_ast.values]
    return create_enum_type_def(
        name=grapple_type_name,
        values=values,
    )


def create_grapple_input_type(input_type_ast: InputObjectTypeDefinition) -> GrappleTypeDef:
    check.isinst(input_type_ast, InputObjectTypeDefinition)
    grapple_type_name = input_type_ast.name.value
    grapple_fields = [create_grapple_input_field(field) for field in input_type_ast.fields]
    input_directive = get_directive(input_type_ast, 'pentMutationData')
    return create_input_type_def(
        name=grapple_type_name,
        fields=grapple_fields,
        is_pent_mutation_data=input_directive is not None
    )


def req_int_argument(directive_ast: Directive, name: str) -> int:
    check.isinst(directive_ast, Directive)
    for argument in directive_ast.arguments:
        if argument.name.value == name:
            check.isinst(argument.value, IntValue)
            return int(argument.value.value)

    raise Exception('argument required')


def req_string_argument(directive_ast: Directive, name: str) -> str:
    check.isinst(directive_ast, Directive)
    for argument in directive_ast.arguments:
        if argument.name.value == name:
            if not isinstance(argument.value, StringValue):
                raise Exception('must be str')
            return str(argument.value.value)

    raise Exception('argument required')


def create_grapple_object_type(object_type_ast: ObjectTypeDefinition) -> GrappleTypeDef:
    check.isinst(object_type_ast, ObjectTypeDefinition)
    grapple_type_name = object_type_ast.name.value
    grapple_fields = [create_grapple_field(field) for field in object_type_ast.fields]
    pent_directive = get_directive(object_type_ast, 'pent')
    type_id = req_int_argument(pent_directive, 'type_id') if pent_directive else None
    pent_payload_directive = get_directive(object_type_ast, 'pentMutationPayload')

    return create_object_type_def(
        name=grapple_type_name,
        fields=grapple_fields,
        is_pent=pent_directive is not None,
        type_id=type_id,
        is_pent_payload=pent_payload_directive is not None
    )


class GrappleFieldArgument(NamedTuple):
    name: str
    type_ref: GrappleTypeRef
    default_value: Any


def value_from_ast(ast: Value) -> Any:
    if not ast:
        return None

    check.isinst(ast, Value)
    if isinstance(ast, IntValue):
        return ast.value
    if isinstance(ast, StringValue):
        return '"' + ast.value + '"'
    if isinstance(ast, BooleanValue):
        return "True" if ast.value else "False"

    check.failed('Unsupported ast value: ' + repr(ast))


def create_grapple_field_arg(graphql_arg: InputValueDefinition) -> GrappleFieldArgument:
    check.isinst(graphql_arg, InputValueDefinition)
    return GrappleFieldArgument(
        name=graphql_arg.name.value,
        type_ref=create_type_ref(graphql_arg.type),
        default_value=value_from_ast(graphql_arg.default_value),
    )


def create_grapple_input_field(graphql_field: Any) -> GrappleField:
    check.isinst(graphql_field, InputValueDefinition)
    return construct_field(
        name=graphql_field.name.value,
        type_ref=create_type_ref(graphql_field.type),
        args=[],
    )


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


def get_field_varietal(graphql_field: FieldDefinition) -> FieldVarietal:
    check.isinst(graphql_field, FieldDefinition)
    for directive_name, varietal_enum in FIELD_VARIETAL_MAPPING.items():
        if has_directive(graphql_field, directive_name):
            return varietal_enum

    return FieldVarietal.VANILLA


def get_field_varietal_data(
    graphql_field: FieldDefinition, field_varietal: FieldVarietal
) -> FieldVarietalsUnion:
    check.isinst(graphql_field, FieldDefinition)
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

    return None


def create_grapple_field(graphql_field: FieldDefinition) -> GrappleField:
    check.isinst(graphql_field, FieldDefinition)
    field_varietal = get_field_varietal(graphql_field)
    return construct_field(
        name=graphql_field.name.value,
        type_ref=create_type_ref(graphql_field.type),
        args=[create_grapple_field_arg(graphql_arg) for graphql_arg in graphql_field.arguments],
        field_varietal=field_varietal,
        field_varietal_data=get_field_varietal_data(graphql_field, field_varietal),
    )


def create_type_ref(graphql_type_ast: Type) -> GrappleTypeRef:
    if isinstance(graphql_type_ast, NamedType):
        graphql_typename = graphql_type_ast.name.value
        return GrappleTypeRef(
            varietal=TypeRefVarietal.NAMED,
            graphql_typename=graphql_typename,
            python_typename=to_python_typename(graphql_typename),
        )
    elif isinstance(graphql_type_ast, NonNullType):
        return GrappleTypeRef(
            varietal=TypeRefVarietal.NONNULL,
            inner_type=create_type_ref(graphql_type_ast.type),
        )
    elif isinstance(graphql_type_ast, ListType):
        return GrappleTypeRef(
            varietal=TypeRefVarietal.LIST,
            inner_type=create_type_ref(graphql_type_ast.type),
        )

    check.failed('unsupported ast: ' + repr(graphql_type_ast))


def construct_field(
    *,
    name: str,
    type_ref: GrappleTypeRef,
    args: List[GrappleFieldArgument],
    field_varietal: FieldVarietal=FieldVarietal.VANILLA,
    field_varietal_data: FieldVarietalsUnion=None
) -> GrappleField:
    return GrappleField(name, type_ref, args, field_varietal, field_varietal_data)
