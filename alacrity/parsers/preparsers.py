# nice-to-have refactoring:
#  instead of using singleton classes, make another folder (preparsers) and put
#  each preparser as a module in that folder, that way it doesn't look like you're
#  constructing an object anew when getting its preparsing results
#   e.g:     self.gst = GameStartTime().results
#   becomes: self.gst = GameStartTime.results
#  and module functions (parse, results) can just be by convention instead of by
#  abstractmethod

import abc
from utils import HeroNameDict, unitIdx

def run_all_preparsers(replay):
    preparser_classes = Preparser.__subclasses__()

    # get general pre-parsing info (e.g. player-hero-team-name mappings)
    # by iterating through replay's full-ticks first
    # this info is available to parsers because preparsers are singletons
    preparsers = []
    for preparser in preparser_classes:
        preparsers.append(preparser(replay))
        preparser().clear() # ew
    for tick in replay.iter_full_ticks(start="pregame", end="postgame"):
        for preparser in preparsers:
            preparser.parse(replay)

    # fail replays with duplicate heroes (ie - allmid isn't supported)
    #  get all dict type preparser results and make sure they have the same length
    preparser_dicts = filter(lambda p: isinstance(p, dict), [q.results for q in preparsers])
    if not all([len(x) == len(preparser_dicts[0]) for x in preparser_dicts]):
        raise DuplicateHeroException()


# http://stackoverflow.com/questions/6760685/creating-a-singleton-in-python
class Singleton(type):
    _instances = {}
    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]

class Preparser(object):
    __metaclass__ = Singleton

    def __init__(self):
        pass

    @abc.abstractmethod
    def parse(self, replay):
        """records/processes data from the current replay state"""
        return

    @abc.abstractproperty
    def results(self):
        """returns the results of parsing, should be a dict"""
        return

    @abc.abstractmethod
    def clear(self):
        """clear internal structure to ready for parsing new replay"""
        return


class GameStartTime(Preparser):
    """Provides the game's starting time in seconds"""
    def __init__(self, replay):
        print 'init gamestarttime'
        self.clear()
    def parse(self, replay):
        if self.gst is None and replay.info.game_state == 'game':
            self.gst = replay.info.game_start_time
    @property
    def results(self):
        print 'GameStartTime providing {}'.format(self.gst)
        return self.gst
    def clear(self):
        self.gst = None

class PlayerHeroMap(Preparser):
    """Provides a dict mapping player index to the standard name of their hero
    Standard name = 'npc_dota_hero_axe' for example"""
    def __init__(self, replay):
        self.clear()
    def parse(self, replay):
        for player in replay.players:
            if player.index not in self.phmap and player.hero is not None:
                self.phmap[player.index] = HeroNameDict[unitIdx(player.hero)]['name']
    @property
    def results(self):
        print 'PlayerHeroMap providing {}'.format(self.phmap)
        return self.phmap
    def clear(self):
        self.phmap = {}

class PlayerTeamMap(Preparser):
    """Provides a dict mapping player index to their team ('radiant'|'dire')"""
    def __init__(self, replay):
        self.clear()
    def parse(self, replay):
        if len(self.ptmap) == 0 and replay.info.game_state == 'game':
            for player in replay.players:
                self.ptmap[player.index] = player.team
    @property
    def results(self):
        print 'PlayerTeamMap providing {}'.format(self.ptmap)
        return self.ptmap
    def clear(self):
        self.ptmap = {}

class HeroNameMap(Preparser):
    """Provides a dict mapping hero name to player name
    Example: {npc_dota_hero_axe: 'Lod[A]', ...}"""
    def __init__(self, replay):
        self.clear()
    def parse(self, replay):
        for player in replay.players:
            if player.hero is not None and player.hero.name not in self.hnmap:
                hero_name = HeroNameDict[unitIdx(player.hero)]['name']
                self.hnmap[hero_name] = player.name.decode('utf-8').replace('.',u'\uff0E')
    @property
    def results(self):
        print 'HeroNameMap providing {}'.format(self.hnmap)
        return self.hnmap
    def clear(self):
        self.hnmap = {}

class TeamGpmList(Preparser):
    """Provides 2 lists (1 for each team) of player indexes, ordered by ending gpm"""
    def __init__(self, replay):
        self.clear()
    def _gpm(self, player, replay):
        if replay.info.game_start_time is None:
            return 0 # game hasn't started yet
        # add +1 to avoid div-by-zero if we land on the game_start_time tick
        gpm = int(60 * player.earned_gold / (replay.info.game_time - replay.info.game_start_time + 1))
        return gpm
    def parse(self, replay):
        for player in replay.players:
            if player.team == 'radiant':
                self.radgpm[player.index] = self._gpm(player, replay)
            else:
                self.diregpm[player.index] = self._gpm(player, replay)
    @property
    def results(self):
        radgpm = [x[0] for x in sorted(self.radgpm.items(), key=lambda x: x[1], reverse=True)]
        diregpm = [x[0] for x in sorted(self.diregpm.items(), key=lambda x: x[1], reverse=True)]
        print 'TeamGpmList providing {} {}'.format(radgpm, diregpm)
        return radgpm, diregpm
    def clear(self):
        self.radgpm = {}
        self.diregpm = {}
