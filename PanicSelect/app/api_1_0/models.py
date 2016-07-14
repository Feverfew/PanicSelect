from cassiopeia import riotapi
from cassiopeia.type.api.exception import APIError
from py_gg import InvalidAPIKeyError
import py_gg
import threading

class ChampionPickGenerator(object):
    """This class collects all API data needed to generate the list of best champs"""

    def __init__(self, summoner, region, role, matchup=None):
        """
        :param summoner: Name of summoner
        :type summoner: str
        :param region: Region of the summoner
        :type region: str
        :param role: The role that the summoner wishes to play
        :type role: str
        :param matchup: The champion that the summoner will play against on lane
        :type matchup: str
        """
        self.summoner_name = summoner
        self.summoner_info = None
        self.region = region
        self.role = role
        self.matchup = matchup
        self.champions = []
        self.api_errors = []
        try:
            riotapi.set_region(region)
            riotapi.set_api_key('3bdf3fcc-39db-4f5a-8a1f-477fb97f7094')
        except APIError: 
            self.api_errors.append("Initialisation error")
        try:
            versions = riotapi.get_versions()
            self.lol_version = versions[0]
        except APIError:
            self.api_errors.append("Riot API error occured")
        try:
            self.summoner_info = riotapi.get_summoner_by_name(self.summoner_name)
        except APIError:
            self.api_errors.append("Summoner not found")
        try:
            py_gg.init('ae89f8f81c1334bf7174a6622d47aa2c')
        except InvalidAPIKeyError:
            self.api_errors.append("Invalid API key error")
        except:
            self.api_errors.append("Champion.gg API failed to respond")
        try:
            champs = riotapi.get_champions()
        except APIError:
            self.api_errors.append("Riot API error occured")
        self.champion_mapping = {champion.name: champion.id for champion in champs}


    def get_champ_data_by_role(self):
        """Gets champion data by role and puts it into a list."""
        try:
            data = py_gg.stats.role(self.role, None, None, p={'limit':1000})
            for champ in data['data']:
                id = self.champion_mapping[champ['name']]
                champ_obj = ChampionPick(champ['name'], champ['key'], id,  self.lol_version, champ['general']['winPercent'])
                self.champions.append(champ_obj)
        except:
            self.api_errors.append("Champion.gg API failed to respond")
    

    def get_matchup_winrates(self):
        """Gets matchup information on matchup and maps it to champions."""
        def search_matchup_winrates(dictionary, key):
            """Finds winrate and games against matchup if they exist
            :param dictionary: Dictionary of matchups
            :type dictionary: dict
            :param key: Champion key to search for
            :type key: str
            :rtype: array [winrate, games]
            """
            for matchup in dictionary:
                try:
                    if matchup['key'] == key:
                        return [matchup['winRate'], matchup['games']]
                except KeyError:
                    # Not sure why this happened...
                    pass
            return [None, None]
        if self.matchup:
            try:
                data = py_gg.champion.matchup(self.matchup)
                role_found = False
                for matchup_list in data:
                    if matchup_list['role'] == self.role:
                        role_found = True
                        data = matchup_list['matchups']
                if role_found:
                    for champ in self.champions:
                        winrate_games = search_matchup_winrates(data, champ.key)
                        if winrate_games[0] and winrate_games[1]:
                            champ.matchup_win_percent = 100 - winrate_games[0]
                            champ.matchup_games = winrate_games[1]
                else:
                    self.api_errors.append("Matchups against {} do not exist for the role of {}".format(self.matchup, self.role))
            except:
                self.api_errors.append("Champion.gg API failed to respond")
            

    def get_champion_masteries(self):
        """Get the champion masteries of a summoner"""
        def search_champion_masteries(dictionary, identifier):
            for champion, mastery in dictionary.items():
                try:
                    if identifier == champion.id:
                        return {
                            'level': mastery.level,
                            'points_since_last_level': mastery.points_since_last_level,
                            'last_played': mastery.last_played
                            }
                except AttributeError:
                    pass #possible riotapi bug
        try:
            masteries = riotapi.get_champion_masteries(self.summoner_info)
            for champion in self.champions:
                personal_masteries = search_champion_masteries(masteries, champion.id)
                if personal_masteries:
                    champion.mastery_level = personal_masteries['level']
                    champion.mastery_points_since_last_level = personal_masteries['points_since_last_level']
                    champion.last_played = personal_masteries['last_played']
        except APIError:
            self.api_errors.append("Riot API error occured")
        


    def order_champions_by_rating(self):
        """"Return champions in order of their rating"""
        self.champions.sort(key=lambda x: x.rating, reverse=True )


    def get_personal_winrates(self):
        """Gets personal winrates on all champs for a role"""
        def search_personal_winrates(dictionary, identifier):
            """Finds winrate and games of a summoner if they exist
            :param dictionary: Dictionary of stats
            :type dictionary: dict
            :param key: Champion id to search for
            :type key: str
            :rtype: array [winrate, games]
            """
            for champion, aggregated in dictionary.items():
                try:
                    if identifier == champion.id:
                        return [100 * aggregated.wins / aggregated.games_played, aggregated.games_played]
                except AttributeError:
                    # riotapi bug: sometimes champion object is None
                    pass
        try:
            stats = riotapi.get_ranked_stats(self.summoner_info)
            for champion in self.champions:
                personal_winrate_games = search_personal_winrates(stats, champion.id)
                if personal_winrate_games:
                    champion.personal_win_percent = personal_winrate_games[0]
                    champion.personal_games = personal_winrate_games[1]
        except APIError:
            self.api_errors.append("Riot API error occured")
        
    
    def run(self):
        self.get_champ_data_by_role()
        t1 = threading.Thread(target=self.get_personal_winrates)
        t1.start()
        t2 = threading.Thread(target=self.get_matchup_winrates)
        t2.start()
        t3 = threading.Thread(target=self.get_champion_masteries)
        t3.start()
        t1.join()
        t2.join()
        t3.join()
        for champ in self.champions:
            if champ.key == self.matchup:
                self.champions.remove(champ)
            else:
                champ.calculate_rating()
        self.order_champions_by_rating()
            


class ChampionPick(object):
    """Class for champion data with which rating is calculated."""

    def __init__(self, name, key, id, lol_version, overall_win_percent=0):
        """"
        :param name: Name of champion
        :type name: str
        :param key: Name of champion but with no special characters
        :type key: str
        :param id: id of champion
        :type id: int
        :param overall_win_percent: Win percentage of champion.
        :type overall_win_percent: int
        """
        self.name = name
        self.key = key
        self.overall_win_percent = overall_win_percent
        self.matchup_win_percent = 0
        self.personal_win_percent = 0
        self.personal_games = 0
        self.matchup_games= 0
        self.id = id
        self.mastery_level = 0
        self.mastery_points_since_last_level = 0
        self.last_played = None
        self.lol_version = lol_version
        self._BASE_IMG_URL = 'http://ddragon.leagueoflegends.com/cdn/{}/img/champion/'.format(self.lol_version)
        self.img_url = '{}{}.png'.format(self._BASE_IMG_URL, self.key)
        self.rating = 0

    def to_json(self):
        champion_json = {
            'name': self.name,
            'key': self.key,
            'img_url': self.img_url,
            'rating': self.rating,
            'overall_win_percent': self.overall_win_percent,
            'personal_win_percent': self.personal_win_percent,
            'personal_games': self.personal_games,
            'matchup_win_percent': self.matchup_win_percent,
            'matchup_games': self.matchup_games,
            'mastery_level': self.mastery_level,
            'mastery_points_since_last_level': self.mastery_points_since_last_level,
            'last_played': self.last_played
        }
        return champion_json

    def calculate_rating(self):
        """Calculates rating based on win percentage"""
        base_rating = 10000
        personal = 42
        matchup = 45
        mastery_multiplier = 1
        if self.personal_games > 40:
            personal = self.personal_win_percent * (1 + self.personal_games/1000)
        elif self.personal_games > 10:
            personal = self.personal_win_percent * (0.8 + self.personal_games/200)
        if self.matchup_games > 2000:
            matchup = self.matchup_win_percent * 1.04
        elif self.matchup_games > 50:
            matchup = self.matchup_win_percent * (1 + self.matchup_games/50000)
        elif self.matchup_games > 30:
            matchup = self.matchup_win_percent * (0.7 + 3 * self.matchup_games/500)
        mastery_multiplier = 1 + (self.mastery_level**2 / 100)
        if self.mastery_level is 5:
            mastery_multiplier = mastery_multiplier + self.mastery_points_since_last_level/1000000
        elif self.mastery_level is 0:
            mastery_multiplier = 0.75
        self.rating = int(base_rating * (self.overall_win_percent/50) * (personal/50) * (matchup/50) * mastery_multiplier)

class ChampionDetailGenerator(object):
    """Generates champion.gg data on a champion on a given role"""

    def __init__(self, champion, role):
        self.champion = champion
        self.role = role
        self.api_errors = []
        try:
            riotapi.set_region("EUW") # Region doesn't matter in this case
            riotapi.set_api_key('3bdf3fcc-39db-4f5a-8a1f-477fb97f7094')
        except APIError: 
            self.api_errors.append("Initialisation error")
        try:
            versions = riotapi.get_versions()
            self.lol_version = versions[0]
        except APIError:
            self.api_errors.append("Riot API error occured")
        try:
            py_gg.init('ae89f8f81c1334bf7174a6622d47aa2c')
        except InvalidAPIKeyError:
            self.api_errors.append("Invalid API Key error")
        except:
            self.api_errors.append("Champion.gg API failed to respond")
    
    def replace_rune_id(self, data):
        """replace the ids with the url to the cdn and add version
        :param data: details of a champion in a given role
        :param type: dict
        :rtype: dict
        """
        runes_list = riotapi.get_runes()
        for rune_number, data_rune in enumerate(data["runes"]["highestWinPercent"]["runes"]):
            for riot_rune in runes_list:
                if riot_rune.id == data_rune["id"]:
                    data["runes"]["highestWinPercent"]["runes"][rune_number]["id"] = riot_rune.image.link
        for rune_number, data_rune in enumerate(data["runes"]["mostGames"]["runes"]):
            for riot_rune in runes_list:
                if riot_rune.id == data_rune["id"]:
                    data["runes"]["mostGames"]["runes"][rune_number]["id"] = riot_rune.image.link
        return data
    
    def get_spell_image_link(self, data):
        """Finds the url to the image of a spell
        :param data: details of a champion in a given role
        :param type: dict
        :rtype: dict
        """
        champions_list = riotapi.get_champions()
        for champion in champions_list:
            if self.champion.upper() == champion.key.upper():
                for counter, spell in enumerate(champion.spells):
                    data["skills"]["skillInfo"][counter]["image"] = spell.image.link
                return data
        self.api_errors("Riot API error occured")
        return data
        
    
    def replace_summoner_id(self, data):
        """Replace names of summoner abilities for the url to the cdn
        :param data: details of a champion in a given role
        :param type: dict
        :rtype: dict
        """
        if data["summoners"]["highestWinPercent"]["summoner1"]["name"] == "Ignite":
            data["summoners"]["highestWinPercent"]["summoner1"]["other"] = "Dot"
        elif data["summoners"]["highestWinPercent"]["summoner1"]["name"] == "Ghost":
            data["summoners"]["highestWinPercent"]["summoner1"]["other"] = "Haste"
        elif data["summoners"]["highestWinPercent"]["summoner1"]["name"] == "Cleanse":
            data["summoners"]["highestWinPercent"]["summoner1"]["other"] = "Boost"
        else:
            data["summoners"]["highestWinPercent"]["summoner1"]["other"] = data["summoners"]["highestWinPercent"]["summoner1"]["name"]
            
        if data["summoners"]["highestWinPercent"]["summoner2"]["name"] == "Ignite":
            data["summoners"]["highestWinPercent"]["summoner2"]["other"] = "Dot"
        elif data["summoners"]["highestWinPercent"]["summoner2"]["name"] == "Ghost":
            data["summoners"]["highestWinPercent"]["summoner2"]["other"] = "Haste"
        elif data["summoners"]["highestWinPercent"]["summoner2"]["name"] == "Cleanse":
            data["summoners"]["highestWinPercent"]["summoner2"]["other"] = "Boost"
        else:
            data["summoners"]["highestWinPercent"]["summoner2"]["other"] = data["summoners"]["highestWinPercent"]["summoner2"]["name"]
            
        if data["summoners"]["mostGames"]["summoner1"]["name"] == "Ignite":
            data["summoners"]["mostGames"]["summoner1"]["other"] = "Dot"
        elif data["summoners"]["mostGames"]["summoner1"]["name"] == "Ghost":
            data["summoners"]["mostGames"]["summoner1"]["other"] = "Haste"
        elif data["summoners"]["mostGames"]["summoner1"]["name"] == "Cleanse":
            data["summoners"]["mostGames"]["summoner1"]["other"] = "Boost"
        else:
            data["summoners"]["mostGames"]["summoner1"]["other"] = data["summoners"]["mostGames"]["summoner1"]["name"]
            
        if data["summoners"]["mostGames"]["summoner2"]["name"] == "Ignite":
            data["summoners"]["mostGames"]["summoner2"]["other"] = "Dot"
        elif data["summoners"]["mostGames"]["summoner2"]["name"] == "Ghost":
            data["summoners"]["mostGames"]["summoner2"]["other"] = "Haste"
        elif data["summoners"]["mostGames"]["summoner2"]["name"] == "Cleanse":
            data["summoners"]["mostGames"]["summoner2"]["other"] = "Boost"
        else:
            data["summoners"]["mostGames"]["summoner2"]["other"] = data["summoners"]["mostGames"]["summoner2"]["name"]
        return data
        

    def get_champion_detail(self):
        data = None
        try:
            champ_data = py_gg.champion.specific(self.champion)
            for role in champ_data:
                if role['role'].upper() == self.role.upper():
                    data = role
        except:
            self.api_errors.append("Champion.gg API failed to respond")
            return None
        data = self.replace_rune_id(data)
        data = self.replace_summoner_id(data)
        data = self.get_spell_image_link(data)
        data["version"] = self.lol_version
        data["key"] = self.champion
        return data
        
        