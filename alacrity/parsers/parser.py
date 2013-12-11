import abc
from preparsers import run_all_preparsers

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

    def end_game(self, replay):
        """called upon reaching postgame, in case parser needs final processing"""
        return

def run_single_parser(cls, replay):
    run_all_preparsers(replay)
    parser = cls(replay)
    for tick in replay.iter_ticks(start="pregame", end="postgame", step=parser.tick_step):
        parser.parse(replay)
    parser.end_game(replay)
    return parser.results

