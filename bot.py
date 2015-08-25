import discord, sys, os, json, urbandict, time, tipoll


client = discord.Client()

# spacing sucks because it's not a monospace font
HELP_MSG = """\
**Ti Discord Bot Functions:**
!help                                 - displays this information
!boat <thing>++/--     - upboat or downboat a thing (useless)
!lookup <word>            - look up a word in the Merriam-Webster dictionary for you illiterate plebs
!seen <user>                 - check to see when the user was last online
!poll <question;choice;choice...>   - Create a poll with choices
    !poll close                   - Closes the poll (must be creator, or 5 minutes passed)
    !vote <choice>                - Votes in a poll 
""" 

currentPoll = None


def main():
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

    client.login(sys.argv[1], sys.argv[2])
    client.run()


@client.event
def on_message(message):
    if message.content.startswith('!test'):
        client.send_message(message.channel, 'Ti Discord Bot is up and running!')
    elif message.content.startswith("!boat"):
        boat(message)
    elif message.content.startswith("!help"):
        client.send_message(message.channel, HELP_MSG)
    elif message.content.startswith("!lookup"):
        lookup(message)
    elif message.content.startswith("!poll"):
        return
    elif message.content.startswith("!seen"):
        seen(message)
    elif message.content.startswith("!vote"):
        return


@client.event
def on_ready():
    print('Logged in as')
    print(client.user.name)
    print(client.user.id)
    print('------')


@client.event
def on_status(server, user, status, gameid):
    # update the last seen data file
    f = open("seen.dat", "r")
    data = json.loads(f.read())
    f.close()

    data[user.name] = time.time()
    print user.name + " seen - logged at " + str(data[user.name])

    f = open("seen.dat", "w")
    f.write(json.dumps(data))
    f.close()


def boat(message):
    """Manage upboats/downboats of things. Stored in flat json file: boats.dat"""
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


def lookup(message):
    """Lookup a word via urbandictionary."""
    word = message.content[len("!lookup "):].strip()
    if not word:
        return

    response = ""
    entry = urbandict.define(word)[0]

    if "There aren't any definitions for " in entry["def"]:
        return

    response = "**" + entry["word"].strip() + "**\n"
    response += entry["def"].strip() + "\n"
    if entry["example"]:
        response += "*" + entry["example"].strip() + "*"

    if response:
        client.send_message(message.channel, response)
    return


def poll(message):
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
                client.send_message(message.channel, "The poll is open for another " + str(currentPoll.time_left()) + ".")
        return

    if poll:
        client.send_message(message.channel, "A poll is already underway. Let that one finish first before starting another.")
        return

    # !poll question;choice;choice...
    opts = opts.split(";")
    if len(opts) < 3:
        return

    currentPoll = tipoll.Poll(message.author, opts[0], opts[1:])
    s = "**" + message.author[0].upper() + message.author[1:] + " starts a poll.**\n" + currentPoll.pretty_print()
    client.send_message(message.channel, s)


def vote(message):
    choice = message.content[len("!vote "):].strip()
    if not choice:
        return

    if isinstance(message.channel, discord.channel.PrivateChannel):
        client.send_message(message.channel, "This command must be run in the general chat channel, not in a PM. Sorry!")
        return

    if choice not in "01234566789":
        return
    if not poll:
        client.send_message(message.channel, "There is no poll underway.")
    choice = int(choice)
    currentPoll.vote(message.author, choice)
    client.send_message(message.channel, message.author.name[0].upper() + message.author.name[1:] + \
        " casts a vote for **" + str(choice) + "**.")
    return


def seen(message):
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


if __name__ == '__main__':
    main()
