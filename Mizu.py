import asyncio
import os
import discord
from discord.ext import commands
from dotenv import load_dotenv
import random
import yt_dlp
from myserver import server_on

# Load Token
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='sm ', intents=intents)

queues = {}
yt_dl_options = {
    "format": "bestaudio/best",
    "cookiefile": "cookies.txt"
}
ytdl = yt_dlp.YoutubeDL(yt_dl_options)

ffmpeg_options = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'options': '-vn -filter:a "volume=0.5"'
}

# first time played?
played = {}

@bot.event
async def on_ready():
    print("Bot is ready!")
    await bot.tree.sync()

# ฟังก์ชัน helper สำหรับการ deafen บอท
async def deafen_bot(voice_client):
    """
    ฟังก์ชันทำการ Server deafen บอท
    """
    member = voice_client.guild.me  # หาตัวบอทในห้องเสียง
    await member.edit(deafen=True)  # ทำการ deafen บอท
    print(f"Bot is now deafened in {voice_client.guild.name}.")

async def play_next(ctx):
    if ctx.guild.id in queues and queues[ctx.guild.id]:  # เช็คว่าคิวไม่ว่าง
        link = queues[ctx.guild.id].pop(0)
        await play_song(ctx, link)

async def play_song(ctx, link):
    voice_client = ctx.guild.voice_client
    if not voice_client:
        voice_client = await ctx.author.voice.channel.connect()
         # ถ้าเป็นการเล่นเพลงครั้งแรก ให้ทำการ deafen
        if ctx.guild.id not in played:
            await deafen_bot(voice_client)  # ทำการ deafen บอท
            played[ctx.guild.id] = True  # ตั้งค่าว่าเคยเล่นเพลงแล้ว

    try:
        loop = asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(link, download=False))
        thumbnail_url = data.get('thumbnail', None)  # URL ของ thumbnail
        
        song_url = data['url']
        player = discord.FFmpegOpusAudio(song_url, **ffmpeg_options)
        
        # แสดงจำนวนเพลงในคิว
        queue_length = len(queues.get(ctx.guild.id, []))
        
        # ดึงเวลาของคลิป (Duration)
        duration = data.get('duration', 0)  # เวลาของคลิปในวินาที
        minutes = duration // 60
        seconds = duration % 60
        duration_str = f"{minutes}m {seconds}s"
        
        # เล่นเพลงและตั้งให้เล่นเพลงถัดไปเมื่อเพลงจบ
        voice_client.play(player, after=lambda e: asyncio.run_coroutine_threadsafe(play_next(ctx), bot.loop))
        
        # Embed
        embedd = discord.Embed(
            title=f"▶️ | {data.get('title')}",
            url=link,
            color=discord.Colour(0x9B59B6)
        )
        if thumbnail_url:
            embedd.set_thumbnail(url=thumbnail_url)  # เพิ่ม thumbnail
        
        print(queue_length)
        if queue_length == 0:
            embedd.add_field(name='\n', value=f'> Length: {duration_str}', inline=True)
        else : 
            embedd.add_field(
                name='\n', 
                value=f'> Length: {duration_str}\n> Queue: {queue_length} song(s).', 
                inline=True
            )
        await ctx.send(embed=embedd)

    except Exception as e:
        print(f"Error playing audio: {e}")

@bot.event
async def on_message(message):
    msg = message.content.lower()
    if msg == 'hello':
        await message.channel.send("Hi!")
    elif msg.startswith('roll'):
        number = random.randint(1, 100)
        await message.channel.send(f"{message.author.mention} just rolled: {number}")

    # Process commands
    await bot.process_commands(message)

@bot.command(name='play', aliases=['p','pl'])
async def play(ctx, link):
    voice_client = ctx.guild.voice_client
    if not voice_client:
        voice_client = await ctx.author.voice.channel.connect()

    # สร้างคิวสำหรับเซิร์ฟเวอร์นี้ถ้าไม่มีอยู่
    if ctx.guild.id not in queues:
        queues[ctx.guild.id] = []

     # Get song title using yt-dlp
    loop = asyncio.get_event_loop()
    try:
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(link, download=False))
        thumbnail_url = data.get('thumbnail', None)  # URL ของ thumbnail
        
        # Add song to the queue
        queues[ctx.guild.id].append(link)
        
        # แสดงจำนวนเพลงในคิว
        queue_length = len(queues.get(ctx.guild.id, []))
        
        # ดึงเวลาของคลิป (Duration)
        duration = data.get('duration', 0)  # เวลาของคลิปในวินาที
        minutes = duration // 60
        seconds = duration % 60
        duration_str = f"{minutes}m {seconds}s"
    
        # Embed
        if queue_length-1 > 0 or voice_client.is_playing():
            embedd = discord.Embed(
                title=f"📝 | {data.get('title')}",
                url=link,
                colour=discord.Colour.greyple()
            )
            
            if thumbnail_url:
                embedd.set_thumbnail(url=thumbnail_url)  # เพิ่ม thumbnail
            
            if queue_length == 0:
                embedd.add_field(name='\n', value=f'> Length: {duration_str}', inline=True)
            else: 
                embedd.add_field(
                    name='\n', 
                    value=f'> Length: {duration_str}\n> Queue: {queue_length} song(s).', 
                    inline=True
                )

            await ctx.reply(embed=embedd)
        
        # If no song is playing, start the next song immediately
        if not voice_client or not voice_client.is_playing():
            await play_next(ctx)

    except Exception as e:
        await ctx.send("Failed to extract song title. Please check the link and try again.")
        print(f"Error extracting song info: {e}")

@bot.command(name='clear_queue', aliases=['cq','clearq'])
async def clear_queue(ctx):
    if ctx.guild.id in queues:
        queues[ctx.guild.id].clear()
        await ctx.send("Queue cleared!")

@bot.command(name='pause', aliases=['pa'])
async def pause(ctx):
    voice_client = ctx.guild.voice_client
    if voice_client and voice_client.is_playing():
        voice_client.pause()
        await ctx.send("Paused the music.")

@bot.command(name='resume', aliases=['r'])
async def resume(ctx):
    voice_client = ctx.guild.voice_client
    if voice_client and voice_client.is_paused():
        voice_client.resume()
        await ctx.send("Resumed the music.")

@bot.command(name='stop', aliases=['s'])
async def stop(ctx):
    voice_client = ctx.guild.voice_client
    if voice_client:
        voice_client.stop()
        queues[ctx.guild.id].clear()  # Clear the queue when stopping
        # await ctx.send("Stopped the music and cleared the queue.")
        await voice_client.disconnect()

@bot.command(name='ping')
async def ping(ctx):
    latency = bot.latency * 1000 
    await ctx.send(f"Pong!\nLatency: {latency:.2f} ms")

# @bot.command(name='join', aliases=['j'])
# async def join(ctx):
#     if ctx.author.voice:
#         voice_client = ctx.guild.voice_client
#         if not voice_client:
#             await ctx.author.voice.channel.connect()

# @bot.command(name='leave', aliases=['l'])
# async def leave(ctx):
#     voice_client = ctx.guild.voice_client
#     if voice_client:
#         await voice_client.disconnect()

@bot.command(name='skip', aliases=['sk'])
async def skip(ctx):
    voice_client = ctx.guild.voice_client
    if voice_client and voice_client.is_playing():
        voice_client.stop()
        await ctx.send("Skipped!👍")
        if ctx.guild.id in queues and queues[ctx.guild.id]:
            link = queues[ctx.guild.id][0]
            await play_song(ctx, link)  # เรียกใช้ play_song โดยตรง
            
@bot.command(name='clean')
async def clean(ctx):
    # ตรวจสอบว่า user มีสิทธิ์ในการลบข้อความ
    if ctx.author.guild_permissions.manage_messages:
        # ลบข้อความทั้งหมดใน channel
        await ctx.channel.purge()  # ลบข้อความทั้งหมดใน channel
        await ctx.send("Channel has been cleaned!", delete_after=1)  # ส่งข้อความยืนยันแล้วลบภายใน 1 วินาที
    else:
        await ctx.send("You do not have permission to clean this channel.", delete_after=1)

@bot.tree.command(name='help', description='Bot Commands')
async def help(interaction: discord.Interaction):
    embedd = discord.Embed(
        title="Mizu's Commands!",
        description='Commands with prefix "sm"',
        color=discord.Colour.dark_red()
    )
    embedd.add_field(
        name='Commands',
        value="play <URL>\nstop\nskip\npause\nresume\nclear_queue\nclean"
    )
    
    embedd.add_field(
        name='Shortcuts',
        value='`pl p`\n`s`\n`sk`\n`pa`\n`r`\n`cq clearq`'
    )
    embedd.add_field(name='',value='')
    embedd.add_field(name='roll',value='roll number 1-100')
    await interaction.response.send_message(embed=embedd)

@bot.tree.command(name='hellobot', description='Muhahahahaha')
async def hellocommand(interaction: discord.Interaction):
    await interaction.response.send_message("YESYESYES")

server_on()
bot.run(TOKEN)
