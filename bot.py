import os
import sys
import urllib
import traceback
import json
import random
import urbandict
import time
import requests
import discord
import flickrapi
from ti_poll import Poll
from ti_traffic import TrafficLight
from ti_twitter import TwitterPoll

try:
    import configparser
except ImportError:
    import ConfigParser as configparser

# TheCatAPI.com information
CAT_API_URL = "http://thecatapi.com/api/images/get"
CAT_API_KEY = ""

# Flickr API access
flickr_api = None

# The actual API client that deals with Discord events.
client = discord.Client()

# Object to manage poll tracking
currentPoll = None

# Object to manage spam tracking
trafficLight = TrafficLight()

# Dictionary of "!function" to cmd_function(message) handlers.
handlers = None


@client.event
def on_message(message):
    global handlers

    if not handlers:
        print "on_message abort - handlers dict not populated"
        return

    # for non PMs bot commands, manage spammage
    if not isinstance(message.channel, discord.channel.PrivateChannel) and message.content.startswith("!"):
        proceed = trafficLight.log(client, message.author)
        if not proceed:
            return

    tokens = message.content.split(" ")
    cmd_token = tokens[0]
    if cmd_token not in handlers:
        return

    # call the handler
    handlers[cmd_token](message)
    

@client.event
def on_ready():
    print('Logged in as %s' % client.user.name)
    print(client.user.id)
    print('------')


@client.event
def on_status(server, user, status, gameid):
    # update the last seen data file
    print "!seen tracking - " + user.name + " - status: " + status

    with open("seen.dat", "r") as f:
        data = json.loads(f.read())

    data[user.name.lower()] = time.time()

    with open("seen.dat", "w") as f:
        f.write(json.dumps(data))
    
    print "    seen.dat file updated"


def cmd_test(message):
    """
    **!test**

    Usage:
      !test

    Tests to make sure the bot is listening to messages.
    """
    client.send_message(message.channel, 'Ti Discord Bot is up and running!')
    return


def cmd_help(message):
    """
    **!help**

    Usage:
      !help [command]

    Gets more information on commands. Specify a command for more detailed 
    information.
    """
    global handlers

    # these are aliases or shortcuts, so don't bother listing them
    ignores = ["!gifcat", "!upboat", "!downboat"]

    help_msg = "**Ti Discord Bot Functions:**\n" + \
        ", ".join(sorted(filter(lambda x: x not in ignores, handlers.keys()))) + \
        "\nType !help <command> in a PM to **ti-bot** for more information on syntax and functions."

    cmd = message.content[len("!help "):].strip()
    if not cmd or cmd not in handlers:
        client.send_message(message.channel, help_msg)
        return

    client.send_message(message.author, handlers[cmd].__doc__)
    return


def cmd_cat(message):
    """
    **!cat**

    Usage:
      !cat

    Post a random picture (png format) of a cat. See **!catgif** for moar cats.
    """
    opt = message.content[len("!cat "):].strip()
    if opt:
        return
    _cmd_cat(message)
    return


def cmd_catgif(message):
    """
    **!catgif**

    Usage:
      !catgif

    Post a random picture (gif format) of a cat. See **!cat** for moar cats.
    """
    opt = message.content[len("!catgif "):].strip()
    if opt:
        return
    _cmd_cat(message, file_type="gif")
    return


def _cmd_cat(message, file_type="png"):
    """Do work function for cats."""
    r = requests.get(CAT_API_URL, {"api_key": CAT_API_KEY, "format": "src", "type": file_type, "size": "small"})
    client.send_message(message.channel, r.url)
    return


def cmd_boat(message):
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
        
        client.send_message(message.channel, s)
        return
    
    op = thing[-2:]

    # !karma ++  not allowed!
    if op == thing:
        return

    # !boat <thing> - list the boat of the thing
    if op not in ("++", "--"):
        if kthing in data:
            client.send_message(message.channel, thing[0].upper() + thing[1:] + " has " + str(data[kthing]) + " boats.")
        return

    thing = thing[:-2]
    _cmd_boat(message, thing, op, data)
    return


def _cmd_boat(message, thing, op, data):
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

    client.send_message(message.channel, sop + " for " + thing + "! " + thing[0].upper() + thing[1:] + " now has " + str(data[kthing]) + " boats.")
    with open("boats.dat", "w") as f:
        f.write(json.dumps(data))
    
    return


def cmd_upboat(message):
    """
    **!upboat**

    Usage:
      !upboat <thing>

    Example:
      !upboat fura
    
    Shorthand for **!boat <thing>++**
    """
    cmd_shortboat(message)


def cmd_downboat(message):
    """
    **!downboat**

    Usage:
      !downboat <thing>

    Example:
      !downboat fura
    
    Shorthand for **!boat <thing>--**
    """
    cmd_shortboat(message)


def cmd_shortboat(message):
    """Do work function of upboat/downboat shorthand functions."""
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
    _cmd_boat(message, thing, op, data)
    return


def cmd_lookup(message):
    """
    **!lookup**

    Usage:
      !lookup <term>

    Example:
      !lookup ironically

    Looks up the term on Merriam-Webster's online dictionary.
    And by Merriam-Webster, we do mean Urban Dictionary.
    """
    word = message.content[len("!lookup "):].strip()
    if not word:
        return

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
            client.send_message(message.channel, response.encode('utf-8'))
        except:
            print "Unicode error in !lookup()"
    return


def cmd_poll(message):
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
    opts = message.content[len("!poll "):].strip()

    if isinstance(message.channel, discord.channel.PrivateChannel):
        client.send_message(message.channel, "This command must be run in the general chat channel, not in a PM. Sorry!")
        return
    
    # !poll - display the poll
    if not opts:
        if currentPoll:
            client.send_message(message.channel, currentPoll.pretty_print())
        else:
            client.send_message(message.channel, "There is no poll underway.")
        return

    # !poll close - close the poll
    if opts == "close":
        if not currentPoll:
            client.send_message(message.channel, "There is no poll underway.")
        else:
            if currentPoll.can_close(message.author):
                client.send_message(message.channel, "**Poll closed!**\n" + currentPoll.pretty_print())
                currentPoll = None
            else:
                client.send_message(message.channel, "The poll is open for another %.0f seconds." % currentPoll.time_left())
        return

    if currentPoll:
        client.send_message(message.channel, "A poll is already underway. Let that one finish first before starting another.")
        return

    # !poll question;choice;choice...
    opts = [s.strip() for s in filter(lambda x: x.strip() != "", opts.split(";"))]

    if len(opts) < 3 or len(opts) > 9:
        return

    for i in range(len(opts)):
        opts[i] = opts[i].strip()


    currentPoll = Poll(message.author, opts[0], opts[1:])
    s = "**" + message.author.name + " starts a poll.**\n" + currentPoll.pretty_print()
    client.send_message(message.channel, s)


def cmd_vote(message):
    """
    **!vote**

    Usage:
      !vote <choice>

    Example:
      !vote 2
    
    Votes for a choice in the current poll.
    """
    choice = message.content[len("!vote "):].strip()
    if not choice:
        return

    if isinstance(message.channel, discord.channel.PrivateChannel):
        client.send_message(message.channel, "This command must be run in the general chat channel, not in a PM. Sorry!")
        return

    if len(choice) != 1 or choice not in "1234566789":
        return

    if not currentPoll:
        client.send_message(message.channel, "There is no poll underway.")
    choice = int(choice)
    currentPoll.vote(message.author, choice)
    client.send_message(message.channel, message.author.name + " casts a vote for **" + str(choice) + "**.")
    return


def cmd_seen(message):
    """
    **!seen**

    Usage:
      !seen <user>

    Example:
      !lookup fura barumaru

    Checks to see the last time a particular user was
    seen online by ti-bot.

    *The user's name must be entered in full.*
    """
    user = message.content[len("!seen "):].strip()
    key = user.lower()
    if not user:
        return

    f = open("seen.dat", "r")
    data = json.loads(f.read())
    f.close()

    # PMs are separate from servers, so running this in a PM doesn't make sense
    if isinstance(message.channel, discord.channel.PrivateChannel):
        client.send_message(message.channel, "This command must be run in the general chat channel, not in a PM. Sorry!")
        return


    found = filter(lambda x: x.status != "offline" and x.name.lower() == key, message.channel.server.members)

    # The user is currently online
    if len(found) > 0:
        client.send_message(message.channel, user + " is currently **online**.")

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
        client.send_message(message.channel, "I haven't seen " + user + " before.")
        return

    t = data[key]
    tdiff = time.time() - t
    days = tdiff // 86400
    hours = tdiff // 3600 % 24
    minutes = tdiff // 60 % 60
    seconds = tdiff % 60
    client.send_message(message.channel, user[0].upper() + user[1:] + \
        " was last seen **%.0f days, %.0f hours, %.0f minutes, and %.0f seconds ago**." \
        % (days, hours, minutes, seconds))
    return


def cmd_roll(message):
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
    client.send_message(message.channel, s)
    return


def cmd_flip(message):
    """
    **!coinflip**

    Usage:
      !coinflip

    Flips a two sided coin.

    *Also see* ***!roll*** and ***!random*** *for more random games.*
    """
    opt = message.content[len("!coinflip "):].strip()

    if opt:
        return

    result = "heads"
    if random.randint(0, 1) == 1:
        result = "tails"

    s = "*" + message.author.name + " flips a coin...* ***" + str(result) + "!***"
    client.send_message(message.channel, s)
    return


def cmd_random(message):
    """
    **!random**

    Usage:
      !random

    Rolls between 1 and 99, Final Fantasy style.

    *Also see* ***!roll*** and ***!coinflip*** *for more random games.*
    """
    opt = message.content[len("!random "):].strip()

    if opt:
        return

    result = random.randint(1, 99)

    s = "*Dice roll! " + message.author.name + " rolls* ***" + str(result) + "!***"
    client.send_message(message.channel, s)
    return


def cmd_wipe(message):
    """
    **!wipe**

    Usage:
      !wipe [number]

    Wipes a certain number of messages from the channel. By default, this is one.
    """
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

    to_remove = [m for m in client.logs_from(message.channel, limit=num + 1)]
    for log_message in to_remove:
        client.delete_message(log_message)


def cmd_wipebot(message):
    """
    **!wipebot**

    Usage:
      !wipebot <number> <history>

    Example:
      !wipebot 10 2000

    Wipes a certain number of !cmd messages and bot responses from the channel.
    This crawls over *history* messages, deleting up to *number* of them that apply.
    """
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

    to_remove = [m for m in client.logs_from(message.channel, limit=history)]
    for log_message in to_remove:
        if log_message.author.name != "ti-bot" and not log_message.content.startswith("!"):
            continue
        client.delete_message(log_message)


def get_channel(client, name):
    tixiv = None

    for server in client.servers:
        if server.name == 'titanium-ffxiv':
            tixiv = server

    if not tixiv:
        return None

    for channel in tixiv.channels:
        if channel.name == name: #There are no hashtags in channel names
            return channel

    return None


def cmd_flickr(message):
    link = message.content[len("!flickr "):].strip()

    # Yay for magic numbers
    flickr_user_id = '135801662@N07'

    if not link:
        return

    album_name = message.author.name + "'s album"
    
    # Make sure the flickr api is valid
    if not flickr_api.token_valid(perms="write"):
        client.send_message(message.channel, "**Flickr functionality requires renewed access. Contact Fura.**")
        return

    # Validate the linked image type
    ext = os.path.splitext(link)[1]
    if ext not in (".jpg", ".png"):
        return

    # We'll use a timestamp as the photo
    fname = "%.0f" % time.time() + ext

    # Grab the photo that was posted at the url
    try:
        urllib.urlretrieve(link, filename=fname)
    except:
        print "Exception thrown while downloading source file."
        return

    # upload photo to flickr
    response = None
    with open(fname) as f:
        response = flickr_api.upload(f.name, fileobj=f)

    # cleanup the file stored locally
    os.remove(fname)

    # validate the upload went okay
    if not response or response.get('stat') == 'ok':
        print "Flickr: upload response returned NOT OK"
    
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
    s = message.author.name + " has uploaded a new photo to their album!  " + album_link
    client.send_message(message.channel, s)
    return 


def cmd_debug(message):
    print "  content: " + str(message.content)
    print "  timestamp: " + str(message.timestamp)
    print "  tts: " + str(message.tts)
    print "  mention_everyone: " + str(message.mention_everyone)
    print "  embeds: " + str(message.embeds)
    print "  id: " + str(message.id)
    print "  channel: " + str(message.channel.name)
    print "  author: " + str(message.author)
    print "  mentions: " + str(message.mentions)
    print "  attachments: " + str(message.attachments)
    return


def main():
    global handlers, alaises, CAT_API_KEY, flickr_api

    # Deal with the configuration file.
    config = configparser.ConfigParser()

    # Default Value
    DEF_VAL = 'REPLACE_ME'

    # Create it, if it doesn't exist.
    if not os.path.isfile("config.txt"):
        print "No config file found. Generating one - please fill out information in " + os.path.join(os.getcwd(), "config.txt")
        with open('config.txt', 'w') as configfile:
            config['Discord'] = {'email': DEF_VAL, 'password': DEF_VAL}
            config['TheCatAPI.com'] = {'api_key': DEF_VAL}
            config['Twitter'] = {"consumer_key": DEF_VAL,
                                 "consumer_secret": DEF_VAL,
                                 "access_token_key": DEF_VAL,
                                 "access_token_secret": DEF_VAL}
            config['Twitter Feed'] = {'default_channel': "general"}
            config['Flickr'] = {'flickr_api_key': DEF_VAL, 'flickr_secret_key': DEF_VAL}
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

    to_fill = [email, password, CAT_API_KEY, twitter_consumer_key, twitter_consumer_secret,
        twitter_access_token_key, twitter_access_token_secret, FLICKR_API_KEY, FLICKR_SECRET_KEY]

    # Prevent execution if the configuration file isn't complete
    for arg in to_fill:
        if arg == DEF_VAL:
            print "config.txt has not been fully completed. Fully fill out config.txt and re-run."
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
        handlers["!help"] = cmd_help
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
        handlers["!debug"] = cmd_debug

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

        # Get the list of channels assigned to the user (or a default), remove any that don't exist
        for channel in filter(lambda x: x is not None, [default] if user not in channels else channels[user]):
            client.send_message(channel, "**%s tweets:** %s  (%s)\n\n" % (user, tweet, tweetdata["created_at"]))

    @tp.register_event("no_tweets")
    def no_tweets():
        return

    tp.start()

    # Set the flicker API
    flickr_api = flickrapi.FlickrAPI(FLICKR_API_KEY, FLICKR_SECRET_KEY)
    if not flickr_api.token_valid(perms=unicode("write")):
        flickr_api.get_request_token(oauth_callback=unicode('oob'))
        authorize_url = flickr_api.auth_url(perms=unicode('write'))
        print "!!!!!!!!!"
        print "FLICKR TOKEN INVALID. Authenticate here: " + authorize_url
        verifier = unicode(raw_input('Verifier code: '))
        flickr_api.get_access_token(unicode(verifier))

    # Connect to Discord, and begin listening to events.
    client.login(email, password)
    try:
        client.run() #This blocks the main thread.
    except KeyboardInterrupt:
        print("\nti-bot: Closing API Client..."),
        client.logout()
        print("Done.")
        print("ti-bot: Closing Twitter Listener..."),
        print "Done."
        tp.stop()
    except:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        traceback.print_exception(exc_type, exc_value, exc_traceback, limit=None, file=sys.stdout)
    print "SEE YOU SPACE COWBOY..."


if __name__ == '__main__':
    main()
