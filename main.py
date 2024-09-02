import os

import discord
from discord.ext import tasks
from pydactyl import PterodactylClient
from dotenv import load_dotenv
import mariadb

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
    node_details = []
    for page in nodes:
        for node in page:
            if node['attributes']['location_id'] not in location_ids:
                continue
            all_mem_size = node['attributes']['memory']
            all_disk_size = node['attributes']['disk']
            allocated_mem_size = node['attributes']['allocated_resources']['memory']
            allocated_disk_size = node['attributes']['allocated_resources']['disk']
            non_allocated_mem_size = all_mem_size - allocated_mem_size
            non_allocated_disk_size = all_disk_size - allocated_disk_size

            node_details.append((non_allocated_mem_size, non_allocated_disk_size))

            node_name = node['attributes']['name']

            status_icon = "✅"
            if non_allocated_mem_size <= 0:
                status_icon = "❌"

            embed.add_field(name=node_name,
                            value=status_icon + " 残り" + str(non_allocated_mem_size / 1000) + "GB")

    await ((await bot.get_channel(1234306814305108068).fetch_message(1234309444360343552))
           .edit(embed=embed))

    conn = mariadb.connect(host=os.environ.get('DB_HOST', None), user=os.environ.get('DB_USER', None)
                                   , password=os.environ.get('DB_PASS', None), database=os.environ.get('DB_NAME', None))
    curs = conn.cursor()
    curs.execute('SELECT * FROM tblproducts WHERE gid=1')
    for row in curs.fetchall():
        disk_size = row[7]
        mem_size = row[8]
        is_enable = False
        for node in node_details:
            if mem_size <= node[0] and disk_size <= node[1]:
                is_enable = True
                break
        if is_enable:
            curs.execute(f'UPDATE tplproducts SET stockcontrol=0 WHERE id={row[0]}')
        else:
            curs.execute(f'UPDATE tplproducts SET stockcontrol=1 WHERE id={row[0]}')

    conn.commit()
    curs.close()
    conn.close()




bot.run(discord_token)
