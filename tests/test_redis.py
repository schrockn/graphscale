import redis
from graphscale.kvetch.kvetch_utils import data_to_body, body_to_data
from uuid import uuid4

import pytest

@pytest.mark.skip
def test_redis():
    redis_instance = redis.StrictRedis(host='localhost', port=6379, db=0, decode_responses=True)
    redis_instance.set('foo', 'bar')
    assert redis_instance.get('foo') == 'bar'

@pytest.mark.skip
def test_store_kvetch_obj():
    redis_instance = redis.StrictRedis(host='localhost', port=6379, db=0, decode_responses=False)
    data = {'num': 4, 'str': 'some string'}
    obj_id = uuid4()
    body = data_to_body(data)
    redis_instance.set(obj_id, body)
    out_body = redis_instance.get(obj_id)
    out_data = body_to_data(out_body)
    assert data == out_data

@pytest.mark.skip
def test_mget():
    redis_instance = redis.StrictRedis(host='localhost', port=6379, db=0, decode_responses=True)
    redis_instance.set('foo1', 'bar1')
    redis_instance.set('foo2', 'bar2')
    out_value = redis_instance.mget(['foo1', 'foo2'])
    assert out_value == ['bar1', 'bar2']


