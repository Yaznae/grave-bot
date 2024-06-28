from discord.ext.commands import command, Cog, has_guild_permissions, guild_only, group, bot_has_permissions
from discord.ext.commands import MemberConverter
from discord import Embed, AllowedMentions
from uwuipy import uwuipy

class Fun(Cog):
    def __init__(self, bot):
        self.bot = bot
        self.uwu_list = {}
        self.uwu_webhooks = {}
        self.su_list = {}

    @Cog.listener()
    async def on_message(self, message):
        
        if message.guild.id in self.su_list.keys():
            su_list = self.su_list[message.guild.id]
            if message.author not in su_list: return
            await message.delete()

        if message.channel.id in self.uwu_list.keys():
            uwu_list = self.uwu_list[message.channel.id]
            w = self.uwu_webhooks[message.channel.id]
            if message.author not in uwu_list: return

            uwu = uwuipy()
            mentions = AllowedMentions()
            mentions.everyone = False
            mentions.roles = False

            cont = uwu.uwuify(message.content)
            await message.delete()
            await w.send(content=cont, username=message.author.display_name, avatar_url=message.author.display_avatar.url, allowed_mentions=mentions)
    
        
    @group(name="uwu", description="changes user messages to furry messages .", invoke_without_command=True)
    @guild_only()
    @has_guild_permissions(administrator=True)
    @bot_has_permissions(manage_webhooks=True)
    async def uwu_group(self, ctx, member):
        webhooks = await ctx.channel.webhooks()
        webhooks_users = [w.user for w in webhooks]
        if self.bot.user not in webhooks_users:
            try:
                w = await ctx.channel.create_webhook(name="uwu // grave")
            except:
                emb = Embed(color=0x2b2d31, description=f"{ctx.author.mention}: couldn't create webhook. maybe check my **permissions** ?")
                await ctx.send(embed=emb)
                return
            self.uwu_webhooks.update({ ctx.channel.id: w })
        else:
            for w in webhooks:
                if w.user == self.bot.user:
                    self.uwu_webhooks.update({ ctx.channel.id: w })

        if ctx.invoked_subcommand is None:
            m_conv = MemberConverter()
            m = await m_conv.convert(ctx, member)
            emb = Embed(color=0x2b2d31)

            if m.bot:
                emb.description = f"{ctx.author.mention}: cannot add **bots** to **uwu-list** ."
                await ctx.send(embed=emb)
                return

            try:
                uwu_list = self.uwu_list[ctx.channel.id]
            except KeyError:
                self.uwu_list.update({ ctx.channel.id: [m] })
                emb.description = f"**uwu** {m.mention} ."
                await ctx.send(embed=emb)
                return

            if m in uwu_list:
                uwu_list.remove(m)
                emb.description = f"**removed** {m.mention} from **uwu-list** ."
            else:
                uwu_list.append(m)
                emb.description = f"**uwu** {m.mention} ."
                
            self.uwu_list.update({ ctx.channel.id: uwu_list })
            await ctx.send(embed=emb)

    @uwu_group.command(name="reset", description="same as `uwu remove all` .")
    @guild_only()
    @has_guild_permissions(administrator=True)
    async def uwu_reset(self, ctx):
        await ctx.invoke(self.bot.get_command('uwu remove all'))
            
    @uwu_group.command(name="add", description="adds user to uwu-list .")
    @guild_only()
    @has_guild_permissions(administrator=True)
    @bot_has_permissions(manage_webhooks=True)
    async def uwu_add(self, ctx, member):
        m_conv = MemberConverter()
        m = await m_conv.convert(ctx, member)
        emb = Embed(color=0x2b2d31)

        if m.bot:
            emb.description = f"{ctx.author.mention}: cannot add **bots** to **uwu-list** ."
            await ctx.send(embed=emb)
            return

        try:
            uwu_list = self.uwu_list[ctx.channel.id]
        except KeyError:
            self.uwu_list.update({ ctx.channel.id: [m] })
            emb.description = f"**uwu** {m.mention} ."
            await ctx.send(embed=emb)
            return

        if m in uwu_list:
            emb.description = f"{m.mention} is already **added** to **uwu-list** ."
        else:
            uwu_list.append(m)
            emb.description = f"**uwu** {m.mention} ."
            
        self.uwu_list.update({ ctx.channel.id: uwu_list })
        await ctx.send(embed=emb)

    @uwu_group.group(name="remove", description="removes user from uwu-list .", invoke_without_command=True)
    @guild_only()
    @has_guild_permissions(administrator=True)
    @bot_has_permissions(manage_webhooks=True)
    async def uwu_remove(self, ctx, member):
        if ctx.invoked_subcommand is None:
            m_conv = MemberConverter()
            m = await m_conv.convert(ctx, member)
            emb = Embed(color=0x2b2d31)

            if m.bot:
                await ctx.send("nigga u cant add even bots there")
                return

            try:
                uwu_list = self.uwu_list[ctx.channel.id]
            except KeyError:
                emb.description = f"{m.mention} is not in **uwu-list** ."
                await ctx.send(embed=emb)
                return

            if m not in uwu_list:
                emb.description = f"{m.mention} is not in **uwu-list** ."
            else:
                uwu_list.remove(m)
                emb.description = f"**removed** {m.mention} from **uwu-list** ."
                
            self.uwu_list.update({ ctx.channel.id: uwu_list })
            await ctx.send(embed=emb)

    @uwu_remove.command(name="all", description="removes **all** users from uwu-list .")
    @guild_only()
    @has_guild_permissions(administrator=True)
    @bot_has_permissions(manage_webhooks=True)
    async def uwu_remove_all(self, ctx):
        try:
            self.uwu_list.pop(ctx.channel.id)
            emb = Embed(color=0x2b2d31, description=f"{ctx.author.mention}: removed **all users** from **uwu-list** for {ctx.channel.mention} .")
            await ctx.send(embed=emb)
        except KeyError:
            emb = Embed(color=0x2b2d31, description=f"{ctx.author.mention}: **uwu-list** is empty .")
            await ctx.send(embed=emb)

    @uwu_group.command(name="list", description="lists members in **uwu-list** .")
    @guild_only()
    @has_guild_permissions(administrator=True)
    @bot_has_permissions(manage_webhooks=True)
    async def uwu_list(self, ctx):
        emb = Embed(color=0x2b2d31)

        try:
            uwu_list = [m.mention for m in self.uwu_list[ctx.channel.id]]
            if len(uwu_list) < 1:
                emb.description = f"**uwu-list** is empty ."
                await ctx.send(embed=emb)
                return
        except KeyError:
            emb.description = f"**uwu-list** is empty ."
            await ctx.send(embed=emb)
            return

        emb.description = " ⋅ ".join(uwu_list)
        emb.set_author(name=f"uwu list for {ctx.channel.name} :")
        await ctx.send(embed=emb)

    @group(name="shutup", aliases=["su", "stfu"], description="shuts up users .", invoke_without_command=True)
    @guild_only()
    @has_guild_permissions(administrator=True)
    @bot_has_permissions(manage_messages=True)
    async def stfu_group(self, ctx, member):
        if ctx.invoked_subcommand is None:
            m_conv = MemberConverter()
            m = await m_conv.convert(ctx, member)
            emb = Embed(color=0x2b2d31)

            if m.bot:
                emb.description = f"{ctx.author.mention}: cannot stfu **bots** ."
                await ctx.send(embed=emb)
                return

            try:
                su_list = self.su_list[ctx.guild.id]
            except KeyError:
                self.su_list.update({ ctx.guild.id: [m] })
                await ctx.send(f"stfu {m.mention}")
                return

            if m in su_list:
                su_list.remove(m)
                self.su_list.update({ ctx.guild.id: su_list })
                emb.description = f"**speak** {m.mention} ."
                await ctx.send(embed=emb)
            else:
                su_list.append(m)
                self.su_list.update({ ctx.guild.id: su_list })
                await ctx.send(f"stfu {m.mention}")
            
    @stfu_group.command(name="add", description="shuts up users .")
    @guild_only()
    @has_guild_permissions(administrator=True)
    @bot_has_permissions(manage_messages=True)
    async def stfu_add(self, ctx, member):
        m_conv = MemberConverter()
        m = await m_conv.convert(ctx, member)
        emb = Embed(color=0x2b2d31)

        if m.bot:
            emb.description = f"{ctx.author.mention}: cannot stfu **bots** ."
            await ctx.send(embed=emb)
            return

        try:
            su_list = self.su_list[ctx.guild.id]
        except KeyError:
            self.su_list.update({ ctx.guild.id: [m] })
            await ctx.send(f"stfu {m.mention}")
            return

        if m in su_list:
            emb.description = f"{m.mention} is already **added** to **stfu-list** ."
            self.su_list.update({ ctx.guild.id: su_list })
            await ctx.send(embed=emb)
        else:
            su_list.append(m)
            self.su_list.update({ ctx.guild.id: su_list })
            ctx.send(f"stfu {m.mention}")

    @stfu_group.group(name="remove", description="removes user from su-list .", invoke_without_command=True)
    @guild_only()
    @has_guild_permissions(administrator=True)
    @bot_has_permissions(manage_messages=True)
    async def stfu_remove(self, ctx, member):
        if ctx.invoked_subcommand is None:
            m_conv = MemberConverter()
            m = await m_conv.convert(ctx, member)
            emb = Embed(color=0x2b2d31)

            if m.bot:
                await ctx.send("nigga u cant add even bots there")
                return

            try:
                su_list = self.su_list[ctx.guild.id]
            except KeyError:
                emb.description = f"{m.mention} is not in **su-list** ."
                await ctx.send(embed=emb)
                return

            if m not in su_list:
                emb.description = f"{m.mention} is not in **su-list** ."
            else:
                su_list.remove(m)
                emb.description = f"**speak** {m.mention} ."
                
            self.su_list.update({ ctx.channel.id: su_list })
            await ctx.send(embed=emb)

    @stfu_remove.command(name="all", description="removes **all** users from su-list .")
    @guild_only()
    @has_guild_permissions(administrator=True)
    @bot_has_permissions(manage_messages=True)
    async def stfu_remove_all(self, ctx):
        try:
            self.su_list.pop(ctx.guild.id)
            emb = Embed(color=0x2b2d31, description=f"{ctx.author.mention}: removed **all users** from **su-list**")
            await ctx.send(embed=emb)
        except KeyError:
            emb = Embed(color=0x2b2d31, description=f"{ctx.author.mention}: **su-list** is empty .")
            await ctx.send(embed=emb)

    @stfu_group.command(name="list", description="lists members in **su-list** .")
    @guild_only()
    @has_guild_permissions(administrator=True)
    @bot_has_permissions(manage_messages=True)
    async def stfu_list(self, ctx):
        emb = Embed(color=0x2b2d31)

        try:
            su_list = [m.mention for m in self.su_list[ctx.guild.id]]
            if len(su_list) < 1:
                emb.description = f"**su-list** is empty ."
                await ctx.send(embed=emb)
                return
        except KeyError:
            emb.description = f"**su-list** is empty ."
            await ctx.send(embed=emb)
            return

        emb.description = " ⋅ ".join(su_list)
        emb.set_author(name=f"stfu list for {ctx.guild.name} :")
        await ctx.send(embed=emb)

async def setup(bot):
    await bot.add_cog(Fun(bot))