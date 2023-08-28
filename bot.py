import discord
import json
import asyncio
import os
from mutagen.mp3 import MP3
import requests
import datetime
import math
import yt_downloader
from discord.ext import commands, tasks

with open("creds.json") as f:
    creds = json.load(f)

TOKEN = creds['token']

client = discord.Client(intents=discord.Intents.all())

queue = []

def get_stalks() -> dict:
    """
    Returns all stalks from stalks.json file
    """
    with open("stalks.json") as f:
        return json.load(f)

def save_stalks(stalks: dict):
    """
    Saves dict in stalks.json
    """
    with open("stalks.json", "w+") as f:
        f.write(json.dumps(stalks, indent=2))

def get_available_sounds() -> list:
    """
    Returns a list of all files in sounds directory
    """
    return [i.split('.')[0] for i in os.listdir("sounds")]

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
    global queue
    queue = []
    for voide_clients in client.voice_clients:
        await voide_clients.disconnect(force=True)

async def list_stalks(message: discord.Message):
    """
    Lists all stalks to channel
    """
    stalks = get_stalks()
    stalks_string= "**Stalks:** \n"
    for userId in stalks:
        username = client.get_user(int(userId)).name
        
        stalks_string += f"`{username}` stalked by `{stalks[userId]}`\n"

    await message.channel.send(stalks_string)

async def add_stalk_to_user(message: discord.Message):
    """
    Adds a sound to stalk user
    """
    if len(message.content.split(" ")) != 3: 
        await message.channel.send("Bruk: `-stalk @brukernavn lydnavn`")
        return

    sound_name = message.content.split(" ")[2].lower()

    if sound_name not in get_available_sounds():
        await message.channel.send(f"lyden: `{sound_name}` eksisterer ikke")
        return
    
    user_id = message.content.split(" ")[1].split("@")[1].split(">")[0]
    username = client.get_user(int(user_id)).name

    stalks = get_stalks()

    stalks[user_id] = sound_name

    save_stalks(stalks)

    await message.channel.send(f"`{username}` blir nå stalket av `{sound_name}`")

async def add_new_sound(message: discord.Message):
    """
    Downloads a new sound from link in message
    """
    if len(message.content.split(" ")) != 3: 
        await message.channel.send("Bruk: `-newsound link.til/sang.mp3 sangnavn`")
        return

    soundUrl = message.content.split(" ")[1]
    newSound = requests.get(soundUrl)
    newSoundName = 'sounds/' + message.content.split(" ")[2] + ".mp3"

    with open(newSoundName.lower(), 'wb') as f:
        f.write(newSound.content)

    formated_name = newSoundName.split('/')[1].split(".")[0]
    await message.channel.send(f"New sound added: `{formated_name}`")
    print(f"New sound added: {newSoundName}")

async def list_available_sounds(message: discord.Message):
    """
    Sends a list with available sounds in message channel of message origin
    """
    sounds = get_available_sounds()
    sounds_string= "**Sounds:** \n"
    for sound in sounds:
        sound_length = MP3(f'sounds/{sound}.mp3').info.length
        min_sec = str(datetime.timedelta(seconds=sound_length)).split(':')[1:3]

        minutes = min_sec[0]

        seconds = str(math.ceil(float(min_sec[1]))).split(".")[0]
        seconds = seconds if len(seconds) > 1 else f'0{seconds}'

        sounds_string += f"`{sound}` {minutes}:{seconds}\n"

    await message.channel.send(sounds_string)
  
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
    # await asyncio.sleep(soundTime)
    # await voice_client.disconnect()

async def parse_YT(message):
    
    if await check_audio_playing():
        await message.channel.send("Bot spiller sang allerede, bruk `-q`")
        return
    
    url = message.content.split("-play ")[1]
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
    if len(client.voice_clients) == 0: 
        message.content = f"-play {url}"
        await parse_YT(message)
        return
    queue.append(url)
    await message.channel.send(str(queue))

@tasks.loop(seconds=1)  # Set the interval to check every 10 seconds
async def check_queue():
    
    if await check_audio_playing(): return

    # Only plays if bot is connected to channel already
    if len(client.voice_clients) == 0: return

    # Checks if there are songs in q
    if len(queue) > 0:
        
        # Double check in case music is currently downloading
        await asyncio.sleep(3)
        if await check_audio_playing() : return

        await play_YT(queue.pop(0))
        
async def play_next_in_q(_=None):
    if await check_audio_playing() : client.voice_clients[0].stop()
    if len(queue) > 0:
        await play_YT(queue.pop(0))

async def check_audio_playing():
    for voice_client in client.voice_clients:
        if voice_client.is_playing():
            return True

    return False

@check_queue.before_loop
async def before_check_queue():
    await client.wait_until_ready()

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
    }
}

@client.event
async def on_message(message: discord.Message): 
    if message.author == client.user:
        return

    if message.content.startswith(tuple(commands)): # Is message a command?
        excecuted_command = message.content.split(" ")[0]
        await commands[excecuted_command]['func'](message)
        return
check_queue.start()
client.run(TOKEN)





