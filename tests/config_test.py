from PyQt5.QtWidgets import QDialog, QFileDialog, QApplication, QMessageBox

from INCode.config import Config
from INCode.entrydialog import EntryDialog
from INCode.models import Callable, CompilationDatabases, Index
from INCode.diagramconfiguration import DiagramConfiguration, CallableTreeItem
from tests.test_environment_generation import build_index_with_file, directory, \
    generate_project, local_and_xref_dep, two_translation_units, two_files_with_classes, build_index
from clang.cindex import CursorKind
from unittest.mock import MagicMock, PropertyMock, patch
import os.path


def setup_config(directory, reset=True):
    config_file = os.path.join(directory, "config.ini")
    if reset and os.path.exists(config_file):
        os.remove(config_file)
    return Config(config_file)


def test__config__load_local_only__default_is_none(directory):
    config = setup_config(directory)
    assert config.load(Config.LOCAL_ONLY) is None


def test__config__enable_local_only__value_is_true(directory):
    config = setup_config(directory)
    config.store(Config.LOCAL_ONLY, True)
    assert config.load(Config.LOCAL_ONLY) is True


def test__config__change_and_reload__same_values(directory):
    config = setup_config(directory)
    config.store(Config.LOCAL_ONLY, False)

    new_config = setup_config(directory, False)
    assert new_config.load(Config.LOCAL_ONLY) is False


def test__config__save_values__changes_stored_in_file(directory):
    config = setup_config(directory)
    config.store(Config.LOCAL_ONLY, True)
    assert os.path.exists(config.file_name_)

    expected_result = "[DEFAULT]\n{} = True".format(Config.LOCAL_ONLY)
    assert expected_result in open(config.file_name_, "r").read()


def test__config__parsing_error__ignore_stored_values(directory):
    config_file = os.path.join(directory, "config.ini")
    if os.path.exists(config_file):
        os.remove(config_file)
    config = Config(config_file)
    config.store(Config.LOCAL_ONLY, True)

    with open(config_file, "w+") as file:
        file.write("\nCause Parsing Error")

    assert Config(config_file).load(Config.LOCAL_ONLY) is None
