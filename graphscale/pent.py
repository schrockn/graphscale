import inspect
from uuid import UUID

from aiodataloader import DataLoader

import graphscale.check as check
from graphscale.kvetch import Schema, Kvetch
from graphscale.utils import execute_gen


def reverse_dict(dict_to_reverse):
    return {v: k for k, v in dict_to_reverse.items()}


def safe_create(context, obj_id, klass, data):
    # if not klass.is_input_data_valid(data):
    #     return None
    return klass(context, obj_id, data)


class PentConfig:
    def __init__(self, class_map, kvetch_schema):
        check.dict_param(class_map, 'class_map')
        check.param(kvetch_schema, Schema, 'kvetch_schema')
        # class map: str ==> cls
        # type id map: str => type_id
        # reverse type id map: type_id => str
        self.__class_map = class_map
        type_id_map = {obj.type_name: obj.type_id for obj in kvetch_schema.objects}
        self.__type_id_map = type_id_map
        self.__reverse_type_id_map = reverse_dict(type_id_map)

    def get_type(self, type_id):
        check.int_param(type_id, 'type_id')

        cls_string = self.__reverse_type_id_map[type_id]
        return self.__class_map[cls_string]

    def get_type_id(self, cls):
        return self.__type_id_map[cls.__name__]

    def get_class_from_name(self, name):
        return self.__class_map[name]

    def get_edge_target_type_from_name(self, _edge_name):
        raise Exception('not implemented')


class OldPentConfig:
    def __init__(self, *, object_config, edge_config):
        self._object_config = object_config
        self._klass_to_id = reverse_dict(object_config)
        self._edge_config = edge_config
        self._name_to_edge = {edge['edge_name']: edge for edge_id, edge in edge_config.items()}

    def get_type(self, type_id):
        return self._object_config[type_id]

    def get_type_id(self, klass):
        if not klass in self._klass_to_id:
            raise Exception('%s not found make sure to add to config map' % str(klass))
        return self._klass_to_id[klass]

    def get_edge_target_type_from_name(self, edge_name):
        return self._name_to_edge[edge_name]['target_type']


class PentLoader(DataLoader):
    __instance = None

    @staticmethod
    def instance(context):
        if PentLoader.__instance is None:
            PentLoader.__instance = PentLoader(context)
        return PentLoader.__instance

    @staticmethod
    def clear_instance():
        PentLoader.__instance = None

    def __init__(self, context):
        super().__init__(batch_load_fn=self.load_pents)
        self.context = context

    async def load_pents(self, ids):
        obj_dict = await self._actual_load_pent_dict(ids)
        return obj_dict.values()

    async def _actual_load_pent_dict(self, ids):
        obj_dict = await self.context.kvetch().gen_objects(ids)
        pent_dict = {}
        for obj_id, data in obj_dict.items():
            if not data:
                pent_dict[obj_id] = None
            else:
                klass = self.context.config().get_type(data['type_id'])
                pent_dict[obj_id] = safe_create(self.context, obj_id, klass, data)
        return pent_dict


async def create_pent(context, cls, input_object):
    check.param(context, PentContext, 'context')
    check.cls_param(cls, 'cls')
    check.param(input_object, PentMutationData, 'input_object')
    type_id = context.config().get_type_id(cls)
    new_id = await context.kvetch().gen_insert_object(type_id, input_object._asdict())
    return await cls.gen(context, new_id)


async def update_pent(context, cls, obj_id, input_object):
    check.param(context, PentContext, 'context')
    check.cls_param(cls, 'cls')
    check.uuid_param(obj_id, 'obj_id')
    if isinstance(input_object, PentMutationData):
        data = input_object._asdict()
    else:
        data = input_object.data
    await context.kvetch().gen_update_object(obj_id, data)
    PentLoader.instance(context).clear(obj_id)
    return await cls.gen(context, obj_id)


async def delete_pent(context, _klass, obj_id):
    check.param(context, PentContext, 'context')
    value = await context.kvetch().gen_delete_object(obj_id)
    PentLoader.instance(context).clear(obj_id)
    return value


class Pent:
    def __init__(self, context, obj_id, data):
        check.param(context, PentContext, 'context')
        check.param(obj_id, UUID, 'obj_id')
        check.param(data, dict, 'dict')

        self._context = context
        self._obj_id = obj_id
        self._data = data

    def kvetch(self):
        return self._context.kvetch()

    def config(self):
        return self._context.config()

    @classmethod
    async def gen(cls, context, obj_id):
        return await PentLoader.instance(context).load(obj_id)

    @classmethod
    async def gen_list(cls, context, ids):
        return await PentLoader.instance(context).load_many(ids)

    @classmethod
    async def gen_dict(cls, context, ids):
        obj_list = await Pent.gen_list(context, ids)
        return dict(zip([obj.get_obj_id() for obj in obj_list], obj_list))

    @classmethod
    async def gen_all(cls, context, after, first):
        if cls == Pent:
            raise Exception('must specify concrete class')

        type_id = context.config().get_type_id(cls)
        data_list = await context.kvetch().gen_objects_of_type(type_id, after, first)
        return [safe_create(context, data['obj_id'], cls, data) for data in data_list.values()]

    @classmethod
    async def gen_from_index(cls, context, index_name, value):
        obj_id = await context.kvetch().gen_id_from_index(index_name, value)
        if not obj_id:
            return None
        return await cls.gen(context, obj_id)

    @property
    def obj_id(self):
        return self._obj_id

    # eliminate once transition to properties is complete
    def get_obj_id(self):
        return self._obj_id

    def context(self):
        return self._context

    def data(self):
        return self._data

    async def gen_edges_to(self, edge_name, after=None, first=None):
        kvetch = self.kvetch()

        edge_definition = kvetch.get_edge_definition_by_name(edge_name)
        edges = await kvetch.gen_edges(edge_definition, self._obj_id, after=after, first=first)
        return edges

    async def gen_associated_pents_dynamic(self, cls_name, edge_name, after=None, first=None):
        check.str_param(cls_name, 'cls_name')
        check.str_param(edge_name, 'edge_name')
        check.opt_uuid_param(after, 'after')
        check.opt_int_param(first, 'first')

        cls = self.context().cls_from_name(cls_name)

        return await self.gen_associated_pents(cls, edge_name, after, first)

    async def gen_from_stored_id_dynamic(self, cls_name, key):
        check.str_param(cls_name, 'cls_name')
        check.str_param(key, 'key')

        obj_id = self._data.get(key)
        if not obj_id:
            return None

        cls = self.context().cls_from_name(cls_name)
        return await cls.gen(self.context(), obj_id)

    async def gen_associated_pents(self, cls, edge_name, after=None, first=None):
        check.cls_param(cls, 'cls')
        check.str_param(edge_name, 'edge_name')
        check.opt_uuid_param(after, 'after')
        check.opt_int_param(first, 'first')

        edges = await self.gen_edges_to(edge_name, after=after, first=first)
        to_ids = [edge['to_id'] for edge in edges]
        return await cls.gen_list(self._context, to_ids)


class PentContext:
    def __init__(self, *, kvetch, config):
        check.param(kvetch, Kvetch, 'kvetch')
        # check.param(config, PentConfig, 'config')
        self._kvetch = kvetch
        self._config = config
        # Being paranoid for now until I figure out the lifecycle for the loader
        PentLoader.clear_instance()

    def cls_from_name(self, name):
        check.str_param(name, 'name')
        return self._config.get_class_from_name(name)

    def kvetch(self):
        return self._kvetch

    def config(self):
        return self._config


class PentMutationData:
    @staticmethod
    def __copy_list(seq):
        return [PentMutationData.__copy_obj(obj) for obj in seq]

    @staticmethod
    def __copy_obj(obj):
        return obj._asdict() if isinstance(obj, PentMutationData) else obj

    def __init__(self, data):
        self._data = data

    def _asdict(self):
        out = dict()
        for key, value in self._data.items():
            if value is None:
                continue
            if isinstance(value, list):
                out[key] = PentMutationData.__copy_list(value)
            else:
                out[key] = PentMutationData.__copy_obj(value)
        return out

    def _hasattr(self, attr):
        return self._data.get(attr, None) is not None


def is_direct_subclass(obj, subcls, mod):
    return inspect.isclass(obj) and issubclass(obj, subcls) and obj.__module__ == mod.__name__


def create_class_map(pent_mod, input_mod):
    types = []
    for name, cls in inspect.getmembers(pent_mod):
        if is_direct_subclass(cls, Pent, pent_mod):
            types.append((name, cls))
    if input_mod:
        for name, cls in inspect.getmembers(input_mod):
            if is_direct_subclass(cls, PentMutationData, input_mod):
                types.append((name, cls))

            if is_direct_subclass(cls, PentMutationPayload, input_mod):
                types.append((name, cls))

    return dict(types)


# should be able to move post sanic
def loader_safe_execute(func):
    PentLoader.clear_instance()
    try:
        return execute_gen(func)
    finally:
        PentLoader.clear_instance()


class PentMutationPayload:
    pass
