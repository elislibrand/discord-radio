import os
import re
import json
import random
import itertools
import discord
import urllib.request as urllib
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()

class Radio(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
        self.current_station = None
        
        self.load_stations()
        self.load_styling()
        
    def load_stations(self):
        with open('stations.json', 'r') as file:
            self.stations = json.load(file)
            
    def dump_stations(self):
        with open('stations.json', 'w') as file:
            json.dump(sorted(self.stations, key = lambda i: i['priority']), file, indent = 4)
        
    def load_styling(self):
        self.d_priority = len(str(len(self.stations)))
        self.d_name = len(max([station['name'] for station in self.stations], key = len))
            
    def update_current_station(self, station):
        self.current_station = station
        
    def get_song_info(self, stream):
        request = urllib.Request(stream)
        
        try:
            request.add_header('Icy-MetaData', 1)
            
            response = urllib.urlopen(request)
            icy_metaint_header = response.headers.get('icy-metaint')
            
            if icy_metaint_header is not None:
                metaint = int(icy_metaint_header)
                
                content = response.read(metaint + 255)
                song_info = content[metaint:].decode(encoding = 'utf-8', errors = 'ignore').split(';', 1)[0][14:-1].split('-', 1)
                
                if len(song_info) < 2:
                    return '', ''
                
                artist = re.sub('\[.*?\]', '', song_info[0]).strip()
                song = re.sub('\[.*?\]', '', song_info[-1]).strip()
                
                return song, artist
            
            return '', ''
        except Exception as e:
            return '', ''

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
        await ctx.send('>>> ```{}```'.format('\n'.join(['{:{priority}d}\t{:{name}s}\t({})'.format(station['priority'], station['name'], station['genre'], priority = self.d_priority, name = self.d_name) for station in sorted(self.stations, key = lambda i: i['priority'])])))

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
                await ctx.send('>>> No radio station found with priority **{}**'.format(query), delete_after = 30)
            else:
                await ctx.send('>>> No radio station found named **{}**'.format(query), delete_after = 30)
                
            return
        
        if ctx.voice_client.is_playing():
            ctx.voice_client.stop()
        
        ctx.voice_client.play(discord.PCMVolumeTransformer(original = discord.FFmpegPCMAudio(station['stream']),
                                                           volume = 1.0))
        
        self.update_current_station(station)
        
        await ctx.send('>>> Tuning in to :flag_{}: **{}**'.format(station['country'].lower(), station['name']))
        
    @commands.command(aliases = ['stop'])
    async def pause(self, ctx):
        ctx.voice_client.stop()

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
    
    #@commands.command(aliases = [])
    #async def guide(self, ctx):
    #    await ctx.send('>>> ```{}```'.format('\n'.join(['{:{digits}d}\t{:20s}\t{}'.format(station['priority'], station['name'], self.get_song_info(station['stream']), digits = len(str(len(self.stations)))) for station in sorted(self.stations, key = lambda i: i['priority'])])))
    
    @commands.command(aliases = [])
    async def station(self, ctx):
        if ctx.voice_client.is_playing():
            await ctx.send('>>> Currently tuned in to :flag_{}: **{}**'.format(self.current_station['country'].lower(), self.current_station['name']))
        else:
            await ctx.send('>>> Currently not tuned in to any radio station', delete_after = 30)
            
    @commands.command(aliases = [])
    async def song(self, ctx):
        if ctx.voice_client.is_playing():
            if not self.current_station['has_metadata']:
                await ctx.send('>>> No song information available', delete_after = 30)
                
                return
            
            song, artist = self.get_song_info(self.current_station['stream'])
            
            if song == '' or artist == '':
                await ctx.send('>>> No song information available', delete_after = 30)
            else:
                await ctx.send('>>> Currently playing **{}** by **{}**'.format(song, artist))
        else:
            await ctx.send('>>> Currently not tuned in to any radio station', delete_after = 30)
            
    @commands.command(aliases = ['pri'])
    async def priority(self, ctx, *, query):
        queries = [''.join(x).strip() for _, x in itertools.groupby(query, key = str.isdigit)] # Update for radio stations with numbers in name
        
        if int(queries[1]) > len(self.stations):
            await ctx.send('>>> Priority cannot be higher than number of radio stations', delete_after = 30)
            
            return
        
        for station in self.stations:
            if station['name'].lower() == queries[0].lower():
                station_name = station['name']
                current_priority = station['priority']
                
                if current_priority == int(queries[1]):
                    await ctx.send('>>> **{}** already has priority **{}**'.format(station['name'], queries[1]), delete_after = 30)
                    
                    return
                
                break
        else:
            await ctx.send('>>> No radio station found named **{}**'.format(queries[0]), delete_after = 30)
                
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
        
    @commands.command()
    async def samuel(self, ctx):
        if ctx.voice_client.is_playing():
            ctx.voice_client.stop()
            
        ctx.voice_client.play(discord.PCMVolumeTransformer(original = discord.FFmpegPCMAudio(os.getenv('SAMUEL')),
                                                           volume = 1.0))
        
        while ctx.voice_client.is_playing():
            pass
            
        ctx.voice_client.play(discord.PCMVolumeTransformer(original = discord.FFmpegPCMAudio(self.current_station['stream']),
                                                           volume = 1.0))

        await ctx.send('>>> ( ͡° ͜ʖ ͡°)')
    
    @play.before_invoke
    @random.before_invoke
    #@hititjoe.before_invoke
    @samuel.before_invoke
    async def ensure_voice(self, ctx):
        if ctx.voice_client is None:
            if ctx.author.voice:
                await ctx.author.voice.channel.connect()
            else:
                await ctx.send('>>> You are not connected to a voice channel', delete_after = 30)
                
                raise commands.CommandError('Author not connected to a voice channel')
    
    @priority.before_invoke
    async def ensure_owner(self, ctx):
        if str(ctx.message.author) != 'elislibrand#5160':
            await ctx.send('>>> You are not allowed to perform that command', delete_after = 30)
            
            raise commands.CommandError('Author not allowed to perform command')
        
bot = commands.Bot(command_prefix = commands.when_mentioned_or('#'))#, help_command = None)

@bot.event
async def on_ready():
    print('Logged in as {0} ({0.id})'.format(bot.user))

bot.add_cog(Radio(bot))
bot.run(os.getenv('TOKEN'))