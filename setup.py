import sys

from setuptools import find_packages, setup

# cargo-culting
if sys.version_info[0] < 3:
    import __builtin__ as builtins
else:
    import builtins

# ???? uncomment once python versioning system is understood
# version = __import__('graphene').get_version()

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
    url='https://github.com/schrockn/graphscale',
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
    # tests_require=tests_require,
    # extras_require={
    #     'test': tests_require,
    #     #'django': [
    #     #    'graphene-django',
    #     #],
    #     #'sqlalchemy': [
    #     #    'graphene-sqlalchemy',
    #     #]
    # },
    # cmdclass={'test': PyTest},
)
