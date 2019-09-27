#!/usr/bin/env python3
""" Utility functions for faceswap Discord bot """
import json
import logging
import os
import sys

from log_tools import log_setup

log_setup()
logger = logging.getLogger(__name__)  # pylint: disable=invalid-name
_LOOKUP = None


def load_lookups():
    """ Load the lookups """
    global _LOOKUP  # pylint: disable=global-statement
    pypath = os.path.dirname(os.path.realpath(sys.argv[0]))
    f_name = os.path.join(pypath, "lookup.json")
    logger.info("Loading lookups from: %s", f_name)
    with open(f_name, "r") as conf:
        _LOOKUP = json.load(conf)
    logger.info("Loaded lookups: %s", _LOOKUP)


load_lookups()


def get_token():
    """ Return the API Token """
    return _LOOKUP["global"]["token"]


def get_roles():
    """ Return the groups permitted to call the command """
    return tuple(_LOOKUP["global"]["roles"])


def get_def(command):
    """ Return the command definition for given command name """
    return _LOOKUP[command]["def"]


async def init_command(context):
    """ Init the command
    Log the call
    Delete the command message
    return lookup, at_users and split message
    """
    command = sys._getframe(1).f_code.co_name  # pylint: disable=protected-access
    logger.info("command: %s, call: %s", command, context.message)
    await context.message.delete()
    lookup = _LOOKUP[command]
    at_users, message = get_at_users(context.message.content.split())
    return lookup, at_users, message


def get_at_users(message):
    """ Pop the users from the message list into their own list """
    at_users = [msg for msg in message if msg.startswith("<@")]
    message = [msg for msg in message if not msg.startswith("<@")]
    logger.info("at_users: '%s', message: %s", at_users, message)
    return at_users, message


def get_task(message, tasks):
    """ Pop the task from the message list and return as string """
    tasks = [task.lower() for task in tasks]
    task = None
    for idx, msg in enumerate(message):
        if msg.lower() in tasks:
            task = message.pop(idx).lower()
            break
    logger.info("task: '%s', message: %s", task, message)
    return task, message


def format_message(message, at_users=None):
    """ Format the given message with or without at_users """
    first, rest = message[:1], message[1:]
    first = "Hey {}, {}".format(", ".join(at_users), first.lower()) if at_users else first.upper()
    msg = first + rest
    logger.info("formatted message: '%s'", msg)
    return msg
