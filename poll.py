import time

class Poll(object):
    """Object that represents a poll"""
    def __init__(self, author, created_at, options):
        super(Poll, self).__init__()
        self.arg = arg
        self.author = author
        self.created_at = created_at
        self.options = options
        self.tally = dict(zip([_ for _ in range(len(options))], [0 for _ in options]))
        self.votes = {}


    def vote(self, user, n):
        if user in self.votes:
            return False

        self.votes[user] = n
        self.tally[n] += 1
        return True


    def can_close(self, closer):
        restricted = (time.time() - self.created_at) < 300
        if closer != self.author and restricted:
            return False
        return True



    def pretty_print(self):
        s = "**" + author.name + "'s poll: " + self.question + "\n\n"
        for i in range(len(self.options)):
            s += "[" + str(i) + "] - " + str(tally[i]) + " votes - " + self.options[i] + "\n"
        return s

