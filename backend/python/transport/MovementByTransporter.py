from backend.python.Logger import Logger
from backend.python.MovementEngine import MovementEngine
from backend.python.enums import Mobility
from backend.python.point.Person import Person
from backend.python.point.Transporter import Transporter
from backend.python.transport.Movement import Movement
import numpy as np
import itertools


class MovementByTransporter(Movement):

    def get_in_transport_transmission_p(self):
        raise NotImplementedError()

    def __init__(self, velocity_cap: float, mobility_pattern: Mobility):
        super().__init__(velocity_cap, mobility_pattern)

    # override
    def get_description_dict(self):
        d = super().get_description_dict()
        return d

    # override
    def add_point_to_transport(self, point, target_location, t):
        super().add_point_to_transport(point, target_location, t)
        if isinstance(point, Transporter):
            self.try_to_latch_people(t)

    # override
    def transport_point(self, idx, destination_xy, t):
        point = self.points[idx]
        if not point.latched_to:
            super().transport_point(idx, destination_xy, t)

    def find_feasibility(self, tr, path2next_tar):
        hops2reach = [-1. for _ in path2next_tar]

        for i in range(len(path2next_tar)):
            tar = path2next_tar[i]
            hops = 0
            for j in range(tr.current_target_idx, len(tr.route)):
                hops += 1
                if tar == tr.route[j]:
                    break
            else:
                hops = -1
            hops2reach[i] = hops
        Logger.log(f"Path to target {list(map(str,path2next_tar))} {hops2reach}", 'e')
        des = None
        best = 1e10

        def cost(arr, x):
            return arr[x] * (len(arr) - x)

        for i in range(len(hops2reach)):
            if hops2reach[i] < 0:
                continue
            if cost(hops2reach, i) < best:
                best = cost(hops2reach, i)
                des = path2next_tar[i]
        return best, des

    def try_to_latch_person(self, p, t):
        possible_transporters = []  # element - (cost, transporter, destination)
        path2next_tar = MovementEngine.get_next_target_path(p)
        for pl in p.get_current_location().points:
            if isinstance(pl, Transporter):
                Logger.log(f"Trying to latch {p.ID} ({path2next_tar[-1].name}) in {self} to transporter "
                           f"{pl.ID} ({list(map(str,pl.route))}) {pl.get_current_location()}", 'e')
                cost, des = self.find_feasibility(pl, path2next_tar)
                if des is not None:
                    possible_transporters.append((cost, pl, des))
        if len(possible_transporters) == 0:
            print("No one to latch")
            return
        possible_transporters.sort(key=lambda x:x[0])

        (cost, transporter, destination) = possible_transporters[0]
        print(f"{p.ID} in {self} latched to transporter {transporter.ID} and will goto {destination.name}")
        transporter.latch(p, destination)


    def try_to_latch_people(self, t):
        # todo find people waiting for long time and make them walk
        for p in self.points:
            if isinstance(p, Transporter):
                continue
            if not p.latched_to:
                self.try_to_latch_person(p, t)
