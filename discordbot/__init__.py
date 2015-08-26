import discord
from discord.client import _null_event

class DiscordLoginError(Exception): pass

class DiscordBot(object):
    def __init__(self, username=None, password=None, handlers={}, client=None):
        self._client = client
        self._user   = "DiscordBot" if not username else username
        if not client:
            self._client = discord.Client()

        self._handlers = {}

        self._client.events = {
            'on_ready': self.on_ready,
            'on_disconnect': _null_event,
            'on_error': _null_event,
            'on_response': _null_event,
            'on_message': self.on_message,
            'on_message_delete': _null_event,
            'on_message_edit': _null_event,
            'on_status': self.on_status,
            'on_channel_delete': _null_event,
            'on_channel_create': _null_event,
        }

        if username and password:
            self.login(username, password)

    def __repr__(self):
        return "<DiscordBot (%s)>" % self.username

    @property
    def username(self):
        return self._user if not self._client.is_logged_in else self._client.user.name

    @property
    def user_id(self):
        return self._client.user.id

    def login(self, username, password):
        self._user = username
        self._client.login(username, password)
        self._client.run()

    def run(self):
        self._client.run()

    def logout(self):
        self._client.logout()

    def send_message(self, message, channel=None, mentions=True):
        if not self._client._is_logged_in:
            raise DiscordLoginError("%s has not logged in" % self) 

        if not channel:
            channel = self._client.servers[0].channels[0]

        self._client.send_message(channel, message)

    def on_ready(self):
        print('Logged in as %s' % self._client.user.name)
        print(self._client.user.id)
        print('------')

        self.send_message("Test message from KigenBot")

    def on_status(self, server, user, status, gameid):
        if status ==  "offline":
            msg = 'KigenBot says, "Goodbye %s I will miss you ;___;"'
        elif status == "online":
            msg = 'KigenBot says, "Hello %s!"'
        elif gameid:
            msg = 'KigenBot says, "ooooo whatcha playin %s?"'

        #NOTE: Phone app seems to "connect" when in front and "disconnect" when not

        self.send_message(msg % user)
        print(status)
        print(server)
        print(user)
        print(gameid)

    def on_message(self, message):
        #NOTES:
        #<discord.message.Message object at 0x025F8590>
        #['__class__', '__delattr__', '__dict__', '__doc__', '__format__', '__getattribut
        #e__', '__hash__', '__init__', '__module__', '__new__', '__reduce__', '__reduce_e
        #x__', '__repr__', '__setattr__', '__sizeof__', '__str__', '__subclasshook__', '_
        #_weakref__', '_parse_time', 'attachments', 'author', 'channel', 'content', 'edit
        #ed_timestamp', 'embeds', 'id', 'mention_everyone', 'mentions', 'timestamp', 'tts']

        #print(message)
        #print(dir(message))
        #print(message.id)
        #print(message.author)
        #print(message.content)
        #print(message.attachments)
        #print(message.embeds)
        #print(message.channel)
        #print(message.mentions) #USER obj

        print("%s:%s" % (message.author, message.content))

if __name__ == "__main__":
    try:
        import configparser
    except ImportError:
        import ConfigParser as configparser

    db = DiscordBot()

    try:
        db.send_message(0, "woo")
    except DiscordLoginError:
        print("Caught login error as expected")

    config = configparser.ConfigParser()
    
    # load in configuration information
    config.read('config.txt')
    email = config['Discord']['email']
    password = config['Discord']['password']
    
    db.login(email, password)

    db.logout()