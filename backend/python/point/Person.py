import numpy as np

from backend.python.Logger import Logger
from backend.python.MovementEngine import MovementEngine
from backend.python.const import DAY
from backend.python.enums import State
from backend.python.functions import find_in_subtree
from backend.python.location.Residential.Home import Home


class Person:
    normal_temperature = (36.8, 1.0)
    infect_temperature = (37.4, 1.2)
    _id = 0
    all_people = []
    n_characteristics = 3

    def __init__(self):
        self.ID = Person._id
        Person._id += 1

        self.gender = 0 if np.random.rand() < 0.5 else 1  # gender of the person
        self.age = np.random.uniform(1, 80)  # age todo add to repr
        self.immunity = 1 / self.age if np.random.rand() < 0.9 else np.random.rand()  # todo find and add to repr
        self.character_vector = np.zeros((Person.n_characteristics,))  # characteristics of the point
        self.behaviour = 0  # behaviour of the point (healthy medical practices -> unhealthy)

        self.x = 0  # x location
        self.y = 0  # y location
        self.vx = 0  # velocity x
        self.vy = 0  # velocity y

        self._backup_route = None
        self._backup_duration_time = None
        self._backup_leaving_time = None

        self.is_day_finished = False

        self.route = []  # route that point is going to take. (list of location refs)
        self.duration_time = []  # time spent on each location
        self.leaving_time = []  # time which the person will not overstay on a given location
        self.current_target_idx = -1  # current location in the route (index of the route list)
        self.current_loc_enter = -1
        self.current_loc_leave = -1

        self.home_loc = None
        self.work_loc = None
        self.current_loc = None

        self.main_trans = None  # main transport medium the point will use
        self.current_trans = None

        self.in_inter_trans = False
        self.latched_to = None
        self.latch_onto_hash = None

        self.state = State.SUSCEPTIBLE.value  # current state of the point (infected/dead/recovered etc.)

        self.source = None  # infected source point
        self.infected_time = -1  # infected time
        self.infected_location = None  # infected location (ID)
        self.disease_state = 0  # disease state, higher value means bad for the patient # todo add to repr

        self.tested_positive_time = -1  # tested positive time

        self.temp = 0  # temperature of the point
        self.update_temp(0.0)
        Person.all_people.append(self)

    def __repr__(self):
        d = self.get_description_dict()
        return ','.join(map(str, d.values()))

    def __str__(self):
        return str(self.ID)

    def get_description_dict(self):
        d = {'class': self.__class__.__name__, 'id': self.ID, 'x': self.x, 'y': self.y, 'vx': self.vx, 'vy': self.vy,
             'state': self.state, 'gender': self.gender, 'is_day_finished': self.is_day_finished,
             'current_target_idx': self.current_target_idx, 'current_loc_enter': self.current_loc_enter,
             'current_loc_leave': self.current_loc_leave, 'in_inter_trans': self.in_inter_trans,
             'wealth': self.character_vector,
             'behaviour': self.behaviour, 'infected_time': self.infected_time, 'temp': self.temp,
             "tested_positive_time": self.tested_positive_time}

        if self.current_loc is None:
            d['current_loc_id'] = -1
        else:
            d['current_loc_id'] = self.current_loc.ID
        if self.main_trans is None:
            d['main_trans_id'] = -1
        else:
            d['main_trans_id'] = self.main_trans.ID
        if self.current_trans is None:
            d['current_trans_id'] = -1
        else:
            d['current_trans_id'] = self.current_trans.ID

        if self.source is None:
            d['source_id'] = -1
        else:
            d['source_id'] = self.source.ID

        if self.infected_location is None:
            d['infected_location_id'] = -1
        else:
            d['infected_location_id'] = self.infected_location.ID

        d['route'] = [r.ID for r in self.route].__str__().replace(',', '|').replace(' ', '')
        d['duration_time'] = self.duration_time.__str__().replace(',', '|').replace(' ', '')
        d['leaving_time'] = self.leaving_time.__str__().replace(',', '|').replace(' ', '')
        return d

    def initialize_character_vector(self, vec):
        self.character_vector = vec

    def get_character_transform_matrix(self):
        return np.random.random((Person.n_characteristics, Person.n_characteristics))

    def backup_route(self):
        if self._backup_route is None:
            self._backup_route = [r for r in self.route]
            self._backup_duration_time = [r for r in self.duration_time]
            self._backup_leaving_time = [r for r in self.leaving_time]

    def restore_route(self):
        if self._backup_route is not None:
            self.route = [r for r in self._backup_route]
            self.duration_time = [r for r in self._backup_duration_time]
            self.leaving_time = [r for r in self._backup_leaving_time]
            self._backup_route = None
            self._backup_duration_time = None
            self._backup_leaving_time = None
            self.current_target_idx = len(self.route) - 1

    def reset_day(self, t):
        self.is_day_finished = False
        self.adjust_leaving_time(t)
        self.character_vector = np.dot(self.get_character_transform_matrix(), self.character_vector.T)

        if self.get_current_location() != self.home_loc and not self.get_current_location().quarantined:
            Logger.log(f"{self.ID} not at home when day resets. (Now at {self.get_current_location().name} "
                       f"from {self.current_trans.points_enter_time[self.current_trans.points.index(self)]}) "
                       f"CTarget {self.current_target_idx}/{len(self.route)} "
                       f"Route {list(map(str, self.route))}. "

                       , 'c')
            return False
        return True

    def on_enter_location(self, t):
        pass

    def adjust_leaving_time(self, t):
        _t = t - t % DAY
        for i in range(len(self.route)):
            if self.leaving_time[i] == -1:
                continue
            if self.leaving_time[i] < _t or self.leaving_time[i] > _t + DAY:
                self.leaving_time[i] = self.leaving_time[i] % DAY + _t

    def increment_target_location(self):
        msg = f"{self.ID} incremented target from {self.get_current_target()} to "
        self.current_target_idx = (self.current_target_idx + 1) % len(self.route)
        next_loc = MovementEngine.find_next_location(self)
        msg += f"{self.get_current_target()} ({self.current_target_idx} th target). Next location is {next_loc}."
        Logger.log(msg, 'c')
        if self.current_target_idx == 0:
            self.is_day_finished = True
            Logger.log(f"{self.ID} finished daily route!", 'c')

    def initialize_main_suggested_route(self):
        if self.home_loc is None:
            raise Exception("Initialize home before initializing route")
        self.route, self.duration_time, self.leaving_time, time = self.home_loc.get_suggested_sub_route(self, 0, False)
        self.route[0].enter_person(self)

    def find_closest(self, target, cur=None):
        if target is None:
            return None
        # find closest (in tree) object to target
        if cur is None:
            cur = self.get_current_target()  # todo current target or current location
        selected = find_in_subtree(cur, target, None)
        while selected is None:
            selected = find_in_subtree(cur.parent_location, target, cur)
            cur = cur.parent_location
        return selected

    def get_suggested_route(self, t, target_classes_or_objs, force_dt=False):
        if self.current_target_idx >= len(self.route):
            self.current_target_idx = len(self.route) - 1
        route, duration, leaving, time = [], [], [], t
        for target in target_classes_or_objs:
            selected = self.find_closest(target)
            if selected is None:
                raise Exception(f"Couldn't find {target} where {self} is currently at {self.get_current_target()}")
            _route, _duration, _leaving, time = selected.get_suggested_sub_route(self, time, force_dt)

            route += _route
            duration += _duration
            leaving += _leaving
        return route, duration, leaving, time

    def set_random_route(self, root, t, target_classes_or_objs=None):
        raise NotImplementedError()

    def update_route(self, root, t, new_route_classes=None, replace=False, keephome=True):
        """
        update the route of the person from current position onwards.
        if new_route_classes are given, new route will be randomly selected suggested routes from those classes
        :param root:
        :param t:
        :param new_route_classes:
        :return:
        """
        if new_route_classes is None:
            return

        Logger.log(f"Current route for {self.ID} is {list(map(str, self.route))}", 'e')
        _t = t % DAY
        self.backup_route()
        if replace:
            self.route = []
            self.duration_time = []
            self.leaving_time = []
        else:
            self.route = self.route[:self.current_target_idx + 1]
            self.duration_time = self.duration_time[:self.current_target_idx + 1]
            self.leaving_time = self.leaving_time[:self.current_target_idx + 1]
            # if self.route[-1] != self.current_loc:
            #     self.route += [self.current_loc]
            #     self.duration_time += [1]
            #     self.leaving_time += [-1]
            #     self.current_location += 1
        if keephome:  # todo update this
            if len(self.route) > 0 and isinstance(self.route[0], Home):
                pass
            else:
                self.route = [self._backup_route[0]] + self.route
                self.duration_time = [self._backup_duration_time[0]] + self.duration_time
                self.leaving_time = [self._backup_leaving_time[0]] + self.leaving_time
        # todo make sure current_target_idx is consistent with route
        route, duration, leaving, time = self.get_suggested_route(_t, new_route_classes, force_dt=True)

        self.route += route
        self.duration_time += duration
        self.leaving_time += leaving
        self.adjust_leaving_time(t)

        Logger.log(f"Route updated for {self.ID} as {list(map(str, self.route))}", 'e')

        if self.latched_to:
            Logger.log(f"{self.ID} is latched to {self.latched_to.ID}. "
                       f"Delatching at {self.get_current_location().name}!", 'e')
            self.latched_to.delatch(self)

        if self.current_target_idx >= len(self.route):
            self.current_target_idx = len(route) - 1
        if replace:
            self.route[0].enter_person(self, target_location=None)

    def set_route(self, route, duration, leaving, t):
        assert len(route) == len(duration) == len(leaving)

        self.x = route[0].x + np.random.normal(0, 1)
        self.y = route[0].y + np.random.normal(0, 1)

        self.route = route
        self.duration_time = duration
        self.leaving_time = leaving
        self.current_target_idx = 0
        self.route[0].enter_person(self)

    def set_position(self, new_x, new_y, is_updated_by_transporter=False):
        if not self.latched_to or is_updated_by_transporter:
            self.x = new_x
            self.y = new_y
        else:
            idx = self.current_trans.points.index(self)
            start = self.current_trans.points_enter_time[idx]
            raise Exception(f"Tried to move {self.ID} in {self.get_current_location()} (enter at:{start})."
                            f"Going to {self.get_next_target()}")

    def set_current_location(self, loc, t):
        self.current_loc = loc

    def get_current_location(self):
        return self.current_loc

    def get_current_target(self):
        return self.route[self.current_target_idx]

    def get_next_target(self):
        return self.route[(self.current_target_idx + 1) % len(self.route)]

    def set_infected(self, t, p, common_p):
        self.state = State.INFECTED.value
        self.infected_time = t
        self.source = p
        self.infected_location = p.get_current_location()
        self.update_temp(common_p)
        self.disease_state = 1

    def set_recovered(self):
        self.state = State.RECOVERED.value
        self.restore_route()
        self.disease_state = 0

    def set_susceptible(self):
        self.state = State.SUSCEPTIBLE.value

    def set_dead(self):
        self.state = State.DEAD.value
        self.temp = 25
        self.vx = 0
        self.vy = 0

    def is_infected(self):
        return self.state == State.INFECTED.value

    def is_recovered(self):
        return self.state == State.RECOVERED.value

    def is_dead(self):
        return self.state == State.DEAD.value

    def is_susceptible(self):
        return self.state == State.SUSCEPTIBLE.value

    def is_tested_positive(self):
        return self.tested_positive_time > 0

    def update_temp(self, common_p):
        if self.is_infected():
            self.temp = np.random.normal(*Person.infect_temperature)
        elif self.is_recovered() or self.is_susceptible():
            if np.random.rand() < common_p:  # Common fever
                self.temp = np.random.normal(*Person.infect_temperature)
            else:
                self.temp = np.random.normal(*Person.normal_temperature)
        elif self.is_dead():
            self.temp = 25
