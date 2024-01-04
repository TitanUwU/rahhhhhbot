import os
import sqlite3
from dotenv import load_dotenv
import discord
from discord.ext import commands


import requests
import praw
from discord.ext import commands
import asyncio
import aiohttp
import datetime
from datetime import datetime, timedelta

import random
import jishaku 
os.system("pip install gTTS")
from gtts import gTTS


load_dotenv()



PREFIX = "."
client = discord.Client(intents=discord.Intents.default())


intents = discord.Intents.all()


client = commands.Bot(command_prefix=[".", ",", "`"], intents=intents)
client.remove_command('help')
allowed_guild_ids = 1184559310622183564
allowed_user_ids = [1165895667110137876,420665593067208724]
snipe_cache = {}
chatting_users = set()
ALLOWED_USER_IDSP = [1165895667110137876]  # IDs of users allowed to run the command
voice_channel_states = {}
TARGET_USER_IDP = 798636380266692628
reddit = praw.Reddit(client_id="je29AZOuk_zhVkrw4r9m5Q",
                     client_secret="gKb_WbzUzy1AgYx1XQiqwFbN5sE21A",
                     username="OnionFeet",
                     user_agent="Onion123saber",
                     check_for_async=False)
activities = ["Happy 2024", "Happy New Year", "2024"]

@client.event
async def on_ready():
    print(f'Logged in as {client.user.name}')
    await cycle_activities()

async def cycle_activities():
    while True:
        for activity in activities:
            await client.change_presence(activity=discord.Game(name=activity))
            await asyncio.sleep(30)


ttsusers = [1165895667110137876, 798636380266692628, 1071718542782771230, 420665593067208724]
#trigger start
trigger_conn = sqlite3.connect('triggers.db')
trigger_cursor = trigger_conn.cursor()

trigger_cursor.execute('''
    CREATE TABLE IF NOT EXISTS triggers (
        id INTEGER PRIMARY KEY,
        server_id INTEGER,
        trigger_text TEXT,
        response_text TEXT,
        UNIQUE (server_id, trigger_text)
    )
''')
trigger_conn.commit()
@client.command(name='trigger', aliases=['triggers'])
@commands.has_permissions(manage_roles=True)
async def manage_trigger(ctx, action: str, *, args: str):
    args_list = args.split()

    if len(args_list) < 2:
        await ctx.send('Please provide both trigger and response.')
        return

    trigger_text = args_list[0]
    response_text = ' '.join(args_list[1:])

    server_id = ctx.guild.id

    if action.lower() == 'add':
        # Add a new trigger to the database
        trigger_cursor.execute('INSERT INTO triggers (server_id, trigger_text, response_text) VALUES (?, ?, ?)',
                       (server_id, trigger_text.lower(), response_text))
        trigger_conn.commit()

        await ctx.send(f'Trigger "{trigger_text}" added successfully with response: "{response_text}"!')
    else:
        await ctx.send('Invalid action. Use `add`.')

@client.command(name='remove_trigger')
@commands.has_permissions(manage_roles=True)
async def remove_trigger(ctx, trigger_id: int):
    server_id = ctx.guild.id

    # Remove a trigger from the database by ID
    trigger_cursor.execute('DELETE FROM triggers WHERE id = ? AND server_id = ?', (trigger_id, server_id))
    trigger_conn.commit()

    await ctx.send(f'Trigger with ID {trigger_id} removed successfully!')

@client.command(name='list_triggers')
@commands.has_permissions(manage_roles=True)
async def list_triggers(ctx):
    server_id = ctx.guild.id

    # Fetch all triggers for the specified server
    trigger_cursor.execute('SELECT id, trigger_text, response_text FROM triggers WHERE server_id = ?', (server_id,))
    triggers = trigger_cursor.fetchall()

    if not triggers:
        await ctx.send('No triggers found for this server.')
    else:
        trigger_list = '\n'.join([f"ID: {trigger[0]}, Trigger: {trigger[1]}, Response: {trigger[2]}" for trigger in triggers])
        await ctx.send(f'Triggers for this server:\n{trigger_list}')

@client.event
async def on_message(message):
    if not message.author.bot:
        server_id = message.guild.id
        message_content = message.content.lower()

        # Check if the message content matches any triggers in the database
        trigger_cursor.execute('SELECT response_text FROM triggers WHERE server_id = ? AND trigger_text = ?',
                       (server_id, message_content))
        response = trigger_cursor.fetchone()

        if response:
            await message.channel.send(response[0])

    await client.process_commands(message)

#trigger end



#warn start




conn = sqlite3.connect('warnings.db')
cursor = conn.cursor()

# Create a table for warnings if it doesn't exist
cursor.execute('''
    CREATE TABLE IF NOT EXISTS warnings (
        id INTEGER PRIMARY KEY,
        user_id INTEGER,
        reason TEXT
    )
''')
conn.commit()
if not hasattr(client, 'warnings'):
  client.warnings = {}

@client.command(name='warn')
@commands.has_permissions(kick_members=True)
async def warn(ctx, user: discord.User, *, reason: str):
  # Check if the user is trying to warn themselves
  if ctx.author.id == user.id:
      await ctx.send(f'You cannot warn yourself.')
      return

  # Insert the new warning into the database
  cursor.execute('INSERT INTO warnings (user_id, reason) VALUES (?, ?)', (user.id, reason))
  conn.commit()

  await ctx.send(f'User {user.mention} has been warned. Reason: {reason}')

@client.command(name='list_warns')
@commands.has_permissions(kick_members=True)
async def list_warns(ctx, user: discord.User):
  # Fetch all warnings for the specified user
  cursor.execute('SELECT * FROM warnings WHERE user_id = ?', (user.id,))
  user_warnings = cursor.fetchall()

  if not user_warnings:
      await ctx.send(f'{user.mention} has no warnings.')
  else:
      # Display the list of warnings
      warning_list = '\n'.join([f"ID: {warn[0]}, Reason: {warn[2]}" for warn in user_warnings])
      await ctx.send(f'{user.mention}\'s warnings:\n{warning_list}')

@client.command(name='remove_warn')
@commands.has_permissions(kick_members=True)
async def remove_warn(ctx, user: discord.User, warn_id: int):
  # Check if the specified warning ID exists
  cursor.execute('SELECT * FROM warnings WHERE id = ? AND user_id = ?', (warn_id, user.id))
  warning = cursor.fetchone()

  if not warning:
      await ctx.send(f'Warning with ID {warn_id} not found for {user.mention}.')
      return

  # Prevent users from removing their own warnings
  if user.id == warning[1]:
      await ctx.send(f'You cannot remove your own warning.')
      return

  # Remove the warning from the database
  cursor.execute('DELETE FROM warnings WHERE id = ?', (warn_id,))
  conn.commit()

  await ctx.send(f'Warning with ID {warn_id} removed for {user.mention}.')



#warn end
#tts
@client.command(name='tts')
async def text_to_speech(ctx, *, text):
    # Delete the user's command message
    await ctx.message.delete()

    # Check if the user is in the ttsusers array
    if ctx.author.id not in ttsusers:
        await ctx.send("You are not authorized to use this command.")
        return

    # Check if the text is provided
    if not text:
        await ctx.send("Please provide text to convert to speech.")
        return

    # Create a gTTS object
    tts = gTTS(text=text, lang='en', slow=False)

    # Save the TTS audio as an MP3 file
    tts.save('tts_output.mp3')

    # Send "File ready" message and delete it
    file_ready_message = await ctx.send("File ready")
    await asyncio.sleep(1)  # Adjust the delay if needed
    await file_ready_message.delete()

    # Send the MP3 file to the Discord channel
    await ctx.send(file=discord.File('tts_output.mp3'))

    # Remove the TTS audio file
    os.remove('tts_output.mp3')

# tts2

#role
@client.command(name='role')
@commands.has_permissions(manage_roles=True)
async def role(ctx, member: discord.Member = None, *, role):
    if member is None:
        await ctx.send('Please mention a member or provide a valid user ID.')
        return

    role_obj = None
    try:
        role_obj = discord.utils.get(ctx.guild.roles, mention=role) or discord.utils.get(ctx.guild.roles, id=int(role))
    except:
        pass

    if not role_obj:
        await ctx.send('Invalid role. Mention the role or provide a valid role ID.')
        return

    if ctx.author.top_role <= member.top_role:
        await ctx.send("You can't modify roles for users with a higher or equal role.")
        return

    if role_obj in member.roles:
        await member.remove_roles(role_obj)
        await ctx.send(f'{role_obj.name} role removed from {member.display_name}.')
    else:
        await member.add_roles(role_obj)
        await ctx.send(f'{role_obj.name} role added to {member.display_name}.')

@role.error
async def role_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("You don't have the `manage_roles` permission to use this command.")
    elif isinstance(error, commands.MemberNotFound):
        await ctx.send("Member not found.")
    elif isinstance(error, commands.RoleNotFound):
        await ctx.send("Role not found.")
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("Missing arguments. Usage: `!role @member @role` or `!role user_id role_id`.")

@client.command(name='fish')
async def react_to_last_messages(ctx):
  # Check if the command sender's ID is in the allowed list
  if ctx.author.id in ALLOWED_USER_IDSP:
    target_user = client.get_user(TARGET_USER_IDP)
    if target_user:
      async for previous_message in ctx.channel.history(limit=10):
        # Check if the message author is the target user
        if previous_message.author.id == TARGET_USER_IDP:
          # React to the last 10 messages from the target user with a fish emoji
          await previous_message.add_reaction('🐟')  # Fish emoji
      await ctx.send(
          f"Fish reaction added to the last 10 messages from {target_user.name}!"
      )
    else:
      await ctx.send("Could not find the target user.")
  else:
    await ctx.send("You are not allowed to use this command.")


###@client.command()
#  async def animefeet(ctx):
  #  if ctx.author.id not in allowed_user_ids:
  #    await ctx.send("You are not authorized to use this command.")
  #    return
  
   # subreddit = reddit.subreddit("AnimeFeets")
  #  all_subs = list(subreddit.top(limit=100))
  
  #  if not all_subs:
  #    await ctx.send("No submissions found in the subreddit.")
   #   return
  
   # random_sub = random.choice(all_subs)
   ## name = random_sub.title
    #url = random_sub.url
  
   # embed = discord.Embed(title=name)
  ##  embed.set_image(url=url)
  #
   # await ctx.send(embed=embed)

###



@client.command(name='help')
async def help(ctx):
  embed = discord.Embed()
  embed.add_field(name=".mute", value="mutes user", inline=False)
  embed.add_field(name=".unmute", value="unmutes user", inline=False)
  embed.add_field(name=".kick", value="kicks user", inline=False)
  embed.add_field(name=".ban", value="bans user", inline=False)
  embed.add_field(name=".lock", value="locks channel", inline=False)
  embed.add_field(name=".unlock", value="unlocks channel", inline=False)
  embed.add_field(name=".purge", value="purges msgs", inline=False)
  embed.add_field(name=".role", value="adds or removes role of user", inline=False)

  await ctx.send(embed=embed)


#dog
@client.command(name='dog')
async def dog(ctx):
  async with aiohttp.ClientSession() as session:
    async with session.get(
        'https://api.thedogapi.com/v1/images/search') as response:
      data = await response.json()
      dog_url = data[0]['url']

  embed = discord.Embed(title='Random Dog Picture',
                        color=discord.Color.orange())
  embed.set_image(url=dog_url)

  await ctx.send(embed=embed)


#cat
@client.command(name='cat')
async def cat(ctx):
  async with aiohttp.ClientSession() as session:
    async with session.get(
        'https://api.thecatapi.com/v1/images/search') as response:
      data = await response.json()
      cat_url = data[0]['url']

  embed = discord.Embed(title='Random Cat Picture',
                        color=discord.Color.orange())
  embed.set_image(url=cat_url)

  await ctx.send(embed=embed)


#unmute


#ban
@client.command(aliases=['fuckoff', 'kill', 'demolish'])
@commands.has_permissions(ban_members=True)
async def ban(ctx, member: discord.Member, *, reason=None):
    if member is None:
        await ctx.send("Please mention a member to ban.")
        return
    if ctx.message.author.top_role <= member.top_role and ctx.message.author.id != ctx.guild.owner_id:
        await ctx.send("You cannot ban someone with a higher or equal role.")
    elif ctx.guild.owner_id == member.id:
        await ctx.send("You cannot ban the server owner.")
    else:
        # Modify the reason to include the user who ran the command
        full_reason = f'{ctx.author.display_name} banned {member.display_name}'
        if reason:
            full_reason += f' for {reason}'

        await member.ban(reason=full_reason)
        await ctx.send(f'{member.display_name} has been banned. Reason: {full_reason}')


@ban.error
async def ban_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("You don't have permission to use this command.")
    elif isinstance(error, commands.BadArgument):
        await ctx.send("Member not found or invalid input.")


#unban
@client.command()
@commands.has_permissions(ban_members=True)
async def unban(ctx, member_id: int):
  # Get the banned users from the server's bans
  banned_users = await ctx.guild.bans()

  # Check if the provided member ID is in the banned users list
  banned_member = discord.utils.get(banned_users, user__id=member_id)

  if banned_member:
    await ctx.guild.unban(banned_member.user)
    await ctx.send(f'{banned_member.user.name} has been unbanned.')
  else:
    await ctx.send('User not found in the ban list.')


@unban.error
async def unban_error(ctx, error):
  if isinstance(error, commands.MissingPermissions):
    await ctx.send("You don't have permission to use this command.")
  elif isinstance(error, commands.BadArgument):
    await ctx.send("Invalid input. Please provide a valid member ID.")


#kick
@client.command(name='kick')
@commands.has_permissions(kick_members=True)
async def kick(ctx, member: discord.Member, *, reason=None):
    if member is None:
        await ctx.send("Please mention a member to kick.")
        return

    if ctx.message.author.top_role <= member.top_role and ctx.message.author.id != ctx.guild.owner_id:
        await ctx.send("You cannot kick someone with a higher or equal role.")
    elif ctx.guild.owner_id == member.id:
        await ctx.send("You cannot kick the server owner.")
    else:
        # Modify the reason to include the user who ran the command
        full_reason = f'{ctx.author.display_name} kicked {member.display_name}'
        if reason:
            full_reason += f' for {reason}'

        await member.kick(reason=full_reason)
        await ctx.send(f'{member.display_name} has been kicked. Reason: {full_reason}')


@kick.error
async def kick_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("You don't have permission to use this command.")
    elif isinstance(error, commands.BadArgument):
        await ctx.send("Member not found or invalid input.")

@client.command()
async def bam(ctx, member: discord.Member):
  if ctx.message.author.top_role <= member.top_role and ctx.message.author.id != ctx.guild.owner_id:
    await ctx.send("You cannot bam someone with a higher or equal role.")
  elif ctx.guild.owner_id == member.id:
    await ctx.send("You cannot bam the server owner.")
  else:

    await ctx.send(f'{member.display_name} has been bammed.')


#lock
@client.command(name='lockchannel', aliases=['lock'])
@commands.has_permissions(manage_channels=True
                          )  # Check for the "Manage Channels" permission
async def lock_channel(ctx, channel: discord.TextChannel = None):
  if channel is None:
    channel = ctx.channel

  overwrite = channel.overwrites_for(ctx.guild.default_role)
  overwrite.send_messages = False
  await channel.set_permissions(ctx.guild.default_role, overwrite=overwrite)
  await ctx.send(
      f'This channel {channel.mention} has been locked. Only users with the "Manage Channels" permission can send messages.'
  )


# Error handling for missing permissions
@lock_channel.error
async def lock_channel_error(ctx, error):
  if isinstance(error, commands.MissingPermissions):
    await ctx.send(
        'You do not have the "Manage Channels" permission to use this command.'
    )


@client.command(name='unlockchannel', aliases=['unlock'])
@commands.has_permissions(manage_channels=True
                          )  # Check for the "Manage Channels" permission
async def unlock_channel(ctx, channel: discord.TextChannel = None):
  if channel is None:
    channel = ctx.channel

  overwrite = channel.overwrites_for(ctx.guild.default_role)
  overwrite.send_messages = True
  await channel.set_permissions(ctx.guild.default_role, overwrite=overwrite)
  await ctx.send(
      f'The channel {channel.mention} has been unlocked. Users can now send messages.'
  )


# Error handling for missing permissions
@unlock_channel.error
async def unlock_channel_error(ctx, error):
  if isinstance(error, commands.MissingPermissions):
    await ctx.send(
        'You do not have the "Manage Channels" permission to use this command.'
    )


#purge
@client.command(name='purge', aliases=['clear'])
@commands.has_permissions(manage_messages=True)
                            # Check for the "Manage Messages" permission
async def purge(ctx, amount: int):
  if amount <= 0:
    await ctx.send("Please provide a positive number of messages to purge.")
    return

  deleted_messages = await ctx.channel.purge(
      limit=amount + 1)  # Add 1 to include the command message
  purge_message = await ctx.send(
      f'{len(deleted_messages) - 1} messages have been purged.')

  # Delete the bot's response message after 5 seconds
  await asyncio.sleep(5)
  await purge_message.delete()


@purge.error
async def purge_error(ctx, error):
  if isinstance(error, commands.MissingPermissions):
    await ctx.send("You don't have permission to use this command.")
  elif isinstance(error, commands.BadArgument):
    await ctx.send(
        "Invalid argument. Please provide a positive number of messages to purge."
    )
@client.command(name="nick", aliases=["nickname"])
@commands.has_permissions(manage_nicknames=True) 
async def change_nickname(ctx, member: discord.Member, *, new_nickname: str = None):
    try:
        if new_nickname is not None:
            await member.edit(nick=new_nickname)
            await ctx.send(f"Nickname of {member.mention} has been changed to `{new_nickname}`.")
        else:
            await member.edit(nick=None)
            await ctx.send(f"Nickname of {member.mention} has been reset.")
    except discord.Forbidden:
        await ctx.send("I don't have permission to change the nickname.")
    except discord.HTTPException as e:
        await ctx.send(f"An error occurred: {e}")


#mute

@client.command(name='snipe')
async def snipe(ctx):
  channel_id = ctx.channel.id
  if channel_id not in snipe_cache:
    await ctx.send("No deleted messages to snipe.")
    return

  deleted_message = snipe_cache[channel_id]
  author_name = deleted_message.author.display_name
  content = deleted_message.content

  embed = discord.Embed(title=f"Sniped Message by {author_name}",
                        description=content,
                        color=discord.Color.red())
  await ctx.send(embed=embed)


@client.command(name='capybara')
async def capybara(ctx):
  async with aiohttp.ClientSession() as session:
    async with session.get(
        'https://api.capy.lol/v1/capybara?json=true') as response:
      data = await response.json()
      capybara_url = data.get('data', {}).get('url')

  if capybara_url:
    embed = discord.Embed(title='Random Capybara Picture',
                          color=discord.Color.orange())
    embed.set_image(url=capybara_url)

    await ctx.send(embed=embed)
  else:
    await ctx.send('Failed to fetch a capybara picture.')






#bops
@client.command(name='ambatukam')
async def ambatukam(ctx):
  with open('bop.txt', 'r') as file:
    image_links = file.read().splitlines()

  random_image = random.choice(image_links)

  embed = discord.Embed(title="Bopsical asked for this", color=0x00ff00)
  embed.set_image(url=random_image)

  await ctx.send(embed=embed)






#bingus bullying me
#timeout





# Importing the timedelta class from the datetime module
@client.command(aliases=['stfu', 'shut', 'donttalk','mute'])
@commands.has_permissions(kick_members=True)
async def timeout(ctx, member: discord.Member, duration: str = "1h", *, reason: str = "No reason provided"):
    # Check role hierarchy within if statement
    if ctx.author.top_role > member.top_role:
        # Convert duration to seconds
        seconds = 0
        if duration[-1] == 's':
            seconds = int(duration[:-1])
        elif duration[-1] == 'm':
            seconds = int(duration[:-1]) * 60
        elif duration[-1] == 'h':
            seconds = int(duration[:-1]) * 3600
        elif duration[-1] == 'd':
            seconds = int(duration[:-1]) * 86400  # Convert days to seconds

        # Calculate the end time of the timeout
        end_time = datetime.utcnow() + timedelta(seconds=seconds)

        # Apply timeout
        await member.timeout(end_time, reason=reason)
        await ctx.send(f'Timeout applied to {member.mention} for {duration} due to: {reason}')
    else:
        await ctx.send("You don't have the necessary permissions to timeout this member.")
@client.command(aliases=['unshut', 'unmute', 'talkagain'])
@commands.has_permissions(kick_members=True)
async def untimeout(ctx, member: discord.Member):

    if ctx.author.top_role > member.top_role:

        await member.edit(timed_out_until=None)

        await ctx.send(f'Untimeout applied to {member.mention}')
    else:
        await ctx.send("You don't have the necessary permissions to untimeout this member.")

#warn shit

token = os.getenv("DISCORD_TOKEN")


client.run(token)



conn.close()
trigger_conn.close()

