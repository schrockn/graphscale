from typing import List, Tuple

from graphscale import check
from graphscale.utils import to_snake_case

from .code_writer import CodeWriter
from .parser import (
    DeletePentData, EdgeToStoredIdData, FieldVarietal, GrappleDocument, GrappleField,
    GrappleFieldArgument, GrappleTypeDef, TypeRefVarietal, GrappleTypeRef, TypeVarietal
)

GENERATED_PENT_HEADER = """#W0611: unused imports lint
#C0301: line too long
#W0613: unused args because of locals hack
#pylint: disable=W0611, C0301, W0613

from collections import namedtuple
from enum import Enum, auto
from typing import List, Any
from uuid import UUID

from graphscale import check
from graphscale.grapple.graphql_impl import (
    gen_create_pent_dynamic,
    gen_delete_pent_dynamic,
    gen_update_pent_dynamic,
    gen_browse_pents_dynamic,
    gen_pent_dynamic,
    typed_or_none,
)
from graphscale.pent import (
    Pent,
    PentMutationData,
    PentMutationPayload,
    create_pent,
    delete_pent,
    update_pent,
    PentContextfulObject,
)

"""


def print_autopents_file_body(document_ast: GrappleDocument) -> str:
    writer = CodeWriter()

    for enum_type in document_ast.enum_types():
        print_generated_enum(writer, enum_type)

    for pent_mutation_data in document_ast.pent_mutation_datas():
        print_generated_pent_mutation_data(writer, document_ast, pent_mutation_data)

    for payload_type in document_ast.pent_payloads():
        print_generated_pent_payload(writer, payload_type)

    return writer.result()


def print_generated_pents_file_body(document_ast: GrappleDocument) -> str:
    writer = CodeWriter()

    print_generated_root_class(writer, document_ast)

    for pent_type in document_ast.pents():
        print_generated_pent(writer, document_ast, pent_type)

    return writer.result()


def print_generated_enum(writer: CodeWriter, enum_type: GrappleTypeDef) -> None:
    check.invariant(enum_type.type_varietal == TypeVarietal.ENUM, 'must be enum')

    writer.line('class {name}(Enum):'.format(name=enum_type.name))
    writer.increase_indent()
    for value in enum_type.values:
        writer.line("{value} = '{value}'".format(value=value))
    writer.decrease_indent()
    writer.blank_line()


PENT_PAYLOAD_DATA_TEMPLATE = """
__{name}DataMixin = namedtuple('__{name}DataMixin', '{field_name}')


class {name}(PentMutationPayload, __{name}DataMixin):
    pass
"""


def print_generated_pent_payload(writer: CodeWriter, payload_type: GrappleTypeDef) -> None:
    check.invariant(payload_type.type_varietal == TypeVarietal.OBJECT, 'must be object')
    check.invariant(len(payload_type.fields) == 1, 'Payload type should only have one field')
    out_field = payload_type.fields[0]
    payload_class_text = PENT_PAYLOAD_DATA_TEMPLATE.format(
        name=payload_type.name, field_name=out_field.python_name
    )
    writer.line(payload_class_text)


def print_autopent_all_export(document_ast: GrappleDocument) -> str:
    writer = CodeWriter()
    exports = []  # type: List[str]

    pentish = (
        document_ast.pent_mutation_datas() + document_ast.pent_payloads() +
        document_ast.enum_types()
    )

    for tpent in pentish:
        exports.append(tpent.name)

    writer.line('__all__ = [')
    writer.increase_indent()
    for export in exports:
        writer.line("'{export}',".format(export=export))
    writer.decrease_indent()
    writer.line(']')
    return writer.result()


def print_generated_pents_file(document_ast: GrappleDocument) -> str:
    return GENERATED_PENT_HEADER + '\n' + print_generated_pents_file_body(document_ast) + '\n'


def print_autopents_file(document_ast: GrappleDocument) -> str:
    return (
        GENERATED_PENT_HEADER + '\n' + print_autopents_file_body(document_ast) + '\n' +
        print_autopent_all_export(document_ast) + '\n'
    )


def print_generated_pent_mutation_data(
    writer: CodeWriter, document_ast: GrappleDocument, grapple_type: GrappleTypeDef
) -> None:
    writer.line('class %s(PentMutationData):' % grapple_type.name)
    writer.increase_indent()  # begin class implementation

    writer.line('def __init__(self, *,')
    writer.increase_indent()  # begin arg list
    for field in grapple_type.fields:
        typing = python_typing_string(field.type_ref)
        if field.type_ref.varietal == TypeRefVarietal.NONNULL:
            writer.line('{name}: {typing},'.format(name=field.python_name, typing=typing))
        else:
            writer.line('{name}: {typing}=None,'.format(name=field.python_name, typing=typing))
    writer.decrease_indent()  # end arg list
    writer.line(') -> None:')
    writer.increase_indent()  # begin __init__ impl

    writer.line('data = locals()')
    writer.line("del data['self']")
    writer.line("super().__init__(data)")

    writer.decrease_indent()  # end __init__ impl
    writer.blank_line()
    print_generated_fields(writer, document_ast, grapple_type.fields)
    writer.decrease_indent()  # end class definition


def print_generated_root_class(writer: CodeWriter, document_ast: GrappleDocument) -> None:
    writer.line('class RootGenerated(PentContextfulObject):')
    writer.increase_indent()  # begin class implementation
    if not document_ast.query_type() and not document_ast.mutation_type():
        writer.line('pass')
    else:
        if document_ast.query_type():
            print_generated_fields(writer, document_ast, document_ast.query_type().fields)
        if document_ast.mutation_type():
            print_generated_fields(writer, document_ast, document_ast.mutation_type().fields)
    writer.blank_line()
    writer.decrease_indent()  # end class definition


def print_generated_pent(
    writer: CodeWriter, document_ast: GrappleDocument, grapple_type: GrappleTypeDef
) -> None:
    writer.line('class {name}Generated(Pent):'.format(name=grapple_type.name))
    writer.increase_indent()  # begin class implementation
    print_generated_fields(writer, document_ast, grapple_type.fields)
    writer.decrease_indent()  # end class definition


def print_generated_fields(
    writer: CodeWriter, document_ast: GrappleDocument, fields: List[GrappleField]
) -> None:
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


def get_first_after_args(field: GrappleField
                         ) -> Tuple[GrappleFieldArgument, GrappleFieldArgument, str]:
    check.invariant(len(field.args) == 2, 'browse/conn should have 2 args')
    first_arg = get_required_arg(field.args, 'first')
    check.invariant(first_arg.default_value, 'must have default value')

    after_arg = get_required_arg(field.args, 'after')
    check.invariant(after_arg.type_ref.graphql_typename == 'UUID', 'arg must be UUID')

    check.invariant(field.type_ref.varietal == TypeRefVarietal.NONNULL, 'outer non null')
    check.invariant(field.type_ref.inner_type.varietal == TypeRefVarietal.LIST, 'then list')
    check.invariant(
        field.type_ref.inner_type.inner_type.varietal == TypeRefVarietal.NONNULL, 'then nonnull'
    )
    check.invariant(
        field.type_ref.inner_type.inner_type.inner_type.varietal == TypeRefVarietal.NAMED,
        'then named'
    )
    target_type = field.type_ref.inner_type.inner_type.inner_type.python_typename
    return (first_arg, after_arg, target_type)


def print_browse_pents_field(writer: CodeWriter, field: GrappleField) -> None:
    _first_arg, _after_arg, browse_type = get_first_after_args(field)

    writer.line(
        "async def %s(self, first: int=100, after: UUID=None) -> List[Pent]: # mypy circ %s" %
        (field.python_name, python_typing_string(field.type_ref))
    )
    writer.increase_indent()  # begin implemenation
    writer.line(
        "return await gen_browse_pents_dynamic(self.context, after, first, '%s') # type: ignore" %
        browse_type
    )
    writer.decrease_indent()  # end implementation
    writer.blank_line()


def print_update_pent_field(
    writer: CodeWriter, document_ast: GrappleDocument, field: GrappleField
) -> None:
    check.invariant(len(field.args) == 2, 'updatePent should have 2 args')
    check_required_id_arg(field)
    pent_cls, data_cls, payload_cls = get_mutation_classes(document_ast, field)

    writer.line(
        (
            "async def {name}(self, obj_id: UUID, data: '{data_cls}')"
            " -> PentMutationPayload: # mypy circ {typing}"
        ).format(
            name=field.python_name, data_cls=data_cls, typing=python_typing_string(field.type_ref)
        )
    )
    writer.increase_indent()  # begin implemenation
    writer.line(
        "return await gen_update_pent_dynamic"
        "(self.context, obj_id, '{pent_cls}', '{data_cls}', '{payload_cls}', data) # type: ignore".
        format(pent_cls=pent_cls, data_cls=data_cls, payload_cls=payload_cls)
    )
    writer.decrease_indent()  # end implementation
    writer.blank_line()


def print_delete_pent_field(writer: CodeWriter, field: GrappleField) -> None:
    check.invariant(len(field.args) == 1, 'deletePent should only have 1 arg')
    check_required_id_arg(field)

    if not isinstance(field.field_varietal_data, DeletePentData):
        check.failed('must be DeletePentData')

    payload_cls = field.type_ref.python_typename
    pent_cls = field.field_varietal_data.type

    writer.line(
        "async def %s(self, obj_id: UUID) -> PentMutationPayload: # mypy circ %s" %
        (field.python_name, python_typing_string(field.type_ref))
    )
    writer.increase_indent()  # begin implemenation
    writer.line(
        (
            "return await gen_delete_pent_dynamic(self.context"
            ", '{pent_cls}', '{payload_cls}', obj_id) # type: ignore"
        ).format(pent_cls=pent_cls, payload_cls=payload_cls)
    )
    writer.decrease_indent()  # end implementation
    writer.blank_line()


def get_mutation_classes(document_ast: GrappleDocument,
                         field: GrappleField) -> Tuple[str, str, str]:
    data_cls = get_data_arg_in_pent(field)
    payload_cls = field.type_ref.python_typename

    payload_type = document_ast.type_named(payload_cls)
    check.invariant(
        len(payload_type.fields) == 1, 'payload class for vanilla crud should only have one field'
    )
    data_field = payload_type.fields[0]
    pent_cls = data_field.type_ref.python_typename
    return (pent_cls, data_cls, payload_cls)


def print_create_pent_field(
    writer: CodeWriter, document_ast: GrappleDocument, field: GrappleField
) -> None:
    check.invariant(len(field.args) == 1, 'createPent should only have 1 arg')

    pent_cls, data_cls, payload_cls = get_mutation_classes(document_ast, field)

    writer.line(
        "async def {name}(self, data: '{data_cls}') -> Pent: # mypy circ {typing}".format(
            name=field.python_name, data_cls=data_cls, typing=python_typing_string(field.type_ref)
        )
    )
    writer.increase_indent()  # begin implemenation
    writer.line(
        "return await gen_create_pent_dynamic"
        "(self.context, '{pent_cls}', '{data_cls}', '{payload_cls}', data) # type: ignore".format(
            pent_cls=pent_cls, data_cls=data_cls, payload_cls=payload_cls
        )
    )
    writer.decrease_indent()  # end implemenation
    writer.blank_line()


def print_read_pent_field(writer: CodeWriter, field: GrappleField) -> None:
    writer.line(
        "async def %s(self, obj_id: UUID) -> Pent: # mypy circ %s" %
        (field.python_name, python_typing_string(field.type_ref))
    )
    writer.increase_indent()  # begin implemenation
    writer.line(
        "return await gen_pent_dynamic(self.context, '%s', obj_id) # type: ignore" %
        field.type_ref.python_typename
    )
    writer.decrease_indent()  # end implemenation
    writer.blank_line()


def python_typing_string(type_ref: GrappleTypeRef) -> str:
    if type_ref.varietal == TypeRefVarietal.NONNULL:
        return python_typing_string(type_ref.inner_type)
    elif type_ref.varietal == TypeRefVarietal.LIST:
        return 'List[' + python_typing_string(type_ref.inner_type) + ']'
    return type_ref.python_typename


def print_vanilla_field(writer: CodeWriter, field: GrappleField) -> None:
    writer.line('@property')
    mypy_type = python_typing_string(field.type_ref)
    primitives = set(['UUID', 'str', 'bool', 'int', 'datetime', 'float'])
    if mypy_type in primitives:
        writer.line(
            'def {name}(self) -> {mypy_type}:'.format(name=field.python_name, mypy_type=mypy_type)
        )
    else:
        writer.line(
            'def {name}(self) -> Any: # mypy circ: {mypy_type}'.
            format(name=field.python_name, mypy_type=mypy_type)
        )
    writer.increase_indent()  # begin property implemenation
    if not field.type_ref.varietal == TypeRefVarietal.NONNULL:
        access = "self._data.get('{name}')".format(name=field.python_name)
    else:
        access = "self._data['{name}']".format(name=field.python_name)

    if mypy_type in primitives:
        writer.line(
            # mypy not typing typed_or_none across module boundaries for some reason
            "return typed_or_none({access}, {mypy_type}) # type: ignore"
            .format(access=access, mypy_type=mypy_type)
        )
    else:
        writer.line("return {access} # type: ignore".format(access=access))
    writer.decrease_indent()  # end property definition
    writer.blank_line()


def get_required_arg(args: List[GrappleFieldArgument], name: str) -> GrappleFieldArgument:
    for arg in args:
        if arg.name == name:
            return arg

    check.failed('arg with name %s could not be found' % name)


def get_data_arg_in_pent(field: GrappleField) -> str:
    data_arg = get_required_arg(field.args, 'data')
    check.invariant(
        data_arg.type_ref.varietal == TypeRefVarietal.NONNULL, 'input argument must be non null'
    )

    return data_arg.type_ref.inner_type.python_typename


def check_required_id_arg(field: GrappleField) -> None:
    id_arg = get_required_arg(field.args, 'id')
    check.invariant(id_arg.type_ref.varietal == TypeRefVarietal.NONNULL, 'arg must be non null')
    check.invariant(id_arg.type_ref.inner_type.graphql_typename == 'UUID', 'arg must be UUID')


def print_edge_to_stored_id_field(writer: CodeWriter, field: GrappleField) -> None:
    if not isinstance(field.field_varietal_data, EdgeToStoredIdData):
        check.failed('not an EdgeToStoredIdData')

    _first_arg, _after_arg, target_type = get_first_after_args(field)
    writer.line(
        "async def %s(self, first: int=100, after: UUID=None) -> List[Pent]: # mypy circ '%s'" %
        (field.python_name, python_typing_string(field.type_ref))
    )
    writer.increase_indent()  # begin implemenation
    writer.line(
        "return await self.gen_associated_pents_dynamic"
        "('{target_type}', '{edge_name}', after, first) # type: ignore".format(
            target_type=target_type, edge_name=field.field_varietal_data.edge_name
        )
    )
    writer.decrease_indent()  # end implementation
    writer.blank_line()


def print_gen_from_stored_id_field(writer: CodeWriter, field: GrappleField) -> None:
    check.invariant(len(field.args) == 0, 'genFromStoredId should have no args')
    check.invariant(
        field.type_ref.varietal == TypeRefVarietal.NAMED, 'only supports bare types for now'
    )

    cls_name = field.type_ref.python_typename
    # very hard coded for now. should be configurable via argument to directive optionally
    prop = to_snake_case(field.name) + '_id'

    writer.line(
        "async def %s(self) -> Pent: # mypy circ %s" %
        (field.python_name, python_typing_string(field.type_ref))
    )
    writer.increase_indent()  # begin implemenation
    writer.line(
        "return await self.gen_from_stored_id_dynamic"
        "('{cls_name}', '{prop}') # type: ignore".format(cls_name=cls_name, prop=prop)
    )
    writer.decrease_indent()  # end implementation
    writer.blank_line()
