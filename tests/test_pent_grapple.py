from graphscale.grapple.parser import parse_grapple, to_python_typename
from graphscale.grapple.pent_printer import print_generated_pents_file_body


def test_no_grapple_types() -> None:
    grapple_string = """type TestObjectField {bar: FooBar}"""
    grapple_document = parse_grapple(grapple_string)
    output = print_generated_pents_file_body(grapple_document)
    assert output == ""


def test_ignore_type() -> None:
    grapple_string = """type TestObjectField @pent(type_id: 1000) {bar: FooBar} type Other { }"""
    grapple_document = parse_grapple(grapple_string)
    output = print_generated_pents_file_body(grapple_document)
    assert output == \
"""class TestObjectField(Pent):
    @property
    def bar(self) -> FooBar:
        return self._data.get('bar') # type: ignore

"""


def test_required_object_field() -> None:
    grapple_string = """type TestObjectField @pent(type_id: 1000) {bar: FooBar!}"""
    grapple_document = parse_grapple(grapple_string)
    output = print_generated_pents_file_body(grapple_document)
    assert output == \
"""class TestObjectField(Pent):
    @property
    def bar(self) -> FooBar:
        return self._data['bar'] # type: ignore

"""


def test_object_field() -> None:
    grapple_string = """type TestObjectField @pent(type_id: 1000) {bar: FooBar}"""
    grapple_document = parse_grapple(grapple_string)
    output = print_generated_pents_file_body(grapple_document)
    assert output == \
"""class TestObjectField(Pent):
    @property
    def bar(self) -> FooBar:
        return self._data.get('bar') # type: ignore

"""


def test_required_field() -> None:
    grapple_string = """type TestRequired @pent(type_id: 1000) {id: ID!, name: String!}"""
    grapple_document = parse_grapple(grapple_string)
    output = print_generated_pents_file_body(grapple_document)
    assert output == \
"""class TestRequired(Pent):
    @property
    def obj_id(self) -> UUID:
        return self._data['obj_id'] # type: ignore

    @property
    def name(self) -> str:
        return self._data['name'] # type: ignore

"""


def test_single_nullable_field() -> None:
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
    output = print_generated_pents_file_body(grapple_document)
    assert output == \
"""class Test(Pent):
    @property
    def name(self) -> str:
        return self._data.get('name') # type: ignore

"""


def test_graphql_type_conversion() -> None:
    assert to_python_typename('String') == 'str'
    assert to_python_typename('Int') == 'int'
    assert to_python_typename('SomeType') == 'SomeType'
