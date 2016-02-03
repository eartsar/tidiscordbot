import discord
import asyncio
import os
import sys
import traceback
import json
import re
import random
import logging
import time
import requests
import urbandict
import flickrapi
import microsofttranslator
from urllib.request import FancyURLopener
from ti_poll import Poll
from ti_traffic import TrafficLight
from ti_twitter import TwitterPoll
from discord.ext import commands


try:
    import configparser
except ImportError:
    import configparser as configparser


# TheCatAPI.com information
CAT_API_URL = "http://thecatapi.com/api/images/get"
CAT_API_KEY = ""

# Microsoft Translate access
mstranslate_api = None

# Flickr API access
flickr_api = None

# The actual API client that deals with Discord events.
logger = logging.getLogger('discord')
logger.setLevel(logging.DEBUG)
handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)

# Object to manage poll tracking
currentPoll = None

# Object to manage spam tracking
trafficLight = TrafficLight()

# Dictionary of "!function" to cmd_function(message) handlers.
handlers = None

tidesc = "Ti bot!"
bot = commands.Bot(command_prefix='!', description=tidesc)


# @bot.event
# async def on_message(message):
#     global handlers

#     if not handlers:
#         print("on_message abort - handlers dict not populated")
#         return

#     # for non PMs bot commands, manage spammage
#     if not isinstance(message.channel, discord.channel.PrivateChannel) and message.content.startswith("!"):
#         proceed = trafficLight.log(client, message.author)
#         if not proceed:
#             return

#     tokens = message.content.split(" ")
#     cmd_token = tokens[0]
#     if cmd_token not in handlers:
#         return

#     # call the handler
#     handlers[cmd_token](message)
    

@bot.event
async def on_ready():
    print(('Logged in as %s' % bot.user.name))
    print((bot.user.id))
    print('------')


@bot.event
async def on_status(member):
    # update the last seen data file
    print("!seen tracking - " + member.name + " - status: " + member.status)

    with open("seen.dat", "r") as f:
        data = json.loads(f.read())

    data[member.name.lower()] = time.time()

    with open("seen.dat", "w") as f:
        f.write(json.dumps(data))
    
    print("    seen.dat file updated")


@bot.command(name="test")
async def cmd_test():
    """
    **!test**

    Usage:
      !test

    Tests to make sure the bot is listening to messages.
    """
    await bot.say('Ti Discord Bot is up and running!')


@bot.command(name="cat")
async def cmd_cat():
    """
    **!cat**

    Usage:
      !cat

    Post a random picture (png format) of a cat. See **!catgif** for moar cats.
    """
    await _cmd_cat()


@bot.command(name="catgif")
async def cmd_catgif():
    """
    **!catgif**

    Usage:
      !catgif

    Post a random picture (gif format) of a cat. See **!cat** for moar cats.
    """
    await _cmd_cat(file_type="gif")


async def _cmd_cat(file_type="png"):
    """Do work function for cats."""
    r = requests.get(CAT_API_URL, {"api_key": CAT_API_KEY, "format": "src", "type": file_type, "size": "small"})
    await bot.say(r.url)


@bot.command(pass_context=True, name="boat")
async def cmd_boat(ctx):
    """
    **!boat**

    Usage:
      !boat [thing[++] | thing[--]]

    Example:
      !boat
      !boat fura
      !boat drakeon--

    Upboats/downboats a thing. Note that this need not be a user - it can 
    be *anything*. Not specifying a thing will show the top 5 upboated and 
    bottom 5 downboated things. Specifying a thing, but no ++/-- operation 
    will display that thing's boat count.

    ***!upboat*** *and* ***!downboat*** *are shorthands for this command.*
    """
    message = ctx.message
    content = message.content

    # load the data as json
    with open("boats.dat", "r") as f:
        data = json.loads(f.read())

    thing = content[len("!boat "):].strip()
    # use lower for key access
    kthing = thing.lower()

    # !boat - list all boats
    if not thing:
        bottom_keys = sorted(data, key=data.get)
        top_keys = bottom_keys[::-1]

        s = "Top 5 upboated things:\n"
        for k in top_keys[:5]:
            s = s + k.lower() + ": " + str(data[k]) + "\n"

        s = s + "\n\nBottom 5 downboated things:\n"
        for k in bottom_keys[:5]:
            s = s + k.lower() + ": " + str(data[k]) + "\n"
        
        await bot.say(s)
        return
    
    op = thing[-2:]

    # !karma ++  not allowed!
    if op == thing:
        return

    # !boat <thing> - list the boat of the thing
    if op not in ("++", "--"):
        if kthing in data:
            await bot.say(thing[0].upper() + thing[1:] + " has " + str(data[kthing]) + " boats.")
        return

    thing = thing[:-2]
    await _cmd_boat(message, thing, op, data)


async def _cmd_boat(message, thing, op, data):
    """Does the actual incrementing of the boats, and prints stuff."""
    kthing = thing.lower()
    sop = ""
    if op == "++":
        sop = "Upboats"
        if kthing not in data:
            data[kthing] = 1
        else:
            data[kthing] = data[kthing] + 1
    elif op == "--":
        sop = "Downboats"
        if kthing not in data:
            data[kthing] = -1
        else:
            data[kthing] = data[kthing] - 1

    await bot.say(sop + " for " + thing + "! " + thing[0].upper() + thing[1:] + " now has " + str(data[kthing]) + " boats.")
    with open("boats.dat", "w") as f:
        f.write(json.dumps(data))


@bot.command(pass_context=True, name="upboat")
async def cmd_upboat(ctx):
    """
    **!upboat**

    Usage:
      !upboat <thing>

    Example:
      !upboat fura
    
    Shorthand for **!boat <thing>++**
    """
    await cmd_shortboat(ctx)


@bot.command(pass_context=True, name="downboat")
async def cmd_downboat(ctx):
    """
    **!downboat**

    Usage:
      !downboat <thing>

    Example:
      !downboat fura
    
    Shorthand for **!boat <thing>--**
    """
    await cmd_shortboat(ctx)


async def cmd_shortboat(ctx):
    """Do work function of upboat/downboat shorthand functions."""
    message = ctx.message
    tokens = message.content.split(" ")
    cmd = tokens[0]
    thing = message.content[len(cmd):].strip()
    if not thing:
        return

    with open("boats.dat", "r") as f:
        data = json.loads(f.read())

    op = ""
    if cmd == "!upboat":
        op = "++"
    else:
        op = "--"
    await _cmd_boat(message, thing, op, data)


@bot.command(name="lookup")
async def cmd_lookup(word):
    """
    **!lookup**

    Usage:
      !lookup <term>

    Example:
      !lookup ironically

    Looks up the term on Merriam-Webster's online dictionary.
    And by Merriam-Webster, we do mean Urban Dictionary.
    """
    response = ""
    entry = urbandict.define(word)[0]

    if "There aren't any definitions for " in entry["def"]:
        return

    response = "**" + entry["word"].strip() + "**\n"
    response += entry["def"].strip() + "\n"
    if entry["example"].strip() != "":
        response += "*" + entry["example"].strip() + "*"

    # TODO: Need to make sure we're not sending unicode that the API can't handle here
    if response:
        try:
            await bot.say(response)
        except:
            print("Unicode error in !lookup()")
    return


@bot.command(pass_context=True, name="poll")
async def cmd_poll(ctx):
    """
    **!poll**

    Usage:
      !poll
      !poll <Question;Choice;Choice[;Choice...]>
      !poll close

    Example:
      !poll Ride zee Shoopuf?; Sure!; Nope.
      !poll Go left or right?;left;right

    Starts a poll. Users can vote on a choice using **!vote**.
    Typing **!poll** with no arguments will show the current poll.
    The *close* argument will end the poll. Note that only the poll's
    creator can close the poll for the first five minutes.

    *Only one poll may be active at a time.*
    """
    global currentPoll
    message = ctx.message
    opts = message.content[len("!poll "):].strip()

    if isinstance(message.channel, discord.channel.PrivateChannel):
        await bot.send_message(message.channel, "This command must be run in the general chat channel, not in a PM. Sorry!")
        return
    
    # !poll - display the poll
    if not opts:
        if currentPoll:
            await bot.send_message(message.channel, currentPoll.pretty_print())
        else:
            await bot.send_message(message.channel, "There is no poll underway.")
        return

    # !poll close - close the poll
    if opts == "close":
        if not currentPoll:
            await bot.send_message(message.channel, "There is no poll underway.")
        else:
            if currentPoll.can_close(message.author):
                await bot.send_message(message.channel, "**Poll closed!**\n" + currentPoll.pretty_print())
                currentPoll = None
            else:
                await bot.send_message(message.channel, "The poll is open for another %.0f seconds." % currentPoll.time_left())
        return

    if currentPoll:
        await bot.send_message(message.channel, "A poll is already underway. Let that one finish first before starting another.")
        return

    # !poll question;choice;choice...
    opts = [s.strip() for s in [x for x in opts.split(";") if x.strip() != ""]]

    if len(opts) < 3 or len(opts) > 9:
        return

    for i in range(len(opts)):
        opts[i] = opts[i].strip()


    currentPoll = Poll(message.author, opts[0], opts[1:])
    s = "**" + message.author.name + " starts a poll.**\n" + currentPoll.pretty_print()
    await bot.send_message(message.channel, s)


@bot.command(pass_context=True, name="vote")
async def cmd_vote(ctx, choice : int):
    """
    **!vote**

    Usage:
      !vote <choice>

    Example:
      !vote 2
    
    Votes for a choice in the current poll.
    """
    message = ctx.message
    if isinstance(message.channel, discord.channel.PrivateChannel):
        await bot.send_message(message.channel, "This command must be run in the general chat channel, not in a PM. Sorry!")
        return

    # if len(choice) != 1 or choice not in "1234566789":
    #     return

    if not currentPoll:
        await bot.send_message(message.channel, "There is no poll underway.")
    msg = message.author.name + " casts a vote for **" + str(choice) + "**."
    if currentPoll.already_voted(message.author.name):
        msg = message.author.name + " changes their vote to **" + str(choice) + "**."

    success = currentPoll.vote(message.author.name, choice)
    if not success:
        return
    await bot.send_message(message.channel, msg)


@bot.command(pass_context=True, name="seen")
async def cmd_seen(ctx):
    """
    **!seen**

    Usage:
      !seen <user>

    Example:
      !seen fura barumaru

    Checks to see the last time a particular user was
    seen online by ti-bot.

    *The user's name must be entered in full.*
    """
    message = ctx.message
    user = message.content[len("!seen "):].strip()
    key = user.lower()
    if not user:
        return

    f = open("seen.dat", "r")
    data = json.loads(f.read())
    f.close()

    # PMs are separate from servers, so running this in a PM doesn't make sense
    if isinstance(message.channel, discord.channel.PrivateChannel):
        await bot.say("This command must be run in the general chat channel, not in a PM. Sorry!")
        return

    found = [x for x in message.channel.server.members if x.status != discord.enums.Status.offline and x.name.lower() == key]

    # The user is currently online
    if len(found) > 0:
        await bot.say(user + " is currently **online**.")

        # Haven't seen the user - add to the dat
        if key not in data:
            with open("seen.dat", "r") as f:
                data = json.loads(f.read())
            data[user] = time.time()
            with open("seen.dat", "w") as f:
                f.write(json.dumps(data))
            return

    # The user isn't online, but hasn't been tracked
    if key not in data:
        await bot.say("I haven't seen " + user + " before.")
        return

    t = data[key]
    tdiff = time.time() - t
    days = tdiff // 86400
    hours = tdiff // 3600 % 24
    minutes = tdiff // 60 % 60
    seconds = tdiff % 60
    await bot.say(user[0].upper() + user[1:] + \
        " was last seen **%.0f days, %.0f hours, %.0f minutes, and %.0f seconds ago**." \
        % (days, hours, minutes, seconds))


@bot.command(pass_context=True, name="roll")
async def cmd_roll(ctx):
    """
    **!roll**

    Usage:
      !roll
      !roll <n>d<s>

    Example:
      !roll
      !roll 2d6

    Rolls N dice of S sides. Defaults to 1d20.

    *Also see* ***!coinflip*** and ***!random*** *for more random games.*
    """
    message = ctx.message
    opt = message.content[len("!roll "):].strip()

    num = None
    sides = None
    
    # same as !roll 1d20
    if not opt:
        num = 1
        sides = 20
        opt = "1d20"
    elif 'd' not in opt:
        return
    else:
        tokens = opt.split('d')
        num, sides = tokens[0], tokens[1]
        try:
            num = int(num)
            sides = int(sides)
        except:
            return
        if num < 1 or num > 10:
            return
        if sides < 3 or sides > 100:
            return

    results = [0 for _ in range(num)]
    for i in range(num):
        results[i] = random.randint(1, sides)

    results = [str(_) for _ in results]
    s = "*Dice roll! " + message.author.name + " rolls* ***" + opt + "!***\n    " + ", ".join(results)
    await bot.say(s)


@bot.command(name="coinflip")
async def cmd_coinflip():
    """
    **!coinflip**

    Usage:
      !coinflip

    Flips a two sided coin.

    *Also see* ***!roll*** and ***!random*** *for more random games.*
    """
    result = "heads"
    if random.randint(0, 1) == 1:
        result = "tails"

    s = "*" + message.author.name + " flips a coin...* ***" + str(result) + "!***"
    await bot.say(s)


@bot.command(name="random")
async def cmd_random():
    """
    **!random**

    Usage:
      !random

    Rolls between 1 and 99, Final Fantasy style.

    *Also see* ***!roll*** and ***!coinflip*** *for more random games.*
    """
    result = random.randint(1, 99)

    s = "*Dice roll! " + message.author.name + " rolls* ***" + str(result) + "!***"
    await bot.say(s)


@bot.command(pass_context=True, name="wipe")
async def cmd_wipe(ctx):
    """
    **!wipe**

    Usage:
      !wipe [number]

    Wipes a certain number of messages from the channel. By default, this is one.
    """
    message = ctx.message
    # TODO: check role
    if not isinstance(message.channel, discord.channel.PrivateChannel) and message.author.name != "Fura Barumaru":
        return

    opt = message.content[len("!wipe "):].strip()
    num = 1
    if opt:
        try:
            num = int(opt)
        except:
            return

    to_remove = [m for m in bot.logs_from(message.channel, limit=num + 1)]
    for log_message in to_remove:
        bot.delete_message(log_message)


@bot.command(pass_context=True, name="wipebot")
async def cmd_wipebot(ctx):
    """
    **!wipebot**

    Usage:
      !wipebot <number> <history>

    Example:
      !wipebot 10 2000

    Wipes a certain number of !cmd messages and bot responses from the channel.
    This crawls over *history* messages, deleting up to *number* of them that apply.
    """
    message = ctx.message
    # TODO: check role
    if not isinstance(message.channel, discord.channel.PrivateChannel) and message.author.name != "Fura Barumaru":
        return

    opts = message.content.split(" ")
    if len(opts) != 3:
        return
    history = None
    try:
        num = int(opts[1])
        history = int(opts[2])
    except:
        return

    to_remove = [m for m in bot.logs_from(message.channel, limit=history)]
    for log_message in to_remove:
        if log_message.author.name != "ti-bot" and not log_message.content.startswith("!"):
            continue
        bot.delete_message(log_message)


@bot.command(pass_context=True, name="flickr")
async def cmd_flickr(ctx):
    """
    **!flickr**

    Usage:
      !flickr
      !flickr <URL>

    Example:
      !flickr http://i.imgur.com/pTGdJej.jpg

    Command you can use to access your album in the Titanium FC Flickr account.
    Typing the command **!flickr** with no arguments will share your album in channel.
    Supplying a URL to the command will upload the image to your album.

    **Important!**
    - The URL **must be to the image file directly** (or a puu.sh URL).
    - The image must be **jpg** or a **png** file.
    - Uploading a picture for the first time will create your album. It will also set
          the album cover to this picture. This can be changed with **!flickrcover**
    - Misuse of this command will be met with Fura's wrath.
    """
    message = ctx.message
    link = message.content[len("!flickr "):].strip()

    # Yay for magic numbers
    flickr_user_id = '135801662@N07'

    album_name = message.author.name + "'s album"
    
    # Make sure the flickr api is valid
    if not flickr_api.token_valid(perms="write"):
        bot.send_message(message.channel, "**Flickr functionality requires renewed access. Contact Fura.**")
        return

    if not link:
        album_id = None
        for photoset in flickr_api.walk_photosets():
            if album_name == photoset.find('title').text:
                album_id = photoset.attrib['id']
        if album_id:
            album_link = "https://www.flickr.com/photos/" + flickr_user_id + "/albums/" + album_id
            bot.send_message(message.channel, message.author.name + " shares their album!\n" + album_link)
        return

    # Validate the linked image type
    ext = os.path.splitext(link)[1]
    if ext not in (".jpg", ".png"):
        return

    # We'll use a timestamp as the photo
    fname = "%.0f" % time.time() + ext

    # Grab the photo that was posted at the url
    try:
        # Force a user agent. Gets around puush cloudflare crap
        class MyOpener(FancyURLopener):
            version = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2227.1 Safari/537.36'
        MyOpener().retrieve(link, filename=fname)
    except:
        print("Exception thrown while downloading source file.")
        return

    # upload photo to flickr
    response = None
    try:
        with open(fname, 'rb') as f:
            response = flickr_api.upload(f.name, fileobj=f)
    except:
        print("Problem uploading " + fname)
        os.remove(fname)
        return

    # cleanup the file stored locally
    os.remove(fname)
    
    # Get the photo id
    photo_id = response.findtext('photoid')

    # Check to see if the poster has a flickr album already
    album_id = None
    for photoset in flickr_api.walk_photosets():
        if album_name == photoset.find('title').text:
            album_id = photoset.attrib['id']
    
    # We've uploaded before! Add our photo to our already existing album
    if album_id:
        flickr_api.photosets.addPhoto(photoset_id=album_id, photo_id=photo_id)
    else:
        # Create a new album with initial photo as this one
        flickr_api.photosets.create(title=album_name, primary_photo_id=photo_id)

    # Now that we've created it, we need to go looking again for the ID
    if not album_id:
        for photoset in flickr_api.walk_photosets():
            if album_name == photoset.find('title').text:
                album_id = photoset.attrib['id']

    # Get the link to share
    album_link = "https://www.flickr.com/photos/" + flickr_user_id + "/albums/" + album_id
    s = message.author.name + " has uploaded a new photo to their album!\n" + album_link
    bot.send_message(message.channel, s)
    return


@bot.command(pass_context=True, name="flickrcover")
async def cmd_flickrcover(ctx):
    """
    **!flickrcover**

    Usage:
      !flickrcover <image ID>

    Example:
      !flickr 20990689891

    Changes the cover of your album in the Titanium FC's Flickr account to another
    album image. You must have uploaded a picture using **!flickr** first, or else
    you will not have an album generated for you.

    **HOW TO FIND YOUR IMAGE ID**        
    1. Type **!flickr** for a link to your album.
    2. Click the link.
    3. Go to the image you desire to be your cover. **This must be in YOUR album!**
    4. Look at the URL for its ID.

    Example:
    /photos/135801662@N07/**COPY_THIS_NUMBER**/in/album-72157655600356143/
    """
    message = ctx.message
    photo_id = message.content[len("!flickrcover"):].strip()
    if not photo_id:
        return

    # Yay for magic numbers
    flickr_user_id = '135801662@N07'

    album_name = message.author.name + "'s album"
    
    # Make sure the flickr api is valid
    if not flickr_api.token_valid(perms="write"):
        bot.send_message(message.channel, "**Flickr functionality requires renewed access. Contact Fura.**")
        return

    # Check to see if the poster has a flickr album already
    album_id = None
    for photoset in flickr_api.walk_photosets():
        if album_name == photoset.find('title').text:
            album_id = photoset.attrib['id']
    
    # We've uploaded before! Add our photo to our already existing album
    if not album_id:
        return

    try:
        flickr_api.photosets.setPrimaryPhoto(photoset_id=album_id, photo_id=photo_id)
    except:
        bot.send_message(message.author, "Cannot set Flickr album cover. \
            Invalid image ID. Check **!help !flickrcover** for instructions.")
        return

    # Get the link to share
    album_link = "https://www.flickr.com/photos/" + flickr_user_id + "/albums/" + album_id
    s = "You changed your album cover successfully.\n" + album_link
    bot.send_message(message.author, s)
    return


@bot.command(pass_context=True, name="debug")
async def cmd_debug(ctx):
    message = ctx.message
    content = message.content.strip()[len("!debug "):]
    result = "```\n" + str(eval(content))  + "```\n"
    bot.send_message(message.channel, result)
    return


def get_channel(client, name):
    tixiv = None

    for server in bot.servers:
        if server.name == 'titanium-ffxiv':
            tixiv = server

    if not tixiv:
        return None

    for channel in tixiv.channels:
        if channel.name == name: #There are no hashtags in channel names
            return channel

    return None


def main():
    global handlers, alaises, CAT_API_KEY, flickr_api, mstranslate_api

    # Deal with the configuration file.
    config = configparser.ConfigParser()

    # Default Value
    DEF_VAL = 'REPLACE_ME'

    # Create it, if it doesn't exist.
    if not os.path.isfile("config.txt"):
        print("No config file found. Generating one - please fill out information in " + os.path.join(os.getcwd(), "config.txt"))
        with open('config.txt', 'w') as configfile:
            config['Discord'] = {'email': DEF_VAL, 'password': DEF_VAL}
            config['TheCatAPI.com'] = {'api_key': DEF_VAL}
            config['Twitter'] = {"consumer_key": DEF_VAL,
                                 "consumer_secret": DEF_VAL,
                                 "access_token_key": DEF_VAL,
                                 "access_token_secret": DEF_VAL}
            config['Twitter Feed'] = {'default_channel': "general"}
            config['Flickr'] = {'flickr_api_key': DEF_VAL, 'flickr_secret_key': DEF_VAL}
            config['Microsoft Translate'] = {'api_key': DEF_VAL, 'secret_key': DEF_VAL}
            config.write(configfile)
        return

    # Load in configuration information
    config.read('config.txt')
    email = config['Discord']['email']
    password = config['Discord']['password']
    CAT_API_KEY = config['TheCatAPI.com']['api_key']

    twitter_consumer_key = config['Twitter']['consumer_key']
    twitter_consumer_secret = config['Twitter']['consumer_secret']
    twitter_access_token_key = config['Twitter']['access_token_key']
    twitter_access_token_secret = config['Twitter']['access_token_secret']

    twitter_default_channel = config['Twitter Feed']['default_channel']

    FLICKR_API_KEY = config['Flickr']['api_key']
    FLICKR_SECRET_KEY = config['Flickr']['secret_key']

    MICROSOFT_TRANSLATE_API = config['Microsoft Translate']['api_key']
    MICROSOFT_TRANSLATE_SECRET = config['Microsoft Translate']['secret_key']

    mstranslate_api = microsofttranslator.Translator(MICROSOFT_TRANSLATE_API, MICROSOFT_TRANSLATE_SECRET)

    to_fill = [email, password, CAT_API_KEY, twitter_consumer_key, twitter_consumer_secret,
        twitter_access_token_key, twitter_access_token_secret, FLICKR_API_KEY, FLICKR_SECRET_KEY]

    # Prevent execution if the configuration file isn't complete
    for arg in to_fill:
        if arg == DEF_VAL:
            print("config.txt has not been fully completed. Fully fill out config.txt and re-run.")
            return

    # Create necessary files for data tracking
    # Boats (!boat)
    if not os.path.isfile("boats.dat"):
        with open('boats.dat', 'w') as f:
            f.write("{}")

    # Seen logs (!seen)
    if not os.path.isfile("seen.dat"):
        with open('seen.dat', 'w') as f:
            f.write("{}")

    # Populate the handler dictionary with function references.
    if not handlers:
        handlers = {}
        handlers["!boat"] = cmd_boat
        handlers["!cat"] = cmd_cat
        handlers["!catgif"] = cmd_catgif
        handlers["!upboat"] = cmd_upboat
        handlers["!downboat"] = cmd_downboat
        handlers["!lookup"] = cmd_lookup
        handlers["!poll"] = cmd_poll
        handlers["!seen"] = cmd_seen
        handlers["!test"] = cmd_test
        handlers["!vote"] = cmd_vote
        handlers["!wipe"] = cmd_wipe
        handlers["!wipebot"] = cmd_wipebot

        handlers["!random"] = cmd_random
        handlers["!roll"] = cmd_roll
        handlers["!coinflip"] = cmd_flip
        handlers["!gifcat"] = cmd_catgif

        handlers["!flickr"] = cmd_flickr
        handlers["!flickrcover"] = cmd_flickrcover
        handlers["!debug"] = cmd_debug
        #handlers["!strip"] = cmd_strip

    # Twitter listener
    tp = TwitterPoll(twitter_access_token_key, twitter_access_token_secret, 
        twitter_consumer_key, twitter_consumer_secret, polling_seconds=70)

    @tp.register_event("new_tweet")
    def new_tweet(user, tweet, tweetdata):
        # Map twitter users to channels
        user = user.lower()
        default = get_channel(client, twitter_default_channel)
        channels = {}

        for (each_key, each_val) in config.items('Twitter Feed'):
            if each_key == 'default_channel':
                continue
            channels[each_key.lower()] = [get_channel(client, cname.strip()) for cname in each_val.split(",")]

        # Pre-processing
        t_content = tweet
        t_translated = None

        t_nourl = re.sub(r"(?:https?\://)\S+", "URL", t_content)
        t_cleaned = ''.join(e for e in t_nourl if e.isalnum() or e in (' '))

        direct_link = "https://twitter.com/Ti_DiscordBot/status/" + tweetdata['id_str']
        
        if mstranslate_api.detect_language(t_cleaned) != 'en':
            t_translated = mstranslate_api.translate(t_nourl, 'en')
        
        msg = direct_link
        #if t_translated:
        #    msg += "\n  *Auto-Translate: " + t_translated.encode('utf-8') + "*"

        # Get the list of channels assigned to the user (or a default), remove any that don't exist
        for channel in filter(lambda x: x is not None, channels.get(user, [default])):
            bot.send_message(channel, msg)

    @tp.register_event("no_tweets")
    def no_tweets():
        return

    tp.start()

    # Set the flicker API
    flickr_api = flickrapi.FlickrAPI(FLICKR_API_KEY, FLICKR_SECRET_KEY)
    if not flickr_api.token_valid(perms=str("write")):
        flickr_api.get_request_token(oauth_callback=str('oob'))
        authorize_url = flickr_api.auth_url(perms=str('write'))
        print("!!!!!!!!!")
        print("FLICKR TOKEN INVALID. Authenticate here: " + authorize_url)
        verifier = str(input('Verifier code: '))
        flickr_api.get_access_token(str(verifier))

    # Connect to Discord, and begin listening to events.
    try:
        bot.run(email, password) #This blocks the main thread.
    except KeyboardInterrupt:
        print("\nti-bot: Closing API bot...", end=' ')
        bot.logout()
        print("Done.")
        print("ti-bot: Closing Twitter Listener...", end=' ')
        print("Done.")
        tp.stop()
    except:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        traceback.print_exception(exc_type, exc_value, exc_traceback, limit=None, file=sys.stdout)
    print("SEE YOU SPACE COWBOY...")


if __name__ == '__main__':
    main()
