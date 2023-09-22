import logging
import sys
import time

log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)

log_once = logging.getLogger("logger_once")
log_once.setLevel(logging.DEBUG)


class LogMessageOnce(logging.Filter):
    """
    For component debug messages (activation, deactivation of ports, entering, leaving places etc)
    prevent msg flooding due to the loop
    """
    msg_logged = set()
    time_period = time.time()

    def filter(self, record):
        if time.time() - self.time_period >= 5:
            self.msg_logged = set()
            self.time_period = time.time()

        if record.msg in self.msg_logged:
            return False
        self.msg_logged.add(record.msg)
        return True


log_once.addFilter(LogMessageOnce())


def handle_exception(exc_type, exc_value, exc_traceback):
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return
    log.debug("Uncaught exception", exc_info=(exc_type, exc_value, exc_traceback))


sys.excepthook = handle_exception


def set_stdout_formatter(assembly_name):
    stdout_handler = logging.StreamHandler(stream=sys.stdout)
    stdout_handler.setFormatter(logging.Formatter(f"{assembly_name} - %(asctime)s %(message)s"))
    log.addHandler(stdout_handler)
    log_once.addHandler(stdout_handler)
