"""
NEO-Sentinel Discord Orchestration Bot
========================================
Command-and-control interface for the asteroid hazard classification pipeline.

Architecture:
  - All synchronous MLflow / DagsHub calls are offloaded via asyncio.to_thread()
    so they never block the Discord event loop.
  - All HTTP (GitHub API) calls are similarly offloaded with explicit timeouts.
  - Credentials are read exclusively from environment variables via os.getenv().
  - All logging routed through core.logging.get_logger() per Engineering Standards.

Commands:
  !list_models   — Render a paginated embed + dropdown to inspect & promote versions
  !promote <v>   — Directly promote a model version to @champion
  !retrain       — Dispatch the GitHub Actions retraining workflow
  !status        — Show the current @champion version at a glance
"""

from __future__ import annotations

import asyncio
import os
from typing import Any

import discord
import mlflow
import requests
from discord.ext import commands
from mlflow.tracking import MlflowClient

from asteroid_classifier.core.logging import get_logger

logger = get_logger()

# ---------------------------------------------------------------------------
# Bot configuration
# ---------------------------------------------------------------------------
intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

MODEL_NAME: str = "asteroid-hazard-classifier"
CHAMPION_ALIAS: str = "champion"

# HTTP timeout (seconds) for GitHub API dispatch calls
GITHUB_API_TIMEOUT: int = 15

# ---------------------------------------------------------------------------
# Colour palette for rich embeds
# ---------------------------------------------------------------------------
COLOUR_SUCCESS = discord.Colour.from_rgb(57, 255, 20)   # neon green
COLOUR_DANGER = discord.Colour.from_rgb(255, 59, 48)    # vivid red
COLOUR_INFO = discord.Colour.from_rgb(10, 132, 255)     # electric blue
COLOUR_WARNING = discord.Colour.from_rgb(255, 159, 10)  # amber


# ---------------------------------------------------------------------------
# MLflow helpers (all blocking — must be called inside asyncio.to_thread)
# ---------------------------------------------------------------------------
def _sync_get_versions() -> list[dict[str, Any]]:
    """Fetch and sort model versions from MLflow (blocking)."""
    client = MlflowClient()
    versions = client.search_model_versions(f"name='{MODEL_NAME}'")
    sorted_versions = sorted(
        versions, key=lambda v: v.creation_timestamp, reverse=True
    )[:25]  # Discord Select supports max 25 options
    return [
        {
            "version": v.version,
            "status": v.current_stage,
            "run_id": v.run_id,
            "creation_timestamp": v.creation_timestamp,
        }
        for v in sorted_versions
    ]


def _sync_get_champion() -> dict[str, Any] | None:
    """Return the current @champion version info (blocking). Returns None if absent."""
    client = MlflowClient()
    try:
        mv = client.get_model_version_by_alias(MODEL_NAME, CHAMPION_ALIAS)
        return {
            "version": mv.version,
            "run_id": mv.run_id,
            "status": mv.current_stage,
        }
    except Exception:  # no champion registered yet
        return None


def _sync_promote(version: str) -> None:
    """Set @champion alias on `version` (blocking)."""
    client = MlflowClient()
    # Verify existence first
    versions = client.search_model_versions(f"name='{MODEL_NAME}'")
    valid = {v.version for v in versions}
    if version not in valid:
        raise ValueError(f"Version {version} does not exist in the registry.")
    client.set_registered_model_alias(MODEL_NAME, CHAMPION_ALIAS, version)


# ---------------------------------------------------------------------------
# UI Components
# ---------------------------------------------------------------------------
class ModelSelect(discord.ui.Select):
    """Dropdown that immediately promotes the selected version to @champion."""

    def __init__(self, versions_info: list[dict[str, Any]]) -> None:
        options = [
            discord.SelectOption(
                label=f"v{v['version']} — {v['status']}",
                description=f"Run: {v['run_id'][:12]}…",
                value=v["version"],
                emoji="🛰️",
            )
            for v in versions_info
        ]
        super().__init__(
            placeholder="🔭  Select a version to promote to @champion …",
            min_values=1,
            max_values=1,
            options=options,
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        version = self.values[0]

        # Defer so Discord doesn't time-out while we hit MLflow
        await interaction.response.defer(ephemeral=True, thinking=True)

        try:
            await asyncio.to_thread(_sync_promote, version)
        except ValueError as exc:
            logger.warning(f"Promotion validation failed: {exc}")
            await interaction.followup.send(
                embed=discord.Embed(
                    title="❌  Promotion Failed",
                    description=str(exc),
                    color=COLOUR_DANGER,
                ),
                ephemeral=True,
            )
            return
        except Exception as exc:
            logger.error(f"MLflow promotion error: {exc}")
            await interaction.followup.send(
                embed=discord.Embed(
                    title="⚠️  MLflow Error",
                    description=f"```{exc}```",
                    color=COLOUR_WARNING,
                ),
                ephemeral=True,
            )
            return

        logger.info(f"Discord user promoted v{version} to @champion.")
        embed = discord.Embed(
            title="🏆  Champion Promoted!",
            description=(
                f"**Model version `v{version}`** has been crowned **@champion**.\n\n"
                "The serving layer will automatically load this version on its next restart."
            ),
            color=COLOUR_SUCCESS,
        )
        embed.set_footer(text="NEO-Sentinel · Model Registry")
        await interaction.followup.send(embed=embed, ephemeral=False)


class ModelSelectView(discord.ui.View):
    """Wraps ModelSelect in a transient (60 s) view."""

    def __init__(self, versions_info: list[dict[str, Any]]) -> None:
        super().__init__(timeout=60)
        self.add_item(ModelSelect(versions_info))


# ---------------------------------------------------------------------------
# Events
# ---------------------------------------------------------------------------
@bot.event
async def on_ready() -> None:
    logger.info(f"NEO-Sentinel Bot online: {bot.user} (ID: {bot.user.id})")
    await bot.change_presence(
        activity=discord.Activity(
            type=discord.ActivityType.watching,
            name="the asteroid belt 🪐",
        )
    )


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------
@bot.command(name="status")
async def status(ctx: commands.Context) -> None:
    """Show the current @champion model version."""
    async with ctx.typing():
        try:
            champion = await asyncio.to_thread(_sync_get_champion)
        except Exception as exc:
            logger.error(f"Status command failed: {exc}")
            await ctx.send(
                embed=discord.Embed(
                    title="⚠️  Registry Unavailable",
                    description=f"```{exc}```",
                    color=COLOUR_WARNING,
                )
            )
            return

    if champion is None:
        embed = discord.Embed(
            title="🔭  No Champion Yet",
            description=(
                "No model has been assigned the `@champion` alias.\n"
                "Use `!list_models` to browse versions and promote one."
            ),
            color=COLOUR_INFO,
        )
    else:
        embed = discord.Embed(
            title="🏆  Current Champion",
            color=COLOUR_SUCCESS,
        )
        embed.add_field(name="Version", value=f"`v{champion['version']}`", inline=True)
        embed.add_field(name="Stage", value=champion["status"] or "—", inline=True)
        embed.add_field(name="Run ID", value=f"`{champion['run_id'][:16]}…`", inline=False)
        embed.set_footer(text="NEO-Sentinel · Model Registry")

    await ctx.send(embed=embed)


@bot.command(name="list_models")
async def list_models(ctx: commands.Context) -> None:
    """Fetch model versions from MLflow and render an interactive promotion dropdown."""
    async with ctx.typing():
        if not _mlflow_configured():
            await ctx.send(
                embed=discord.Embed(
                    title="⚠️  MLflow Not Configured",
                    description=(
                        "The following environment variables are missing:\n"
                        "`MLFLOW_TRACKING_URI`, `DAGSHUB_REPO_OWNER`, `DAGSHUB_REPO_NAME`.\n\n"
                        "Set them in your container / `.env` file and restart the bot."
                    ),
                    color=COLOUR_DANGER,
                )
            )
            return

        try:
            versions_info: list[dict[str, Any]] = await asyncio.to_thread(_sync_get_versions)
        except Exception as exc:
            logger.error(f"Failed to fetch model versions: {exc}")
            await ctx.send(
                embed=discord.Embed(
                    title="⚠️  Registry Error",
                    description=f"```{exc}```",
                    color=COLOUR_WARNING,
                )
            )
            return

    if not versions_info:
        await ctx.send(
            embed=discord.Embed(
                title="🔭  Registry Empty",
                description=f"No versions found for model `{MODEL_NAME}`.",
                color=COLOUR_INFO,
            )
        )
        return

    # Build a rich embed listing all versions
    embed = discord.Embed(
        title="🛰️  NEO-Sentinel Model Registry",
        description=(
            f"Showing **{len(versions_info)}** most recent versions of "
            f"`{MODEL_NAME}`.\n\n"
            "**Select a version below to immediately promote it to `@champion`.**"
        ),
        color=COLOUR_INFO,
    )
    for v in versions_info:
        embed.add_field(
            name=f"v{v['version']} — {v['status'] or 'None'}",
            value=f"Run ID: `{v['run_id'][:16]}…`",
            inline=True,
        )
    embed.set_footer(text="Dropdown expires in 60 s  ·  NEO-Sentinel")

    view = ModelSelectView(versions_info)
    await ctx.send(embed=embed, view=view)


@bot.command(name="promote")
async def promote(ctx: commands.Context, version: str) -> None:
    """Promote a specific model version to @champion directly (no dropdown)."""
    if not _mlflow_configured():
        await ctx.send(
            embed=discord.Embed(
                title="⚠️  MLflow Not Configured",
                description="Set `MLFLOW_TRACKING_URI`, `DAGSHUB_REPO_OWNER`, and `DAGSHUB_REPO_NAME`.",
                color=COLOUR_DANGER,
            )
        )
        return

    async with ctx.typing():
        try:
            await asyncio.to_thread(_sync_promote, version)
        except ValueError as exc:
            logger.warning(f"Promote command: {exc}")
            await ctx.send(
                embed=discord.Embed(
                    title="❌  Invalid Version",
                    description=str(exc),
                    color=COLOUR_DANGER,
                )
            )
            return
        except Exception as exc:
            logger.error(f"Promote command failed: {exc}")
            await ctx.send(
                embed=discord.Embed(
                    title="⚠️  Promotion Error",
                    description=f"```{exc}```",
                    color=COLOUR_WARNING,
                )
            )
            return

    logger.info(f"Version {version} promoted to @champion via !promote command.")
    embed = discord.Embed(
        title="🏆  Champion Promoted!",
        description=(
            f"Model version **`v{version}`** is now the **@champion**.\n\n"
            "The serving layer will reload on its next restart."
        ),
        color=COLOUR_SUCCESS,
    )
    embed.set_footer(text="NEO-Sentinel · Model Registry")
    await ctx.send(embed=embed)


@bot.command(name="retrain")
async def retrain(ctx: commands.Context) -> None:
    """Dispatch the GitHub Actions retraining workflow asynchronously."""
    github_token = os.getenv("GITHUB_TOKEN")
    github_repo = os.getenv("GITHUB_REPOSITORY")

    if not github_token or not github_repo:
        await ctx.send(
            embed=discord.Embed(
                title="⚠️  CI/CD Not Configured",
                description=(
                    "Missing environment variables:\n"
                    "`GITHUB_TOKEN` and/or `GITHUB_REPOSITORY`.\n\n"
                    "Set them in your container / `.env` and restart the bot."
                ),
                color=COLOUR_DANGER,
            )
        )
        return

    # Acknowledge instantly — HTTP dispatch runs in background thread
    ack_embed = discord.Embed(
        title="🚀  Dispatching Retrain Pipeline …",
        description=(
            "Sending workflow dispatch to GitHub Actions.\n"
            "This will trigger the full **Ingest → Train → Benchmark → Promote** sequence."
        ),
        color=COLOUR_INFO,
    )
    await ctx.send(embed=ack_embed)

    def _trigger_workflow() -> requests.Response:
        url = (
            f"https://api.github.com/repos/{github_repo}"
            "/actions/workflows/retrain.yml/dispatches"
        )
        headers = {
            "Accept": "application/vnd.github.v3+json",
            "Authorization": f"token {github_token}",
        }
        # Explicit connect + read timeout — never blocks indefinitely
        resp = requests.post(
            url,
            headers=headers,
            json={"ref": "main"},
            timeout=(5, GITHUB_API_TIMEOUT),
        )
        resp.raise_for_status()
        return resp

    try:
        await asyncio.to_thread(_trigger_workflow)
    except requests.exceptions.Timeout:
        logger.error("GitHub API request timed out during workflow dispatch.")
        await ctx.send(
            embed=discord.Embed(
                title="⏱️  Dispatch Timed Out",
                description="The GitHub API did not respond within the timeout window. Try again.",
                color=COLOUR_DANGER,
            )
        )
        return
    except requests.exceptions.HTTPError as exc:
        logger.error(f"GitHub API HTTP error: {exc}")
        await ctx.send(
            embed=discord.Embed(
                title="❌  Dispatch Failed",
                description=f"**GitHub API returned an error:**\n```{exc}```",
                color=COLOUR_DANGER,
            )
        )
        return
    except Exception as exc:
        logger.error(f"Unexpected retrain dispatch error: {exc}")
        await ctx.send(
            embed=discord.Embed(
                title="⚠️  Unexpected Error",
                description=f"```{exc}```",
                color=COLOUR_WARNING,
            )
        )
        return

    logger.info(f"Retrain workflow dispatched for repo '{github_repo}'.")
    success_embed = discord.Embed(
        title="✅  Pipeline Dispatched!",
        description=(
            f"**`{github_repo}`** — `retrain.yml` is now queued.\n\n"
            f"[📊 Monitor on GitHub Actions](https://github.com/{github_repo}/actions)"
        ),
        color=COLOUR_SUCCESS,
    )
    success_embed.set_footer(text="NEO-Sentinel · CI/CD")
    await ctx.send(embed=success_embed)


# ---------------------------------------------------------------------------
# MLflow initialisation guard
# ---------------------------------------------------------------------------
def _mlflow_configured() -> bool:
    """Return True only when all three required MLflow env-vars are present."""
    missing = [
        var
        for var in ("MLFLOW_TRACKING_URI", "DAGSHUB_REPO_OWNER", "DAGSHUB_REPO_NAME")
        if not os.getenv(var)
    ]
    if missing:
        logger.warning(f"MLflow env-vars not set: {missing}")
        return False
    return True


def init_mlflow() -> None:
    """
    Connect to DagsHub-hosted MLflow tracking server.

    Validates that all required environment variables are present before
    attempting any network call.  On failure, logs a WARNING — the bot will
    still start; only registry commands will be unavailable.
    """
    if not _mlflow_configured():
        logger.warning(
            "MLflow not initialised — MLFLOW_TRACKING_URI, DAGSHUB_REPO_OWNER, "
            "or DAGSHUB_REPO_NAME is missing.  Registry commands will be unavailable."
        )
        return

    repo_owner = os.getenv("DAGSHUB_REPO_OWNER")
    repo_name = os.getenv("DAGSHUB_REPO_NAME")
    tracking_uri = os.getenv("MLFLOW_TRACKING_URI")

    # Force non-interactive headless mode
    os.environ["DAGSHUB_NON_INTERACTIVE"] = "1"
    dagshub_token = os.getenv("DAGSHUB_TOKEN")
    if dagshub_token:
        os.environ["DAGSHUB_USER_TOKEN"] = dagshub_token

    try:
        import dagshub

        dagshub.init(repo_owner=repo_owner, repo_name=repo_name, mlflow=True)
        mlflow.set_tracking_uri(tracking_uri)
        logger.info("Connected to DagsHub MLflow Registry.")
    except Exception as exc:
        logger.error(f"MLflow initialisation failed: {exc}")


def main() -> None:
    """Entry-point: validate token, init MLflow, start the bot."""
    token = os.getenv("DISCORD_BOT_TOKEN")
    if not token:
        logger.error(
            "DISCORD_BOT_TOKEN is not set. "
            "The bot cannot start without a valid Discord application token."
        )
        return

    init_mlflow()
    logger.info("Starting NEO-Sentinel Discord bot …")
    bot.run(token)


if __name__ == "__main__":
    main()
