import time


# Messages before being warned
WARNING_COUNT = 8

# Messages before a gag
LIMITER_COUNT = 10

# How far back we keep track of messages
LIMITER_WINDOW = 120

# Penalty duration
REDLIGHT_TIME = 60

# Status codes
GREEN_LIGHT = 0
YELLOW_LIGHT = 1
RED_LIGHT = 2
STILL_RED_LIGHT = 3


class TrafficLight(object):
    """Magical object that manages spam abuse"""
    def __init__(self):
        super(TrafficLight, self).__init__()
        self.history = {}
        self.stopped = {}


    def _update(self, user):
        if user not in self.history:
            self.history[user] = []
        
        if user in self.stopped:
            if (time.time() - self.stopped[user]) > REDLIGHT_TIME:
                del self.stopped[user]
                self.history[user] = []
            else:
                return STILL_RED_LIGHT

        self.history[user] = filter(lambda x: (time.time() - x) < LIMITER_WINDOW, self.history[user])
        if len(self.history[user]) >= LIMITER_COUNT:
            self.stopped[user] = time.time()
            return RED_LIGHT
        elif len(self.history[user]) >= WARNING_COUNT:
            return YELLOW_LIGHT
        else:
            return GREEN_LIGHT


    def log(self, client, user):
        status = self._update(user)
        if status == GREEN_LIGHT:
            self.history[user].append(time.time())
            return True
        elif status == YELLOW_LIGHT:
            self.history[user].append(time.time())
            client.send_message(user, "You are spamming #general with too many bot commands! **Slow it down, cowboy!**")
            return True
        elif status == RED_LIGHT:
            client.send_message(user, "Due to excessive use, **you will be ignored by ti-bot for a while.** Wait a few minutes before resuming your spam.")
            return False
        elif status == STILL_RED_LIGHT:
            return False

