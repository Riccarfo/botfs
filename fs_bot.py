#!/usr/bin/env python3
""" Discord bot for faceswap """

import logging
from time import sleep

from commands import FS_BOT
from scraper import faq_cache
from utils import get_token

logger = logging.getLogger(__name__)  # pylint: disable=invalid-name

if __name__ == "__main__":
    while True:
        # Wait for FAQ Cache
        if faq_cache.loaded.is_set():
            break
        sleep(1)

    @FS_BOT.event
    async def on_ready() -> None:
        """ Log facebot startup """
        assert FS_BOT.user is not None
        logger.info("Logged in (client_name: %s, client_id: %s",
                    FS_BOT.user.name, FS_BOT.user.id)

    FS_BOT.run(get_token())
