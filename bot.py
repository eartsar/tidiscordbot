import discord, sys, os, json, random, urbandict, time, tipoll, requests


CAT_API = "http://thecatapi.com/api/images/get"

client = discord.Client()
currentPoll = None
handlers = None


@client.event
def on_message(message):
    global handlers

    if not handlers:
        print "on_message abort - handlers dict not populated"
        return

    tokens = message.content.split(" ")
    cmd_token = tokens[0]
    if cmd_token not in handlers:
        return

    # call the handler
    handlers[cmd_token](message)
    

@client.event
def on_ready():
    print('Logged in as')
    print(client.user.name)
    print(client.user.id)
    print('------')


@client.event
def on_status(server, user, status, gameid):
    # update the last seen data file
    print "!seen tracking - " + user.name + " - status: " + status

    f = open("seen.dat", "r")
    data = json.loads(f.read())
    f.close()

    data[user.name.lower()] = time.time()

    f = open("seen.dat", "w")
    f.write(json.dumps(data))
    f.close()
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
    r = requests.get(CAT_API, {"format": "src", "type": file_type, "size": "small"})
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
    f = open("boats.dat", "r")
    data = json.loads(f.read())
    f.close()

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
    f = open("boats.dat", "w")
    f.write(json.dumps(data))
    f.close()
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
    f = open("boats.dat", "r")
    data = json.loads(f.read())
    f.close()

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

    if response:
        client.send_message(message.channel, response)
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


    currentPoll = tipoll.Poll(message.author, opts[0], opts[1:])
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

    if isinstance(message.channel, discord.channel.PrivateChannel):
        client.send_message(message.channel, "This command must be run in the general chat channel, not in a PM. Sorry!")
        return

    for member in message.channel.server.members:
        if member.name.lower() == key:
            client.send_message(message.channel, user + " is currently **online**.")

            if key not in data:
                f = open("seen.dat", "r")
                data = json.loads(f.read())
                f.close()

                data[user] = time.time()

                f = open("seen.dat", "w")
                f.write(json.dumps(data))
                f.close()
            return

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

    *Also see* ***!flip*** and ***!random*** *for more random games.*
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
    **!flip**

    Usage:
      !flip

    Flips a two sided coin.

    *Also see* ***!roll*** and ***!random*** *for more random games.*
    """
    opt = message.content[len("!flip "):].strip()

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

    *Also see* ***!roll*** and ***!flip*** *for more random games.*
    """
    opt = message.content[len("!random "):].strip()

    if opt:
        return

    result = random.randint(1, 99)

    s = "*Dice roll! " + message.author.name + " rolls* ***" + str(result) + "!***"
    client.send_message(message.channel, s)
    return


def main():
    global handlers, alaises

    if len(sys.argv) != 3:
        print "Usage: python bot.py <email> <password>"

    # Create necessary files for data tracking
    if not os.path.isfile("boats.dat"):
        f = open("boats.dat", "w")
        f.write("{}")
        f.close()

    if not os.path.isfile("seen.dat"):
        f = open("seen.dat", "w")
        f.write("{}")
        f.close()

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

        handlers["!random"] = cmd_random
        handlers["!roll"] = cmd_roll
        handlers["!flip"] = cmd_flip
        handlers["!gifcat"] = cmd_catgif


    client.login(sys.argv[1], sys.argv[2])
    client.run()


if __name__ == '__main__':
    main()
