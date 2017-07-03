from graphscale.utils import reverse_dict


def test_reverse_dictionary():
    assert reverse_dict({1: '1', 2: '2'}) == {'2': 2, '1': 1}


def test_reverse_dictionary_dup_key():
    print(reverse_dict({1: '1', 2: '1'}))
