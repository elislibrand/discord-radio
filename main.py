import os
import re
import json
import string
import random
import itertools
import discord
import urllib.request as urllib
from urllib.parse import urlparse
from discord.ext import commands
from time import sleep
from pytz import utc, timezone
from datetime import datetime
from dotenv import load_dotenv

discord.opus.load_opus
load_dotenv()

class Radio(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
        self.timezone = timezone('Europe/Stockholm')

        self.current_station = None
        self.is_locked = False
        self.bitrate = 96
        
        self.load_stations()
        self.load_flags()
        self.load_styling()
        
    def load_stations(self):
        with open('stations.json', 'r') as file:
            self.stations = json.load(file)
            
    def dump_stations(self):
        with open('stations.json', 'w') as file:
            json.dump(sorted(self.stations, key = lambda i: i['priority']), file, indent = 4)

    def load_flags(self):
        with open('flags.json', 'r') as file:
            self.flags = json.load(file)

    def load_styling(self):
        self.d_priority = len(str(len(self.stations)))
        self.d_title = len(max([station['title'] for station in self.stations], key = len))
        
    def update_current_station(self, station):
        self.current_station = station

    def get_datetime(self):
        dt = datetime.now(utc).astimezone(self.timezone)

        return dt.strftime('%Y-%m-%d %H:%M')

    #def get_song_info(self, stream):
    #    request = urllib.Request(stream)
    #    
    #    try:
    #        request.add_header('Icy-MetaData', 1)
    #        
    #        response = urllib.urlopen(request)
    #        icy_metaint_header = response.headers.get('icy-metaint')
    #        
    #        if icy_metaint_header is not None:
    #            metaint = int(icy_metaint_header)
    #            
    #            content = response.read(metaint + 255)
    #            song_info = content[metaint:].decode(encoding = 'utf-8', errors = 'ignore').split(';', 1)[0][14:-1].split('-', 1)
    #            
    #            if len(song_info) < 2:
    #                return '', ''
    #            
    #            artist = re.sub('\[.*?\]', '', song_info[0]).strip()
    #            song = re.sub('\[.*?\]', '', song_info[-1]).strip()
    #            
    #            return re.sub('\\b(?<!\')[a-z]', lambda m: m.group().upper(), song), re.sub('\\b(?<!\')[a-z]', lambda m: m.group().upper(), artist)
    #        
    #        return '', ''
    #    except Exception as e:
    #        return '', ''

    def get_song_info(self, station_id):
        request = urllib.Request('https://feed.tunein.com/profiles/{}/nowPlaying'.format(station_id))
        
        try:            
            response = urllib.urlopen(request)

            content = json.loads(response.read())
            
            song_info = content['Secondary']['Title'].split(' - ', 1)
            
            if len(song_info) < 2:
                return '', '', ''
            
            artist = re.sub('\\b(?<!\')[a-z]', lambda m: m.group().upper(), re.sub('\[.*?\]', '', song_info[0]).strip())
            song = re.sub('\\b(?<!\')[a-z]', lambda m: m.group().upper(), re.sub('\[.*?\]', '', song_info[1]).strip())

            album_image = urlparse(content['Secondary']['Image'])._replace(scheme = 'https', params = '', query = '', fragment = '').geturl()

            return artist, song, album_image
        except Exception as e:
            return '', '', ''

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
        await ctx.send('>>> ```{}```'.format('\n'.join(['{:{priority}d}\t{:{title}s}\t({})'.format(station['priority'], station['title'], station['genre'], priority = self.d_priority, title = self.d_title) for station in sorted(self.stations, key = lambda i: i['priority'])])))

    @commands.command(aliases = ['p', 'start'])
    async def play(self, ctx, *, query = None):
        if query is None:
            query = self.current_station['title'] if self.current_station is not None else '1'
        
        for station in self.stations:
            if query.isdecimal():
                if station['priority'] == int(query):
                    break
            else:
                if station['title'].lower() == query.lower():
                    break
        else:
            if query.isdecimal():
                await ctx.send('>>> No radio station found with priority **{}**'.format(query), delete_after = 30)
            else:
                await ctx.send('>>> No radio station found named **{}**'.format(query), delete_after = 30)
                
            return
        
        if ctx.voice_client.is_playing():
            ctx.voice_client.stop()
        
        ctx.voice_client.play(discord.FFmpegOpusAudio(station['stream'], bitrate = self.bitrate))
        
        self.update_current_station(station)
        
        for flag in self.flags:
            if flag['country'].lower() == station['country'].lower():
                break

        embed = discord.Embed(title = station['title'], description = station['subtitle'])

        embed.set_author(name = 'Tuning in to...', icon_url = flag['url'])
        embed.set_thumbnail(url = station['image'])

        await ctx.send(embed = embed)

    @commands.command(aliases = ['stop'])
    async def pause(self, ctx):
        ctx.voice_client.stop()

    @commands.command(aliases = ['hitme'])
    async def random(self, ctx):
        station = random.choice(self.stations)
            
        while station == self.current_station:
            station = random.choice(self.stations)
        
        if ctx.voice_client.is_playing():
            ctx.voice_client.stop()

        ctx.voice_client.play(discord.FFmpegOpusAudio(station['stream'], bitrate = self.bitrate))
        
        self.update_current_station(station)
        
        for flag in self.flags:
            if flag['country'].lower() == station['country'].lower():
                break

        embed = discord.Embed(title = station['title'], description = station['subtitle'])

        embed.set_author(name = 'Tuning in to...', icon_url = flag['url'])
        embed.set_thumbnail(url = station['image'])

        await ctx.send(embed = embed)

    #@commands.command(aliases = [])
    #async def guide(self, ctx):
    #    await ctx.send('>>> ```{}```'.format('\n'.join(['{:{digits}d}\t{:20s}\t{}'.format(station['priority'], station['title'], self.get_song_info(station['stream']), digits = len(str(len(self.stations)))) for station in sorted(self.stations, key = lambda i: i['priority'])])))
    
    @commands.command()
    async def station(self, ctx):
        if ctx.voice_client.is_playing():
            for flag in self.flags:
                if flag['country'].lower() == self.current_station['country'].lower():
                    break

            embed = discord.Embed(title = self.current_station['title'], description = self.current_station['subtitle'])

            embed.set_author(name = 'Currently tuned in to...', icon_url = flag['url'])
            embed.set_thumbnail(url = self.current_station['image'])

            await ctx.send(embed = embed)
        else:
            await ctx.send('>>> Currently not tuned in to any radio station', delete_after = 30)
            
    @commands.command()
    async def song(self, ctx):
        if ctx.voice_client.is_playing():
            station_id = self.current_station['id']
            
            #if station_id == '':
            #    await ctx.send('>>> No song information available', delete_after = 30)

            artist, song, album_image = self.get_song_info(station_id)

            if artist == '' or song == '':
                await ctx.send('>>> No song information available', delete_after = 30)
            else:
                for flag in self.flags:
                    if flag['country'].lower() == self.current_station['country'].lower():
                        break

                if album_image == '' or album_image == self.current_station['image']:
                    album_image = 'https://images.vexels.com/media/users/3/132597/isolated/preview/e8c7c6b823f6df05ec5ae37ea03a5c88-vinyl-record-icon-by-vexels.png'

                embed = discord.Embed(title = song, description = artist)
                
                embed.set_author(name = 'Now playing...', icon_url = self.current_station['image'])
                embed.set_thumbnail(url = album_image)

                await ctx.send(embed = embed)
        else:
            await ctx.send('>>> Currently not tuned in to any radio station', delete_after = 30)
            
    @commands.command(aliases = ['pri'])
    async def priority(self, ctx, *, query):
        queries = [''.join(x).strip() for _, x in itertools.groupby(query, key = str.isdigit)] # Update for radio stations with numbers in name
        
        if int(queries[1]) > len(self.stations):
            await ctx.send('>>> Priority cannot be higher than number of radio stations', delete_after = 30)
            
            return
        
        for station in self.stations:
            if station['title'].lower() == queries[0].lower():
                station_title = station['title']
                current_priority = station['priority']
                
                if current_priority == int(queries[1]):
                    await ctx.send('>>> **{}** already has priority **{}**'.format(station['title'], queries[1]), delete_after = 30)
                    
                    return
                
                break
        else:
            await ctx.send('>>> No radio station found named **{}**'.format(queries[0]), delete_after = 30)
                
            return
        
        for station in self.stations:
            if station['title'].lower() == queries[0].lower():
                station['priority'] = int(queries[1])
            else:
                if current_priority < int(queries[1]):
                    if current_priority < station['priority'] <= int(queries[1]):
                        station['priority'] -= 1
                else:
                    if int(queries[1]) <= station['priority'] < current_priority:
                        station['priority'] += 1
                        
        self.dump_stations()
        
        await ctx.send('>>> Changing priority of **{}** to **{}**'.format(station_title, queries[1]))
    
    @commands.command()
    async def lock(self, ctx):
        self.is_locked = True

        await ctx.send('>>> Locking **Radio**')

    @commands.command()
    async def unlock(self, ctx):
        self.is_locked = False
        
        await ctx.send('>>> Unlocking **Radio**')

    @commands.command()
    async def samuel(self, ctx):
        if ctx.voice_client.is_playing():
            ctx.voice_client.stop()
            
        ctx.voice_client.play(discord.FFmpegOpusAudio(os.getenv('SAMUEL'), bitrate = 96))
        
        while ctx.voice_client.is_playing():
            pass
            
        if self.current_station is not None:
            ctx.voice_client.play(discord.FFmpegOpusAudio(self.current_station['stream'], bitrate = self.bitrate))
        
        embed = discord.Embed(title = '( ͡° ͜ʖ ͡°)')
        
        embed.set_author(name = 'Samuel...', icon_url = 'https://emojipedia-us.s3.dualstack.us-west-1.amazonaws.com/thumbs/120/joypixels/275/manual-wheelchair_1f9bd.png')
        embed.set_thumbnail(url = 'https://media.tenor.com/images/75ed46f4833ddfd3316dd45d8fae1393/tenor.gif')

        await ctx.send(embed = embed)

    @commands.command()
    async def hititjoe(self, ctx):
        if ctx.voice_client.is_playing():
            ctx.voice_client.stop()
            
        ctx.voice_client.play(discord.FFmpegOpusAudio(os.getenv('HITITJOE'), bitrate = 96))
        
        while ctx.voice_client.is_playing():
            pass
            
        if self.current_station is not None:
            ctx.voice_client.play(discord.FFmpegOpusAudio(self.current_station['stream'], bitrate = self.bitrate))
        
        embed = discord.Embed(title = '( ͡° ͜ʖ ͡°)')
        
        embed.set_author(name = 'Hitting it...', icon_url = 'https://emojipedia-us.s3.dualstack.us-west-1.amazonaws.com/thumbs/120/joypixels/275/musical-keyboard_1f3b9.png')
        embed.set_thumbnail(url = 'https://i.imgur.com/IaUegDL.gif')

        await ctx.send(embed = embed)

    @commands.command()
    async def bitrate(self, ctx, *, query = None):
        if query is None:
            embed_author_name = 'Bitrate is set to...'
        else:
            self.bitrate = int(query) if int(query) > 0 and int(query) <= 96 else 96
            
            embed_author_name = 'Setting bitrate to...'

            if ctx.voice_client.is_playing():
                ctx.voice_client.stop()

                ctx.voice_client.play(discord.FFmpegOpusAudio(self.current_station['stream'], bitrate = self.bitrate))

        embed = discord.Embed(title = '{} kb/s'.format(self.bitrate), description = '(1 – 96 kb/s)')

        embed.set_author(name = embed_author_name, icon_url = 'https://emojipedia-us.s3.dualstack.us-west-1.amazonaws.com/thumbs/120/softbank/145/radio_1f4fb.png')

        await ctx.send(embed = embed)

        #await ctx.send('>>> Setting bitrate to **{}**'.format(self.bitrate))
    
    @play.before_invoke
    @random.before_invoke
    @samuel.before_invoke
    @hititjoe.before_invoke
    async def ensure_connected(self, ctx):
        if ctx.author.voice:
            if ctx.voice_client is not None:
                return await ctx.voice_client.move_to(channel)

            await ctx.author.voice.channel.connect()
        else:
            await ctx.send('>>> You are not connected to a voice channel', delete_after = 30)
                
            raise commands.CommandError('Author not connected to a voice channel')            
    
    @priority.before_invoke
    @lock.before_invoke
    @unlock.before_invoke
    @bitrate.before_invoke
    async def ensure_owner(self, ctx):
        if str(ctx.message.author) not in os.getenv('AUTHORS').split(','):
            await ctx.send('>>> You are not allowed to perform that command', delete_after = 30)
            
            raise commands.CommandError('Author not allowed to perform command')

    @play.before_invoke
    @pause.before_invoke
    @random.before_invoke
    @samuel.before_invoke
    @hititjoe.before_invoke
    @bitrate.before_invoke
    async def ensure_unlocked(self, ctx):
        if self.is_locked:
            await ctx.send('>>> Radio is locked', delete_after = 30)
            
            raise commands.CommandError('Radio is locked')

    @disconnect.after_invoke    
    async def cleanup(self, ctx):
        self.current_station = None
        self.bitrate = 96

bot = commands.Bot(command_prefix = commands.when_mentioned_or('!'))#, help_command = None)

@bot.event
async def on_ready():
    print('Logged in as {0} ({0.id})'.format(bot.user))

bot.add_cog(Radio(bot))
bot.run(os.getenv('TOKEN'))