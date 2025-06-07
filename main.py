import os
import sys
import discord
import json
import random
import asyncio
import math
import time
from discord.ext import commands

from threading import Thread

from flask import Flask

app = Flask(__name__)
@app.route('/')

warnings = {}

def home():
    return "Bot is running!"

def run_web():
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)

Thread(target=run_web).start()

intents = discord.Intents.all()
intents.messages = True

disabled_commands = []

bot = commands.Bot(command_prefix=lambda bot, message: "!", intents=intents)

@bot.event
async def on_ready():
    guild = discord.Object(id=1292978415552434196)
    try:
        synced = await bot.tree.sync()
    except Exception as e:
        pass

@bot.event
async def on_disconnect():
    print("Bot disconnected. Attempting to reconnect in 5 seconds...")
    await asyncio.sleep(5)

@bot.event
async def on_resumed():
    print("Bot reconnected!")

@bot.event
async def on_message(msg):
    if msg.author == bot.user or msg.author.bot:
        return
    
    user_id = msg.author.id

    await msg.channel.send(embed=discord.Embed(
        color=int("50B4E6", 16),
        description=f"annoying message"
    ).set_author(name=msg.author.name, icon_url=msg.author.avatar.url))
    
    await bot.process_commands(msg)

@bot.command(help="Warn a user.", aliases=["wn"])
async def warn(ctx, name: str = None, reason: str = ""):
    user = None
    if name is None:
        user = ctx.author
    else:
        matching_names = []
        for member in ctx.guild.members:
            if name.lower() in member.name.lower() and not member.bot:
                matching_names.append(member.name)
        if matching_names:
            if len(matching_names) > 1:
                msg = ""
                for i, n in enumerate(matching_names):
                    msg += str(i + 1) + ". " + n
                    if i != len(matching_names) - 1:
                        msg += "\n"
                try:
                    await ctx.send(embed=discord.Embed(
                        color=int("50B4E6", 16),
                        description=f"Mutiple users found. Please select a user below, or type cancel:\n{msg}"
                    ).set_author(name=ctx.author.name, icon_url=ctx.author.avatar.url))

                    selection = None
                    response = await bot.wait_for('message', check=lambda msg: msg.channel == ctx.channel and msg.author == ctx.author, timeout=15.0)

                    if "cancel" in response.content.lower():
                        await ctx.send(embed=discord.Embed(
                            color=int("FA3939", 16),
                            description="❌ The command has been canceled."
                        ).set_author(name=ctx.author.name, icon_url=ctx.author.avatar.url))
                        return
                    try:
                        selection = int(response.content)
                    except ValueError:
                        await ctx.send(embed=discord.Embed(
                            color=int("FA3939", 16),
                            description="❌ Invalid selection."
                        ).set_author(name=ctx.author.name, icon_url=ctx.author.avatar.url))
                        return
                    else:
                        if selection is not None:
                            if (selection - 1) >= 0 and (selection - 1) <= (len(matching_names) - 1):
                                matching_name = matching_names[selection - 1]
                                for member in ctx.guild.members:
                                    if member.name.lower() == matching_name.lower():
                                        user = member
                                        break
                            else:
                                await ctx.send(embed=discord.Embed(
                                    color=int("FA3939", 16),
                                    description="❌ Invalid selection."
                                ).set_author(name=ctx.author.name, icon_url=ctx.author.avatar.url))
                                return
                except asyncio.TimeoutError:
                    await ctx.send(embed=discord.Embed(
                        color=int("FA3939", 16),
                        description="⏳ The command has been canceled because you took too long to reply."
                    ).set_author(name=ctx.author.name, icon_url=ctx.author.avatar.url))
                    return
            else:
                for member in ctx.guild.members:
                    if member.name.lower() == matching_names[0].lower():
                        user = member
                        break
    if user is not None:
        if !user.bot:
            user_warnings = warnings[user.id]
    
            if !user_warnings:
                warnings[user.id] = {amount: 1, reason: reason}
            else:
                user_warnings.amount += 1
    
            warning_amount = user_warnings.amount
            
            await ctx.send(embed=discord.Embed(
                color=int("50B4E6", 16),
                description=f"✅ Sucessfully warned **{user.name}**! {user.name} now has {warning_amount} warnings!"
            )).set_author(name=ctx.author.name, icon_url=ctx.author.avatar.url))
        else:
            await ctx.send(embed=discord.Embed(
                color=int("FA3939", 16),
                description=f"❌ Cannot warn **{user.name}** because it is a bot!"
            )).set_author(name=ctx.author.name, icon_url=ctx.author.avatar.url))

@bot.command(help="View the warnings of a user.", aliases=["view_warn", "view_w", "vw"])
async def view_warnings(ctx, name: str = None):
    user = None
    if name is None:
        user = ctx.author
    else:
        matching_names = []
        for member in ctx.guild.members:
            if name.lower() in member.name.lower() and not member.bot:
                matching_names.append(member.name)
        if matching_names:
            if len(matching_names) > 1:
                msg = ""
                for i, n in enumerate(matching_names):
                    msg += str(i + 1) + ". " + n
                    if i != len(matching_names) - 1:
                        msg += "\n"
                try:
                    await ctx.send(embed=discord.Embed(
                        color=int("50B4E6", 16),
                        description=f"Mutiple users found. Please select a user below, or type cancel:\n{msg}"
                    ).set_author(name=ctx.author.name, icon_url=ctx.author.avatar.url))

                    selection = None
                    response = await bot.wait_for('message', check=lambda msg: msg.channel == ctx.channel and msg.author == ctx.author, timeout=15.0)

                    if "cancel" in response.content.lower():
                        await ctx.send(embed=discord.Embed(
                            color=int("FA3939", 16),
                            description="❌ The command has been canceled."
                        ).set_author(name=ctx.author.name, icon_url=ctx.author.avatar.url))
                        return
                    try:
                        selection = int(response.content)
                    except ValueError:
                        await ctx.send(embed=discord.Embed(
                            color=int("FA3939", 16),
                            description="❌ Invalid selection."
                        ).set_author(name=ctx.author.name, icon_url=ctx.author.avatar.url))
                        return
                    else:
                        if selection is not None:
                            if (selection - 1) >= 0 and (selection - 1) <= (len(matching_names) - 1):
                                matching_name = matching_names[selection - 1]
                                for member in ctx.guild.members:
                                    if member.name.lower() == matching_name.lower():
                                        user = member
                                        break
                            else:
                                await ctx.send(embed=discord.Embed(
                                    color=int("FA3939", 16),
                                    description="❌ Invalid selection."
                                ).set_author(name=ctx.author.name, icon_url=ctx.author.avatar.url))
                                return
                except asyncio.TimeoutError:
                    await ctx.send(embed=discord.Embed(
                        color=int("FA3939", 16),
                        description="⏳ The command has been canceled because you took too long to reply."
                    ).set_author(name=ctx.author.name, icon_url=ctx.author.avatar.url))
                    return
            else:
                for member in ctx.guild.members:
                    if member.name.lower() == matching_names[0].lower():
                        user = member
                        break
    if user is not None:
        pass
        
