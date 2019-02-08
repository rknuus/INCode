import pytest
import os.path
import tempfile
from unittest.mock import MagicMock
from INCode.models import CompilationDatabases, Index


def generate_project(directory, files):
    for file, content in files.items():
        generate_file(directory, file, content)
    generate_compilation_database(directory, files.keys())


def generate_file(directory, file, content):
    with open(os.path.join(directory, file), 'w') as file:
        file.write(content)


def generate_compilation_database(directory, source_files):
    entries = []
    for source_file in source_files:
        entry = ('{ "directory": "%(directory)s", "command": "clang++ -o %(source_file)s.o -c %(source_file)s", '
                 '"file": "%(source_file)s" }' % locals())
        entries.append(entry)
    content = '[{}]'.format(','.join(entries))
    generate_file(directory, 'compile_commands.json', content)


@pytest.fixture(scope='module')
def directory():
    with tempfile.TemporaryDirectory() as fixture_directory:
        yield fixture_directory


@pytest.fixture(scope='module')
def two_translation_units():
    with tempfile.TemporaryDirectory('two_translation_units') as directory:
        generate_project(directory, {
            os.path.join(directory, 'dependency.h'): '''
                      #pragma once
                      void a();
                      ''',
            os.path.join(directory, 'dependency.cpp'): '''
                      #include "dependency.h"
                      void a() {}
                      ''',
            os.path.join(directory, 'cross_tu_referencing_function.cpp'): '''
                      #include "dependency.h"
                      void b() {
                          a();
                      }
                      '''
        })
        yield directory


@pytest.fixture(scope='module')
def two_files_with_classes():
    with tempfile.TemporaryDirectory('two_files_with_classes') as directory:
        generate_project(directory, {
            os.path.join(directory, 'a.h'): '''
                      #pragma once
                      class A {
                      public:
                        void a();
                      }
                      ''',
            os.path.join(directory, 'a.cpp'): '''
                      #include "a.h"
                      #include "b.h"
                      void A::a() {
                        B b;
                        b.b()
                      }
                      ''',
            os.path.join(directory, 'b.h'): '''
                      #pragma once
                      class B {
                      public:
                        void b();
                      }
                      ''',
            os.path.join(directory, 'b.cpp'): '''
                      #include "b.h"
                      void B::b() {}
                      '''
        })
        yield directory


@pytest.fixture(scope='module')
def local_and_xref_dep():
    with tempfile.TemporaryDirectory('local_and_xref_dep') as directory:
        generate_project(directory, {
            os.path.join(directory, 'dependency.h'): '''
                      #pragma once
                      void a();
                      ''',
            os.path.join(directory, 'dependency.cpp'): '''
                      #include "dependency.h"
                      void c() {}
                      void a() {
                          c();
                      }
                      ''',
            os.path.join(directory, 'cross_tu_referencing_function.cpp'): '''
                      #include "dependency.h"
                      void b() {
                          a();
                      }
                      '''
        })
        yield directory


def build_index(db=CompilationDatabases(), common_path=''):
    Index(db).common_path = common_path
    return Index()


def build_index_with_file(directory, file_name='empty.cpp', file_content=''):
    file_path = os.path.join(directory, file_name)
    generate_project(directory, {file_path: file_content})
    db = CompilationDatabases()
    db.add_compilation_database(directory)
    index = build_index(db, directory+"/")
    return index.load(file_path)
