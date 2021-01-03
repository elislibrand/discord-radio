import os
import discord
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()

class Radio(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    #@commands.command(aliases = ['h'])
    #async def help(self, ctx):
    #    await ctx.send('\n'.join([method for method in set(dir(self)) if callable(getattr(self, method)) and method.startswith('__') is False]))

    @commands.command()
    async def connect(self, ctx):
        channel = ctx.author.voice.channel
        
        if ctx.voice_client is not None:
            return await ctx.voice_client.move_to(channel)

        await channel.connect()

    @commands.command()
    async def disconnect(self, ctx):
        await ctx.voice_client.disconnect()

    @commands.command(aliases = ['p'])
    async def play(self, ctx):
        ctx.voice_client.play(discord.PCMVolumeTransformer(original = discord.FFmpegPCMAudio('http://fm05-ice.stream.khz.se/fm05_aac'),
                                                           volume = 1.0))
        
        await ctx.send('>>> Tuning in to **{}**'.format('Star FM'))

    @play.before_invoke
    async def ensure_voice(self, ctx):
        if ctx.voice_client is None:
            if ctx.author.voice:
                await ctx.author.voice.channel.connect()
            else:
                await ctx.send('You are not connected to a voice channel.')
                
                raise commands.CommandError('Author not connected to a voice channel.')
        elif ctx.voice_client.is_playing():
            ctx.voice_client.stop()
        
bot = commands.Bot(command_prefix = commands.when_mentioned_or('#'))#, help_command = None)

@bot.event
async def on_ready():
    print('Logged in as {0} ({0.id})'.format(bot.user))

bot.add_cog(Radio(bot))
bot.run(os.getenv('TOKEN'))