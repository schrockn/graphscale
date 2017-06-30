from graphscale.grapple.parser import parse_grapple, to_python_typename
from graphscale.grapple.pent_printer import print_generated_pents_file_body


def test_no_grapple_types():
    grapple_string = """type TestObjectField {bar: FooBar}"""
    grapple_document = parse_grapple(grapple_string)
    output = print_generated_pents_file_body(grapple_document)
    assert output == ""


def test_ignore_type():
    grapple_string = """type TestObjectField @pent(type_id: 1000) {bar: FooBar} type Other { }"""
    grapple_document = parse_grapple(grapple_string)
    output = print_generated_pents_file_body(grapple_document)
    assert output == \
"""class TestObjectFieldGenerated(Pent):
    @property
    def bar(self):
        return self._data.get('bar')

"""


def test_required_object_field():
    grapple_string = """type TestObjectField @pent(type_id: 1000) {bar: FooBar!}"""
    grapple_document = parse_grapple(grapple_string)
    output = print_generated_pents_file_body(grapple_document)
    assert output == \
"""class TestObjectFieldGenerated(Pent):
    @property
    def bar(self):
        return self._data['bar']

"""


def test_object_field():
    grapple_string = """type TestObjectField @pent(type_id: 1000) {bar: FooBar}"""
    grapple_document = parse_grapple(grapple_string)
    output = print_generated_pents_file_body(grapple_document)
    assert output == \
"""class TestObjectFieldGenerated(Pent):
    @property
    def bar(self):
        return self._data.get('bar')

"""


def test_required_field():
    grapple_string = """type TestRequired @pent(type_id: 1000) {id: ID!, name: String!}"""
    grapple_document = parse_grapple(grapple_string)
    output = print_generated_pents_file_body(grapple_document)
    assert output == \
"""class TestRequiredGenerated(Pent):
    @property
    def obj_id(self):
        return self._data['obj_id']

    @property
    def name(self):
        return self._data['name']

"""


def test_single_nullable_field():
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
"""class TestGenerated(Pent):
    @property
    def name(self):
        return self._data.get('name')

"""


def test_graphql_type_conversion():
    assert to_python_typename('String') == 'str'
    assert to_python_typename('Int') == 'int'
    assert to_python_typename('SomeType') == 'SomeType'
