import discord, sys, os, json


client = discord.Client()
HELP_MSG = """\
Ti Discord Bot Functions:
!help               - displays this information
!boat <thing>++/--   - upboat or downboat a thing (useless)
""" 


def main():
    if len(sys.argv) != 3:
        print "Usage: python bot.py <email> <password>"
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


@client.event
def on_ready():
    print('Logged in as')
    print(client.user.name)
    print(client.user.id)
    print('------')



def boat(message):
    content = message.content
    # create the file if it doesn't exist
    if not os.path.isfile("boats.dat"):
        f = open("boats.dat", "w")
        f.write("{}")
        f.close()

    # load the data as json
    f = open("boats.dat", "r")
    data = json.loads(f.read())
    f.close()

    thing = content[len("!boat "):].strip()
    # use lower for key access
    kthing = thing.lower()

    # !boat - list all boats
    if not thing:
        s = "All of these things have boats:\n"
        for k in data:
            s = s + k.lower() + ": " + str(data[k]) + "\n"
        client.send_message(message.channel, s)
        return
    
    op = thing[-2:]

    # !karma ++  not allowed!
    if op == thing:
        return

    # !boat <thing> - list the boat of the thing
    if op not in ("++", "--") and kthing in data:
        client.send_message(message.channel, thing[0] + thing[1:] + " has " + str(data[kthing]) + " boats.")
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













if __name__ == '__main__':
    main()
