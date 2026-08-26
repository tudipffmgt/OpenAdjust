import json
from openadjust.core.network import Network
from openadjust.core.point import Point
from openadjust.models.distance import DistanceObservation
from openadjust.core.adjustment import LeastSquaresAdjustment
from openadjust.io.serialization import result_to_dict


def run_simple_triangle():
    net = Network(name="Einfaches Dreieck")

    # 2 Festpunkte + 1 Neupunkt (Näherungskoordinaten für N)
    net.add_point(Point(id="A", x=0.0,   y=0.0,  z=0.0, fixed_x=True, fixed_y=True, fixed_z=True))
    net.add_point(Point(id="B", x=100.0, y=0.0,  z=0.0, fixed_x=True, fixed_y=True, fixed_z=True))
    net.add_point(Point(id="N", x=50.0,  y=80.0, z=0.0, fixed_z=True))

    # 3 Strecken (σ = 2 mm). z ist fixiert → reines 2D-Problem.
    net.add_observation(DistanceObservation(id="d1", station="A", target="N", value=94.34, std_dev=0.002))
    net.add_observation(DistanceObservation(id="d2", station="B", target="N", value=94.34, std_dev=0.002))
    net.add_observation(DistanceObservation(id="d3", station="A", target="B", value=100.00, std_dev=0.002))

    result = LeastSquaresAdjustment(net, verbose=False).run()
    return json.dumps(result_to_dict(result))
