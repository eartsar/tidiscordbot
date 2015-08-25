import time

class Poll(object):
    """Object that represents a poll"""
    def __init__(self, author, question, options):
        super(Poll, self).__init__()
        self.author = author
        self.question = question
        self.created_at = time.time()
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
        restricted = self.time_left() > 0
        if closer != self.author and restricted:
            return False
        return True


    def time_left(self):
        return max(0, (300 - (time.time() - self.created_at)))


    def pretty_print(self):
        s = "**" + self.author.name + "'s poll: " + self.question + "\n\n"
        for i in range(len(self.options)):
            s += "[" + str(i) + "] - " + str(self.tally[i]) + " votes - " + self.options[i] + "\n"
        return s

