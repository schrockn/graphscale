from typing import Any

from graphscale.grapple.graphql_printer import print_graphql_defs
from graphscale.grapple.parser import parse_grapple


def assert_graphql_def(snapshot: Any, graphql: str) -> None:
    result = print_graphql_defs(parse_grapple(graphql))
    snapshot.assert_match(result)


def test_basic_type(snapshot: Any) -> None:
    assert_graphql_def(snapshot, """type Test { name: String }""")


def test_non_pythonic_name(snapshot: Any) -> None:
    assert_graphql_def(snapshot, """type Test { longName: String }""")


def test_nonnullable_type(snapshot: Any) -> None:
    assert_graphql_def(snapshot, """type Test { name: String! }""")


def test_list_type(snapshot: Any) -> None:
    assert_graphql_def(snapshot, """type Test { names: [String] }""")


def test_list_of_reqs(snapshot: Any) -> None:
    assert_graphql_def(snapshot, """type Test { names: [String!] }""")


def test_req_list(snapshot: Any) -> None:
    assert_graphql_def(snapshot, """type Test { names: [String]! }""")


def test_req_list_of_reqs(snapshot: Any) -> None:
    assert_graphql_def(snapshot, """type Test { names: [String!]! }""")


def test_double_list(snapshot: Any) -> None:
    assert_graphql_def(snapshot, """type Test { matrix: [[String]] }""")


def test_ref_to_self(snapshot: Any) -> None:
    assert_graphql_def(snapshot, """type Test { other: Test }""")


def test_args(snapshot: Any) -> None:
    assert_graphql_def(snapshot, """type Test { relatives(skip: Int, take: Int) : [Test] }""")


def test_args_defaults(snapshot: Any) -> None:
    assert_graphql_def(
        snapshot, """type Test {
        many_args(
            defaultTen: Int = 10,
            defaultTwenty: Int = 20,
            defaultZero: Int = 0,
            strArg: String = "foo",
            defaultTrue: Boolean = true,
            defaultFalse: Boolean = false,
        ) : [Test]
    }"""
    )


def test_enum(snapshot: Any) -> None:
    assert_graphql_def(
        snapshot, """
type Hospital {
    status: HospitalStatus
    reqStatus: HospitalStatus!
}

enum HospitalStatus {
    AS_SUBMITTED
}
"""
    )
