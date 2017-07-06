from typing import Any

from graphscale.grapple.parser import parse_grapple, to_python_typename
from graphscale.grapple.pent_printer import print_generated_pents_file_body


def assert_generated_pent(snapshot: Any, graphql: str) -> None:
    grapple_document = parse_grapple(graphql)
    output = print_generated_pents_file_body(grapple_document)
    snapshot.assert_match(output)


def test_no_grapple_types(snapshot: Any) -> None:
    assert_generated_pent(snapshot, """type TestObjectField {bar: FooBar}""")


def test_ignore_type(snapshot: Any) -> None:
    assert_generated_pent(
        snapshot, """type TestObjectField @pent(type_id: 1000) {bar: FooBar} type Other { }"""
    )


def test_required_object_field(snapshot: Any) -> None:
    assert_generated_pent(snapshot, """type TestObjectField @pent(type_id: 1000) {bar: FooBar!}""")


def test_object_field(snapshot: Any) -> None:
    assert_generated_pent(snapshot, """type TestObjectField @pent(type_id: 1000) {bar: FooBar}""")


def test_required_field(snapshot: Any) -> None:
    assert_generated_pent(
        snapshot, """type TestRequired @pent(type_id: 1000) {id: ID!, name: String!}"""
    )


def test_single_nullable_field(snapshot: Any) -> None:
    grapple_string = """type Test @pent(type_id: 1) {name: String}"""
    grapple_document = parse_grapple(grapple_string)
    grapple_type = grapple_document.object_types()[0]
    assert grapple_type.name == 'Test'
    fields = grapple_type.fields
    assert len(fields) == 1
    name_field = fields[0]
    assert name_field.name == 'name'
    assert name_field.type_ref.graphql_typename == 'String'
    assert name_field.type_ref.python_typename == 'str'
    assert_generated_pent(snapshot, grapple_string)


def test_graphql_type_conversion() -> None:
    assert to_python_typename('String') == 'str'
    assert to_python_typename('Int') == 'int'
    assert to_python_typename('SomeType') == 'SomeType'
