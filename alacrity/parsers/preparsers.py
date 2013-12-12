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

class DuplicateHeroException(Exception):
    """Exception for when multiple players play same hero (e.g. all-mid)"""
    pass


def run_all_preparsers(replay):
    preparser_classes = Preparser.__subclasses__()

    # get general pre-parsing info (e.g. player-hero-team-name mappings)
    # by iterating through replay's full-ticks first
    # this info is available to parsers because preparsers are singletons
    preparsers = []
    for preparser in preparser_classes:
        preparsers.append(preparser(replay))
    for tick in replay.iter_full_ticks(start="pregame", end="postgame"):
        for preparser in preparsers:
            preparser.parse(replay)


# http://stackoverflow.com/questions/6760685/creating-a-singleton-in-python
class Singleton(type):
    """Returns the same instance each time called, UNLESS an argument is provided
    This is used to clear the internal state of preparsers between replays"""
    _instances = {}
    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances or len(args) > 0:
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


class GameStartTime(Preparser):
    """Provides the game's starting time in seconds"""
    def __init__(self, replay):
        print 'init gamestarttime'
        self.gst = None
    def parse(self, replay):
        if self.gst is None and replay.info.game_state == 'game':
            self.gst = replay.info.game_start_time
    @property
    def results(self):
        print 'GameStartTime providing {}'.format(self.gst)
        return self.gst

class PlayerHeroMap(Preparser):
    """Provides a dict mapping player index to the standard name of their hero
    Standard name = 'npc_dota_hero_axe' for example"""
    def __init__(self, replay):
        self.phmap = {i:p.hero_name \
                for i,p in enumerate(replay.demo.file_info.game_info.dota.player_info)}
    def parse(self, replay):
        pass
    @property
    def results(self):
        print 'PlayerHeroMap providing {}'.format(self.phmap)
        return self.phmap

class PlayerTeamMap(Preparser):
    """Provides a dict mapping player index to their team ('radiant'|'dire')"""
    def __init__(self, replay):
        self._teams = {2:'radiant', 3:'dire'}
        self.ptmap = {i:self._teams[p.game_team] \
                for i,p in enumerate(replay.demo.file_info.game_info.dota.player_info)}
    def parse(self, replay):
        pass
    @property
    def results(self):
        print 'PlayerTeamMap providing {}'.format(self.ptmap)
        return self.ptmap

class HeroNameMap(Preparser):
    """Provides a dict mapping hero name to player name
    Example: {npc_dota_hero_axe: 'Lod[A]', ...}"""
    def __init__(self, replay):
        self.hnmap = {}
        for p in replay.demo.file_info.game_info.dota.player_info:
            if p.hero_name in self.hnmap:
                raise DuplicateHeroException()
            self.hnmap[p.hero_name] = p.player_name.replace('.',u'\uff0E')
    def parse(self, replay):
        pass
    @property
    def results(self):
        print 'HeroNameMap providing {}'.format(self.hnmap)
        return self.hnmap

class TeamGpmList(Preparser):
    """Provides 2 lists (1 for each team) of player indexes, ordered by ending gpm"""
    def __init__(self, replay):
        self.radgpm = {}
        self.diregpm = {}
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

class MatchMetadata(Preparser):
    """Extracts metadata (that would otherwise come from the API)
    Includes: match_id, leagueid, game_mode, radiant_win, duration, start_time,
        radiant_team_id, radiant_name, dire_team_id, dire_name,
        for each player: account_id, player_name, hero_name, player_slot, team"""
    def __init__(self, replay):
        self._teams = {2:'radiant', 3:'dire'}
        self.data = {}
        self.data['match_id'] = replay.demo.file_info.game_info.dota.match_id
        self.data['leagueid'] = replay.demo.file_info.game_info.dota.leagueid
        self.data['game_mode'] = replay.demo.file_info.game_info.dota.game_mode
        self.data['radiant_win'] = replay.demo.file_info.game_info.dota.game_winner == 2
        self.data['duration'] = replay.demo.file_info.playback_time
        self.data['start_time'] = replay.demo.file_info.game_info.dota.end_time - self.data['duration']
        self.data['radiant_team_id'] = replay.demo.file_info.game_info.dota.radiant_team_id
        self.data['dire_team_id'] = replay.demo.file_info.game_info.dota.dire_team_id
        self.data['radiant_name'] = replay.demo.file_info.game_info.dota.radiant_team_tag or 'Radiant'
        self.data['dire_name'] = replay.demo.file_info.game_info.dota.dire_team_tag or 'Dire'
        self.data['players'] = [
                {
                    'account_id': p.steamid,
                    'player_name': p.player_name.replace('.',u'\uff0E'),
                    'hero_name': p.hero_name, # e.g: npc_dota_hero_axe
                    'player_slot': i,
                    'team': self._teams[p.game_team]
                }
                for i,p in enumerate(replay.demo.file_info.game_info.dota.player_info)]
    def parse(self, replay):
        pass
    @property
    def results(self):
        print 'MatchMetadata providing {}'.format(self.data)
        return self.data
