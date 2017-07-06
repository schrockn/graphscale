# -*- coding: utf-8 -*-
# snapshottest: v1 - https://goo.gl/zC4yUc
from __future__ import unicode_literals

from snapshottest import Snapshot


snapshots = Snapshot()

snapshots['test_generated_mutations 1'] = '''class Root(PentContextfulObject):
    async def gen_create_todo_user(self, data: 'CreateTodoUserData') -> 'CreateTodoUserPayload':
        return await gen_create_pent_dynamic(self.context, 'TodoUser', 'CreateTodoUserData', 'CreateTodoUserPayload', data) # type: ignore

    async def gen_update_todo_user(self, obj_id: UUID, data: 'UpdateTodoUserData') -> 'UpdateTodoUserPayload':
        return await gen_update_pent_dynamic(self.context, obj_id, 'TodoUser', 'UpdateTodoUserData', 'UpdateTodoUserPayload', data) # type: ignore

    async def gen_delete_todo_user(self, obj_id: UUID) -> 'DeleteTodoUserPayload':
        return await gen_delete_pent_dynamic(self.context, 'TodoUser', 'DeleteTodoUserPayload', obj_id) # type: ignore


class CreateTodoUserData(PentMutationData):
    def __init__(self, *,
        name: str,
        username: str,
    ) -> None:
        data = locals()
        del data['self']
        super().__init__(data)

    @property
    def name(self) -> str:
        return self._data['name'] # type: ignore

    @property
    def username(self) -> str:
        return self._data['username'] # type: ignore

class UpdateTodoUserData(PentMutationData):
    def __init__(self, *,
        name: str=None,
    ) -> None:
        data = locals()
        del data['self']
        super().__init__(data)

    @property
    def name(self) -> str:
        return self._data.get('name') # type: ignore


__CreateTodoUserPayloadDataMixin = namedtuple('__CreateTodoUserPayloadDataMixin', 'todo_user')


class CreateTodoUserPayload(PentMutationPayload, __CreateTodoUserPayloadDataMixin):
    pass


__UpdateTodoUserPayloadDataMixin = namedtuple('__UpdateTodoUserPayloadDataMixin', 'todo_user')


class UpdateTodoUserPayload(PentMutationPayload, __UpdateTodoUserPayloadDataMixin):
    pass


__DeleteTodoUserPayloadDataMixin = namedtuple('__DeleteTodoUserPayloadDataMixin', 'deleted_id')


class DeleteTodoUserPayload(PentMutationPayload, __DeleteTodoUserPayloadDataMixin):
    pass
'''

snapshots['test_no_grapple_types 1'] = ''

snapshots['test_ignore_type 1'] = '''class TestObjectField(manual_mixins.TestObjectFieldManualMixin):
    @property
    def bar(self) -> FooBar:
        return self._data.get('bar') # type: ignore
'''

snapshots['test_required_object_field 1'] = '''class TestObjectField(manual_mixins.TestObjectFieldManualMixin):
    @property
    def bar(self) -> FooBar:
        return self._data['bar'] # type: ignore
'''

snapshots['test_object_field 1'] = '''class TestObjectField(manual_mixins.TestObjectFieldManualMixin):
    @property
    def bar(self) -> FooBar:
        return self._data.get('bar') # type: ignore
'''

snapshots['test_required_field 1'] = '''class TestRequired(manual_mixins.TestRequiredManualMixin):
    @property
    def obj_id(self) -> UUID:
        return self._data['obj_id'] # type: ignore

    @property
    def name(self) -> str:
        return self._data['name'] # type: ignore
'''

snapshots['test_single_nullable_field 1'] = '''class Test(manual_mixins.TestManualMixin):
    @property
    def name(self) -> str:
        return self._data.get('name') # type: ignore
'''

snapshots['test_read_pent 1'] = '''class Root(PentContextfulObject):
    async def gen_todo_user(self, obj_id: UUID) -> 'TodoUser':
        return await gen_pent_dynamic(self.context, 'TodoUser', obj_id) # type: ignore

'''

snapshots['test_browse_pent 1'] = '''class Root(PentContextfulObject):
    async def gen_all_todo_users(self, first: int, after: UUID=None) -> 'List[TodoUser]':
        return await gen_browse_pents_dynamic(self.context, after, first, 'TodoUser') # type: ignore

'''

snapshots['test_stored_id_edge 1'] = '''class TodoUser(manual_mixins.TodoUserManualMixin):
    @property
    def obj_id(self) -> UUID:
        return self._data['obj_id'] # type: ignore

    async def gen_todo_lists(self, first: int, after: UUID=None) -> 'List[TodoList]':
        return await self.gen_associated_pents_dynamic('TodoList', 'user_to_list_edge', after, first) # type: ignore

class TodoList(manual_mixins.TodoListManualMixin):
    @property
    def obj_id(self) -> UUID:
        return self._data['obj_id'] # type: ignore

    @property
    def name(self) -> str:
        return self._data['name'] # type: ignore

    async def gen_owner(self) -> 'TodoUser':
        return await self.gen_from_stored_id_dynamic('TodoUser', 'owner_id') # type: ignore
'''

snapshots['test_merge_query_mutation 1'] = '''class Root(PentContextfulObject):
    async def gen_todo_user(self, obj_id: UUID) -> 'TodoUser':
        return await gen_pent_dynamic(self.context, 'TodoUser', obj_id) # type: ignore

    async def gen_create_todo_user(self, data: 'CreateTodoUserData') -> 'CreateTodoUserPayload':
        return await gen_create_pent_dynamic(self.context, 'TodoUser', 'CreateTodoUserData', 'CreateTodoUserPayload', data) # type: ignore


class CreateTodoUserData(PentMutationData):
    def __init__(self, *,
        name: str,
        username: str,
    ) -> None:
        data = locals()
        del data['self']
        super().__init__(data)

    @property
    def name(self) -> str:
        return self._data['name'] # type: ignore

    @property
    def username(self) -> str:
        return self._data['username'] # type: ignore


__CreateTodoUserPayloadDataMixin = namedtuple('__CreateTodoUserPayloadDataMixin', 'todo_user')


class CreateTodoUserPayload(PentMutationPayload, __CreateTodoUserPayloadDataMixin):
    pass
'''
