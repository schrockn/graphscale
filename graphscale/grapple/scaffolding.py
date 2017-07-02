import os
import re

from graphscale import check

from .kvetch_printer import print_kvetch_decls
from .graphql_printer import print_graphql_file
from .pent_printer import print_generated_pents_file
from .parser import parse_grapple

GRAPHQL_INIT_SCAFFOLD = """from graphql import GraphQLSchema
from . import generated


def graphql_schema():
    return GraphQLSchema(query=generated.GraphQLQuery, mutation=generated.GraphQLMutation)
"""


def write_file(path, text):
    with open(path, 'w') as fobj:
        fobj.write(text)


def write_if_new_file(path, text):
    if os.path.exists(path):
        return
    with open(path, 'w') as fobj:
        fobj.write(text)


def read_file(path):
    with open(path, 'r') as fobj:
        return fobj.read()


PENTS_SCAFFOLD = "from . import generated \n"

PENT_INIT_SCAFFOLD = """from .pents import *
"""

PENT_CONFIG_TEMPLATE = """from graphscale.pent import PentConfig, PentContext, create_class_map
from graphscale.kvetch import init_from_conn, init_in_memory
from .kvetch import kvetch_schema
from .pent import pents, mutations

CLASS_MAP = create_class_map(pents, mutations)


def pent_config():
    return PentConfig(class_map=CLASS_MAP, kvetch_schema=kvetch_schema())


def pent_context(kvetch):
    return PentContext(kvetch=kvetch, config=pent_config())


def single_db_context(conn_info):
    return pent_context(init_from_conn(conn_info=conn_info, schema=kvetch_schema()))


def in_mem_context():
    return pent_context(init_in_memory(kvetch_schema()))
"""

KVETCH_INIT_SCAFFOLD = "from .kvetch_schema import kvetch_schema\n"
KVETCH_SCHEMA_SCAFFOLD = """from graphscale.kvetch import define_schema
from .generated import generated_objects, generated_indexes, generated_edges

def kvetch_schema():
    objects = generated_objects()
    indexes = generated_indexes()
    edges = generated_edges()
    return define_schema(objects=objects, indexes=indexes, edges=edges)
"""

SERVE_SCAFFOLD = """from graphscale.server import run_graphql_endpoint
from {module_name}.pent import Root
from {module_name}.config import in_mem_context
from {module_name}.graphql_schema import graphql_schema


def serve(context):
    run_graphql_endpoint(Root(context), graphql_schema())


if __name__ == '__main__':
    serve(in_mem_context())
"""


def write_scaffold(structure, current_dir, *, overwrite=False):
    write_func = write_file if overwrite else write_if_new_file
    for key, value in structure.items():
        if isinstance(value, str):  # string means a file
            target_file = os.path.join(current_dir, key)
            write_func(target_file, value)
        elif isinstance(value, dict):  # dict means a directory
            new_dir = os.path.join(current_dir, key)
            if not os.path.exists(new_dir):
                os.makedirs(new_dir)
            write_scaffold(value, new_dir, overwrite=overwrite)
        else:
            raise Exception('internal structure')


def create_scaffolding(base_dir, module_name):
    # this creates a directory structure that mimics the dict hierarchy.
    # leaf nodes are strings which are file contents
    scaffold_structure = {
        module_name: {
            'graphql_schema': {
                '__init__.py': GRAPHQL_INIT_SCAFFOLD,
            },
            'pent': {
                '__init__.py': PENT_INIT_SCAFFOLD,
                'pents.py': PENTS_SCAFFOLD,
            },
            'kvetch': {
                '__init__.py': KVETCH_INIT_SCAFFOLD,
                'kvetch_schema.py': KVETCH_SCHEMA_SCAFFOLD,
            },
            'config.py': PENT_CONFIG_TEMPLATE.format(module_name=module_name),
        },
        'serve.py': SERVE_SCAFFOLD.format(module_name=module_name),
    }

    write_scaffold(scaffold_structure, base_dir, overwrite=False)


def overwrite_generated_files(module_dir, document_ast):
    generated_files_scaffold = {
        'graphql_schema': {
            'generated.py': print_graphql_file(document_ast)
        },
        'pent': {
            'generated.py': print_generated_pents_file(document_ast)
        },
        'kvetch': {
            'generated.py': print_kvetch_decls(document_ast)
        },
    }

    write_scaffold(generated_files_scaffold, module_dir, overwrite=True)


MANUAL_PENT_CLASS_TEMPLATE = """

class {name}(generated.{name}Generated):
    pass
"""

MANUAL_ROOT_CLASS = """

class Root(generated.QueryGenerated, generated.MutationGenerated):
    def __init__(self, context):
        self.__context = context

    @property
    def context(self):
        return self.__context
"""


def append_to_file(path, text):
    with open(path, 'a') as fobj:
        fobj.write(text)


def append_to_pents(document_ast, directory):
    pents_path = os.path.join(directory, 'pent', 'pents.py')
    pents_text = read_file(pents_path)
    written_once = False

    pattern = r'^class Root\('
    if not re.search(pattern, pents_text, re.MULTILINE):
        append_to_file(pents_path, MANUAL_ROOT_CLASS)

    for pent_type in types_not_in_file(document_ast.pents(), pents_text):
        written_once = True
        class_text = MANUAL_PENT_CLASS_TEMPLATE.format(name=pent_type.name)
        append_to_file(pents_path, class_text)

    if written_once:
        append_to_file(pents_path, '\n')


MANUAL_PENT_MUTATION_DATA_CLASS_TEMPLATE = """

class {name}(generated.{name}Generated):
    pass
"""

MANUAL_PENT_PAYLOAD_CLASS_TEMPLATE = """

class {name}(PentMutationPayload, generated.{name}DataMixin):
    pass
"""


def types_not_in_file(types, file_text):
    for ttype in types:
        name = ttype.name
        pattern = r'^class ' + name + r'\('
        if not re.search(pattern, file_text, re.MULTILINE):
            yield ttype


def append_to_mutations(document_ast, directory):
    mutations_path = os.path.join(directory, 'pent', 'mutations.py')
    mutations_text = read_file(mutations_path)
    written_once = False
    for data_type in types_not_in_file(document_ast.pent_mutation_datas(), mutations_text):
        written_once = True
        class_text = MANUAL_PENT_MUTATION_DATA_CLASS_TEMPLATE.format(name=data_type.name)
        append_to_file(mutations_path, class_text)

    for payload_type in types_not_in_file(document_ast.pent_payloads(), mutations_text):
        written_once = True
        check.invariant(len(payload_type.fields) == 1, 'Payload type should only have one field')
        out_field = payload_type.fields[0]
        payload_class_text = MANUAL_PENT_PAYLOAD_CLASS_TEMPLATE.format(
            name=payload_type.name, field_name=out_field.python_name
        )
        append_to_file(mutations_path, payload_class_text)

    if written_once:
        append_to_file(mutations_path, '\n')


def rescaffold_graphql(graphql_file_path, directory, module_name):
    graphql_text = read_file(graphql_file_path)
    document_ast = parse_grapple(graphql_text)
    module_dir = os.path.join(directory, module_name)

    create_scaffolding(directory, module_name)
    overwrite_generated_files(module_dir, document_ast)
    append_to_pents(document_ast, module_dir)
    append_to_mutations(document_ast, module_dir)
