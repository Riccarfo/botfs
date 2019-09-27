#!/usr/bin/env python3
""" Discord bot for faceswap """

import logging
from time import sleep

from commands import fs_bot
from scraper import faq_cache
from utils import get_token

logger = logging.getLogger(__name__)  # pylint: disable=invalid-name

if __name__ == "__main__":
    while True:
        # Wait for FAQ Cache
        if faq_cache.loaded.is_set():
            break
        sleep(1)

    @fs_bot.event
    async def on_ready():
        """ Log facebot startup """
        logger.info("Logged in (client_name: %sm client_id: %s",
                    fs_bot.user.name, fs_bot.user.id)

    fs_bot.run(get_token())
