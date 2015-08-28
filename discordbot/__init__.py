import discord
from discord.client import _null_event

class DiscordLoginError(Exception): pass

class DiscordBot(object):
    def __init__(self, username=None, password=None, handlers={}, client=None, **kwargs):
        self._client = client
        self._user   = "DiscordBot" if not username else username
        if not client:
            self._client = discord.Client()

        self._handlers = {}

        self._client.events.update({
            'on_ready': self.on_ready,
            'on_message': self.on_message,
            'on_status': self.on_status,
        })

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

    @property
    def servers(self):
        return self._client.servers

    def login(self, username, password, autorun=False):
        self._user = username
        self._client.login(username, password)

        if autorun:
            self._client.run()

    def run(self):
        self._client.run()

    def logout(self):
        self._client.logout()

    def find_server(self, server_name):
        for server in self.servers:
            if server.name == server_name:
                return server

        return None

    def find_channel(self, server_name, channel_name):
        _server = None

        for server in self.servers:
            if server.name == server_name:
                _server = server
                break

        if not _server:
            raise Exception("Cannot find server (%s)" % server_name)

        for channel in _server.channels:
            if channel.name == channel_name: #There are no hashtags in channel names
                return channel

        raise Exception("Cannot find channel (%s) on server (%s)" % (channel_name, server_name))


class KigenBot(DiscordBot):
    def send_message(self, message, server=None, channel=None, mentions=True):
        if not self._client._is_logged_in:
            raise DiscordLoginError("%s has not logged in" % self) 

        if not server:
            server = self.servers[0]
        elif type(server) == str:
            server = self.find_server(server)

        if type(channel) ==  str:
            for _channel in _server.channels:
                if _channel.name == channel_name: #There are no hashtags in channel names
                    channel = _channel

        if not channel:
            channel = server.channels[0]

        return

        self._client.send_message(channel, message)

    def on_ready(self):
        print('Logged in as %s' % self._client.user.name)
        print(self._client.user.id)
        print('------')

        for s in self._client.servers:
            print s.name

            for c in s.channels:
                print("\t%s" % c.name)

        print('------')

        channel = self.find_channel("titanium-ffxiv", "Group Channel 1")
        print(channel)

        #self.join_channel(channel)

        self.send_message("Test message from KigenBot", server="titanium-ffxiv")

    def join_channel(self, channel):
        import json
        from pprint import pprint

        payload = {u'd': 
                   {u'channel_id': channel.id,
                    u'deaf': False,
                    u'guild_id': channel.server.id,
                    u'mute': False,
                    u'self_deaf': False,
                    u'self_mute': True,
                    u'session_id': u'9f5844ca6cb81bc440a385b352024242',
                    u'suppress': False,
                    u'token': self._client.token,
                    u'user_id': self._client.user.id},
         u'op': 0,
         #u't': u'VOICE_STATE_UPDATE'
         }

        pprint(payload)

        print("sending payload...")

        self._client.ws.send(json.dumps(payload))


    def on_status(self, server, user, status, gameid):
        if status ==  "offline":
            msg = 'KigenBot says, "Goodbye %s I will miss you ;___;"'
        elif status == "online":
            msg = 'KigenBot says, "Hello %s!"'
        elif gameid:
            msg = 'KigenBot says, "ooooo whatcha playin %s?"'

        #NOTE: Phone app seems to "connect" when in front and "disconnect" when not

        if server.name != "titanium-ffxiv":
            return

        self.send_message(msg % user, server=server, channel="general")
        print(status)
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
        #print(message.channel.name)
        #print(message.channel.server.name)
        #print(dir(message.channel))
        #print(message.mentions) #USER obj

        print("%s(%s - %s):%s" % (message.author, message.channel.server.name, message.channel.name, message.content))


from discord.client import _keep_alive_handler, Client
from discord import endpoints
import requests
from ws4py.client.threadedclient import WebSocketClient
import time
import json
import pprint

class VoiceClient(Client):
    def __init__(self, **kwargs):
        self.token = ''

        gateway = requests.get(endpoints.GATEWAY)
        if gateway.status_code != 200:
            raise GatewayNotFound()
        gateway_js = gateway.json()
        url = gateway_js.get('url')
        if url is None:
            raise GatewayNotFound()

        self.ws = WebSocketClient(url, protocols=['http-only', 'chat', 'voice'])

        # this is kind of hacky, but it's to avoid deadlocks.
        # i.e. python does not allow me to have the current thread running if it's self
        # it throws a 'cannot join current thread' RuntimeError
        # So instead of doing a basic inheritance scheme, we're overriding the member functions.

        self.ws.opened = self._opened
        self.ws.closed = self._closed
        self.ws.received_message = self._received_message

        # the actual headers for the request...
        # we only override 'authorization' since the rest could use the defaults.
        self.headers = {
            'authorization': self.token,
        }

    def _closed(self, code, reason=None):
        print('Closed with {} ("{}") at {}'.format(code, reason, int(time.time())))

    def login(self, email, password):
        """Logs in the user with the following credentials and initialises
        the connection to Discord.

        After this function is called, :attr:`is_logged_in` returns True if no
        errors occur.

        :param str email: The email used to login.
        :param str password: The password used to login.
        """

        self.ws.connect()

        payload = {
            'email': email,
            'password': password
        }

        r = requests.post(endpoints.LOGIN, json=payload)

        if r.status_code == 200:
            body = r.json()
            self.token = body['token']
            self.headers['authorization'] = self.token
            second_payload = {
                'op': 4,
                'd': {
                    'token': self.token,
                    'properties': {
                        '$os': '',
                        '$browser': 'discord.py',
                        '$device': 'discord.py',
                        '$referrer': '',
                        '$referring_domain': ''
                    },
                    'v': 2
                }
            }

            self.ws.send(json.dumps(second_payload))

            self._is_logged_in = True

    def _received_message(self, msg):
        response = json.loads(str(msg))

        s = pprint.pformat(response)
        
        event = response.get('t')
        data = response.get('d')

        if event == 'READY':
            with open("test.txt", "w+") as f:
                f.write(s)

            data = response.get('d')
            interval = data.get('heartbeat_interval') / 1000.0
            self.keep_alive = _keep_alive_handler(interval, self.ws)

        else:
            print(s)

if __name__ == "__main__":
    try:
        import configparser
    except ImportError:
        import ConfigParser as configparser

    config = configparser.ConfigParser()
    
    # load in configuration information
    config.read('config.txt')
    email = config.get('Discord', 'email')
    password = config.get('Discord', 'password')

    vc = VoiceClient()
    vc.login(email, password)
    vc.run()
    exit()
    
    kb = KigenBot(username = email,
                  password = password,
                  server = "titanium-ffix",
                  channel = "general")

    kb.run()