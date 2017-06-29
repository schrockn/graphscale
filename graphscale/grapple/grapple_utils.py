def req_data_elem_valid(data, key, klass):
    return (key in data) and data[key] and isinstance(data[key], klass)


def req_data_elem_invalid(data, key, klass):
    return not req_data_elem_valid(data, key, klass)


def optional_data_elem_valid(data, key, klass):
    if not data.get(key):  # Falsely or not present is fine
        return True
    return isinstance(data[key], klass)


def opt_data_elem_invalid(data, key, klass):
    return not optional_data_elem_valid(data, key, klass)
