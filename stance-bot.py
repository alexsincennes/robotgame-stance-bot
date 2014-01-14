import rg
import itertools
import random


class Quadrant:
	"""A cartesian quadrant section of the arena.
	Properties currently hardcoded.

	Constructor:
		Quadrant(quad_num)

	Fields:
		Location min_corner
		Location max_corner
		Location center
		Robot[] quad_friends
		Robot[] quad_foes
		int twin"""


	def __init__(self, quad_num, arena_data):

		# define min and max corners and center

		min_corner = []
		size = []

		if quad_num == 1 or quad_num == 3:
			size = [9,10]
		elif quad_num == 2 or quad_num == 4:
			size = [10,9]

		if quad_num == 1:
			min_corner = [9,0]
			self.center = (12,6)
		elif quad_num == 2:
			min_corner = [0,0]
			self.center = (6,6)
		elif quad_num == 3:
			min_corner = [0,8]
			self.center = (6,12)
		elif quad_num == 4:
			min_corner = [8,9]
			self.center = (12,12)

		max_corner = [x + y for x, y in zip(min_corner, size)]

		self.min_corner = list(min_corner)
		self.max_corner = list(max_corner)


		# define friends and foes in the quad
		
		self.quad_friends = []
		self.quad_foes = []

		range_x = xrange(self.min_corner[0], self.max_corner[0])
		range_y = xrange(self.min_corner[1], self.max_corner[1])

		for x,y in itertools.product(range_x, range_y):
			if (x,y) in arena_data.game.robots:
				if arena_data.game.robots[(x,y)].player_id != arena_data.robot.player_id:
					self.quad_foes.append(arena_data.game.robots[(x,y)])
				else:
					self.quad_friends.append(arena_data.game.robots[(x,y)])

		# assign twin quad (link quad_num & II, and IIquad_num & IV)

		if quad_num % 2 == 0:
			self.twin = quad_num - 1
		else:
			self.twin = quad_num + 1


	########################################################################


class ArenaData:
	"""Collection of data the robot constructs and queries each turn.
	
	Constructor:
		ArenaData(robot, game)

	Fields:
		Game game
		Robot robot
		Robot[] total_friends
		Robot[] total_foes
		Robot[] group
		Quadrant[] quadrants: I, II, III, IV
		int current_quad_num
		int regroup_quad_num
	
	Public methods:
		Robot[] get_quad_friends()
		Robot[] get_quad_foes()
		int get_twin()
		Quadrant get_quadrant(quad_num)
		Quadrant get_current_quadrant()
		Location get_regroup_point()
		Loaction find_closest_foe()
		boolean quadrant_superiority()"""


	def __init__(self, robot, game, local_data):
		
		self.robot = robot
		self.game = game

		self.total_friends = []
		self.total_foes = []
		self._index_bots()


		self.quadrants = [Quadrant(1, self), Quadrant(2, self), Quadrant(3, self), Quadrant(4, self)]

		self.current_quad_num = self._find_quad()

		self.group = []
		self._find_group(self.group, [], local_data)

		self.regroup_quad_num = self._find_regroup_quad()


	def _find_regroup_quad(self):

		if len(self.get_current_quadrant().quad_foes) == 0:
			this_quad_ratio = 0
		else:
			this_quad_ratio = len(self.get_current_quadrant().quad_friends) / len(self.get_current_quadrant().quad_foes)
		
		if len(self.get_quadrant(self.get_twin()).quad_foes) == 0:
			twin_quad_ratio = 0
		else:
			twin_quad_ratio = len(self.get_quadrant(self.get_twin()).quad_friends) / len(self.get_quadrant(self.get_twin()).quad_foes)

		# if this quad less friendly than twin quad
		if this_quad_ratio < twin_quad_ratio:
			return self.get_twin()
		else: # >=
			return self.current_quad_num



	def _find_group(self, group, visited, local_data):
		"""Helper method. Finds coherent group robot is attached to, if exists"""

		# find immediate friends
		for friendly_robot in local_data.immediate_friends:
			if not friendly_robot in group:
				group.append(friendly_robot)


		# recursively iterate through the others
		visited.append(self.robot)
		for rob in group:
			if not rob in visited:
				self._find_group(group, visited, LocalData(rob, local_data.game))


	def _index_bots(self):
		"""Helper method. Index all robots by friend and foe."""

		for loc, rob in self.game.robots.items():
			# #print robot
			if rob.player_id == self.robot.player_id:
				self.total_friends.append(rob)
			else:
				self.total_foes.append(rob)

	def _find_quad(self):
		"""Helper method. Find which quadrant the robot belongs to."""

		for num in range(1,5):
			for other_robot in self.get_quadrant(num).quad_friends:
				if self.robot.location == other_robot.location:
					return num
		
		print "Severe error: bot not found!"
		return 0


	def get_quad_friends(self):
		return self.quadrants[self.current_quad_num-1].friends

	def get_quad_foes(self):
		return self.quadrants[self.current_quad_num-1].quad_foes

	def get_twin(self):
		return self.quadrants[self.current_quad_num-1].twin

	def get_quadrant(self, quad_num):
		return self.quadrants[quad_num-1]

	def get_current_quadrant(self):
		return self.get_quadrant(self.current_quad_num)

	def get_regroup_point(self):
		return self.get_quadrant(self.regroup_quad_num).center

	def find_closest_foe(self):
		""""Finds enemy robot closest to location of given robot and returns its location.
		Breaks ties by lowest HP. Assumes there are enemies remaining"""

		closest_robots = []
		if self.total_foes:
			closest_robot = self.total_foes[0] # take any robot to start out
			for rob in self.total_foes:
				current_dist = rg.wdist(self.robot.location, rob.location)
				if current_dist < rg.wdist(self.robot.location, closest_robot.location):
					closest_robot = rob

			# make list of closest robots (may include more than one)

			for rob in self.total_foes:
				current_dist = rg.wdist(self.robot.location, rob.location)
				if current_dist == rg.wdist(self.robot.location, closest_robot.location):
					closest_robots.append(rob)
			
			# break ties with lowest HP if more than one closest robot

			if len(closest_robots) > 1:
				lowest_HP_rob = closest_robots[0]
				for rob in closest_robots:
					if rob.hp < lowest_HP_rob.hp:
						lowest_HP_rob = rob

				return lowest_HP_rob.location

			else: # only one robot, pick him
				return closest_robots[0].location

	def quadrant_superiority(self):
		"""Returns true if #friends >= #enemies in this quadrant"""
		return len(self.get_quad_friends()) >= len(self.get_quad_foes())


	########################################################################

class LocalData:
	"""Collection of data about the immediate surroundings of the robot.

	Fields:
		Robot robot
		Game game
		Location[] valid_locs -> not invalid locs and not a wall
		Location[] unobstructed_locs -> no friends or enemies in it
		Location[] normal_unobstructed_locs -> unobstructed + not spawn
		Location[] safe_locs	-> unobstructed + no enemies around it
		string[] current_loc_types
		Robot[] immediate_friends
		Robot[] immediate_enemies

	Public methods:
		Robot[] enemies_around(location, player_id)"""

	def __init__(self, robot, game):

		self.robot = robot
		self.game = game
		self.current_loc_types = rg.loc_types(robot.location)

		self.unobstructed_locs = []
		self.normal_unobstructed_locs = []
		self.safe_locs = []

		self.immediate_friends = []
		self.immediate_enemies = []
		
		valid_and_wall_locs = rg.locs_around(robot.location, filter_out='invalid')

		self.valid_locs = []
		for vwloc in valid_and_wall_locs:
			if 'obstacle' in rg.loc_types(vwloc):
				for rob_loc in game.robots:
					#print rob_loc
					#print game.robots[rob_loc]
					if rob_loc == vwloc:
						self.valid_locs.append(vwloc)
						if game.robots[rob_loc].player_id == robot.player_id:
							self.immediate_friends.append(game.robots[rob_loc])
						else:
							self.immediate_enemies.append(game.robots[rob_loc])

				# if obstacle and not robot location -> not 'valid'
			else:
				self.valid_locs.append(vwloc)
				self.unobstructed_locs.append(vwloc)

		for unobloc in self.unobstructed_locs:
			if not 'spawn' in rg.loc_types(unobloc):
				self.normal_unobstructed_locs.append(unobloc)

			if not self.enemies_around(unobloc, robot.player_id):
				self.safe_locs.append(unobloc)
			

	def enemies_around(self, location, player_id):
		"""Returns list of enemies around that tile."""

		actual_enemies = []
		potential_enemies = self.valid_locs

		if potential_enemies:
			for loc, bot in self.game.robots.iteritems():
				if bot.player_id != player_id:
					if rg.wdist(loc, location) <= 1:
						actual_enemies.append(bot)

		return actual_enemies


	########################################################################

class RobotCalculations:
	"""Wrapper class around a robot and game, to permit recursion."""

	def __init__(self, robot, game, recursion_count = 0):

		self.recursion_count = recursion_count
		self.max_recursive = 2 # only allow one recursive iteration

		self.robot = robot
		self.game = game
		
		random.seed()
		self.local_data = LocalData(self.robot, self.game)
		self.arena_data = ArenaData(self.robot, self.game, self.local_data)


	########################################################################


	def evaluate_direction(self):
		"""Set robot's ultimate direction based on situation of quadrant."""

		# very early game -> head to center
		if self.game.turn < rg.settings.spawn_every / 3:
			return rg.CENTER_POINT
		# later game -> context specific
		else:
			# if less enemies here than in our twin --> TODO wrapper for twin foes
			if len(self.arena_data.get_quad_foes() ) < len(self.arena_data.get_quadrant(self.arena_data.get_twin()).quad_foes ):
				# get closest enemy and set it as destination
				return self.arena_data.find_closest_foe()

			# not grouped -> regroup
			# more enemies here than twin -> regroup (in twin)
			# no enemies -> regroup
			return self.arena_data.get_regroup_point()


	########################################################################

	# set of LOCAL STANCE METHODS which return a move
	# TODO put reused code in seperate methods

	def endangered_stance(self):
		"""Simply suicide for now.
		
		Preconditions:
			no safe locations or where a friend used to be
			1 or more enemies can lethally attack it"""

		print "endangered_stance"

		return ['suicide']

	def cautious_stance(self, towards, recursive = False):
		"""Attacks neighbours, then tries to help friends, otherwise attacks towards.
		
		Preconditions:
			no safe location exists
			is not endangered"""

		print "cautious_stance"

		# if we're already there, try to move to attack nearby enemies
		# not random for now, maybe fix later
		if not recursive:
			if self.robot.location == towards:
				for loc, bot in self.arena_data.game.robots.iteritems():
					if bot.player_id != self.robot.player_id:
						if rg.dist(loc, self.robot.location) <= 3:
							return self.cautious_stance(rg.toward(self.robot.location, loc), recursive=True)

			# help adjacent allies as second priority
			for loc in self.local_data.unobstructed_locs:
				if self.can_flank_enemy_safely(loc):
					if not recursive:
						if not self.friendly_running_into_me(loc):
							return ['move', loc]
					else:
						return ['move', loc]

			# attack immediate neighbours first
			possible_attack = self.attack_if_beside(self.robot)
			if possible_attack:
				return possible_attack

		# attack possible enemy move locations
		return ['attack', towards]

	def passive_stance(self, towards, recursive=False):
		"""Ignores neighbours, otherwise moves to towards.
		
		Preconditions:
			can move into a safe location or where a friend used to be"""

		print "passive_stance"

		
		if not recursive:

			# if we're already there, try to move to attack nearby enemies
			if self.robot.location == towards:
				for loc, bot in self.game.robots.iteritems():
					if bot.player_id != self.robot.player_id:
						if rg.dist(loc, self.robot.location) <= 3:
							return self.aggressive_stance(rg.toward(loc), recursive=True)

			# help adjacent allies as second priority
			for loc in self.local_data.unobstructed_locs:
				if self.can_flank_enemy_safely(loc):
					if not recursive:
						if not self.friendly_running_into_me(loc):
							return ['move', loc]
					else:
						return ['move', loc]

			# make sure we're not running into a friendly
			if self.friendly_running_into_me(towards):
				if self.local_data.safe_locs > 1:
					for sloc in self.local_data.safe_locs:
						if sloc != towards:
							self.passive_stance(sloc, recursive=True)
				else: # no safe locs -> let's aggressive stance for now
					return self.aggressive_stance(towards, recursive=True)

		return ['move', towards]

	def aggressive_stance(self, towards, recursive=False):
		"""Attacks neighbours, then tries to help friends, otherwise moves to towards.
		
		Preconditions:
			towards is a safe location
			is not endangered"""

		print "aggressive_stance and recursive=" + str(recursive)

		# if we're already there, try to move to attack nearby enemies
		# not random for now, maybe fix later
		if not recursive:
			if self.robot.location == towards:
				for loc, bot in self.robots.iteritems():
					if bot.player_id != self.robot.player_id:
						if rg.dist(loc, self.robot.location) <= 3:
							return self.aggressive_stance(rg.toward(self.robot.location, loc), recursive=True)

			# attack immediate neighbours first
			possible_attack = self.attack_if_beside(self.robot)
			if possible_attack:
				return possible_attack

			# help adjacent allies as second priority
			for loc in self.local_data.unobstructed_locs:
				if self.can_flank_enemy_safely(loc):
					if not recursive:
						if not self.friendly_running_into_me(loc):
							return ['move', loc]
					else:
						return ['move', loc]

			# make sure we're not running into a friendly
			if self.friendly_running_into_me(towards):
				if self.local_data.safe_locs > 1:
					for sloc in self.local_data.safe_locs:
						if sloc != towards:
							self.aggressive_stance(sloc, recursive=True)
				else: # no safe locs -> let's guard for now
					return self.guarded_stance()

		return ['move', towards]

	def guarded_stance(self):
		"""Simply guard for now.
		
		Preconditions:
			no safe locations or where a friend used to be
			1 or more enemies can lethally attack it
			said enemies all have at least 1 other friendly on them"""

		print "guarded_stance"

		return ['guard']

	def spawn_evac_stance(self):
		"""Special case for when at spawn and will die if does not move.
		Simply suicide for now."""

		print "spawn_evac_stance"

		return ['suicide']


	########################################################################

	# helpers

	def avg_attack(self):
		"""Return the average attack value of a bot attack."""
		return (rg.settings.attack_range[0] + rg.settings.attack_range[1])/2

	def attack_if_beside(self, robot):

		# taken from example bot
		# if there are enemies around, attack them
		#hostiles = False
		for loc, bot in self.game.robots.iteritems():
			if bot.player_id != robot.player_id:
				if rg.dist(loc, robot.location) <= 1:
					#hostiles = True
					#if bot.hp > (local_data.immediate_enemies()-1) * avg_attack():
					return ['attack', loc]

		# flee if not worth time to kill anything / might be suicide
		# if no hostiles -> carry out other game plan
		#if hostiles:
		#	for adj_loc in rg.locs_around(robot.location, filter_out=('invalid', 'obstacle')):
		#		if safe_to_move(robot, arena_data, adj_loc):
		#			return ['move', adj_loc]


	def can_flank_enemy_safely(self, location):
		"""Look for enemies that are beside friends, whom we can flank. If so, output True."""

		try:
			if self.game.robots[location]:
				return False
		except Exception:
			#print "no robot here"
			x=1

		enemy_count = 0
		enemies_low_HP = 0
		# all true enemies must be "busy" in order to move in	

		for loc, bot in self.arena_data.game.robots.iteritems():
			if bot.player_id != self.arena_data.robot.player_id:
				if rg.wdist(loc, location) <= 1:
					enemy_count += 1
					if bot.hp < self.avg_attack():
						enemies_low_HP += 1
					if not self.attack_if_beside(bot):
						return False

		#if enemy_count:
			#print "bot #" + str(robot.robot_id) + " " + str(enemy_count) + " and all enemies busy"

		# 0 -> false -> no enemies to flank
		# if all enemies have low HP -> not worth the flank, AND might be a suicide
		return enemy_count > 0 and enemy_count != enemies_low_HP


	def friendly_running_into_me(self, move_loc):
		"""Avoid wasting a turn running into a friendly."""

		if self.recursion_count < self.max_recursive:
			for loc, bot in self.arena_data.game.robots.iteritems():
				if bot.player_id == self.robot.player_id and bot.robot_id != self.robot.robot_id:
					if rg.dist(loc, move_loc) <= 1:
						#print "friendlies beside my move tile" # (overly simplified)
						self.recursion_count += 1
						rec_robo_calc = RobotCalculations(bot, self.game, self.recursion_count)
						self.recursion_count -= 1
						if move_loc in rec_robo_calc.main():
							#print "friendlies running into me"
							return True

		return False

	########################################################################

	def main(self):
		"""Dispatch other methods based on situation."""

		# pick direction (macro-scale)
		direction = self.evaluate_direction()
		toward_loc = rg.toward(self.robot.location, direction)

		print "destination :  " + str(direction) + " and predicted next move: " + str(toward_loc)


		# pick stance (micro-scale)

		# extreme failure case
		if 'invalid' in self.local_data.current_loc_types:
			print "Robot on invalid tile; impossible!"
			return ['suicide']

		# special cases where if does not evacuate NOW it will die
		elif 'spawn' in self.local_data.current_loc_types:
			# in two turns it will be destroyed
			# check that next turn it can leave to a 'normal' location
			if self.game.turn % rg.settings.spawn_every == rg.settings.spawn_every - 1:
				# can't move anywhere
				if not self.local_data.normal_unobstructed_locs: 
					return self.endangered_stance()
				# can't move to non-spawn
				elif not self.local_data.normal_unobstructed_locs: 
					if not self.local_data.safe_locs:
						return self.endangered_stance()
					else:
						return self.passive_stance(random.choice(self.local_data.safe_locs))
				# can move to non-spawn
				else:
					if not self.local_data.safe_locs:
						return self.guarded_stance()
					else:
						return self.passive_stance(random.choice(self.local_data.safe_locs))

			# in one turn it will be destroyed
			elif self.game.turn % rg.settings.spawn_every == 0:
				# can move to non-spawn
				if not self.local_data.normal_unobstructed_locs: 
					if self.local_data.safe_locs:
						return self.passive_stance(random.choice(self.local_data.safe_locs))

				return self.spawn_evac_stance()
			
			else:
				# nothing special -> get out passively IF WE CAN
				if toward_loc in self.local_data.safe_locs:
					return self.passive_stance(toward_loc)
				elif self.local_data.safe_locs:
					return self.passive_stance(random.choice(self.local_data.safe_locs))
				else:
					return cautious_stance(toward_loc)

		########################################################################

		# normal location 
		elif 'normal' in self.local_data.current_loc_types:
			# early game -> ignore ignore ignore!
			if self.game.turn < rg.settings.spawn_every / 2 - 1:
				return self.passive_stance(toward_loc)
			
			else: #later game
				if self.local_data.immediate_enemies:
					# if in a bad spot!
					lethally_threatened = len(self.local_data.immediate_enemies) * self.avg_attack() > self.robot.hp
					badly_surrounded = self.local_data.immediate_enemies >= 2 or not self.arena_data.quadrant_superiority()
					if lethally_threatened or badly_surrounded:
						if self.local_data.safe_locs:
							return self.passive_stance(random.choice(local_data.safe_locs))
						elif self.local_data.immediate_friends:
							for f in local_data.immediate_friends:
								rec_robo_calc = RobotCalculations(f, self.game)
								fmove = rec_robo_calc.main()
								if 'move' in fmove:
									return passive_stance(fmove[1])

						# other cases where robot is lethally threatened:
						# if all enemies 'occupied' with friends, guarded stance
						# else endangered stance (surrounded with no help)
						for e in self.local_data.immediate_enemies:
							if not (len(self.local_data.enemies_around(e.location, e.player_id)) <= 1):
								return self.endangered_stance()

						return self.guarded_stance()

				# not a lethal threat or no threat:
				# stance based on our destination this time
				if toward_loc in self.local_data.safe_locs:
					print "entry into aggresstive from dispatcher"
					return self.aggressive_stance(toward_loc)
				else:
					return self.cautious_stance(toward_loc)

			print "Not supposed to be here..."
			return ['guard']

	########################################################################

class Robot:

	def act(self, game):

		print "robot ID: " + str(self.robot_id)

		# set up globals
		random.seed()
		robo_calc = RobotCalculations(self, game)

		# act
		move = robo_calc.main()

		# prevent move to one's own tile
		if self.location in move:
			print "Moving to itself... fix before it gets here!"
			return ['guard']

		return move