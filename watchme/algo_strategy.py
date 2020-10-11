import gamelib
import random
import math
import warnings
from sys import maxsize
import json

class AlgoStrategy(gamelib.AlgoCore):
    def __init__(self):
        super().__init__()
        seed = random.randrange(maxsize)
        random.seed(seed)
        gamelib.debug_write('Random seed: {}'.format(seed))

    def on_game_start(self, config):

        gamelib.debug_write('Configuring your custom algo strategy...')
        self.config = config
        global WALL, FACTORY, TURRET, SCOUT, DEMOLISHER, INTERCEPTOR, MP, SP
        WALL = config["unitInformation"][0]["shorthand"]
        FACTORY = config["unitInformation"][1]["shorthand"]
        TURRET = config["unitInformation"][2]["shorthand"]
        SCOUT = config["unitInformation"][3]["shorthand"]
        DEMOLISHER = config["unitInformation"][4]["shorthand"]
        INTERCEPTOR = config["unitInformation"][5]["shorthand"]
        MP = 1
        SP = 0

        self.level_0_defense = {
            0: (WALL, [[0, 13], [27, 13], [26, 12], [1, 12], [3, 13], [23, 12]]),
            1: (TURRET, [[3, 12], [23, 11], [7, 8]])
        }
        self.level_0_interceptor_locations = [[25, 11], [21, 7], [10, 3], [4, 9], [25, 11]]

        self.level_1_defense = {
            0: (WALL,[[25, 11], [24, 10], [23, 9], [22, 8],
                   [23, 9], [22, 8], [21, 7], [20, 6],
                   [19, 5], [18, 5], [17, 5], [16, 4],
                   [15, 3], [14, 3], [13, 3], [12, 3],
                   [11, 4], [10, 5], [9, 6], [8, 7],
                   [6, 9], [5, 10]]),
            1: (TURRET, [[5, 11], [6, 11]]),
            2: (WALL, [[2, 12], [6, 12], [5, 12]])
        }
        self.level_1_interceptor_locations = [[4, 9], [7, 6]]

        self.level_2_defense = {
            0: (WALL, [[26, 13], [25, 12]]),
            1: (TURRET, [[25, 13]])
        }

        self.replace_health_threshold = 0.7

        self.stage_0_defense_upgrades = [[3, 12], [5, 11], [6, 11], [3, 13],
                                         [5, 12], [6, 12]]

        self.stage_1_defense_upgrades = [[27, 13], [0, 13], [26, 13], [1, 12],
                                         [26, 12], [25, 12], [25, 11], [25, 13]]

        self.most_critical_units = [[27, 13], [26, 13], [0, 13]]

        self.stage_0_replace_units = {
            0: (WALL, [[27, 13], [26, 13], [26, 12]]),
            1: (TURRET, [[25, 13]]),
            2: (WALL, [[25, 12], [25, 11]])
        }

        self.stage_1_replace_units = {
            0: (TURRET, [[3, 12], [5, 11], [6, 11]]),
            1: (WALL, [[6, 12], [5, 12], [3, 13]])
        }

        self.critical_defense_units = {}

        self.factory_locations =  [[i, 4] for i in range(13, 16)] + \
                                  [[i, 5] for i in range(13, 17)] + \
                                  [[i, 6] for i in range(13, 20)] + \
                                  [[i, 7] for i in range(12, 21)] + \
                                  [[i, 8] for i in range(11, 22)] + \
                                  [[i, 9] for i in range(10, 23)] + \
                                  [[i, 10] for i in range(9, 24)]

    def on_turn(self, turn_state):

        game_state = gamelib.GameState(self.config, turn_state)
        gamelib.debug_write('Performing turn {} of your custom algo strategy'.format(game_state.turn_number))
        game_state.suppress_warnings(True)  #Comment or remove this line to enable warnings.

        self.watchme_strategy(game_state)

        game_state.submit_turn()


    def watchme_strategy(self, game_state):

        self.build_defense(game_state)
        self.build_factory(game_state)


    def build_defense(self, game_state):
        turn = game_state.turn_number
        if turn <= 2:
            self.build_defense_for_round(game_state, self.level_0_defense)
            game_state.attempt_spawn(INTERCEPTOR, self.level_0_interceptor_locations)
        elif turn <= 4:
            self.build_defense_for_round(game_state, self.level_0_defense)
            self.build_defense_for_round(game_state, self.level_1_defense)
            game_state.attempt_spawn(INTERCEPTOR, self.level_1_interceptor_locations)
        else:
            self.build_defense_for_round(game_state, self.level_0_defense)
            self.build_defense_for_round(game_state, self.level_1_defense)
            self.build_defense_for_round(game_state, self.level_2_defense)

            self.replace_defense_for_round(game_state, self.stage_0_replace_units)
            self.replace_defense_for_round(game_state, self.stage_1_replace_units)

            self.upgrade_defense_for_round(game_state, self.stage_0_defense_upgrades)
            self.upgrade_defense_for_round(game_state, self.stage_1_defense_upgrades)
            game_state.attempt_spawn(INTERCEPTOR, self.level_1_interceptor_locations)

            curr_mp = game_state.get_resource(MP, 0)
            if curr_mp > 100:
                game_state.attempt_spawn(SCOUT, [[15, 1] for _ in range(110)])


    def build_factory(self, game_state):

        for location in self.factory_locations:
            game_state.attempt_spawn(FACTORY, location)
            game_state.attempt_upgrade(location)

    def build_defense_for_round(self, game_state, defense_dict):

        for order in defense_dict.keys():
            unit_type, unit_locations = defense_dict[order]
            game_state.attempt_spawn(unit_type, unit_locations)

    def replace_defense_for_round(self, game_state, replace_dict):
        # curr_sp = game_state.get_resource(SP, 0)
        for i in replace_dict.keys():
            unit_type, unit_locations = replace_dict[i]
            for unit in unit_locations:
                curr_units = game_state.game_map[unit[0], unit[1]]
                if len(curr_units) > 0:
                    if unit in self.most_critical_units:
                        game_state.attempt_remove(unit)
                    else:
                        unit_max_health = curr_units[0].max_health
                        unit_cur_health = curr_units[0].health
                        is_unit_upgraded = curr_units[0].upgraded
                        unit_initial_cost = game_state.type_cost(unit_type, is_unit_upgraded)[0]
                        refund = 0.75 * unit_initial_cost * (unit_cur_health / unit_max_health)
                        if float(unit_cur_health / unit_max_health) < 0.5:
                            game_state.attempt_remove(unit)

    def upgrade_defense_for_round(self, game_state, upgrade_list):
        for unit in upgrade_list:
            game_state.attempt_upgrade(unit)

if __name__ == "__main__":
    algo = AlgoStrategy()
    algo.start()
