
import argparse
import sys

import numpy as np

from backend.python.enums import Mobility, Shape, TestSpawn, Containment
from backend.python.functions import get_random_element, separate_into_classes
from backend.python.location.Blocks.UrbanBlock import UrbanBlock
from backend.python.location.Cemetery import Cemetery
from backend.python.location.Residential.Home import Home
from backend.python.main import main
from backend.python.const import work_map
from backend.python.point.BusDriver import BusDriver
from backend.python.point.Student import Student
from backend.python.transport.Bus import Bus
from backend.python.transport.CommercialZoneBus import CommercialZoneBus
from backend.python.transport.SchoolBus import SchoolBus
from backend.python.transport.Tuktuk import Tuktuk
from backend.python.transport.Walk import Walk

iterations = 100000
testing_freq = 10
test_center_spawn_check_freq = 10
test_center_spawn_method = TestSpawn.HEATMAP.value
test_center_spawn_threshold = 100



def initialize2():
    # initialize people
    people = []
    # people += [GarmentWorker() for _ in range(100)]
    # people += [GarmentAdmin() for _ in range(10)]
    # people += [CommercialWorker() for _ in range(10)]
    people += [Student() for _ in range(2)]

    # people += [TuktukDriver() for _ in range(5)]
    # people += [BusDriver() for _ in range(10)]
    # people += [CommercialZoneBusDriver() for _ in range(10)]
    # people += [SchoolBusDriver() for _ in range(10)]
    for _ in range(0):
        idx = np.random.randint(0, len(people))
        people[idx].set_infected(0, people[idx], args.common_p)

    # initialize location tree
    root = Home(Shape.CIRCLE.value, 0, 0, "UB", r=10)
    root.add_sub_location(Cemetery(Shape.CIRCLE.value, 0, -80, "Cemetery", r=3))


    # set random routes for each person and set their main transportation method
    walk = Walk(Mobility.RANDOM.value)
    bus = Bus(Mobility.RANDOM.value)
    combus = CommercialZoneBus(Mobility.RANDOM.value)
    schoolbus = SchoolBus(Mobility.RANDOM.value)
    tuktuk = Tuktuk(Mobility.RANDOM.value)
    main_trans = [walk]

    for person in people:
        if person.main_trans is None:
            person.main_trans = get_random_element(main_trans)
        person.set_home_loc(root)
    return people, root


if __name__ == "__main__":
    global args
    parser = argparse.ArgumentParser(description='Create emulator for COVID-19 pandemic')
    parser.add_argument('-n', help='target population', default=100)
    parser.add_argument('-i', help='initial infected', type=int, default=10)

    parser.add_argument('--infect_r', help='infection radius', type=float, default=1)
    parser.add_argument('--common_p', help='common fever probability', type=float, default=0.1)

    parser.add_argument('--containment', help='containment strategy used ', type=int,
                        default=Containment.NONE.value)
    parser.add_argument('--testing', help='testing strategy used (0-Random, 1-Temperature based)', type=int, default=1)
    parser.add_argument('--test_centers', help='Number of test centers', type=int, default=3)
    parser.add_argument('--test_acc', help='Test accuracy', type=float, default=0.80)
    parser.add_argument('--test_center_r', help='Mean radius of coverage from the test center', type=int, default=20)
    parser.add_argument('--asymptotic_t',
                        help='Mean asymptotic period. (Test acc gradually increases with disease age)',
                        type=int, default=14)

    parser.add_argument('--initialize',
                        help='How to initialize the positions (0-Random, 1-From file 2-From probability map)',
                        type=int, default=0)

    args = parser.parse_args()
    sys.setrecursionlimit(1000000)
    main(initialize2, args)
