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
