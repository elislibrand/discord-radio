import os
import json
import discord
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()

class Radio(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
        self.load_stations()
        
    def load_stations(self):
        with open("stations.json", "r") as file:
            self.stations = json.load(file)

    #@commands.command(aliases = ['h'])
    #async def help(self, ctx):
    #    await ctx.send('\n'.join([method for method in set(dir(self)) if callable(getattr(self, method)) and method.startswith('__') is False]))

    @commands.command(aliases = ['join'])
    async def connect(self, ctx):
        channel = ctx.author.voice.channel

        if ctx.voice_client is not None:
            return await ctx.voice_client.move_to(channel)

        await channel.connect()

    @commands.command(aliases = ['leave'])
    async def disconnect(self, ctx):
        await ctx.voice_client.disconnect()
        
    @commands.command(aliases = ['list'])
    async def l(self, ctx):
        await ctx.send('>>> ```{}```'.format('\n'.join('{}\t{}'.format(station['priority'], station['name']) for station in self.stations)))

    @commands.command(aliases = ['p'])
    async def play(self, ctx, *, query = '1'):
        for station in self.stations:
            if query.isdecimal():
                if station['priority'] == int(query):
                    name = station['name']
                    stream = station['stream']
                    
                    break
            else:
                if station['name'].lower() == query.lower():
                    name = station['name']
                    stream = station['stream']
                    
                    break
        else:
            if query.isdecimal():
                await ctx.send('>>> No radio station found with priority **{}**'.format(query))
            else:
                await ctx.send('>>> No radio station found named **{}**'.format(query))
                
            return
        
        if ctx.voice_client.is_playing():
            ctx.voice_client.stop()
        
        ctx.voice_client.play(discord.PCMVolumeTransformer(original = discord.FFmpegPCMAudio(stream),
                                                           volume = 1.0))
        
        await ctx.send('>>> Tuning in to **{}**'.format(name))
        
    @commands.command(aliases = ['stop'])
    async def pause(self, ctx):
        ctx.voice_client.stop()
        
    @commands.command()
    async def hititjoe(self, ctx):
        if ctx.voice_client.is_playing():
            ctx.voice_client.stop()
            
        ctx.voice_client.play(discord.PCMVolumeTransformer(original = discord.FFmpegPCMAudio('/mnt/d/Downloads/hititjoe.mp3'),
                                                           volume = 1.0))
        
        await ctx.send('>>> Hit it **Joe**')
        
    @commands.command()
    async def samuel(self, ctx):
        if ctx.voice_client.is_playing():
            ctx.voice_client.stop()
            
        ctx.voice_client.play(discord.PCMVolumeTransformer(original = discord.FFmpegPCMAudio('/mnt/d/Downloads/samuel.mp3'),
                                                           volume = 1.0))
        
        await ctx.send('>>> ( ͡° ͜ʖ ͡°)')
    
    @play.before_invoke
    @hititjoe.before_invoke
    @samuel.before_invoke
    async def ensure_voice(self, ctx):
        if ctx.voice_client is None:
            if ctx.author.voice:
                await ctx.author.voice.channel.connect()
            else:
                await ctx.send('You are not connected to a voice channel.')
                
                raise commands.CommandError('Author not connected to a voice channel.')
        
bot = commands.Bot(command_prefix = commands.when_mentioned_or('#'))#, help_command = None)

@bot.event
async def on_ready():
    print('Logged in as {0} ({0.id})'.format(bot.user))

bot.add_cog(Radio(bot))
bot.run(os.getenv('TOKEN'))