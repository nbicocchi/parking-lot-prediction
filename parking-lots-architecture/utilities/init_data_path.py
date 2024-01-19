from pathlib import Path


def paths_exist():
    return path.exists() and log_path.exists()


def create_paths():
    if not path.exists():
        path.mkdir()
    if not log_path.exists():
        log_path.mkdir()


def get_data_path():
    return path


def get_log_path():
    return log_path


def get_log_filename(module_name):
    return log_path.joinpath(module_name + '.log')


path = Path.home().joinpath('.bosch_pls')
log_path = path.joinpath('log')
if not paths_exist():
    create_paths()
