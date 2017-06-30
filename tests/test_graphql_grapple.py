from graphscale.grapple.parser import parse_grapple
from graphscale.grapple.graphql_printer import print_graphql_defs


def test_basic_type():
    graphql = """type Test { name: String }"""
    result = print_graphql_defs(parse_grapple(graphql))
    assert result == """GraphQLTest = GraphQLObjectType(
    name='Test',
    fields=lambda: {
        'name': GraphQLField(
            type=GraphQLString,
            resolver=define_default_resolver('name'),
        ),
    },
)
"""


def test_non_pythonic_name():
    graphql = """type Test { longName: String }"""
    result = print_graphql_defs(parse_grapple(graphql))
    assert result == """GraphQLTest = GraphQLObjectType(
    name='Test',
    fields=lambda: {
        'longName': GraphQLField(
            type=GraphQLString,
            resolver=define_default_resolver('long_name'),
        ),
    },
)
"""


def test_nonnullable_type():
    graphql = """type Test { name: String! }"""
    result = print_graphql_defs(parse_grapple(graphql))
    assert result == """GraphQLTest = GraphQLObjectType(
    name='Test',
    fields=lambda: {
        'name': GraphQLField(
            type=req(GraphQLString),
            resolver=define_default_resolver('name'),
        ),
    },
)
"""


def test_list_type():
    graphql = """type Test { names: [String] }"""
    result = print_graphql_defs(parse_grapple(graphql))
    assert result == """GraphQLTest = GraphQLObjectType(
    name='Test',
    fields=lambda: {
        'names': GraphQLField(
            type=list_of(GraphQLString),
            resolver=define_default_resolver('names'),
        ),
    },
)
"""


def test_list_of_reqs():
    graphql = """type Test { names: [String!] }"""
    result = print_graphql_defs(parse_grapple(graphql))
    assert result == """GraphQLTest = GraphQLObjectType(
    name='Test',
    fields=lambda: {
        'names': GraphQLField(
            type=list_of(req(GraphQLString)),
            resolver=define_default_resolver('names'),
        ),
    },
)
"""


def test_req_list():
    graphql = """type Test { names: [String]! }"""
    result = print_graphql_defs(parse_grapple(graphql))
    assert result == """GraphQLTest = GraphQLObjectType(
    name='Test',
    fields=lambda: {
        'names': GraphQLField(
            type=req(list_of(GraphQLString)),
            resolver=define_default_resolver('names'),
        ),
    },
)
"""


def test_req_list_of_reqs():
    graphql = """type Test { names: [String!]! }"""
    result = print_graphql_defs(parse_grapple(graphql))
    assert result == """GraphQLTest = GraphQLObjectType(
    name='Test',
    fields=lambda: {
        'names': GraphQLField(
            type=req(list_of(req(GraphQLString))),
            resolver=define_default_resolver('names'),
        ),
    },
)
"""


def test_double_list():
    graphql = """type Test { matrix: [[String]] }"""
    result = print_graphql_defs(parse_grapple(graphql))
    assert result == """GraphQLTest = GraphQLObjectType(
    name='Test',
    fields=lambda: {
        'matrix': GraphQLField(
            type=list_of(list_of(GraphQLString)),
            resolver=define_default_resolver('matrix'),
        ),
    },
)
"""


def test_ref_to_self():
    graphql = """type Test { other: Test }"""
    result = print_graphql_defs(parse_grapple(graphql))
    assert result == """GraphQLTest = GraphQLObjectType(
    name='Test',
    fields=lambda: {
        'other': GraphQLField(
            type=GraphQLTest,
            resolver=define_default_resolver('other'),
        ),
    },
)
"""


def test_args():
    graphql = """type Test { relatives(skip: Int, take: Int) : [Test] }"""
    result = print_graphql_defs(parse_grapple(graphql))
    assert result == """GraphQLTest = GraphQLObjectType(
    name='Test',
    fields=lambda: {
        'relatives': GraphQLField(
            type=list_of(GraphQLTest),
            args={
                'skip': GraphQLArgument(type=GraphQLInt),
                'take': GraphQLArgument(type=GraphQLInt),
            },
            resolver=define_default_resolver('relatives'),
        ),
    },
)
"""


def test_args_defaults():
    graphql = """type Test {
        many_args(
            defaultTen: Int = 10,
            defaultTwenty: Int = 20,
            defaultZero: Int = 0,
            strArg: String = "foo",
            defaultTrue: Boolean = true,
            defaultFalse: Boolean = false,
        ) : [Test]
    }"""
    result = print_graphql_defs(parse_grapple(graphql))
    assert result == """GraphQLTest = GraphQLObjectType(
    name='Test',
    fields=lambda: {
        'many_args': GraphQLField(
            type=list_of(GraphQLTest),
            args={
                'defaultTen': GraphQLArgument(type=GraphQLInt, default_value=10),
                'defaultTwenty': GraphQLArgument(type=GraphQLInt, default_value=20),
                'defaultZero': GraphQLArgument(type=GraphQLInt, default_value=0),
                'strArg': GraphQLArgument(type=GraphQLString, default_value="foo"),
                'defaultTrue': GraphQLArgument(type=GraphQLBoolean, default_value=True),
                'defaultFalse': GraphQLArgument(type=GraphQLBoolean, default_value=False),
            },
            resolver=define_default_resolver('many_args'),
        ),
    },
)
"""


def test_enum():
    graphql = """
type Hospital {
    status: HospitalStatus
    reqStatus: HospitalStatus!
}

enum HospitalStatus {
    AS_SUBMITTED
}
"""
    result = print_graphql_defs(parse_grapple(graphql))
    assert result == """GraphQLHospital = GraphQLObjectType(
    name='Hospital',
    fields=lambda: {
        'status': GraphQLField(
            type=GraphQLHospitalStatus,
            resolver=lambda obj, args, *_: obj.status(*args).name if obj.status(*args) else None,
        ),
        'reqStatus': GraphQLField(
            type=req(GraphQLHospitalStatus),
            resolver=lambda obj, args, *_: obj.req_status(*args).name if obj.req_status(*args) else None,
        ),
    },
)

GraphQLHospitalStatus = GraphQLEnumType(
    name='HospitalStatus',
    values={
        'AS_SUBMITTED': GraphQLEnumValue(),
    },
)
"""
