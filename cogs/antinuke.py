from discord.ext.commands import Cog, command, group, guild_only, has_guild_permissions, check
from discord import Embed

class AntiNuke(Cog):
    def __init__(self, bot):
        self.bot = bot

    def guild_owner_only():
        async def predicate(ctx):
            return ctx.author == ctx.guild.owner
        return check(predicate)

    @group(name="antinuke", aliases=["an"], description="protect your server with antinuke .", invoke_without_command=True)
    @guild_only()
    @guild_owner_only()
    async def antinuke_group(self, ctx):
        if ctx.invoked_subcommand is None:
            await ctx.invoke(self.bot.get_command('help'), command="antinuke")
            return

async def setup(bot):
    await bot.add_cog(AntiNuke(bot))