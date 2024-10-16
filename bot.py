import discord
import json
import asyncio
import yt_downloader
from discord.ext import tasks

with open("creds.json") as f:
    creds = json.load(f)

TOKEN = creds['token']

client = discord.Client(intents=discord.Intents.all())

queue = []
loop = ""


async def send_help(message: discord.Message):
    """
    Sends a list of commands to the channel
    """
    help_string = "**Kommandoer:**\n"
    for command in commands:
        help_string += f"`{command}`: {commands[command]['desc']}\n"

    await message.channel.send(help_string)

async def stop_bot_play(message: discord.Message):
    """
    Disconnects the bot from its channel
    """
    global queue, loop
    queue = []
    loop = ""
    for voide_clients in client.voice_clients:
        await voide_clients.disconnect(force=True)
  
async def play_audio(message: discord.Message, filename: str, channel = None, voice_client = None):
    """
    Plays mp3 file in audio channel. If channel is not specified will use message.user.voice.channel
    """

    if channel == None and voice_client == None:
        channel: discord.VoiceChannel = message.author.voice.channel
    
    if voice_client == None:
        try:
            voice_client = await channel.connect()
        except discord.errors.ClientException:
            try: 
                await message.channel.send("Bot spiller lyd, bruk `-stop` for å stoppe den.")
            except AttributeError:
                print("Bot is playing sound for another user")
                return
            return

    sound_source = discord.FFmpegPCMAudio(executable="ffmpeg.exe", source=filename)
    voice_client.play(sound_source)
    song_name = filename.split("sounds\\")[1].split(".")[0]
    activity = discord.Game(name=f"Listening to: {song_name}")
    await client.change_presence(status=discord.Status.online, activity=activity)
    # await asyncio.sleep(soundTime)
    # await voice_client.disconnect()

async def parse_YT(message):
    url = message.content.split("-play ")[1]

    if await url_validator(url, message): return
    
    if await check_audio_playing():
        client.voice_clients[0].stop()
        await asyncio.sleep(2)
    
    await play_YT(url, message=message)
   
async def play_YT(url, message=None):
    song_path = yt_downloader.download_youtube_audio(url)
    
    if len(client.voice_clients) > 0: 
        await play_audio(message, song_path, voice_client=client.voice_clients[0])
        return
    
    await play_audio(message, song_path)

async def add_song_to_queue(message):
    global queue
    url = message.content.split('-q ')[1]
    
    if await url_validator(url, message): return
    
    if len(client.voice_clients) == 0: 
        message.content = f"-play {url}"
        await parse_YT(message)
        return
    
    queue.append(url)
    await send_queue(message)

async def url_validator(url, message=None):
    """
    Returns true if URL is invalid yt link
    """
    if yt_downloader.is_valid_url(url): return False

    if message != None:
        await message.channel.send("***URL is not valid YT video***")
    return True
    
def beatify_q(queue):
    titles = yt_downloader.get_list_of_titles(queue)

    return_string = '***Queue:***\n'

    for i, title in enumerate(titles):
        return_string += f"  ***{i + 1}*** : `{title}`\n"
    
    return return_string

async def send_queue(message: discord.message):
    if len(queue) == 0:
        await message.channel.send("***Queue is empty***")
        return 
    await message.channel.send(beatify_q(queue))

@tasks.loop(seconds=1)  # Set the interval to check every 1 seconds
async def check_queue():
    
    if await check_audio_playing(): return

    # Only plays if bot is connected to channel already
    if len(client.voice_clients) == 0: return

    if loop != "":
        await play_YT(loop)
        return
    # Checks if there are songs in q
    if len(queue) > 0:
        
        # Double check in case music is currently downloading
        await asyncio.sleep(3)
        if await check_audio_playing() : return

        await play_next_in_q()
        
async def play_next_in_q(message=None):
    if await check_audio_playing() :
        client.voice_clients[0].stop()
        await asyncio.sleep(2)
    
    if len(queue) > 0:
        await play_YT(queue.pop(0))

    if message == None: return
    await send_queue(message)

async def set_loop(message=None):
    global loop
    if type(message) == str: 
        loop = message
        return
    
    url = message.content.split("-loop ")[1]
    
    await play_YT(url, message)
    loop = url

async def stop_loop(message=None):
    global loop
    loop = ""
    if message == None: return

    message.channel.send("Stopped loop")

async def check_audio_playing():
    for voice_client in client.voice_clients:
        if voice_client.is_playing():
            return True

    return False

commands = {
    '-help':{
        'desc': "Lister kommandoer",
        'func': send_help
    },
    '-stop':{
        'desc': "Stopper botens lyd hvis den spilles",
        'func': stop_bot_play
    },
    '-play': {
        'desc': "Spiller av sang med YT link",
        'func': parse_YT
    },
    '-q': {
        'desc': "Quererer en sang",
        'func': add_song_to_queue
    },
    '-skip': {
        'desc': 'Skipper en sang',
        'func': play_next_in_q
    },
    '-loop': {
        'desc': 'Looper spesifisert sang',
        'func': set_loop
    },
    '-list': {
        'desc': "Viser liste av queuedede sanger",
        'func': send_queue
    }
}

@client.event
async def on_ready():
    check_queue.start()

@client.event
async def on_message(message: discord.Message): 
    if message.author == client.user:
        return

    if message.content.startswith(tuple(commands)): # Is message a command?
        excecuted_command = message.content.split(" ")[0]
        await commands[excecuted_command]['func'](message)
        return

client.run(TOKEN)