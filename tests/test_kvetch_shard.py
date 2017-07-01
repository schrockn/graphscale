from uuid import UUID, uuid4

import pytest

import graphscale.kvetch as kvetch
from graphscale.kvetch.sync import SyncedShard

from graphscale.kvetch.dbschema import drop_shard_db_tables, init_shard_db_tables
from graphscale.kvetch.dbshard import KvetchDbShard, KvetchDbSingleConnectionPool
from graphscale.kvetch.memshard import KvetchMemShard

from graphscale.test.utils import MagnusConn, db_mem_fixture

from graphscale import check

#W0621 display redefine variable for test fixture
#pylint: disable=W0621,C0103,W0401,W0614


def related_edge():
    return kvetch.define_stored_id_edge(
        edge_name='related_edge',
        edge_id=12345,
        from_id_attr='related_id',
    )


def num_index():
    return kvetch.define_int_index(
        index_name='num_index',
        indexed_type='Test',
        indexed_attr='num',
    )


def mem_single_edge_shard():
    edges = {
        'related_edge': related_edge(),
    }
    return (KvetchMemShard(), edges, {})


def db_single_edge_shard():
    shard = KvetchDbShard(
        pool=KvetchDbSingleConnectionPool(MagnusConn.get_unittest_conn_info()),
    )
    indexes = []
    edges = {
        'related_edge': related_edge(),
    }
    drop_shard_db_tables(shard, indexes)
    init_shard_db_tables(shard, indexes)
    return (shard, edges, indexes)


def mem_edge_and_index_shard():
    edges = {'related_edge': related_edge()}
    indexes = [num_index()]
    return (KvetchMemShard(), edges, indexes)


def db_edge_and_index_shard():
    shard = KvetchDbShard(
        pool=KvetchDbSingleConnectionPool(MagnusConn.get_unittest_conn_info()),
    )
    edges = {'related_edge': related_edge()}
    indexes = [num_index()]
    drop_shard_db_tables(shard, indexes)
    init_shard_db_tables(shard, indexes)
    return (shard, edges, indexes)


@pytest.fixture(params=db_mem_fixture(mem=mem_edge_and_index_shard, db=db_edge_and_index_shard))
def sync_index_shard(request):
    shard, edges, indexes = request.param()
    return (SyncedShard(shard), edges, indexes)


@pytest.fixture(params=db_mem_fixture(mem=mem_edge_and_index_shard, db=db_edge_and_index_shard))
def test_shard_single_index(request):
    return request.param()


@pytest.fixture(params=db_mem_fixture(mem=mem_single_edge_shard, db=db_single_edge_shard))
def only_shard(request):
    shard, _, _ = request.param()
    return shard


@pytest.fixture(params=db_mem_fixture(mem=mem_single_edge_shard, db=db_single_edge_shard))
def sync_shard(request):
    shard, _, _ = request.param()
    return SyncedShard(shard)


@pytest.fixture(params=db_mem_fixture(mem=mem_single_edge_shard, db=db_single_edge_shard))
def sync_edge_shard(request):
    shard, edges, indexes = request.param()
    return (SyncedShard(shard), edges, indexes)


@pytest.fixture(params=db_mem_fixture(mem=mem_single_edge_shard, db=db_single_edge_shard))
def test_shard_single_edge(request):
    return request.param()


def insert_test_obj(shard, data):
    return SyncedShard(shard).insert_object(uuid4(), 1000, data)


def sync_insert_test_obj(sync_shard, data):
    return sync_shard.insert_object(uuid4(), 1000, data)


def test_object_insert(sync_shard):
    data = {'num': 2}
    new_id = sync_insert_test_obj(sync_shard, data)
    assert isinstance(new_id, UUID)


def test_object_insert_get(sync_shard):
    data = {'num': 3}
    new_id = sync_insert_test_obj(sync_shard, data)
    new_data = sync_shard.get_object(new_id)
    assert new_data['obj_id'] == new_id
    assert new_data['num'] == 3
    assert new_data['type_id'] == 1000


def test_objects_insert_get(sync_shard):
    data_one = {'num': 4}
    data_two = {'num': 5}
    id_one = sync_insert_test_obj(sync_shard, data_one)
    id_two = sync_insert_test_obj(sync_shard, data_two)
    obj_dict = sync_shard.get_objects([id_one, id_two])
    assert len(obj_dict) == 2
    assert obj_dict[id_one]['obj_id'] == id_one
    assert obj_dict[id_one]['num'] == 4
    assert obj_dict[id_two]['obj_id'] == id_two
    assert obj_dict[id_two]['num'] == 5


def test_objects_insert_update_get(sync_shard):
    data_one = {'num': 4}
    id_one = sync_insert_test_obj(sync_shard, data_one)
    obj_t_one = sync_shard.get_object(id_one)
    assert obj_t_one['num'] == 4
    sync_shard.update_object(id_one, {'num': 5})
    obj_t_two = sync_shard.get_object(id_one)
    assert obj_t_two['num'] == 5


def test_delete_object(sync_shard):
    data_one = {'num': 4}
    id_one = sync_insert_test_obj(sync_shard, data_one)
    assert sync_shard.get_object(id_one)['num'] == 4
    sync_shard.delete_object(id_one)
    assert sync_shard.get_object(id_one) is None


def get_sorted_ids(num):
    ids = []
    for i in range(0, num):
        ids.append(uuid4())
    return tuple(sorted(ids))


def test_get_objects_of_type(sync_shard):
    id_one, id_two, id_three, id_four = get_sorted_ids(4)
    sync_shard.insert_object(id_one, 1000, {'num': 5})
    sync_shard.insert_object(id_two, 1000, {'num': 6})
    sync_shard.insert_object(id_three, 1000, {'num': 7})
    sync_shard.insert_object(id_four, 1001, {'num': 8})
    ids_out_1000 = [obj_id for obj_id in sync_shard.get_objects_of_type(1000).keys()]
    assert ids_out_1000 == [id_one, id_two, id_three]
    datas_out_1000 = [obj for obj in sync_shard.get_objects_of_type(1000).values()]
    assert [data['num'] for data in datas_out_1000] == [5, 6, 7]
    ids_out_1001 = [obj_id for obj_id in sync_shard.get_objects_of_type(1001).keys()]
    assert ids_out_1001 == [id_four]
    datas_out_1001 = [obj for obj in sync_shard.get_objects_of_type(1001).values()]
    assert [data['num'] for data in datas_out_1001] == [8]


def test_objects_of_type_first(sync_shard):
    id_one, id_two, id_three, id_four = get_sorted_ids(4)
    sync_shard.insert_object(id_one, 1000, {'num': 5})
    sync_shard.insert_object(id_two, 1000, {'num': 6})
    sync_shard.insert_object(id_three, 1000, {'num': 7})
    sync_shard.insert_object(id_four, 1001, {'num': 8})

    first_one_objs = sync_shard.get_objects_of_type(1000, after=None, first=1)
    assert list(first_one_objs.keys()) == [id_one]

    first_two_objs = sync_shard.get_objects_of_type(1000, after=None, first=2)
    assert list(first_two_objs.keys()) == [id_one, id_two]

    first_three_objs = sync_shard.get_objects_of_type(1000, after=None, first=3)
    assert list(first_three_objs.keys()) == [id_one, id_two, id_three]


def test_objects_of_type_after(sync_shard):
    id_before, id_one, id_gap, id_two, id_three, id_four, id_off_end = get_sorted_ids(7)

    sync_shard.insert_object(id_one, 1000, {'num': 5})
    sync_shard.insert_object(id_two, 1000, {'num': 6})
    sync_shard.insert_object(id_three, 1000, {'num': 7})
    sync_shard.insert_object(id_four, 1001, {'num': 8})

    after_id_before_objs = sync_shard.get_objects_of_type(1000, after=id_before)
    assert list(after_id_before_objs.keys()) == [id_one, id_two, id_three]

    after_one_objs = sync_shard.get_objects_of_type(1000, after=id_one)
    assert list(after_one_objs.keys()) == [id_two, id_three]

    after_gap_objs = sync_shard.get_objects_of_type(1000, after=id_gap)
    assert list(after_gap_objs.keys()) == [id_two, id_three]

    after_two_objs = sync_shard.get_objects_of_type(1000, after=id_two)
    assert list(after_two_objs.keys()) == [id_three]

    after_three_objs = sync_shard.get_objects_of_type(1000, after=id_three)
    assert list(after_three_objs.keys()) == []

    after_end_objs = sync_shard.get_objects_of_type(1000, after=id_off_end)
    assert list(after_end_objs.keys()) == []


def test_objects_of_type_after_first(sync_shard):
    id_before, id_one, id_gap, id_two, id_three, id_four = get_sorted_ids(6)

    sync_shard.insert_object(id_one, 1000, {'num': 5})
    sync_shard.insert_object(id_two, 1000, {'num': 6})
    sync_shard.insert_object(id_three, 1000, {'num': 7})
    sync_shard.insert_object(id_four, 1001, {'num': 8})

    after_before_first_one_objs = sync_shard.get_objects_of_type(1000, after=id_before, first=1)
    assert list(after_before_first_one_objs.keys()) == [id_one]

    after_before_first_two_objs = sync_shard.get_objects_of_type(1000, after=id_before, first=2)
    assert list(after_before_first_two_objs.keys()) == [id_one, id_two]

    after_one_first_one_objs = sync_shard.get_objects_of_type(1000, after=id_one, first=1)
    assert list(after_one_first_one_objs.keys()) == [id_two]

    after_gap_first_one_objs = sync_shard.get_objects_of_type(1000, after=id_gap, first=1)
    assert list(after_gap_first_one_objs.keys()) == [id_two]


def test_get_zero_objects(sync_shard):
    with pytest.raises(check.ParameterInvariantViolation):
        sync_shard.get_objects([])


def test_object_insert_id(sync_shard):
    new_id = uuid4()
    with pytest.raises(check.ParameterInvariantViolation):
        sync_shard.insert_object(new_id, 1000, None)
    with pytest.raises(check.ParameterInvariantViolation):
        sync_shard.insert_object(new_id, 1000, [])
    with pytest.raises(check.ParameterInvariantViolation):
        sync_shard.insert_object(new_id, 1000, {'obj_id': 234})
    with pytest.raises(check.ParameterInvariantViolation):
        sync_shard.insert_object(new_id, 1000, {'type_id': 234})
    with pytest.raises(check.ParameterInvariantViolation):
        sync_shard.insert_object(new_id, None, {'name': 'Joe'})
    with pytest.raises(check.ParameterInvariantViolation):
        sync_shard.insert_object(None, 1000, {})
    with pytest.raises(check.ParameterInvariantViolation):
        sync_shard.insert_object(101, 1000, {})


def test_bad_args(sync_shard):
    with pytest.raises(check.ParameterInvariantViolation):
        sync_shard.get_object(None)


def test_id_edge(sync_edge_shard):
    sync_shard, edges, _ = sync_edge_shard
    data_one = {'num': 4}
    id_one = sync_insert_test_obj(sync_shard, data_one)
    data_two = {'num': 5, 'related_id': id_one}
    id_two = sync_insert_test_obj(sync_shard, data_two)
    data_three = {'num': 6, 'related_id': id_one}
    id_three = sync_insert_test_obj(sync_shard, data_three)

    edge_name = 'related_edge'
    related_edge = edges[edge_name]
    assert related_edge is not None
    sync_shard.insert_edge(related_edge, id_one, id_two)
    sync_shard.insert_edge(related_edge, id_one, id_three)
    ids = sync_shard.get_edge_ids(related_edge, id_one)
    assert len(ids) == 2
    assert id_one not in ids
    assert id_two in ids
    assert id_three in ids


def test_first_edge(sync_edge_shard):
    sync_shard, edges, _ = sync_edge_shard
    id_one = UUID('f2d41433-a996-40c9-ba3b-6047b2bd27f7')
    id_two = UUID('54c4c971-e7a3-42ff-858a-64a73cca3286')
    id_three = UUID('0ddf55de-0f37-4152-8f41-7e64c7359a9e')
    id_four = UUID('e5a34f23-c14f-49cc-a9ad-f3a8165e141c')

    sync_shard.insert_object(id_one, 1000, {})
    sync_shard.insert_object(id_two, 1000, {})
    sync_shard.insert_object(id_three, 1000, {})
    sync_shard.insert_object(id_four, 1000, {})

    related_edge = edges['related_edge']

    sync_shard.insert_edge(related_edge, id_one, id_two)
    sync_shard.insert_edge(related_edge, id_one, id_three)
    sync_shard.insert_edge(related_edge, id_one, id_four)

    assert len(sync_shard.get_edge_ids(related_edge, id_one)) == 3

    def get_after(a, f=None):
        return sync_shard.get_edge_ids(related_edge, id_one, after=a, first=f)

    assert len(get_after(id_two)) == 2
    assert not id_two in get_after(id_two)
    assert id_three in get_after(id_two)
    assert id_four in get_after(id_two)

    assert len(get_after(id_three)) == 1
    assert not id_two in get_after(id_three)
    assert not id_three in get_after(id_three)
    assert id_four in get_after(id_three)

    after_four_len = len(get_after(id_four))
    assert after_four_len == 0


def test_after_edge(sync_edge_shard):
    sync_shard, edges, _ = sync_edge_shard
    id_one = UUID('50ce64f1-3e76-462c-8a03-91475503e496')
    id_two = UUID('a5c99e91-8084-4405-8378-db0af38d8b61')
    id_three = UUID('5301d18f-c3bd-42c4-bcfb-50924b3aca39')
    data_one = {'num': 4}
    data_two = {'num': 5, 'related_id': id_one}
    data_three = {'num': 6, 'related_id': id_one}
    sync_shard.insert_object(id_one, 1000, data_one)
    sync_shard.insert_object(id_two, 1000, data_two)
    sync_shard.insert_object(id_three, 1000, data_three)

    related_edge = edges['related_edge']
    assert related_edge is not None

    sync_shard.insert_edge(related_edge, id_one, id_two)
    sync_shard.insert_edge(related_edge, id_one, id_three)

    all_edge_ids = sync_shard.get_edge_ids(related_edge, id_one)
    assert all_edge_ids == [id_two, id_three]
    edge_ids = sync_shard.get_edge_ids(related_edge, id_one, after=id_two)
    assert len(edge_ids) == 1
    assert not id_two in edge_ids
    assert id_three in edge_ids


def test_string_index(sync_index_shard):
    sync_shard, _, indexes = sync_index_shard
    data_one = {'num': 4, 'related_id': None, 'text': 'first insert'}
    id_one = sync_insert_test_obj(sync_shard, data_one)
    data_two = {'num': 4, 'related_id': id_one, 'text': 'second insert'}
    id_two = sync_insert_test_obj(sync_shard, data_two)
    data_three = {'num': 5, 'related_id': id_one, 'text': 'third insert'}
    id_three = sync_insert_test_obj(sync_shard, data_three)

    num_index = indexes[0]
    sync_shard.insert_index_entry(num_index, 4, id_one)
    sync_shard.insert_index_entry(num_index, 4, id_two)
    sync_shard.insert_index_entry(num_index, 5, id_three)

    four_ids = sync_shard.get_index_ids(num_index, 4)

    assert id_one in four_ids
    assert id_two in four_ids
    assert id_three not in four_ids

    five_ids = sync_shard.get_index_ids(num_index, 5)

    assert id_one not in five_ids
    assert id_two not in five_ids
    assert id_three in five_ids
