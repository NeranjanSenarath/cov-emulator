from backend.python.enums import Mobility
from backend.python.transport.Transport import Transport
import numpy as np
import itertools


class TransportVehicle(Transport):

    def __init__(self, velocity_cap: float, mobility_pattern: Mobility):
        super().__init__(velocity_cap, mobility_pattern)

        self._vehicle_capacity = 60
        self._current_label = 0
        self._vehicle_waiting_time_after_initialization = 50
        self.route_label = {}
        self.vehicles_in_route = {}
        self.vehicles_in_route_leaving_t = {}

    @staticmethod
    def get_route_name(f, t):
        return str(f) + '->' + str(t)

    def initialize_locations(self, location):
        self.route_label[TransportVehicle.get_route_name(location, location)] = 0
        locs = [str(location)] + [str(l) for l in location.locations]

        pairs = list(itertools.combinations(locs, 2))
        n = len(pairs)
        for idx, pair in enumerate(pairs):
            self.route_label[TransportVehicle.get_route_name(pair[0], pair[1])] = idx // 3
            self.route_label[TransportVehicle.get_route_name(pair[1], pair[0])] = idx // 3
        if TransportVehicle.DEBUG:
            print(self.route_label)

    def add_point_to_transport(self, point, target_location, t):

        fr = point.current_loc
        to = target_location
        if to is not None:
            self.insert_into_vehicle(point, fr, to, t)

        super().add_point_to_transport(point, target_location, t)

    def remove_point_from_transport(self, point):
        idx = self.points.index(point)
        f = self.points_source[idx]
        t = self.points_destination[idx]
        if t is not None:
            rlabel = self.route_label[TransportVehicle.get_route_name(f, t)]
            vehicle_label = self.points_label[idx]
            self.vehicles_in_route[rlabel][vehicle_label].remove(point)

        super().remove_point_from_transport(point)

    def insert_into_vehicle(self, point, fr, to, t):
        rlabel = self.route_label[TransportVehicle.get_route_name(fr, to)]
        if rlabel not in self.vehicles_in_route.keys():
            self.vehicles_in_route[rlabel] = {}
            self.vehicles_in_route_leaving_t[rlabel] = {}

        success = False

        for key in self.vehicles_in_route[rlabel].keys():
            if len(self.vehicles_in_route[rlabel][key]) < self._vehicle_capacity:
                self.vehicles_in_route[rlabel][key].append(point)
                self._current_label = key
                success = True
                break
            else:
                self.vehicles_in_route_leaving_t[rlabel][key] = t - 1  # vehicle full. leave
        if not success:
            key = len(self.vehicles_in_route[rlabel].keys())
            self.vehicles_in_route[rlabel][key] = [point]
            self.vehicles_in_route_leaving_t[rlabel][key] = t + self._vehicle_waiting_time_after_initialization
            self._current_label = key
        if Transport.DEBUG:
            print(f"""Added person {point} going in {TransportVehicle.get_route_name(fr,
                                                                                     to)} which belong to route {rlabel} to {self} {self._current_label} {len(
                self.vehicles_in_route[rlabel][key])}/{self._vehicle_capacity}""")

    def get_point_label(self, point):
        return self._current_label

    def get_in_transport_transmission_p(self):
        return 0.8

    def transport_point(self, idx, destination_xy, t):
        rlabel = self.route_label[TransportVehicle.get_route_name(self.points_source[idx], self.points_destination[idx])]
        vlabel = self.points_label[idx]
        point = self.points[idx]
        if t > self.vehicles_in_route_leaving_t[rlabel][vlabel] or self.points_source[idx]==self.points_destination[idx]:
            point.x += np.sign(destination_xy[0] - point.x) * self.vcap if abs(
                destination_xy[0] - point.x) > self.vcap else destination_xy[0] - point.x
            point.y += np.sign(destination_xy[1] - point.y) * self.vcap if abs(
                destination_xy[1] - point.y) > self.vcap else destination_xy[1] - point.y
        else:
            if Transport.DEBUG:
                print(f"""At {t} point {point} is waiting till vehicle leaves at {self.vehicles_in_route_leaving_t[rlabel][vlabel]}. {len(
                self.vehicles_in_route[rlabel][vlabel])}/{self._vehicle_capacity}""")
            point.x += np.random.rand() / 10
            point.y += np.random.rand() / 10