import abc

class Parser(object):
    __metaclass__ = abc.ABCMeta

    def __init__(self):
        pass

    @abc.abstractproperty
    def tick_step(self):
        """# ticks between calls to this parser's parse method
        Should be a multiple of 30!"""
        return

    @abc.abstractmethod
    def parse(self, replay):
        """records/processes data from the current replay state"""
        return

    @abc.abstractproperty
    def results(self):
        """returns the results of parsing, should be a dict"""
        return

