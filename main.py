import os
import discord
import commander
import prefix

intents = discord.Intents().all()
client = discord.Client(intents=intents)
bot = commander.Bot.create(client, prefix.get_prefix)

@client.event
async def on_ready():
    print(f"Logged in as {client.user}!")

if __name__ == '__main__':
    token = os.environ['TOKEN']
    try:
        client.run(token)
    except:
        os.system("kill 1")