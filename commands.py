#!/usr/bin/env python3
""" Commands for faceswap Discord bot """

import logging

from discord.ext.commands import Bot, has_any_role
from discord import Embed
from utils import format_message, get_def, get_roles, get_task, init_command, load_lookups
from scraper import faq_cache
logger = logging.getLogger(__name__)  # pylint: disable=invalid-name
fs_bot = Bot(command_prefix=("?", "!"))  # pylint: disable=invalid-name


@fs_bot.command(name="dfl", pass_context=True, **get_def("dfl"))
@has_any_role(*get_roles())
async def dfl(context):
    """ Output that we don't support DFL """
    lookup, at_users, _ = await init_command(context)
    msg = format_message(lookup["msg"], at_users)
    await context.send(msg)


@fs_bot.command(name="donate", pass_context=True, **get_def("donate"))
@has_any_role(*get_roles())
async def donate(context):
    """ Display donation messages """
    lookup, at_users, message = await init_command(context)

    content = dict()
    for key, val in lookup["tasks"].items():
        kwargs = dict(embed=dict(title=val["title"], type="rich"),
                      author=dict(name=val["name"], icon_url=val["icon"]))
        if "url" in val:
            kwargs["embed"]["url"] = val["url"]
            kwargs["author"]["url"] = val["url"]
        embed = Embed(**kwargs["embed"])
        embed.set_thumbnail(url=val["thumbnail"])
        embed.set_author(**kwargs["author"])

        if val.get("fields", None) is not None:
            for field in val["fields"]:
                embed.add_field(inline=False, **field)
        content[key] = embed
    logger.info("donator content: %s", content)

    donatee, _ = get_task(message, list(content.keys()))

    msg = format_message(lookup["msg"], at_users)
    await context.send(msg)
    await context.send(embed=content.pop("patreon"))

    if donatee != "patreon":
        embeds = [content[donatee]] if donatee else [content[key] for key in list(content.keys())]
        msg = ("Alternatively you can give a one off donation to any of our Devs below:")
        await context.send(msg)
        for embed in embeds:
            await context.send(embed=embed)


@fs_bot.command(name="faqs", pass_context=True, **get_def("faqs"))
@has_any_role(*get_roles())
async def faqs(context):
    """ Link to FAQs """
    lookup, at_users, message = await init_command(context)

    is_task = True
    tasks = faq_cache.contents
    if "search" in message:
        is_task = False
        search_term = " ".join(message[message.index("search") + 1:])
        logger.info("search_term: %s", search_term)
        if not search_term:
            is_task = True
            task = None
        else:
            task = faq_cache.search(search_term)
            logger.info("results: %s", task)
            if len(task) > lookup["results"]:
                logger.info("Too many results. Limiting: %s / %s",
                            lookup["results"], len(task))
                task = None
            if not task:
                is_task = True
                task = None
    else:
        task, _ = get_task(message, list(tasks.keys()))
    logger.info("final task: %s", task)
    if is_task:
        url = lookup["url"] if task is None else lookup["url"] + tasks[task]
        section = "on" if task is None else "in the {} section of".format(task.title())
        msg = "Your question is answered {} our FAQ page at: {}".format(section, url)
        msg = format_message(msg, at_users)
    else:
        urls = "\n\t".join(["`{}`: {}".format(val, lookup["url"] + key)
                            for key, val in task.items()])
        msg = ("Your question is answered on our FAQ page. Try one of these answers related to "
               "the term `{}`: \n\t{}".format(search_term, urls))
        msg = format_message(msg, at_users)
    await context.send(msg)


@fs_bot.command(name="forums", pass_context=True, **get_def("forums"))
@has_any_role(*get_roles())
async def forums(context):
    """ Link to the forums """
    lookup, at_users, message = await init_command(context)
    task, _ = get_task(message, lookup["tasks"])
    ext = "index.php" if task is None else "viewforum.php?f={}".format(lookup["tasks"][task])
    section = "" if task is None else "the {} section of ".format(task.title())
    msg = "You should check out {}our Forum at: {}".format(section, lookup["url"] + ext)
    msg = format_message(msg, at_users)
    await context.send(msg)


@fs_bot.command(name="guide", pass_context=True, **get_def("guide"))
@has_any_role(*get_roles())
async def guide(context):
    """ Link to guide on the forum """
    lookup, at_users, message = await init_command(context)
    task, _ = get_task(message, list(lookup["tasks"].keys()))
    if not task:
        return
    msg = "There's a guide for {} here: {}".format(task.title(),
                                                   lookup["url"] + lookup["tasks"][task])
    msg = format_message(msg, at_users)
    await context.send(msg)


@fs_bot.command(name="log", pass_context=True, **get_def("log"))
@has_any_role(*get_roles())
async def log(context):
    """ Request a crash report """
    lookup, at_users, _ = await init_command(context)
    msg = format_message(lookup["msg"], at_users)
    await context.send(msg)


@fs_bot.command(name="refresh", pass_context=True, **get_def("refresh"))
@has_any_role(*get_roles())
async def refresh(context):
    """ Refresh the FAQ and lookup caches """
    logger.info("command: refresh, call: %s", context.message)
    await context.message.delete()
    faq_cache.refresh_cache()
    load_lookups()
    msg = "FAQs and Lookups cache has been refreshed"
    logger.info(msg)
    await context.send(msg)


@fs_bot.command(name="search", pass_context=True, **get_def("search"))
@has_any_role(*get_roles())
async def search(context):
    """ Search the forum command """
    lookup, at_users, message = await init_command(context)
    terms = None
    url = lookup["url"]
    if len(message) > 1:
        terms = "+".join(message[1:])
        url += "?keywords={}".format(terms)

    if terms is None:
        results = ""
    else:
        results = ". Here are the results for `{}`".format(" ".join(terms.split("+")))
    msg = "You should try the Search page at our forum{}: {}".format(results, url)
    msg = format_message(msg, at_users)
    await context.send(msg)


@fs_bot.command(name="support", pass_context=True, **get_def("support"))
@has_any_role(*get_roles())
async def support(context):
    """ Support section of forum command """
    lookup, at_users, message = await init_command(context)
    task, _ = get_task(message, list(lookup["tasks"].keys()))
    url = "{}{}".format(lookup["url"], "3" if task is None else lookup["tasks"][task])
    section = "in" if task is None else "in the {} section of".format(task.title())
    msg = format_message("This question has been asked and answered {} our Support Forum at: "
                         "{}".format(section, url), at_users)
    await context.send(msg)


@fs_bot.command(name="sysinfo", pass_context=True, **get_def("sysinfo"))
@has_any_role(*get_roles())
async def sysinfo(context):
    """ Output System Information """
    lookup, at_users, _ = await init_command(context)
    msg = format_message(lookup["msg"], at_users)
    await context.send(msg)

@fs_bot.command(name="tag", pass_context=True, **get_def("tag"))
@has_any_role(*get_roles())
async def tag(context):
    """ Tag search  command """
    lookup, at_users, message = await init_command(context)
    url = lookup["url"]

    if len(message) != 2:
        logger.debug("No or multiple tags provided")
        return

    tag = message[1]
    url += tag

    msg = "You should try these posts tagged `{}` at our forum: {}".format(tag, url)
    msg = format_message(msg, at_users)
    await context.send(msg)
