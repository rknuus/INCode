'''
Package install setup script.
'''

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

setup(
    name='INCode',
    version='0.0.1',
    description='INCode is an interactive diagram generator of C/C++ source code.',
    keywords='INCode, clang, llvm, diagram, generator',
    author='R. Knuus',
    author_email='rknuus@gmail.com',
    url='https://github.com/rknuus/INCode',
    download_url='https://github.com/rknuus/INCode/releases',
    license='GPL-3.0',
    packages=[
        'INCode'
    ],
    scripts=[
        'INCode/bin/INCode'
    ],
    install_requires=[
        'clang>=5.0'
    ],
    classifiers=[
        'Intended Audience :: Developers', 'Natural Language :: English', 'Programming Language :: Python :: 2'
    ],
    setup_requires=[
        'pytest-runner'
    ],
    tests_require=[
        'mock', 'pytest'
    ],
    long_description='''
INCode is an interactive diagram generator of C/C++ source code.
You specify an entry point, from where on INCode let's you navigate callables
(e.g. functions, methods, operators, lambdas etc.) and decide which ones to use
for sequence and class diagrams in plantuml format.
    ''')
