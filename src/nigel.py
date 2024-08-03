import discord
import os
import asyncio
import yt_dlp
from dotenv import load_dotenv
from datetime import datetime, timedelta

commandDictator = "?"
commandMessages = {
    "play"  : commandDictator + "play",
    "pause" : commandDictator + "pause",
    "resume": commandDictator + "resume",
    "stop"  : commandDictator + "stop",
    "fart"  : commandDictator + "fart"
}

ytdlOptions = {"format": "bestaudio/best"}
ffmpegOptions = {"options": "-vn"}

ytdl = yt_dlp.YoutubeDL(ytdlOptions)
voiceClients = {}

def run():
    load_dotenv()
    TOKEN = os.getenv('TOKEN')
    intents = discord.Intents.default()
    intents.message_content = True
    client = discord.Client(intents=intents)

    """Handles the event when the bot is ready."""
    @client.event
    async def on_ready():
        print(f"{client.user} is going absolutely crazy")

    """
        Handles incoming messages and dispatches commands.

        Args:
            message (discord.Message): The message received from a user.
    """
    @client.event
    async def on_message(message):
        if message.author == client.user:
            return

        if message.content.startswith(commandMessages["play"]):
            await handle_play(message)
            
        elif message.content.startswith(commandMessages["pause"]):
            await handle_pause(message)

        elif message.content.startswith(commandMessages["resume"]):
            await handle_resume(message)
            
        elif message.content.startswith(commandMessages["stop"]):
            await handle_stop(message)

        elif message.content.startswith(commandMessages["fart"]):
            await handle_fart(message)

    """
        Handles the play command.

        Args:
            message (discord.Message): The message containing the play command.
    """
    async def handle_play(message):
        try:
            await join_voice_channel(message)
        except Exception as e:
            await message.channel.send("Get in a channel, stink")

        try:
            url = message.content.split()[1]
            song_info = await get_song_info(url)
            await play_song(message, song_info)
        except Exception as e:
            await search_and_play_song(message)
            
    """
        Handles the pause command.
        
        Args:
            message (discord.Message): The message containing the stop command.
    """        
    async def handle_pause(message):
        try:
            voiceClients[message.guild.id].pause()
        except Exception as e:
            await message.channel.send("no")
    
    """
        Handles the resume command.
        
        Args:
            message (discord.Message): The message containing the stop command.
    """
    async def handle_resume(message):
        try:
            voiceClients[message.guild.id].resume()
        except Exception as e:
            await message.channel.send("no")

    """
        Handles the stop command.

        Args:
            message (discord.Message): The message containing the stop command.
    """
    async def handle_stop(message):
        try:
            await voiceClients[message.guild.id].disconnect()
        except Exception as e:
            await message.channel.send("erm what the deuce")

    """
        Handles the fart command.

        Args:
            message (discord.Message): The message containing the fart command.
    """
    async def handle_fart(message):
        try:
            await join_voice_channel(message)
            song_info = await get_song_info("https://www.youtube.com/watch?v=9FLRHejWAo8")
            await play_song(message, song_info)
            await message.channel.send("farding")
        except Exception as e:
            await message.channel.send("no fard")

    """
        Joins the voice channel of the message author.

        Args:
            message (discord.Message): The message from the user requesting the bot to join a voice channel.
    """
    async def join_voice_channel(message):
        voice_client = await message.author.voice.channel.connect()
        voiceClients[voice_client.guild.id] = voice_client


    """
        Fetches the song URL from YouTube using yt-dlp.

        Args:
            url (str): The URL or search term for the song.

        Returns:
            str: The direct URL of the song's audio stream.
    """
    async def get_song_info(url):
        loop = asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=False))
        song_info = {
            "url"       :   data['url'],
            "title"     :   data.get('title', 'What song is this bruh'),
            "duration"  :   data.get('duration', 0),
            "thumbnail" :   data.get('thumbnail', '')
        }
        return song_info

    """
        Searches YouTube for a song and plays the first result.

        Args:
            message (discord.Message): The message containing the search query.
    """
    async def search_and_play_song(message):
        try:
            search_query = " ".join(message.content.split()[1:])
            loop = asyncio.get_event_loop()
            data = await loop.run_in_executor(None, lambda: ytdl.extract_info(f"ytsearch:{search_query}", download=False))

            if 'entries' in data and len(data['entries']) > 0:
                first_song = data['entries'][0]
                song_url = first_song['url']
                song_info = await get_song_info(song_url)
                await play_song(message, song_info)
            else:
                await message.channel.send("No results found for the search query.")
        except Exception as e:
            await message.channel.send("Shut the fuck up dawg")
            await message.channel.send("Actual Error: " + str(e))

    """
        Plays a song in the voice channel.

        Args:
            message (discord.Message): The message from the user requesting to play a song.
            song_info (dictionary): Map of song attributes (url, title, duration, thumbnail)
    """
    async def play_song(message, song_info):
        player = discord.FFmpegPCMAudio(song_info['url'], **ffmpegOptions)
        voiceClients[message.guild.id].play(player)
        if song_info['title']:
            embed = discord.Embed(title="Now Playing", description=f"[{song_info['title']}]({song_info['url']})", color=0x00ff00)
            embed.add_field(name="Duration", value=f"{song_info['duration'] // 60}:{song_info['duration'] % 60:02d}")
            embed.set_thumbnail(url=song_info['thumbnail'])
            embed.set_footer(text="Playing in the voice channel")
            
            progress_message = await message.channel.send(embed=embed)
            await update_song_progress(progress_message, song_info)
            
    """
        Updates the progress of the song in the embed message.

        Args:
            message (discord.Message): The message to update.
            song_info (dictionary): Map of song attributes (url, title, duration, thumbnail)
    """            
    async def update_song_progress(message, song_info):
        duration = song_info['duration']
        start_time = datetime.now()
        while True:
            elapsed = (datetime.now() - start_time).total_seconds()
            if elapsed > duration:
                break

            progress = int((elapsed / duration) * 20)
            progress_bar = "█" * progress + "░" * (20 - progress)
            embed = discord.Embed(title="Now Playing", description=f"[{song_info['title']}]({song_info['url']})", color=0x00ff00)
            embed.add_field(name="Duration", value=f"{duration // 60}:{duration % 60:02d}")
            embed.add_field(name="Progress", value=f"{progress_bar} {elapsed // 60}:{elapsed % 60:02d}")
            embed.set_thumbnail(url=song_info['thumbnail'])
            embed.set_footer(text="Playing in the voice channel")
            await message.edit(embed=embed)
            await asyncio.sleep(5)

    client.run(TOKEN)
