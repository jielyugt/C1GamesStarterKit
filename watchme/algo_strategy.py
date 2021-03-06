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

        # gamelib.debug_write('Configuring your custom algo strategy...')
        gamelib.debug_write('GAME STARTED!!!')
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
        self.level_0_interceptor_locations = [[25, 11], [21, 7], [10, 3], [4, 9], [10, 3]]

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
        self.level_1_interceptor_locations = [[4, 9], [10, 3], [10, 3]]

        self.failsafe_interceptor_locations = [[7, 6], [7, 6]]

        self.level_2_defense = {
            0: (WALL, [[26, 13], [25, 12]]),
            1: (TURRET, [[25, 13]])
        }

        self.level_3_defense = {
            0: (WALL, [[1, 13]]),
            1: (TURRET, [[6, 10], [3, 11], [21, 10], [18, 10], [15, 10], [12, 10]])
        }

        self.replace_unit_health_threshold = 0.5

        self.stage_0_defense_upgrades = [[3, 12], [5, 11], [6, 11], [3, 13],
                                         [5, 12], [6, 12], [6, 10], [3, 11]]

        self.stage_1_defense_upgrades = [[27, 13], [0, 13], [1, 13], [26, 13], [1, 12],
                                         [26, 12], [25, 12], [25, 11], [25, 13]]

        # self.stage_2_defense_upgrades = [[6, 10], [3, 11]]

        self.last_hit_corner = {
            'left': None,
            'right': None
        }

        self.left_emergency = False
        self.right_emergency = False
        self.corner_peace_period_threshold = 5
        self.left_critical_units = [[0, 13], [1, 12]]
        self.right_critical_units = [[27, 13], [26, 13]]

        self.stage_0_replace_units = {
            0: (WALL, [[0, 13], [1, 12], [2, 12], [27, 13],
                       [26, 13], [26, 12]]),
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
                                  [[i, 9] for i in range(10, 23)]
        self.total_factories = 0
        self.upgraded_factories = 0

        # last_rush_attack = [turn_number, scout count, enemy health]
        self.last_rush_attack = (None, None, None)
        self.rush_efficiency_threshold = 0.5
        self.min_rush_scout_count = 5
        self.inc_rush_scout_count = 15
        self.max_rush_scout_count = 40

        self.enemy_critical_locations = [[0, 14], [1, 14], [1, 15], [2, 14], [2, 15]]
        self.enemy_critical_wall_count = 0
        self.enemy_critical_turret_cont = 0


        self.assassinate_mode_on = False
        self.assassinate_ready = False
        self.assassinate_roadblock = {
            0: (WALL, [[4, 11], [2, 13]])
        }
        self.assassinate_to_remove = [[0, 13], [1, 13], [1, 12], [2, 12], [2, 11], [3, 11]]
        self.assassinate_bomb_count = 15
        self.assassinate_dagger_count = 40
        self.assassinate_MP_requirement = self.assassinate_bomb_count + self.assassinate_dagger_count

        self.enemy_MP_threshold_list = [27, 47, 67]

    def on_turn(self, turn_state):

        game_state = gamelib.GameState(self.config, turn_state)
        game_state.suppress_warnings(True)  #Comment or remove this line to enable warnings.

        self.watchme_strategy(game_state)

        game_state.submit_turn()


    def watchme_strategy(self, game_state):
        try:
            if self.assassinate_mode_on:

                if game_state.get_resource(MP, 0) > self.assassinate_MP_requirement:
                    self.assassinate_ready = True
                else:
                    self.assassinate_ready = False
        except:
            gamelib.debug_write("EXCEPTION IN CHECKING ASSASSINATION!!!")

        # Building basic defense
        try:
            self.build_defense(game_state)
        except:
            gamelib.debug_write("EXCEPTION IN BUILD DEFENSE!!!")
        # Building factories
        try:
            self.build_factory(game_state)
        except:
            gamelib.debug_write("EXCEPTION IN BUILD FACTORY!!!")
        # Initiating attack
        try:
            self.initiate_attack(game_state)
        except:
            gamelib.debug_write("EXCEPTION IN INITIATE ATTACK!!!")

        if self.assassinate_mode_on:
            game_state.attempt_remove(self.assassinate_to_remove)

    # def detect_enemy_critical_units(self, game_state):
    #     wall_count = 0
    #     turret_count = 0
    #     for location in self.enemy_critical_locations:
    #         unit_list = game_state.game_map[location[0], location[1]]
    #         if len(curr_units) > 0:
    #             unit = curr_units[0]



    def initiate_attack(self, game_state):
        curr_mp = game_state.get_resource(MP, 0)
        last_rush_attack_round, last_rush_attack_scout_count, last_rush_attack_enemy_health = self.last_rush_attack
        curr_enemy_health = game_state.enemy_health

        if last_rush_attack_round is not None:
            damage_dealt = last_rush_attack_enemy_health - curr_enemy_health
            # gamelib.debug_write("CURRENT ROUND NUMBER: {}".format(game_state.turn_number))
            # gamelib.debug_write("LAST EFFICIENCY: {}".format(float(damage_dealt / last_rush_attack_scout_count)))

            if game_state.turn_number == last_rush_attack_round + 1 and float(damage_dealt / last_rush_attack_scout_count) < self.rush_efficiency_threshold:
                self.min_rush_scout_count += self.inc_rush_scout_count
                if self.min_rush_scout_count > self.max_rush_scout_count:
                    self.assassinate_mode_on = True


        if curr_mp > self.min_rush_scout_count and not self.assassinate_mode_on:
            spawn_number = game_state.attempt_spawn(SCOUT, [[15, 1] for _ in range(100)])
            self.last_rush_attack = (game_state.turn_number, spawn_number, curr_enemy_health)

        if self.assassinate_ready:
            game_state.attempt_spawn(SCOUT, [[17, 3] for _ in range(self.assassinate_bomb_count)])
            game_state.attempt_spawn(SCOUT, [[18, 4] for _ in range(1000)])


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
            if self.assassinate_ready:
                self.build_defense_for_round(game_state, self.assassinate_roadblock)
                game_state.attempt_remove(self.assassinate_roadblock[0][1])

            self.build_defense_for_round(game_state, self.level_0_defense)
            self.build_defense_for_round(game_state, self.level_1_defense)
            self.build_defense_for_round(game_state, self.level_2_defense)

            self.total_factories, self.upgraded_factories = self.count_factories(game_state)
            if self.total_factories >= 7:
                self.build_defense_for_round(game_state, self.level_3_defense)

            enemy_MP = game_state.get_resource(MP, 1)
            for thresh in self.enemy_MP_threshold_list:
                if enemy_MP >= thresh:
                    game_state.attempt_spawn(INTERCEPTOR, self.failsafe_interceptor_locations)

            self.detect_corner_attacked(game_state)

            self.replace_defense_for_round(game_state, self.stage_0_replace_units)
            self.replace_defense_for_round(game_state, self.stage_1_replace_units)

            self.upgrade_defense_for_round(game_state, self.stage_0_defense_upgrades)
            self.upgrade_defense_for_round(game_state, self.stage_1_defense_upgrades)

    def build_factory(self, game_state):
        for location in self.factory_locations:
            game_state.attempt_spawn(FACTORY, location)
            game_state.attempt_upgrade(location)

    def count_factories(self, game_state):
        total_count = 0
        upgraded_count = 0
        for location in self.factory_locations:
            curr_units = game_state.game_map[location[0], location[1]]
            if len(curr_units) > 0:
                unit = curr_units[0]
                total_count += 1
                if unit.upgraded:
                    upgraded_count += 1
        return total_count, upgraded_count


    def detect_corner_attacked(self, game_state):
        curr_turn = game_state.turn_number
        # Check left corner
        for unit in self.left_critical_units:
            curr_units = game_state.game_map[unit[0], unit[1]]
            if len(curr_units) > 0:
                unit_max_health = curr_units[0].max_health
                unit_cur_health = curr_units[0].health
                if unit_cur_health < unit_max_health:
                    self.last_hit_corner['left'] = curr_turn
                    self.left_emergency = True
                else:
                    last_hit_turn = self.last_hit_corner['left']
                    if last_hit_turn is not None:
                        if curr_turn - last_hit_turn > self.corner_peace_period_threshold:
                            self.left_emergency = False
        # Check right corner
        for unit in self.right_critical_units:
            curr_units = game_state.game_map[unit[0], unit[1]]
            if len(curr_units) > 0:
                unit_max_health = curr_units[0].max_health
                unit_cur_health = curr_units[0].health
                if unit_cur_health < unit_max_health:
                    self.last_hit_corner['right'] = curr_turn
                    self.right_emergency = True
                else:
                    last_hit_turn = self.last_hit_corner['right']
                    if last_hit_turn is not None:
                        if curr_turn - last_hit_turn > self.corner_peace_period_threshold:
                            self.right_emergency = False

    def build_defense_for_round(self, game_state, defense_dict):

        for order in defense_dict.keys():
            unit_type, unit_locations = defense_dict[order]
            if self.assassinate_ready:
                unit_locations = [i for i in unit_locations if i not in self.assassinate_to_remove]
            if len(unit_locations) > 0:
                game_state.attempt_spawn(unit_type, unit_locations)

    def replace_defense_for_round(self, game_state, replace_dict):
        # curr_sp = game_state.get_resource(SP, 0)
        for i in replace_dict.keys():
            unit_type, unit_locations = replace_dict[i]
            for unit in unit_locations:
                curr_units = game_state.game_map[unit[0], unit[1]]
                if len(curr_units) > 0:
                    if (self.left_emergency and unit in self.left_critical_units) or \
                       (self.right_emergency and unit in self.right_critical_units):
                        game_state.attempt_remove(unit)
                    else:
                        unit_max_health = curr_units[0].max_health
                        unit_cur_health = curr_units[0].health
                        is_unit_upgraded = curr_units[0].upgraded
                        unit_initial_cost = game_state.type_cost(unit_type, is_unit_upgraded)[0]
                        refund = 0.75 * unit_initial_cost * (unit_cur_health / unit_max_health)
                        if float(unit_cur_health / unit_max_health) < self.replace_unit_health_threshold:
                            game_state.attempt_remove(unit)

    def upgrade_defense_for_round(self, game_state, upgrade_list):
        for unit in upgrade_list:
            game_state.attempt_upgrade(unit)

if __name__ == "__main__":
    algo = AlgoStrategy()
    algo.start()
