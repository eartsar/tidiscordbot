import os
import sys
import traceback
import json
import re
import random
import urbandict
import time
import requests
import discord
import flickrapi
import microsofttranslator
from urllib import FancyURLopener
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

# Microsoft Translate access
mstranslate_api = None

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
def on_status(member):
    # update the last seen data file
    print "!seen tracking - " + member.name + " - status: " + member.status

    with open("seen.dat", "r") as f:
        data = json.loads(f.read())

    data[member.name.lower()] = time.time()

    with open("seen.dat", "w") as f:
        f.write(json.dumps(data))
    
    print "    seen.dat file updated"


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


def main():
    global handlers, alaises, CAT_API_KEY, flickr_api, mstranslate_api

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


    # TODO: Consider making this entire portion a generator/command pattern
    # Local level imports for all the commands
    from commands import cmd_boat, cmd_cat, cmd_catgif, cmd_upboat, cmd_downboat, cmd_help, \
        cmd_lookup, cmd_poll, cmd_seen, cmd_test, cmd_vote, cmd_wipe, cmd_wipebot, cmd_random, \
        cmd_roll, cmd_flip, cmd_catgif, cmd_flickr, cmd_debug

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
        contains_links = re.search(r"(?:https?\://)\S+", t_content) is not None
        t_content = re.sub(r"(?:https?\://)\S+", "URL", t_content)
        t_cleaned = ''.join(e for e in t_content if e.isalnum() or e in (' '))

        direct_link = "https://twitter.com/Ti_DiscordBot/status/" + tweetdata['id_str']
        translated_tag = ''

        if mstranslate_api.detect_language(t_cleaned) != u'en':
            t_content = mstranslate_api.translate(t_content, 'en')
            translated_tag = "(translated)"

        if contains_links:
            t_content = t_content + u"\n" + direct_link
        
        msg = '**@{}** tweets {}: {}'.format(user, translated_tag, t_content.encode('utf-8'))

        # Get the list of channels assigned to the user (or a default), remove any that don't exist
        for channel in filter(lambda x: x is not None, [default] if user not in channels else channels[user]):
            client.send_message(channel, msg)

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
