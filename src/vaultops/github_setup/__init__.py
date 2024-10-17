"""
This module provides functionality to set up GitHub access for the bot and users.

Functions:
    setup_github(vault_ha_client: VaultHaClient) -> None:
        Sets up GitHub access for the bot and users by adding vault access to GitHub user repositories
        and adding a GPG key to the bot GitHub account.

Modules:
    github: Contains functions to add vault access to GitHub.
    github_bot: Contains functions to add GPG keys to the bot GitHub account.
"""

import logging

from ..models.ha_client import VaultHaClient
from .github import add_vault_access_to_github
from .github_bot import add_gpg_to_bot_github

LOGGER = logging.getLogger(__name__)


def setup_github(vault_ha_client: VaultHaClient) -> None:
    """
    Setup GitHub access for the bot and users.
    """

    LOGGER.info("Adding vault access to GitHub user repositories")
    add_vault_access_to_github(vault_ha_client=vault_ha_client)

    LOGGER.info("Add gpg key to bot GitHub account")
    add_gpg_to_bot_github(vault_ha_client=vault_ha_client)
