#!/usr/bin/env python3
""" Utility functions for faceswap Discord bot """
from __future__ import annotations
import json
import logging
import os
import sys
import typing as T

from log_tools import log_setup

if T.TYPE_CHECKING:
    from discord.ext.commands.context import Context

log_setup()
logger = logging.getLogger(__name__)  # pylint: disable=invalid-name
_LOOKUP: T.Optional[T.Dict[str, T.Dict[str, T.Any]]] = None


def load_lookups() -> None:
    """ Load the lookups """
    global _LOOKUP  # pylint: disable=global-statement
    pypath = os.path.dirname(os.path.realpath(sys.argv[0]))
    f_name = os.path.join(pypath, "lookup.json")
    logger.info("Loading lookups from: %s", f_name)
    with open(f_name, "r", encoding="utf-8") as conf:
        _LOOKUP = json.load(conf)
    logger.info("Loaded lookups: %s", _LOOKUP)


load_lookups()


def get_token() -> str:
    """ Return the API Token """
    assert _LOOKUP is not None
    return _LOOKUP["global"]["token"]


def get_roles() -> T.Tuple[str, ...]:
    """ Return the groups permitted to call the command """
    assert _LOOKUP is not None
    return tuple(_LOOKUP["global"]["roles"])


def get_def(command: str) -> T.Dict[str, T.Any]:
    """ Return the command definition for given command name """
    assert _LOOKUP is not None
    return _LOOKUP[command]["def"]


async def init_command(context: Context) -> T.Tuple[T.Dict[str, T.Any], T.List[str], T.List[str]]:
    """ Init the command
    Log the call
    Delete the command message
    return lookup, at_users and split message
    """
    assert _LOOKUP is not None
    command = sys._getframe(1).f_code.co_name  # pylint: disable=protected-access
    logger.info("command: %s, call: %s", command, context.message)
    await context.message.delete()
    lookup = _LOOKUP[command]
    at_users, message = get_at_users(context.message.content.split())
    return lookup, at_users, message


def get_at_users(message: T.List[str]) -> T.Tuple[T.List[str], T.List[str]]:
    """ Pop the users from the message list into their own list """
    at_users = [msg for msg in message if msg.startswith("<@")]
    message = [msg for msg in message if not msg.startswith("<@")]
    logger.info("at_users: '%s', message: %s", at_users, message)
    return at_users, message


def get_task(message: T.List[str], tasks: T.List[str]) -> T.Tuple[T.Optional[str], T.List[str]]:
    """ Pop the task from the message list and return as string """
    tasks = [task.lower() for task in tasks]
    task = None
    for idx, msg in enumerate(message):
        if msg.lower() in tasks:
            task = message.pop(idx).lower()
            break
    logger.info("task: '%s', message: %s", task, message)
    return task, message


def format_message(message: str, at_users: T.Optional[T.List[str]] = None) -> str:
    """ Format the given message with or without at_users """
    first, rest = message[:1], message[1:]
    first = f"Hey {', '.join(at_users)}, {first.lower()}" if at_users else first.upper()
    msg = first + rest
    logger.info("formatted message: '%s'", msg)
    return msg
