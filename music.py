import discord
from discord.ext import commands
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import sqlite3

class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        super().__init__()
        self.spotify = spotipy.Spotify(client_credentials_manager=SpotifyClientCredentials(
            client_id='edb73d1722664867b1###',
            client_secret='8fbe1319ca1c4499b6965#####',
        ))
        self.con = sqlite3.connect('queues.db')
        self.cursor = self.con.cursor()
        self.set()

    def set(self):
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS queues (guild_id INTEGER PRIMARY KEY,queue TEXT)''')
        self.con.commit()

    def loadq(self, guild_id):
        self.cursor.execute("SELECT queue FROM queues WHERE guild_id=?", (guild_id,))
        r = self.cursor.fetchone()
        if r:
            return r[0].split(',')
        return []

    def saveq(self, guild_id, queue):
        self.cursor.execute("INSERT OR REPLACE INTO queues (guild_id, queue) VALUES (?, ?)", (guild_id, ','.join(queue)))
        self.con.commit()

    async def plays(self, interaction, song_url):
        guild_id = interaction.guild.id
        guild_queue = self.loadq(guild_id)
        if not guild_queue:
            e = discord.Embed(description="Que Is Empty")
            await interaction.reply(embed=e)
            return

        if not guild_id in self.bot.voice_clients:
            if interaction.author.voice:
                await interaction.author.voice.channel.connect()
            else:
                e = discord.Embed(description="You are not connected to a voice channel.")
                await interaction.reply(embed=e)
                return

        voice_client = self.bot.voice_clients[guild_id]
        voice_client.stop()
        voice_client.play(discord.FFmpegPCMAudio(song_url))
        e = discord.Embed()
        e.add_field(name="Now Playing:",value=f"{song_url}")
        await interaction.reply(embed=e)
       

    @commands.hybrid_command(name="play",description="Play a Song")
    async def play(self, interaction, query: str):
        res = self.spotify.search(q=query, type='track', limit=1)
        if res['tracks']['items']:
            song_url = res['tracks']['items'][0]['external_urls']['spotify']
            await self.plays(interaction, song_url)
        else:
            e = discord.Embed(description=f"Song not found.")
            await interaction.reply(embed=e)
            

    @commands.hybrid_command(name="skip", description="Skip The Current Song")
    async def skip(self, interaction):
        guild_id = interaction.guild.id
        guild_queue = self.loadq(guild_id)
        if not guild_queue:
            e = discord.Embed(description=f"Queue is Empty.")
            await interaction.reply(embed=e)
            return

        voice_client = self.bot.voice_clients.get(guild_id)
        if voice_client:
            voice_client.stop()
            if guild_queue:
                guild_queue.pop(0)
                self.saveq(guild_id, guild_queue)
                if guild_queue:
                    await self.plays(interaction, guild_queue[0])
                else:
                    e = discord.Embed(description=f"No more songs in the queue.")
                    await interaction.reply(embed=e)
                    
            else:
                e = discord.Embed(description=f"No more songs in the queue.")
                await interaction.reply(embed=e)
        else:
            e = discord.Embed(description=f"Not currently playing anything.")
            await interaction.reply(embed=e)
           

    @commands.hybrid_command(name="queue",description="List the current queue")
    async def queue(self, interaction):
        guild_id = interaction.guild.id
        guild_queue = self.loadq(guild_id)
        if guild_queue:
            queue_list = "\n".join([f"{index+1}. {song}" for index, song in enumerate(guild_queue)])
            e = discord.Embed()
            e.add_field(name=f"Current queue:", value=f"\n{queue_list}")
            await interaction.reply(embed=e)
           
        else:
            e = discord.Embed(description=f"Queue is Empty.")
            await interaction.reply(embed=e)
            

    @commands.hybrid_command(name="addque",description="Add a Sng To The Que")
    async def addque(self, interaction, query: str):
        r = self.spotify.search(q=query, type='track', limit=1)
        if r['tracks']['items']:
            song_url = r['tracks']['items'][0]['external_urls']['spotify']
            guild_id = interaction.guild.id
            guild_queue = self.loadq(guild_id)
            guild_queue.append(song_url)
            self.saveq(guild_id, guild_queue)
            e = discord.Embed(description=f"{query} added to queue.")
            await interaction.reply(embed=e)
            
        else:
            e = discord.Embed(description=f"Song Not Found")
            await interaction.reply(embed=e)
            

def setup(bot):
    bot.add_cog(Music(bot))
