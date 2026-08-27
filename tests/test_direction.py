import numpy as np
from openadjust.core.network import Network
from openadjust.core.point import Point
from openadjust.models.direction import DirectionObservation
from openadjust.core.adjustment import LeastSquaresAdjustment

net = Network(name="Richtungstest")
net.add_point(Point(id="A", x=0.0,   y=0.0, z=0.0, fixed_x=True, fixed_y=True, fixed_z=True))
net.add_point(Point(id="B", x=100.0, y=0.0, z=0.0, fixed_x=True, fixed_y=True, fixed_z=True))
net.add_point(Point(id="N", x=48.0,  y=42.0, z=0.0, fixed_z=True))   # Näherung leicht daneben

N_true, A, B = (50.0, 40.0), (0.0, 0.0), (100.0, 0.0)
def bearing(fr, to):
    b = np.arctan2(to[1]-fr[1], to[0]-fr[0]); return b + 2*np.pi if b < 0 else b
def meas(fr, to, o): return (bearing(fr, to) - o) % (2*np.pi)  # r = Azimut - o

oA, oB, std = 1.2, 2.7, 1e-4     # wahre Orientierungen, ~6 mgon
net.add_observation(DirectionObservation(id="A_B", station="A", target="B", value=meas(A,B,oA),      std_dev=std))
net.add_observation(DirectionObservation(id="A_N", station="A", target="N", value=meas(A,N_true,oA), std_dev=std))
net.add_observation(DirectionObservation(id="B_A", station="B", target="A", value=meas(B,A,oB),      std_dev=std))
net.add_observation(DirectionObservation(id="B_N", station="B", target="N", value=meas(B,N_true,oB), std_dev=std))

res = LeastSquaresAdjustment(net, verbose=True).run()
print("N (soll 50.000 / 40.000):", round(net.points['N'].x, 4), round(net.points['N'].y, 4))
print("oA (soll 1.2):", round(net.orientations['A'], 4), " oB (soll 2.7):", round(net.orientations['B'], 4))
