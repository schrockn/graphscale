import pickle
import zlib
# import json

from uuid import UUID


def data_to_body(data):
    return zlib.compress(pickle.dumps(data))
    # this should switch to json, but I need to do some special support
    # for correct serializing and deserializing UUIDS
    # return zlib.compress(json.dumps(data).encode())


def body_to_data(body):
    if body is None:
        return {}
    return pickle.loads(zlib.decompress(body))
    # return json.loads(zlib.decompress(body).decode())


def row_to_obj(row):
    id_dict = {'obj_id': UUID(bytes=row['obj_id']), 'type_id': row['type_id']}
    body_dict = body_to_data(row['body'])
    return {**id_dict, **body_dict}
