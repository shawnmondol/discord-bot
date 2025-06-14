import discord
import os
import asyncio
import yt_dlp
import logger
from musicQueue import MusicQueue
from dotenv import load_dotenv
from datetime import datetime, timedelta

commandDictator =""
commandMessages = {}

musicQueue = MusicQueue()

ytdlOptions = {"format": "bestaudio/best"}
ffmpegOptions = {"options": "-vn"}

ytdl = yt_dlp.YoutubeDL(ytdlOptions)
voiceClients = {}

def run():
    global commandDictator, commandMessages
    load_dotenv()
    commandDictator = "$" if os.getenv('TESTING') else "?"
    commandMessages = {
        "play"   : f"{commandDictator}play",
        "pause"  : f"{commandDictator}pause",
        "resume" : f"{commandDictator}resume",
        "stop"   : f"{commandDictator}stop",
        "fart"   : f"{commandDictator}fart",
        "skip"   : f"{commandDictator}skip"
    }
    TOKEN = os.getenv('TOKEN')
    intents = discord.Intents.default()
    intents.message_content = True
    intents.voice_states    = True
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
            
        elif message.content.startswith(commandMessages["skip"]):
            await handle_skip(message)

    """
        Handles the play command.

        Args:
            message (discord.Message): The message containing the play command.
    """
    async def handle_play(message):
        try:
            await join_voice_channel(message)
        except Exception as e:
            await message.channel.send("Get in a channel")

        try:
            if not (message.content.split()[1].startswith("https://")):
                await search_and_play_song(message)
                return
            url = message.content.split()[1]
            song_info = await get_song_info(url)
            await play_song(message, song_info)
        except Exception as e:
            await message.channel.send("No url provided. Did you mean to resume?")
            
    """
        Handles the pause command.
        
        Args:
            message (discord.Message): The message containing the stop command.
    """        
    async def handle_pause(message):
        try:
            voiceClients[message.guild.id].pause()
        except Exception as e:
            await message.channel.send("no: " + str(e))
    
    """
        Handles the resume command.
        
        Args:
            message (discord.Message): The message containing the stop command.
    """
    async def handle_resume(message):
        try:
            voiceClients[message.guild.id].resume()
        except Exception as e:
            await message.channel.send("no: " + str(e))

    """
        Handles the stop command.

        Args:
            message (discord.Message): The message containing the stop command.
    """
    async def handle_stop(message):
        try:
            await voiceClients[message.guild.id].disconnect()
        except Exception as e:
            await message.channel.send("erm what the deuce" + str(e))
            
    """
        Handles the skip command.

        Args:
            message (discord.Message): The message containing the stop command.
    """
    async def handle_skip(message):
        try:
            voiceClients[message.guild.id].stop()
            if musicQueue.next():
                await play_song(message, musicQueue.peek())
            else:
                await message.channel.send("No song bruh")
        except Exception as e:
            await message.channel.send("erm what the deuce" + str(e))

    """
        Handles the fart command.

        Args:
            message (discord.Message): The message containing the fart command.
    """
    async def handle_fart(message):
        try:
            await join_voice_channel(message)
            song_info = await get_song_info(os.getenv('FART_URL'))
            await play_song(message, song_info)
            await message.channel.send("farding")
        except Exception as e:
            await message.channel.send("no fard")
            await message.channel.send("Error: " + str(e))

    """
        Joins the voice channel of the message author.

        Args:
            message (discord.Message): The message from the user requesting the bot to join a voice channel.
    """
    async def join_voice_channel(message):
        channel = message.author.voice.channel
        guild_id = message.guild.id

        # If we have a cached client, try to clean it up
        old_vc = voiceClients.get(guild_id)
        if old_vc:
            # force-disconnect if still connected (this also calls cleanup())
            if old_vc.is_connected():
                await old_vc.disconnect()
            voiceClients.pop(guild_id, None)

        # Now make a fresh connection
        voice_client = await channel.connect()
        voiceClients[guild_id] = voice_client
        
        return voice_client

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
            "url"       :   data['webpage_url'],
            "stream"    :   data.get('url', ''),
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

            entries = data.get('entries', [])
            if not entries:
                await message.channel.send("No results found for the search query.")
                return
            # Get first entry from search results
            first_song = entries[0]
            song_url = first_song['webpage_url']
            print(song_url)
            song_info = await get_song_info(song_url)
            await play_song(message, song_info)
        except Exception as e:
            await message.channel.send("pooooooooooooooooooooop")
            await message.channel.send("Error: " + str(e))

    """
        Plays a song in the voice channel.

        Args:
            message (discord.Message): The message from the user requesting to play a song.
            song_info (dictionary): Map of song attributes (url, title, duration, thumbnail)
    """
    async def play_song(message, song_info):
        if voiceClients[message.guild.id].is_playing():
            musicQueue.enqueue(song_info)
            await message.channel.send(f"{song_info['title']} has been added to the queue")
            return
            
        player = discord.FFmpegPCMAudio(song_info['stream'], **ffmpegOptions)
        voiceClients[message.guild.id].play(player)
        #musicQueue.enqueue(song_info) CAUSING ERRORS OF NONETYPE
        if song_info['url'] != os.getenv('FART_URL'):
            embed = discord.Embed(title="Now Playing", description=f"[{song_info['title']}]({song_info['url']})", color=0x00ff00)
            # zero-pad seconds for display
            mins, secs = divmod(song_info['duration'], 60)
            embed.add_field(name="Duration", value=f"{mins}:{secs:02d}")
            embed.set_thumbnail(url=song_info['thumbnail'])
            embed.set_footer(text="Playing in the voice channel")
            
            progress_message = await message.channel.send(embed=embed)
            asyncio.create_task(update_song_progress(progress_message, song_info))
            if not musicQueue.is_empty():
                await handle_skip(message)
          
    """
        Updates the progress of the song in the embed message.

        Args:
            message (discord.Message): The message to update.
            song_info (dictionary): Map of song attributes (url, title, duration, thumbnail)
    """            
    async def update_song_progress(message, song_info):
        duration = song_info['duration']
        start_time = datetime.now()
        elapsed = 1
        while True:
            # Breaks once the song duration is reached
            if elapsed > duration or not (voiceClients[message.guild.id].is_playing() or voiceClients[message.guild.id].is_paused()):
                break

            # Display the song data card
            embed = discord.Embed(title="Now Playing", description=f"[{song_info['title']}]({song_info['url']})", color=0xff0000)

            segments = 12
            progress   = int((elapsed / duration) * segments)
            progress_bar = "▰" * progress + "▱" * (segments - progress)
            # zero-pad seconds for display
            total_mins, total_secs = divmod(duration, 60)
            elapsed_mins, elapsed_secs = divmod(int(elapsed), 60)
            embed.add_field(name="Duration", value=f"{total_mins}:{total_secs:02d}")
            embed.add_field(name="Progress", value=f"{progress_bar} {elapsed_mins}:{elapsed_secs:02d}/{total_mins}:{total_secs:02d}")
            embed.set_thumbnail(url=song_info['thumbnail'])
            embed.set_footer(text="Playing in the voice channel")
            await message.edit(embed=embed)

            # Update the elapsed time
            await asyncio.sleep(1)
            if not voiceClients[message.guild.id].is_paused():
                elapsed = (datetime.now() - start_time).total_seconds()

    client.run(TOKEN)

