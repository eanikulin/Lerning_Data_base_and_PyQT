# decors

import inspect
import logging
from functools import wraps
import sys


class FilenameFilter(logging.Filter):
    def __init__(self, filename):
        super().__init__()
        self.filename = filename

    def filter(self, record):
        record.filename = self.filename
        return True


class Log:
    def __init__(self, logger=None):
        self.logger = logger

    def __call__(self, func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            parent_func_name = inspect.currentframe().f_back.f_code.co_name
            module_name = inspect.currentframe().f_back.f_code.co_filename.split("/")[-1]
            if not self.logger:
                if 'client' in module_name:
                    self.logger = logging.getLogger(f"client_func")
                elif 'server' in module_name:
                    self.logger = logging.getLogger(f"server_func")
                else:
                    self.logger = logging.getLogger()
            self.logger.addFilter(FilenameFilter(module_name))
            self.logger.debug(f'Функция (метод) {func.__name__} вызвана из функции (метода) {parent_func_name} '
                              f'в модуле {module_name} с аргументами:'
                              f'{args}; {kwargs}')
            result = func(*args, **kwargs)
            return result

        return wrapper


def logs(logger):
    def decorator(func):
        @wraps(func)
        def decorated(*args, **kwargs):
            parent_func_name = inspect.currentframe().f_back.f_code.co_name
            module_name = inspect.currentframe().f_back.f_code.co_filename.split("/")[-1]
            logger.addFilter(FilenameFilter(module_name))
            logger.debug(f' {func.__name__} вызванах из функции {parent_func_name} '
                         f'в модуле {module_name} с аргументами: {args}; {kwargs}')
            res = func(*args, **kwargs)
            return res

        return decorated

    return decorator


# метод определения модуля, источника запуска.
if sys.argv[0].find('client') == -1:
    # если не клиент то сервер!
    logger = logging.getLogger('server')
else:
    # ну, раз не сервер, то клиент
    logger = logging.getLogger('client')


def log(func_to_log):
    def log_saver(*args, **kwargs):
        logger.debug(f'Была вызвана функция {func_to_log.__name__} c параметрами {args} , {kwargs}. Вызов из модуля '
                     f'{func_to_log.__module__}')
        ret = func_to_log(*args, **kwargs)
        return ret

    return log_saver


# метод определения модуля, источника запуска.
if sys.argv[0].find('client') == -1:
    # если не клиент то сервер!
    logger = logging.getLogger('server')
else:
    # ну, раз не сервер, то клиент
    logger = logging.getLogger('client')


def log(func_to_log):
    def log_saver(*args, **kwargs):
        logger.debug(f'Была вызвана функция {func_to_log.__name__} c параметрами {args} , {kwargs}. Вызов из модуля '
                     f'{func_to_log.__module__}')
        ret = func_to_log(*args, **kwargs)
        return ret

    return log_saver
