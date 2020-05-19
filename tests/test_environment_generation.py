from contextlib import contextmanager
# from unittest.mock import MagicMock
import os.path
import tempfile


@contextmanager
def generate_file(file, content):
    with tempfile.TemporaryDirectory() as fixture_directory:
        with open(os.path.join(fixture_directory, file), 'w') as file:
            file_name = file.name
            file.write(content)
        yield file_name
