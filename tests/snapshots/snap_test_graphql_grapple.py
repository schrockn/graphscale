# -*- coding: utf-8 -*-
# snapshottest: v1 - https://goo.gl/zC4yUc
from __future__ import unicode_literals

from snapshottest import Snapshot


snapshots = Snapshot()

snapshots['test_basic_type 1'] = '''GraphQLTest = GraphQLObjectType(
    name='Test',
    fields=lambda: {
        'name': GraphQLField(
            type=GraphQLString, # type: ignore
            resolver=define_default_resolver('name'),
        ),
    },
)
'''

snapshots['test_non_pythonic_name 1'] = '''GraphQLTest = GraphQLObjectType(
    name='Test',
    fields=lambda: {
        'longName': GraphQLField(
            type=GraphQLString, # type: ignore
            resolver=define_default_resolver('long_name'),
        ),
    },
)
'''

snapshots['test_nonnullable_type 1'] = '''GraphQLTest = GraphQLObjectType(
    name='Test',
    fields=lambda: {
        'name': GraphQLField(
            type=req(GraphQLString), # type: ignore
            resolver=define_default_resolver('name'),
        ),
    },
)
'''

snapshots['test_list_type 1'] = '''GraphQLTest = GraphQLObjectType(
    name='Test',
    fields=lambda: {
        'names': GraphQLField(
            type=list_of(GraphQLString), # type: ignore
            resolver=define_default_resolver('names'),
        ),
    },
)
'''

snapshots['test_list_of_reqs 1'] = '''GraphQLTest = GraphQLObjectType(
    name='Test',
    fields=lambda: {
        'names': GraphQLField(
            type=list_of(req(GraphQLString)), # type: ignore
            resolver=define_default_resolver('names'),
        ),
    },
)
'''

snapshots['test_req_list 1'] = '''GraphQLTest = GraphQLObjectType(
    name='Test',
    fields=lambda: {
        'names': GraphQLField(
            type=req(list_of(GraphQLString)), # type: ignore
            resolver=define_default_resolver('names'),
        ),
    },
)
'''

snapshots['test_req_list_of_reqs 1'] = '''GraphQLTest = GraphQLObjectType(
    name='Test',
    fields=lambda: {
        'names': GraphQLField(
            type=req(list_of(req(GraphQLString))), # type: ignore
            resolver=define_default_resolver('names'),
        ),
    },
)
'''

snapshots['test_double_list 1'] = '''GraphQLTest = GraphQLObjectType(
    name='Test',
    fields=lambda: {
        'matrix': GraphQLField(
            type=list_of(list_of(GraphQLString)), # type: ignore
            resolver=define_default_resolver('matrix'),
        ),
    },
)
'''

snapshots['test_ref_to_self 1'] = '''GraphQLTest = GraphQLObjectType(
    name='Test',
    fields=lambda: {
        'other': GraphQLField(
            type=GraphQLTest, # type: ignore
            resolver=define_default_resolver('other'),
        ),
    },
)
'''

snapshots['test_args 1'] = '''GraphQLTest = GraphQLObjectType(
    name='Test',
    fields=lambda: {
        'relatives': GraphQLField(
            type=list_of(GraphQLTest), # type: ignore
            args={
                'skip': GraphQLArgument(type=GraphQLInt), # type: ignore
                'take': GraphQLArgument(type=GraphQLInt), # type: ignore
            },
            resolver=define_default_resolver('relatives'),
        ),
    },
)
'''

snapshots['test_args_defaults 1'] = '''GraphQLTest = GraphQLObjectType(
    name='Test',
    fields=lambda: {
        'many_args': GraphQLField(
            type=list_of(GraphQLTest), # type: ignore
            args={
                'defaultTen': GraphQLArgument(type=GraphQLInt, default_value=10), # type: ignore
                'defaultTwenty': GraphQLArgument(type=GraphQLInt, default_value=20), # type: ignore
                'defaultZero': GraphQLArgument(type=GraphQLInt, default_value=0), # type: ignore
                \'strArg\': GraphQLArgument(type=GraphQLString, default_value="foo"), # type: ignore
                'defaultTrue': GraphQLArgument(type=GraphQLBoolean, default_value=True), # type: ignore
                'defaultFalse': GraphQLArgument(type=GraphQLBoolean, default_value=False), # type: ignore
            },
            resolver=define_default_resolver('many_args'),
        ),
    },
)
'''

snapshots['test_enum 1'] = '''GraphQLHospital = GraphQLObjectType(
    name='Hospital',
    fields=lambda: {
        'status': GraphQLField(
            type=GraphQLHospitalStatus, # type: ignore
            resolver=lambda obj, args, *_: obj.status(*args).name if obj.status(*args) else None,
        ),
        'reqStatus': GraphQLField(
            type=req(GraphQLHospitalStatus), # type: ignore
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
'''
