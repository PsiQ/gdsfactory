""" bends with grating couplers inside the spiral
maybe: need to add grating coupler loopback as well
"""

import numpy as np
import pp
from pp.components.bend_circular import bend_circular
from pp.components.bend_circular import bend_circular180
from pp.components import waveguide
from pp.routing import round_corners
from numpy import float64
from pp.component import Component
from typing import Callable, Optional, Tuple


def get_bend_port_distances(bend: Component) -> Tuple[float64, float64]:
    p0, p1 = bend.ports.values()
    return abs(p0.x - p1.x), abs(p0.y - p1.y)


@pp.autoname
def spiral_external_io(
    N: int = 6,
    x_inner_length_cutback: float = 300.0,
    x_inner_offset: float = 0.0,
    y_straight_inner_top: float = 0.0,
    dx: float = 3.0,
    dy: float = 3.0,
    bend90_function: Callable = bend_circular,
    bend180_function: Callable = bend_circular180,
    bend_radius: float = 50.0,
    wg_width: float = 0.5,
    straight_factory: Callable = waveguide,
    straight_factory_fall_back_no_taper: None = None,
    taper: Optional[Callable] = None,
    cutback_length: Optional[float] = None,
    **kwargs_round_corner
) -> Component:
    """

    Args:
        cutback_length: length in um, it is the approximates total length
        N: number of loops
        x_straight_inner_right:
        x_straight_inner_left:
        y_straight_inner_top:
        dx: center to center x-spacing
        dy: center to center y-spacing
        grating_coupler
        bend90_function
        bend180_function
        bend_radius
        wg_width
        straight_factory
        taper

    .. plot::
      :include-source:

      import pp

      c = pp.c.spiral_external_io()
      pp.plotgds(c)
    """
    if straight_factory_fall_back_no_taper is None:
        straight_factory_fall_back_no_taper = straight_factory

    if cutback_length:
        x_inner_length_cutback = cutback_length / (4 * (N - 1))

    y_straight_inner_top += 5

    x_inner_length_cutback += x_inner_offset
    _bend180 = pp.call_if_func(bend180_function, radius=bend_radius, width=wg_width)
    _bend90 = pp.call_if_func(bend90_function, radius=bend_radius, width=wg_width)

    rx, ry = get_bend_port_distances(_bend90)
    _, rx180 = get_bend_port_distances(_bend180)  # rx180, second arg since we rotate

    component = pp.Component()

    inner_loop_spacing = 2 * bend_radius + 5.0

    # Create manhattan path going from west grating to westest port of bend 180

    x_inner_length = x_inner_length_cutback + 5.0 + dx

    y_inner_bend = y_straight_inner_top - bend_radius - 5.0
    x_inner_loop = x_inner_length - 5.0
    p1 = (x_inner_loop, y_inner_bend)
    p2 = (x_inner_loop + inner_loop_spacing, y_inner_bend)

    _pt = np.array(p1)
    pts_w = [_pt]

    for i in range(N):
        y1 = y_straight_inner_top + ry + (2 * i + 1) * dy
        x2 = inner_loop_spacing + 2 * rx + x_inner_length + (2 * i + 1) * dx
        y3 = -ry - (2 * i + 2) * dy
        x4 = -(2 * i + 1) * dx
        if i == N - 1:
            x4 = x4 - rx180 + dx

        _pt1 = np.array([_pt[0], y1])
        _pt2 = np.array([x2, _pt1[1]])
        _pt3 = np.array([_pt2[0], y3])
        _pt4 = np.array([x4, _pt3[1]])
        _pt5 = np.array([_pt4[0], 0])
        _pt = _pt5

        pts_w += [_pt1, _pt2, _pt3, _pt4, _pt5]

    pts_w = pts_w[:-2]

    # Create manhattan path going from east grating to eastest port of bend 180
    _pt = np.array(p2)
    pts_e = [_pt]

    for i in range(N):
        y1 = y_straight_inner_top + ry + (2 * i) * dy
        x2 = inner_loop_spacing + 2 * rx + x_inner_length + 2 * i * dx
        y3 = -ry - (2 * i + 1) * dy
        x4 = -2 * i * dx

        _pt1 = np.array([_pt[0], y1])
        _pt2 = np.array([x2, _pt1[1]])
        _pt3 = np.array([_pt2[0], y3])
        _pt4 = np.array([x4, _pt3[1]])
        _pt5 = np.array([_pt4[0], 0])
        _pt = _pt5

        pts_e += [_pt1, _pt2, _pt3, _pt4, _pt5]

    pts_e = pts_e[:-2]

    # Join the two bits of paths and extrude the spiral geometry
    route_ref = round_corners(
        pts_w[::-1] + pts_e,
        bend90=_bend90,
        straight_factory=straight_factory,
        straight_factory_fall_back_no_taper=straight_factory_fall_back_no_taper,
        taper=taper,
        **kwargs_round_corner,
    )
    component.add(route_ref)
    component.absorb(route_ref)

    component.ports = route_ref.ports
    component.length = route_ref.info["length"]
    component.settings["total_length"] = route_ref.info["length"]
    component.settings["length"] = route_ref.info["length"]
    component.settings["cutback_length"] = cutback_length

    return component


if __name__ == "__main__":
    c = spiral_external_io(bend_radius=10, cutback_length=10000)
    print(c.settings["total_length"] / 1e4)
    pp.show(c)
