import os
import time

import discord
from discord.ext import tasks
from pydactyl import PterodactylClient
from dotenv import load_dotenv

load_dotenv()

api_key = os.environ.get('API_KEY', None)
discord_token = os.environ.get('DISCORD_TOKEN', None)
api = PterodactylClient('https://panel.nyahost.com', api_key)
bot = discord.Bot()
location_ids = [1]


@bot.event
async def on_ready():
    job.start()


@tasks.loop(minutes=5)
async def job():
    nodes = api.nodes.list_nodes()
    print(nodes)
    embed = discord.Embed(
        title="現在の空き状況",
        description="5分おきに更新されます。",
        color=discord.Colour.blurple(),
    )
    for page in nodes:
        for node in page:
            if node['attributes']['location_id'] not in location_ids:
                continue
            print(type(node))
            all_mem_size = node['attributes']['memory']
            allocated_mem_size = node['attributes']['allocated_resources']['memory']
            non_allocated_mem_size = all_mem_size - allocated_mem_size
            node_name = node['attributes']['name']

            status_icon = "✅"
            if non_allocated_mem_size <= 0:
                status_icon = "❌"

            embed.add_field(name=node_name,
                            value=status_icon + " 残り" + str(non_allocated_mem_size / 1000) + "GB")

    await ((await bot.get_channel(1234306814305108068).fetch_message(1234309444360343552))
           .edit(embed=embed))


bot.run(discord_token)
