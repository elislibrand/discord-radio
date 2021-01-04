import os
import json
import random
import itertools
import discord
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()

class Radio(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
        self.current_station = None
        
        self.load_stations()
        
    def load_stations(self):
        with open('stations.json', 'r') as file:
            self.stations = json.load(file)
            
    def dump_stations(self):
        with open('stations.json', 'w') as file:
            json.dump(sorted(self.stations, key = lambda i: i['priority']), file, indent = 4)
            
    def update_current_station(self, station):
        self.current_station = station

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
        await ctx.send('>>> ```{}```'.format('\n'.join(['{:{digits}d}\t{}'.format(station['priority'], station['name'], digits = len(str(len(self.stations)))) for station in sorted(self.stations, key = lambda i: i['priority'])])))

    @commands.command(aliases = ['p', 'start'])
    async def play(self, ctx, *, query = None):        
        if query is None:
            query = self.current_station['name'] if self.current_station is not None else '1'
        
        for station in self.stations:
            if query.isdecimal():
                if station['priority'] == int(query):
                    break
            else:
                if station['name'].lower() == query.lower():
                    break
        else:
            if query.isdecimal():
                await ctx.send('>>> No radio station found with priority **{}**'.format(query))
            else:
                await ctx.send('>>> No radio station found named **{}**'.format(query))
                
            return
        
        if ctx.voice_client.is_playing():
            ctx.voice_client.stop()
        
        ctx.voice_client.play(discord.PCMVolumeTransformer(original = discord.FFmpegPCMAudio(station['stream']),
                                                           volume = 1.0))
        
        self.update_current_station(station)
        
        await ctx.send('>>> Tuning in to **{}**'.format(station['name']))
        
    @commands.command(aliases = ['stop'])
    async def pause(self, ctx):
        ctx.voice_client.stop()
        
    @commands.command(aliases = ['current'])
    async def station(self, ctx):
        if ctx.voice_client.is_playing():
            await ctx.send('>>> Currently tuned in to **{}**'.format(self.current_station['name']))
        else:
            await ctx.send('>>> Currently not tuned in to any radio station')
            
    @commands.command(aliases = ['hitme'])
    async def random(self, ctx):
        station = random.choice(self.stations)
        
        if ctx.voice_client.is_playing():
            ctx.voice_client.stop()
            
            while station == self.current_station:
                station = random.choice(self.stations)
        
        ctx.voice_client.play(discord.PCMVolumeTransformer(original = discord.FFmpegPCMAudio(station['stream']),
                                                           volume = 1.0))
        
        self.update_current_station(station)
        
        await ctx.send('>>> Tuning in to **{}**'.format(station['name']))
        
    @commands.command(aliases = ['pri'])
    async def priority(self, ctx, *, query):
        queries = [''.join(x).strip() for _, x in itertools.groupby(query, key = str.isdigit)]
        
        for station in self.stations:
            if station['name'].lower() == queries[0].lower():
                station_name = station['name']
                current_priority = station['priority']
                
                if current_priority == int(queries[1]):
                    await ctx.send('>>> **{}** already has priority **{}**'.format(station['name'], queries[1]))
                    
                    return
                
                break
        else:
            await ctx.send('>>> No radio station found named **{}**'.format(queries[0]))
                
            return
        
        for station in self.stations:
            if station['name'].lower() == queries[0].lower():
                station['priority'] = int(queries[1])
            else:
                if current_priority < int(queries[1]):
                    if current_priority < station['priority'] <= int(queries[1]):
                        station['priority'] -= 1
                else:
                    if int(queries[1]) <= station['priority'] < current_priority:
                        station['priority'] += 1
                        
        self.dump_stations()
        
        await ctx.send('>>> Changing priority of **{}** to **{}**'.format(station_name, queries[1]))
    
    #@commands.command()
    #async def hititjoe(self, ctx):
    #    if ctx.voice_client.is_playing():
    #        ctx.voice_client.stop()
    #       
    #    ctx.voice_client.play(discord.PCMVolumeTransformer(original = discord.FFmpegPCMAudio('/mnt/d/Downloads/hititjoe.mp3'),
    #                                                       volume = 1.0))
    #    
    #    await ctx.send('>>> Hit it **Joe**')
        
    #@commands.command()
    #async def samuel(self, ctx):
    #    if ctx.voice_client.is_playing():
    #        ctx.voice_client.stop()
    #        
    #    ctx.voice_client.play(discord.PCMVolumeTransformer(original = discord.FFmpegPCMAudio('/mnt/d/Downloads/samuel.mp3'),
    #                                                       volume = 1.0))
    #    
    #    await ctx.send('>>> ( ͡° ͜ʖ ͡°)')
    
    @play.before_invoke
    @random.before_invoke
    #@hititjoe.before_invoke
    #@samuel.before_invoke
    async def ensure_voice(self, ctx):
        if ctx.voice_client is None:
            if ctx.author.voice:
                await ctx.author.voice.channel.connect()
            else:
                await ctx.send('>>> You are not connected to a voice channel')
                
                raise commands.CommandError('Author not connected to a voice channel')
    
    @priority.before_invoke
    async def ensure_owner(self, ctx):
        if str(ctx.message.author) != 'elislibrand#5160':
            await ctx.send('>>> You are not allowed to perform that command')
            
            raise commands.CommandError('Author not allowed to perform command')
        
bot = commands.Bot(command_prefix = commands.when_mentioned_or('#'))#, help_command = None)

@bot.event
async def on_ready():
    print('Logged in as {0} ({0.id})'.format(bot.user))

bot.add_cog(Radio(bot))
bot.run(os.getenv('TOKEN'))