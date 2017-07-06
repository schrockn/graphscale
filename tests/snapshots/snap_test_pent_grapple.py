# -*- coding: utf-8 -*-
# snapshottest: v1 - https://goo.gl/zC4yUc
from __future__ import unicode_literals

from snapshottest import Snapshot


snapshots = Snapshot()

snapshots['test_no_grapple_types 1'] = ''

snapshots['test_ignore_type 1'] = '''class TestObjectField(Pent):
    @property
    def bar(self) -> FooBar:
        return self._data.get('bar') # type: ignore

'''

snapshots['test_required_object_field 1'] = '''class TestObjectField(Pent):
    @property
    def bar(self) -> FooBar:
        return self._data['bar'] # type: ignore

'''

snapshots['test_object_field 1'] = '''class TestObjectField(Pent):
    @property
    def bar(self) -> FooBar:
        return self._data.get('bar') # type: ignore

'''

snapshots['test_required_field 1'] = '''class TestRequired(Pent):
    @property
    def obj_id(self) -> UUID:
        return self._data['obj_id'] # type: ignore

    @property
    def name(self) -> str:
        return self._data['name'] # type: ignore

'''

snapshots['test_single_nullable_field 1'] = '''class Test(Pent):
    @property
    def name(self) -> str:
        return self._data.get('name') # type: ignore

'''
