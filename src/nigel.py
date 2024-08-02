import discord
import os
import asyncio
import yt_dlp
from dotenv import load_dotenv

def run():
    load_dotenv()
    TOKEN = os.getenv('TOKEN')
    intents = discord.Intents.default()
    intents.message_content = True
    client = discord.Client(intents=intents)
    
    voiceClients = {}
    ytdlOptions = {"format": "bestaudio/best"}
    ytdl = yt_dlp.YoutubeDL(ytdlOptions)
    
    ffmpegOptions = {"options": "-vn"}
    
    @client.event
    async def on_ready():
        print(f"{client.user} is going absolutely crazy")
        
    @client.event
    async def on_message(message):
        if message.content.startswith("?play"):
            try:
                voiceClient = await message.author.voice.channel.connect()
                voiceClients[voiceClient.guild.id] = voiceClient
            except Exception as e:
                print(e)
                
            try:
                url = message.content.split()[1]
                
                loop = asyncio.get_event_loop()
                data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=False))
                
                song = data['url']
                player = discord.FFmpegPCMAudio(song, **ffmpegOptions)
                
                voiceClients[message.guild.id].play(player) 
            except Exception as e:
                print(e)
    
    client.run(TOKEN)
                