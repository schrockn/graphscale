import sys

from setuptools import find_packages, setup
from setuptools.command.test import test as TestCommand

# cargo-culting
if sys.version_info[0] < 3:
    import __builtin__ as builtins
else:
    import builtins

# ???? uncomment once python versioning system is understood
# version = __import__('graphene').get_version()

class PyTest(TestCommand):
    user_options = [('pytest-args=', 'a', "Arguments to pass to py.test")]

    def initialize_options(self):
        TestCommand.initialize_options(self)
        self.pytest_args = []

    def finalize_options(self):
        TestCommand.finalize_options(self)
        self.test_args = []
        self.test_suite = True

    def run_tests(self):
        # import here, cause outside the eggs aren't loaded
        import pytest
        errno = pytest.main(self.pytest_args)
        sys.exit(errno)

tests_require = [
    'pytest>=2.7.2',
    # 'pytest-benchmark',
    # 'pytest-cov',
    # 'snapshottest',
    # 'coveralls',
    # 'six',
    # 'mock',
    # 'pytz',
    # 'iso8601',
]

setup(
    name='graphscale',
    #version=version,

    # description='GraphQL Framework for Python',
    # long_description=open('README.rst').read(),

    # url='https://github.com/graphql-python/graphene',

    author='Nicholas Schrock',
    author_email='schrockn@gmail.com',

    license='MIT',

    #classifiers=[
    #    'Development Status :: 3 - Alpha',
    #    'Intended Audience :: Developers',
    #    'Topic :: Software Development :: Libraries',
    #    'Programming Language :: Python :: 2',
    #    'Programming Language :: Python :: 2.7',
    #    'Programming Language :: Python :: 3',
    #    'Programming Language :: Python :: 3.3',
    #    'Programming Language :: Python :: 3.4',
    #    'Programming Language :: Python :: 3.5',
    #    'Programming Language :: Python :: Implementation :: PyPy',
    #],

    #keywords='api graphql protocol rest relay graphene',

    packages=find_packages(exclude=['tests']),

    install_requires=[
        'pymysql',
        'six',
        'graphql-core',
        'redis',
        'iso8601',
    #    'graphql-relay>=0.4.5',
    #    'promise>=2.0',
    ],
    tests_require=tests_require,
    extras_require={
        'test': tests_require,
        #'django': [
        #    'graphene-django',
        #],
        #'sqlalchemy': [
        #    'graphene-sqlalchemy',
        #]
    },
    cmdclass={'test': PyTest},
)
