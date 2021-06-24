import numpy as np

from backend.python.functions import get_random_element
from backend.python.point.Transporter import Transporter
from backend.python.transport.Bus import Bus


class BusDriver(Transporter):
    def __init__(self):
        super().__init__()
        self.max_latches = 10

    def set_random_route(self, root, t, target_classes_or_objs=None):
        arr_locs = []

        def dfs(rr):
            if rr.override_transport == Bus or rr.override_transport is None:
                arr_locs.append(rr)
            for child in rr.locations:
                dfs(child)

        dfs(root)

        target_classes_or_objs = [self.home_loc]
        for i in range(np.random.randint(10, 20)):  # todo find a good way to set up route of the transporters
            loc = get_random_element(get_random_element(arr_locs).locations)
            if loc == root:  # if we put root to bus route, people will drop at root. then he/she will get stuck
                continue
            target_classes_or_objs += [loc]

        route, duration, leaving, final_time = self.get_suggested_route(t, target_classes_or_objs)
        # route.append(route[-1])
        # duration.append(0)
        # leaving.append(-1)
        print(f"Bus route for {self.ID} is {list(map(str,route))}")
        self.set_route(route, duration, leaving, t)
