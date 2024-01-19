import logging
import logging.handlers
import sys


def init_logging(log_filename, to_sysout):
    # workaround to save log to file (some import sets its handlers then saving to file doesn't work)
    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)

    logger = logging.getLogger()
    if to_sysout:
        logging_handler = logging.StreamHandler()
        logger.setLevel(logging.DEBUG)
    else:
        logging_handler = logging.handlers.TimedRotatingFileHandler(str(log_filename), when="midnight")
        logger.setLevel(logging.INFO)
    logging_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logger.addHandler(logging_handler)
    sys.excepthook = lambda exc, value, traceback: \
        logging.exception('Uncaught exception: {}'.format(value), exc_info=(exc, value, traceback))
    return logger
