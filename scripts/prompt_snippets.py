#!/usr/bin/env python3
"""Helpers for managing LaunchDarkly AI Config prompt snippets.

A prompt snippet is a reusable, versioned chunk of prompt text stored at the
project level. It is referenced from an AI Config variation via
``{{snippet.<key>#<version>}}`` and rendered in by the LaunchDarkly AI SDK at
``agent_config()`` / ``completion_config()`` time.

This module exposes three things:

* :class:`PromptSnippetsClient` — thin wrapper around the LaunchDarkly REST API
  for CRUD on prompt snippets and patching variations to reference them.
* CLI subcommands — see ``python -m scripts.prompt_snippets --help``.
* Convenience helpers (``create``, ``update``, ``patch_instructions``,
  ``patch_messages``, ``references``) for use from other scripts.

All operations require ``LAUNCHDARKLY_PROJECT_KEY`` and
``LAUNCHDARKLY_ACCESS_TOKEN`` (or ``LAUNCHDARKLY_API_KEY``) in the environment
or .env file. The token must have AI Configs write permissions.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

import requests
from dotenv import load_dotenv

load_dotenv()


def _env_token() -> str:
    token = (
        os.getenv("LAUNCHDARKLY_ACCESS_TOKEN")
        or os.getenv("LAUNCHDARKLY_API_KEY")
        or os.getenv("LD_API_KEY")
    )
    if not token:
        raise RuntimeError(
            "No LaunchDarkly API token found. Set LAUNCHDARKLY_ACCESS_TOKEN, "
            "LAUNCHDARKLY_API_KEY, or LD_API_KEY in your environment / .env."
        )
    return token


def _env_project() -> str:
    pk = os.getenv("LAUNCHDARKLY_PROJECT_KEY")
    if not pk:
        raise RuntimeError("LAUNCHDARKLY_PROJECT_KEY is not set.")
    return pk


@dataclass
class PromptSnippetsClient:
    project_key: str
    token: str
    base: str = "https://app.launchdarkly.com/api/v2"

    @classmethod
    def from_env(cls) -> "PromptSnippetsClient":
        return cls(project_key=_env_project(), token=_env_token())

    def _headers(self) -> dict[str, str]:
        return {"Authorization": self.token, "Content-Type": "application/json"}

    def _snip_url(self, key: str | None = None) -> str:
        url = f"{self.base}/projects/{self.project_key}/ai-configs/prompt-snippets"
        return f"{url}/{key}" if key else url

    def _var_url(self, config_key: str, variation_key: str) -> str:
        return (
            f"{self.base}/projects/{self.project_key}/ai-configs/{config_key}"
            f"/variations/{variation_key}"
        )

    def get(self, snippet_key: str) -> dict[str, Any]:
        r = requests.get(self._snip_url(snippet_key), headers=self._headers())
        r.raise_for_status()
        return r.json()

    def create(
        self,
        key: str,
        name: str,
        text: str,
        description: str = "",
        tags: Iterable[str] = (),
    ) -> dict[str, Any]:
        """Create a snippet, or return the existing one if it already exists."""
        payload = {
            "key": key,
            "name": name,
            "text": text,
            "description": description,
            "tags": list(tags),
        }
        r = requests.post(self._snip_url(), headers=self._headers(), json=payload)
        if r.status_code == 201:
            return r.json()
        if r.status_code == 409:
            return self.get(key)
        r.raise_for_status()
        return r.json()

    def update(self, key: str, *, text: str | None = None, **fields: Any) -> dict[str, Any]:
        """Patch a snippet (creates a new version when ``text`` changes)."""
        body: dict[str, Any] = {}
        if text is not None:
            body["text"] = text
        body.update(fields)
        r = requests.patch(self._snip_url(key), headers=self._headers(), json=body)
        r.raise_for_status()
        return r.json()

    def references(self, key: str) -> dict[str, Any]:
        r = requests.get(f"{self._snip_url(key)}/references", headers=self._headers())
        r.raise_for_status()
        return r.json()

    def reference_token(self, key: str, version: int | None = None) -> str:
        if version is None:
            version = self.get(key)["version"]
        return "{{snippet." + key + "#" + str(version) + "}}"

    def patch_variation(
        self,
        config_key: str,
        variation_key: str,
        *,
        instructions: str | None = None,
        messages: list[dict[str, str]] | None = None,
        comment: str | None = None,
        **fields: Any,
    ) -> dict[str, Any]:
        """Update a variation. Only provided fields are touched."""
        body: dict[str, Any] = dict(fields)
        if instructions is not None:
            body["instructions"] = instructions
        if messages is not None:
            body["messages"] = messages
        if comment is not None:
            body["comment"] = comment
        r = requests.patch(
            self._var_url(config_key, variation_key),
            headers=self._headers(),
            data=json.dumps(body),
        )
        if not r.ok:
            raise RuntimeError(f"PATCH {variation_key} -> HTTP {r.status_code}: {r.text}")
        return r.json()


def _cmd_create(args: argparse.Namespace) -> None:
    text = (
        Path(args.text_file).read_text() if args.text_file else (args.text or sys.stdin.read())
    )
    client = PromptSnippetsClient.from_env()
    snip = client.create(
        key=args.key,
        name=args.name,
        text=text,
        description=args.description or "",
        tags=args.tag or (),
    )
    print(f"snippet `{snip['key']}` ready at version {snip['version']}")


def _cmd_show(args: argparse.Namespace) -> None:
    client = PromptSnippetsClient.from_env()
    print(json.dumps(client.get(args.key), indent=2))


def _cmd_refs(args: argparse.Namespace) -> None:
    client = PromptSnippetsClient.from_env()
    refs = client.references(args.key)
    print(f"{refs['totalCount']} references to `{refs['resourceKey']}`:")
    for item in refs["items"]:
        print(
            f"  • {item['aiConfigKey']}/{item['variationKey']} "
            f"(name: {item['variationName']!r}, snippet v{item['resourceVersion']})"
        )


def _cmd_patch_instructions(args: argparse.Namespace) -> None:
    client = PromptSnippetsClient.from_env()
    ref = client.reference_token(args.snippet, args.snippet_version)
    for vk in args.variation:
        client.patch_variation(
            args.config,
            vk,
            instructions=ref,
            comment=args.comment or f"Replace inline instructions with {ref}",
        )
        print(f"  ✅ {args.config}/{vk}: instructions -> {ref}")


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="prompt_snippets", description=__doc__)
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_create = sub.add_parser("create", help="Create (or upsert) a prompt snippet")
    p_create.add_argument("--key", required=True)
    p_create.add_argument("--name", required=True)
    p_create.add_argument("--description", default="")
    p_create.add_argument("--tag", action="append")
    g = p_create.add_mutually_exclusive_group()
    g.add_argument("--text", help="Inline snippet body")
    g.add_argument("--text-file", help="Path to file containing snippet body")
    p_create.set_defaults(func=_cmd_create)

    p_show = sub.add_parser("show", help="Show a snippet")
    p_show.add_argument("key")
    p_show.set_defaults(func=_cmd_show)

    p_refs = sub.add_parser("refs", help="List variations referencing a snippet")
    p_refs.add_argument("key")
    p_refs.set_defaults(func=_cmd_refs)

    p_patch = sub.add_parser(
        "patch-instructions",
        help="Replace `instructions` field on one or more agent-mode variations with a snippet ref",
    )
    p_patch.add_argument("--config", required=True)
    p_patch.add_argument("--snippet", required=True)
    p_patch.add_argument("--snippet-version", type=int)
    p_patch.add_argument("--variation", action="append", required=True)
    p_patch.add_argument("--comment")
    p_patch.set_defaults(func=_cmd_patch_instructions)

    return parser


def main(argv: list[str] | None = None) -> None:
    parser = _build_parser()
    args = parser.parse_args(argv)
    args.func(args)


if __name__ == "__main__":
    main()
