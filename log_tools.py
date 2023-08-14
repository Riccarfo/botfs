#!/usr/bin/env python3
""" Logging for faceswap Discord bot """

import logging
import os
import sys

from logging.handlers import TimedRotatingFileHandler


def log_setup() -> None:
    """ initial log set up.
     Check valid log level supplied and set log level """
    loglevel = logging.INFO
    numeric_level = loglevel
    if not isinstance(numeric_level, int):
        raise ValueError(f"Invalid log level: {loglevel} ({numeric_level})")

    logger = logging.getLogger()
    logger.setLevel(numeric_level)

    log_format = logging.Formatter("%(asctime)s %(processName)-15s %(threadName)-15s "
                                   "%(module)-15s %(funcName)-25s %(levelname)-8s %(message)s",
                                   datefmt="%m/%d/%Y %H:%M:%S")
    stream_log_format = logging.Formatter("%(asctime)s %(levelname)-8s %(message)s",
                                          datefmt="%m/%d/%Y %H:%M:%S")

    pypath = os.path.dirname(os.path.realpath(sys.argv[0]))
    log_path = os.path.join(pypath, "fs_bot.log")
    log_file = TimedRotatingFileHandler(log_path, when="midnight", backupCount=14)
    log_file.setFormatter(log_format)
    logger.addHandler(log_file)

    log_console = logging.StreamHandler()
    log_console.setFormatter(stream_log_format)
    logger.addHandler(log_console)

    logging.debug("Log level set to: %s", loglevel)
    logging.info('Started')
