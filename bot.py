import discord
from discord.ext import commands, tasks
import datetime
import os
from dotenv import load_dotenv

# نحمّلو الـ TOKEN من ملف .env
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)

voice_start_times = {}
timer_tasks = {}
original_names = {}


@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")


@bot.event
async def on_voice_state_update(member, before, after):
    if after.channel and after.channel.type == discord.ChannelType.voice:
        channel = after.channel
        if len(channel.members) == 1:  # أول واحد دخل
            voice_start_times[channel.id] = datetime.datetime.now()
            if channel.id not in original_names:
                original_names[channel.id] = channel.name
            if channel.id not in timer_tasks or not timer_tasks[channel.id].is_running():
                task = update_timer(channel.id)
                timer_tasks[channel.id] = task
                task.start()

    if before.channel and before.channel.type == discord.ChannelType.voice:
        channel = before.channel
        if len(channel.members) == 0:  # آخر واحد خرج
            if channel.id in timer_tasks and timer_tasks[channel.id].is_running():
                timer_tasks[channel.id].cancel()
            voice_start_times.pop(channel.id, None)
            if channel.id in original_names:
                await channel.edit(name=original_names[channel.id])


def update_timer(channel_id):
    @tasks.loop(seconds=1)
    async def _update():
        channel = bot.get_channel(channel_id)
        if channel and channel_id in voice_start_times:
            elapsed = datetime.datetime.now() - voice_start_times[channel_id]
            hours, remainder = divmod(elapsed.seconds, 3600)
            minutes, seconds = divmod(remainder, 60)
            base_name = original_names.get(channel_id, "🎤 Voice Chat")
            await channel.edit(
                name=f"{base_name} [{hours:02d}:{minutes:02d}:{seconds:02d}]"
            )
    return _update


bot.run(TOKEN)
