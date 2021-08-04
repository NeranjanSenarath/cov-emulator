import numpy as np

from backend.python.MovementEngine import MovementEngine
from backend.python.RoutePlanningEngine import RoutePlanningEngine
from backend.python.Time import Time
from backend.python.enums import Mobility
from backend.python.functions import get_random_element, separate_into_classes
from backend.python.point.Transporter import Transporter
from backend.python.transport.Bus import Bus
from backend.python.transport.CommercialZoneBus import CommercialZoneBus


class CommercialZoneBusDriver(Transporter):
    max_latches = 30

    def __init__(self):
        super().__init__()
        self.main_trans = CommercialZoneBus(Mobility.RANDOM.value)

    def get_random_route(self, t, end_at):
        route_so_far = super(CommercialZoneBusDriver, self).get_random_route(t,Time.get_random_time_between(t, 5, 0,9, 0))

        # finally visit the working location
        route_so_far = self.get_random_route_through(route_so_far, [self.work_loc], find_from_level=1)
        route_so_far[-1].leaving_time = Time.get_random_time_between(t, 16, 30,18, 30)
        # add all the stop in between major route destinations
        route_so_far = RoutePlanningEngine.add_stops_as_targets_in_route(route_so_far, self)

        # come back the same way that bus went in the morning
        route_so_far = RoutePlanningEngine.mirror_route(route_so_far, self, duplicate_last=False, duplicate_first=False)
        return route_so_far
