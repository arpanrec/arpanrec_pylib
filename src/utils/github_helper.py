"""
Module to manage GitHub Action Secrets.
"""

import base64
import os
from typing import Optional, Dict

import requests
from github import Auth, Github


# pylint: disable=too-many-arguments,too-many-locals,too-many-return-statements,too-many-branches,too-many-statements,too-many-positional-arguments
def github_variable(
    pat: str,
    name: str,
    unencrypted_value: str,
    environment: Optional[str] = None,
    repository: Optional[str] = None,
    organization: Optional[str] = None,
    is_base64_encoded: bool = False,
    visibility: Optional[str] = None,
    is_secret: bool = True,
    state: str = "present",
    api_ep: str = "https://api.github.com",
) -> None:
    """
    Performs Create, Read, Update, and Delete (CRUD) operations.

    This function is responsible for performing CRUD operations
    on GitHub Action Secrets based on the provided parameters.

    Parameters:
        api_ep: (str): The GitHub API endpoint. Optional.
        pat: (str): The personal access token (PAT) to authenticate with GitHub. Required.
        is_secret: (bool): Whether the value is a secret. Optional.
        environment: (str): The environment to which the secret belongs. Optional.
        unencrypted_value: (str): The unencrypted value of the secret. Required.
        is_base64_encoded: (bool): Whether to base64 encode the secret. Optional.
        visibility (str): The visibility of the secret. Optional.
        state (str): The state of the secret. Optional.
        repository (str): The name of the repository. Optional.
        organization (str): The organization of the repository. Optional.
        name (str): The name of the secret. Required.

    Returns:
        dict: A dictionary containing the results of the CRUD operation.
    """

    if repository and organization:
        raise ValueError("repository and organization are mutually exclusive")

    if repository and visibility:
        raise ValueError("repository and visibility are mutually exclusive")

    if not repository and not organization:
        raise ValueError("repository or organization is mandatory")

    if organization and environment:
        raise ValueError("organization and environment are mutually exclusive")

    if state not in ("present", "absent"):
        raise ValueError(f"state should be either present or absent, {state}")

    if visibility and visibility not in ["private", "all", "selected"]:
        raise ValueError("visibility should in 'private', 'all', 'selected'")

    if state == "absent" and unencrypted_value:
        raise ValueError("unencrypted_value is not required for state absent")

    if state == "absent" and is_base64_encoded:
        raise ValueError("is_base64_encoded is not required for state absent")

    if state == "absent" and visibility:
        raise ValueError("visibility is not required for state absent")

    if state == "present" and not unencrypted_value:
        raise ValueError("unencrypted_value is required for state present")

    if is_base64_encoded:
        unencrypted_value = base64.b64encode(unencrypted_value.encode()).decode()

    if not visibility:
        visibility = "all"

    auth = Auth.Token(pat)
    github = Github(base_url=api_ep, auth=auth)
    if state == "present":
        if repository:
            repo = github.get_repo(repository)
            if environment:
                env = repo.get_environment(environment)
                if is_secret:
                    env.create_secret(name, unencrypted_value)
                else:
                    env.create_variable(name, unencrypted_value)
            else:
                if is_secret:
                    repo.create_secret(name, unencrypted_value)
                else:
                    repo.create_variable(name, unencrypted_value)
        else:
            org = github.get_organization(str(organization))
            if is_secret:
                org.create_secret(name, unencrypted_value, visibility)
            else:
                org.create_variable(name, unencrypted_value, visibility)
    else:
        if repository:
            repo = github.get_repo(repository)
            if environment:
                env = repo.get_environment(environment)
                if is_secret:
                    env.delete_secret(name)
                else:
                    env.delete_variable(name)
            else:
                if is_secret:
                    repo.delete_secret(name)
                else:
                    repo.delete_variable(name)
        else:
            raise ValueError("organization delete not supported")


def github_release_search(
    github_repo: str,
    github_token: Optional[str] = os.getenv("GITHUB_TOKEN", None),
    github_api_url: str = "https://api.github.com",
    prefix: Optional[str] = None,
    suffix: Optional[str] = None,
    contains: Optional[str] = None,
    max_pages: int = 100,
    timeout: int = 10,
) -> str:
    """
    Search for the latest release in a GitHub repository.

    Args:
        github_repo (str): The GitHub repository to search.
        github_token (str):
            The GitHub token to authenticate with. Optional.
            Default is the `GITHUB_TOKEN` environment variable.
        github_api_url (str): The GitHub API URL. Optional. Default is "https://api.github.com".
        prefix (str): The prefix of the tag to search for. Optional.
        suffix (str): The suffix of the tag to search for. Optional.
        contains (str): The substring that the tag should contain. Optional.
        max_pages (int): The maximum number of pages to search. Optional. Default is 100.
        timeout (int): The timeout in seconds. Optional. Default is 10.

    Raises:
        ValueError:
            If no matching tag is found.
            If no releases are found for the repository.

    Returns:
        str: The latest tag in the GitHub repository.
    """

    tag_version: Optional[str] = None
    url: str = f"{github_api_url}/repos/{github_repo}/releases"
    headers: Dict[str, str] = {
        "Accept": "application/vnd.github.v3+json",
        "X-GitHub-Api-Version": "2022-11-28"
    }

    if github_token:
        headers["Authorization"] = f"Bearer {github_token}"

    params: Dict[str, str | int] = {
        "per_page": 50,
    }
    page_num: int = 0

    while page_num < max_pages:
        page_num += 1
        params["page"] = page_num

        response = requests.get(url, headers=headers, params=params, timeout=timeout)
        response.raise_for_status()
        if response.status_code != 200:
            raise ValueError(f"Error fetching releases: {response.status_code}, {response.text}")
        response_data = response.json()
        if len(response_data) == 0:
            raise ValueError(f"No releases found for {github_repo}")
        for release in response_data:
            tag_name = release.get("tag_name")

            if tag_name:
                if prefix and not tag_name.startswith(prefix):
                    continue

                if suffix and not tag_name.endswith(suffix):
                    continue

                if contains and contains not in tag_name:
                    continue

                tag_version = tag_name
                break

        if tag_version:
            break

    if not tag_version:
        raise ValueError(f"No matching tag found for {github_repo}")

    return tag_version
