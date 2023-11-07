#!/usr/bin/env python3
""" Commands for faceswap Discord bot """
from __future__ import annotations
import asyncio
import logging
import sys
import typing as T

import discord
from discord.ext.commands import Bot, has_any_role
from discord import Embed, Intents
from utils import format_message, get_def, get_roles, get_task, init_command, load_lookups
from scraper import faq_cache

if T.TYPE_CHECKING:
    from discord.ext.commands.context import Context
    from discord.automod import AutoModAction


logger = logging.getLogger(__name__)

INTENTS = Intents.default()
INTENTS.message_content = True
INTENTS.members = True

FS_BOT = Bot(intents=INTENTS, command_prefix=("?", "!", "/"))


# COMMANDS

@FS_BOT.command(name="dfl", pass_context=True, **get_def("dfl"))
@has_any_role(*get_roles())
async def dfl(context: Context) -> None:
    """ Output that we don't support DFL """
    lookup, at_users, _ = await init_command(context)
    msg = format_message(lookup["msg"], at_users)
    await context.send(msg)


@FS_BOT.command(name="donate", pass_context=True, **get_def("donate"))
@has_any_role(*get_roles())
async def donate(context: Context) -> None:
    """ Display donation messages """
    lookup, at_users, message = await init_command(context)

    content = {}
    for key, val in lookup["tasks"].items():
        kwargs = {"embed": {"title": val["title"], "type": "rich"},
                  "author": {"name": val["name"], "icon_url": val["icon"]}}
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
        msg = "Alternatively you can give a one off donation to any of our Devs below:"
        await context.send(msg)
        for embed in embeds:
            await context.send(embed=embed)


@FS_BOT.command(name="faqs", pass_context=True, **get_def("faqs"))
@has_any_role(*get_roles())
async def faqs(context: Context) -> None:
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
        section = "on" if task is None else f"in the {task.title()} section of"
        msg = f"Your question is answered {section} our FAQ page at: {url}"
        msg = format_message(msg, at_users)
    else:
        assert task is not None
        urls = "\n\t".join([f"`{val}`: {lookup['url'] + key}"
                            for key, val in task.items()])
        msg = ("Your question is answered on our FAQ page. Try one of these answers related to "
               f"the term `{search_term}`: \n\t{urls}")
        msg = format_message(msg, at_users)
    await context.send(msg)


@FS_BOT.command(name="forums", pass_context=True, **get_def("forums"))
@has_any_role(*get_roles())
async def forums(context: Context) -> None:
    """ Link to the forums """
    lookup, at_users, message = await init_command(context)
    task, _ = get_task(message, lookup["tasks"])
    ext = "index.php" if task is None else f"viewforum.php?f={lookup['tasks'][task]}"
    section = "" if task is None else f"the {task.title()} section of "
    msg = f"You should check out {section}our Forum at: {lookup['url'] + ext}"
    msg = format_message(msg, at_users)
    await context.send(msg)


@FS_BOT.command(name="guide", pass_context=True, **get_def("guide"))
@has_any_role(*get_roles())
async def guide(context: Context) -> None:
    """ Link to guide on the forum """
    lookup, at_users, message = await init_command(context)
    task, _ = get_task(message, list(lookup["tasks"].keys()))
    if not task:
        return
    msg = f"There's a guide for {task.title()} here: {lookup['url'] + lookup['tasks'][task]}"
    msg = format_message(msg, at_users)
    await context.send(msg)


@FS_BOT.command(name="log", pass_context=True, **get_def("log"))
@has_any_role(*get_roles())
async def log(context: Context) -> None:
    """ Request a crash report """
    lookup, at_users, _ = await init_command(context)
    msg = format_message(lookup["msg"], at_users)
    await context.send(msg)


@FS_BOT.command(name="refresh", pass_context=True, **get_def("refresh"))
@has_any_role(*get_roles())
async def refresh(context: Context) -> None:
    """ Refresh the FAQ and lookup caches """
    logger.info("command: refresh, call: %s", context.message)
    await context.message.delete()
    faq_cache.refresh_cache()
    load_lookups()
    msg = "FAQs and Lookups cache has been refreshed"
    logger.info(msg)
    await context.send(msg)


@FS_BOT.command(name="search", pass_context=True, **get_def("search"))
@has_any_role(*get_roles())
async def search(context: Context) -> None:
    """ Search the forum command """
    lookup, at_users, message = await init_command(context)
    terms = None
    url = lookup["url"]
    if len(message) > 1:
        terms = "+".join(message[1:])
        url += f"?keywords={terms}"

    if terms is None:
        results = ""
    else:
        results = f". Here are the results for `{' '.join(terms.split('+'))}`"
    msg = f"You should try the Search page at our forum{results}: {url}"
    msg = format_message(msg, at_users)
    await context.send(msg)


@FS_BOT.command(name="support", pass_context=True, **get_def("support"))
@has_any_role(*get_roles())
async def support(context: Context) -> None:
    """ Support section of forum command """
    lookup, at_users, message = await init_command(context)
    task, _ = get_task(message, list(lookup["tasks"].keys()))
    url = f"{lookup['url']}{'3' if task is None else lookup['tasks'][task]}"
    section = "in" if task is None else f"in the {task.title()} section of"
    msg = format_message(f"This question has been asked and answered {section} our Support Forum "
                         f"at: {url}", at_users)
    await context.send(msg)


@FS_BOT.command(name="sysinfo", pass_context=True, **get_def("sysinfo"))
@has_any_role(*get_roles())
async def sysinfo(context: Context) -> None:
    """ Output System Information """
    lookup, at_users, _ = await init_command(context)
    msg = format_message(lookup["msg"], at_users)
    await context.send(msg)


@FS_BOT.command(name="tag", pass_context=True, **get_def("tag"))
@has_any_role(*get_roles())
async def tag(context: Context) -> None:
    """ Tag search  command """
    lookup, at_users, message = await init_command(context)
    url = lookup["url"]

    if len(message) != 2:
        logger.debug("No or multiple tags provided")
        return

    m_tag = message[1]
    url += m_tag

    msg = f"You should try these posts tagged `{m_tag}` at our forum: {url}"
    msg = format_message(msg, at_users)
    await context.send(msg)


#@FS_BOT.command(name="insightface", pass_context=True, **get_def("insightface"))
#async def insightface(context: Context) -> None:
#    """ Delete user message and notify user """
#    command = sys._getframe(1).f_code.co_name  # pylint: disable=protected-access
#    await context.message.delete()
#    logger.info("command: %s, call: %s", command, context.message)
#
#    msg = ("You appear to have landed up in the wrong Discord server. This is the Discord for "
#           "https://faceswap.dev. With a bit more work you will almost definitely get better "
#           "results with us than the Bot you were looking for. Perhaps you should stick around?")
#    user = [f"<@{context.message.author.id}>"]
#    msg = format_message(msg, user)
#    sent = await context.send(msg)
#    await asyncio.sleep(300)
#    await sent.delete()


@FS_BOT.command(name="nobot", pass_context=True, **get_def("nobot"))
@has_any_role(*get_roles())
async def nobot(context: Context) -> None:
    """ Delete the replied to user's message and notify we are not a bot """
    command = sys._getframe(1).f_code.co_name  # pylint: disable=protected-access
    await context.message.delete()
    logger.info("command: %s, call: %s", command, context.message)

    if context.message.reference is None or context.message.reference.message_id is None:
        logger.warning("No message replied to. Doing nothing")
        return

    channel = context.channel
    original_msg = await channel.fetch_message(context.message.reference.message_id)
    logger.info("Original Message: %s", original_msg)
    await original_msg.delete()

    msg = ("You appear to have landed up in the wrong Discord server. This is the Discord for "
           "https://faceswap.dev. With a bit more work you will almost definitely get better "
           "results with us than the Bot you were looking for. Perhaps you should stick around?")

    user = [f"<@{original_msg.author.id}>"]
    msg = format_message(msg, user)
    sent = await context.send(msg)
    await asyncio.sleep(300)
    await sent.delete()


@FS_BOT.command(name="iwillnotusebots", pass_context=True, **get_def("iwillnotusebots"))
async def iwillnotusebots(context: Context) -> None:
    """ Give user full server access back """
    command = sys._getframe(1).f_code.co_name  # pylint: disable=protected-access
    await context.message.delete()
    logger.info("command: %s, call: %s", command, context.message)
    if context.channel.name != "bot-jail":
        return

    role = discord.utils.get(context.guild.roles, name="Bot Abuser")
    await context.message.author.remove_roles(role)


# EVENTS
@FS_BOT.event
async def on_automod_action(execution: AutoModAction):
    """ On AutoMod capture of someone trying to invoke InsightFace, handle the user:

    - Change role to 'Bot Abuser'
    - Move user to bot-jail
    - Send message explaining how to get out of jail
    """
    if execution.rule_id != 1171530119630831689:  # InsightFace Bot AutoMod rule
        return

    if execution.alert_system_message_id is None:  # AutoMod ephemeral response
        return

    if execution.member is None:
        return

    role = discord.utils.get(execution.guild.roles, name="Bot Abuser")
    channel = discord.utils.get(execution.guild.channels, name="bot-jail")

    await execution.member.add_roles(role)

    msg = ("You appear to have landed up in the wrong Discord server. This is the Discord for "
           "https://faceswap.dev. With a bit more work you will almost definitely get better "
           "results with us than the Bot you were looking for.\n\n**IMPORTANT PLEASE READ**\n"
           "Your access has been limited as this server does not support Bot commands.\n\n"
           f"Any further attempts to issue Bot commands will land you back in {channel.mention}."
           "\n\nYou can restore full access to this server by entering the command:\n\n"
           "`/IWillNotUseBots`\n\n----------------------------------\n ")

    user = [f"<@{execution.user_id}>"]
    msg = format_message(msg, user)
    await channel.send(msg)
