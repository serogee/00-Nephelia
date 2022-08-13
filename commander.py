import re
import os
import discord
import prefix
import asyncio
        
# use importlib

class Flags:

    def __init__(self, flags) -> None:
        self.text = flags

    def __str__(self):
        if self.text:
            return self.text
        return ""

    def __contains__(self, flag: str):
        try:
            return flag in self.text
        except TypeError:
            return None        

    def has_flag(self, flag):
        try:
            return flag in self.text
        except TypeError:
            return None

    def input(self, input):
        try:
            return re.search(input, self.text)
        except TypeError:
            return None

class Context:

    def __init__(self, message, prefix, trigger, flags, command) -> None:
        self.message = message
        self.channel = message.channel
        self.guild = message.guild
        self.send = message.channel.send
        self.delete = message.delete
        self.author = message.author
        self.prefix = prefix
        self.trigger = trigger
        self.command = command
        self.flags = Flags(flags)
        
    async def reply(self, content=None, embed=None, mention_author=False):
        await self.message.reply(content, embed=embed, mention_author=mention_author)

    async def get_reference(self):
        try:
            return await self.channel.fetch_message(self.message.reference.message_id)
        except:
            return None

class Command:

    def __init__(self, traceback, cluster, flag_modes: dict={}, aliases: list=[], mention_as_prefix=False, ignore_case=True) -> None:
        self.traceback = traceback
        self.cluster = cluster
        self.client = cluster.client
        self.flag_modes = flag_modes
        self.mention_as_prefix = mention_as_prefix
        self.ignore_case = ignore_case
        self.aliases = aliases
        self.name = traceback.__name__
        self.description = traceback.__doc__
        regex = []
        def anycase(mat):
            group1 = mat.group(1)
            return f"[{group1.lower()}{group1.upper()}]"
        self.triggers = [name] + aliases
        for trigger in self.triggers:
            trigger = re.sub(r"([\W])", r"\\\1", trigger)
            if ignore_case: regex = re.sub(r"([a-zA-Z])", anycase, trigger)
            regex.append(trigger)
        self.triggers_regex = fr"{'|'.join(regex)}"
        self.pattern = re.compile(fr"^[ \n]*({self.triggers_regex})([^ \t\n\u200b]+)?(?:[ \t\n\u200b]+(.+)?)?$", re.DOTALL)

    def embed(self, prefix) -> discord.Embed:
        """Returns the help information of a command as a discord.Embed"""
        embed = discord.Embed(
            title=f"═════════\nHelp: **{self.name}**\n\u200b",
            color=color
            )
        embed.set_author(name=bot_name, icon_url=self.client.user.avatar)
        embed.set_thumbnail(url=self.client.user.avatar)
        embed.set_footer(text=f"{bot_emoji} {prefix}{self.name} {bot_emoji}")
        embed.description = f"```\n - {self.description}\n```\u200b"
        if self.aliases:
            embed.add_field(name=f"__Aliases__", value=", ".join([f"`{prefix}{alias}`" for alias in self.aliases]) + "\n\u200b", inline=False)
        for mode, flags in self.flag_modes.items():
            embed.add_field(name=f"__{mode}__", value="\n".join([f"> **{flag}**\n```\n  {desc}\n```" for flag, desc in flags.items()]) + "\u200b", inline=False)
        return embed
        

class Cluster:

    def __init__(self, parent: MyBot, name, description, hidden=False) -> None:
        self.parent = parent
        self.client = parent.client
        self.name = name
        self.description = description
        self.hidden = hidden
        self.commands = list()
        self.get_prefix = parent.get_prefix

    def command(self, *args, **kwargs):
        def deco(func):
            command = Command(
                traceback=func,
                cluster=self,
                *args,
                **kwargs
            )
            self.commands.append(command)
            return func
        return deco

    def process_commands(self, message) -> None:
        p = self.get_prefix(message)
        content = message.content

        if (prefixed := content.startswith(p)):
            content = content.replace(p, "")
        else:
            mention = f"<@{self.client.user.id}>"
            if content.startswith(mention):
                content = content.replace(mention, "")
            else: return

        for command in self.commands:
            if not prefixed: #guards if content doesn't start with prefix
                if not command.mention_as_prefix: #skips command if not mention_as_prefix
                    continue
            match = command.pattern(content)
            if match:
                asyncio.create_task(command.traceback(
                    Context(message, p, match.group(1), match.group(2), command),
                    match.group(3)
                ))
        
    def __eq__(self, __o: object) -> bool:
        return self.name == __o
        

class MyBot:

    def __init__(self, client: discord.Client, bot_prefix) -> None:
        self.client = client
        if type(bot_prefix) is str:
            self.get_prefix = lambda _: bot_prefix
        elif callable(bot_prefix):
            self.get_prefix = bot_prefix
        else:
            raise TypeError("Given bot_prefix is neither a string object nor a callable")
        self.clusters = list()

    def cluster(self, name, *args, **kwargs) -> Cluster:
        for cluster in self.clusters:
            if cluster == name: return cluster
        cluster = Cluster(self, name, *args, **kwargs)
        self.clusters.append(cluster)
        return cluster 
        
    def process_commands(self, message) -> None:
        p = self.get_prefix(message)
        content = message.content

        if (prefixed := content.startswith(p)):
            content = content.replace(p, "")
        else:
            mention = f"<@{self.client.user.id}>"
            if content.startswith(mention):
                content = content.replace(mention, "")
            else: return

        for cluster in self.clusters:
            for command in cluster.commands:
                if not prefixed: #guards if content doesn't start with prefix
                    if not command.mention_as_prefix: #skips command if not mention_as_prefix
                        continue
                match = command.pattern(content)
                if match:
                    asyncio.create_task(command.traceback(
                        Context(message, p, match.group(1), match.group(2), command),
                        match.group(3)
                    ))

class Bot:
    bots = dict()

    @classmethod
    def create(cls, key="__default", *args, **kwargs) -> MyBot:
        if key in cls.bots:
            raise KeyError("Key already taken")
        cls.bots[key] = mybot = MyBot(*args, **kwargs)
        return mybot

    @classmethod
    def connect(cls, key="__default") -> MyBot:
        return cls.bots[key]
