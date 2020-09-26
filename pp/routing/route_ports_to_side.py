import numpy as np
import pp
from pp.routing.connect import connect_strip
from pp.routing.connect import connect_elec
from pp.port import is_electrical_port
from pp.port import flipped

BEND_RADIUS = pp.config.BEND_RADIUS


def route_elec_ports_to_side(ports, side="north", wire_sep=20.0, x=None, y=None):
    return route_ports_to_side(
        ports, side=side, bend_radius=0, separation=wire_sep, x=x, y=y
    )


def route_ports_to_side(
    ports, side="north", x=None, y=None, routing_func=None, **kwargs
):
    """ Routes ports to a given side

    Args:
        ports: the list of ports to be connected to the side
            can also be a dictionnary, a <pp.Component> or a phidl
            <ComponentReference>
        side should be 'north', 'south', 'east' or 'west'

        x: only for east/west side routing: the x position where the ports should be sent
            If None, will use the eastest/westest value

        y: only for south/north side routing: the y position where the ports should be send
            If None, will use the southest/northest value

        routing_func: the routing function. By default uses either `connect_elec`
        or `connect_strip` depending on the ports layer.

        kwargs: may include:
            `bend_radius`
            `extend_bottom`, `extend_top` for east/west routing
            `extend_left`, `extend_right` for south/north routing
    """

    if not ports:
        return [], []

    # Accept list of ports, Component or dict of ports
    if isinstance(ports, dict):
        ports = list(ports.values())

    elif isinstance(ports, pp.Component) or isinstance(ports, pp.ComponentReference):
        ports = list(ports.ports.values())

    # Convenient default selection for connection function point to point
    if routing_func is None:
        if is_electrical_port(ports[0]):
            routing_func = connect_elec
        else:
            routing_func = connect_strip

    # Choose which
    if side in ["north", "south"]:
        func_route = connect_ports_to_y
        if y is not None:
            xy = y
        else:
            xy = side

    elif side in ["west", "east"]:
        if x is not None:
            xy = x
        else:
            xy = side

        func_route = connect_ports_to_x

    return func_route(ports, xy, routing_func=routing_func, **kwargs)


def route_ports_to_north(list_ports, **kwargs):
    return route_ports_to_side(list_ports, side="north", **kwargs)


def route_ports_to_south(list_ports, **kwargs):
    return route_ports_to_side(list_ports, side="south", **kwargs)


def route_ports_to_west(list_ports, **kwargs):
    return route_ports_to_side(list_ports, side="west", **kwargs)


def route_ports_to_east(list_ports, **kwargs):
    return route_ports_to_side(list_ports, side="east", **kwargs)


def connect_ports_to_x(
    list_ports,
    x="east",
    separation=10.0,
    bend_radius=BEND_RADIUS,
    extend_bottom=0,
    extend_top=0,
    extension_length=0,
    y0_bottom=None,
    y0_top=None,
    routing_func=connect_strip,
    routing_func_args={},
    backward_port_side_split_index=0,
):
    """
     * ``list_ports``: reasonably well behaved list of ports
            i.e
            ports facing north ports are norther than any other ports
            ports facing south ports are souther ...
            ports facing west ports are the wester ...
            ports facing east ports are the easter ...

     * ``x``: float or string:
                if float: x coordinate to which the ports will be routed
                if string: "east" -> route to east
                if string: "west" -> route to west

     * ``backward_port_side_split_index``: integer
            this integer represents and index in the list of backwards ports
                (bottom to top)
            all ports with an index strictly lower or equal are routed bottom
            all ports with an index larger or equal are routed top

    Returns:
        - a list of connectors which can be added to an element list
        - a list of the new optical ports

    """

    north_ports = [p for p in list_ports if p.angle == 90]
    south_ports = [p for p in list_ports if p.angle == 270]
    east_ports = [p for p in list_ports if p.angle == 0]
    west_ports = [p for p in list_ports if p.angle == 180]

    epsilon = 1.0
    a = epsilon + max(bend_radius, separation)
    xs = [p.x for p in list_ports]
    ys = [p.y for p in list_ports]

    if y0_bottom is None:
        y0_bottom = min(ys) - a
    y0_bottom -= extend_bottom

    if y0_top is None:
        y0_top = max(ys) + a
    y0_top += extend_top

    if x == "west" and extension_length > 0:
        extension_length = -extension_length

    if x == "east":
        x = max([p.x for p in list_ports]) + a
    elif x == "west":
        x = min([p.x for p in list_ports]) - a
    elif type(x) == float:
        pass
    else:
        pass
        # raise ValueError('``x`` should be a float or "east" or "west"')

    sort_key_west_to_east = lambda p: p.x
    sort_key_east_to_west = lambda p: -p.x

    sort_key_south_to_north = lambda p: p.y
    sort_key_north_to_south = lambda p: -p.y

    if x < min(xs):
        sort_key_north = sort_key_west_to_east
        sort_key_south = sort_key_west_to_east
        forward_ports = west_ports
        backward_ports = east_ports
        angle = 0

    elif x > max(xs):
        sort_key_south = sort_key_east_to_west
        sort_key_north = sort_key_east_to_west
        forward_ports = east_ports
        backward_ports = west_ports
        angle = 180
    else:
        raise ValueError("x should be either to the east or to the west of all ports")
    """
    First route the bottom-half of the back ports
        (back ports are the one facing opposite side of x)
    Then route the south ports
    then the front ports
    then the north ports
    """

    # forward_ports.sort()
    north_ports.sort(key=sort_key_north)
    south_ports.sort(key=sort_key_south)
    forward_ports.sort(key=sort_key_south_to_north)

    backward_ports.sort(key=sort_key_south_to_north)
    backward_ports_thru_south = backward_ports[0:backward_port_side_split_index]
    backward_ports_thru_north = backward_ports[backward_port_side_split_index:]
    backward_ports_thru_south.sort(key=sort_key_south_to_north)
    backward_ports_thru_north.sort(key=sort_key_north_to_south)

    elements = []
    ports = []

    def add_port(p, y, l_elements, l_ports, start_straight=0.01):
        new_port = p._copy()
        new_port.angle = angle
        new_port.position = (x + extension_length, y)
        l_elements += [
            routing_func(
                p,
                new_port,
                start_straight=start_straight,
                bend_radius=bend_radius,
                **routing_func_args
            )
        ]
        l_ports += [flipped(new_port)]

    y_optical_bot = y0_bottom
    for p in south_ports:
        add_port(p, y_optical_bot, elements, ports)
        y_optical_bot -= separation

    for p in forward_ports:
        add_port(p, p.y, elements, ports)

    y_optical_top = y0_top
    for p in north_ports:
        add_port(p, y_optical_top, elements, ports)
        y_optical_top += separation

    start_straight = 0.01
    start_straight0 = 0
    max_x = max(xs)
    min_x = min(xs)

    for p in backward_ports_thru_north:
        # Extend ports if necessary
        if angle == 0 and p.x < max_x:
            start_straight0 = max_x - p.x
        elif angle == 180 and p.x > min_x:
            start_straight0 = p.x - min_x
        else:
            start_straight0 = 0

        add_port(
            p,
            y_optical_top,
            elements,
            ports,
            start_straight=start_straight + start_straight0,
        )
        y_optical_top += separation
        start_straight += separation

    start_straight = 0.01
    start_straight0 = 0
    for p in backward_ports_thru_south:
        # Extend ports if necessary
        if angle == 0 and p.x < max_x:
            start_straight0 = max_x - p.x
        elif angle == 180 and p.x > min_x:
            start_straight0 = p.x - min_x
        else:
            start_straight0 = 0

        add_port(
            p,
            y_optical_bot,
            elements,
            ports,
            start_straight=start_straight + start_straight0,
        )
        y_optical_bot -= separation
        start_straight += separation

    return elements, ports


def connect_ports_to_y(
    list_ports,
    y="north",
    separation=10.0,
    bend_radius=BEND_RADIUS,
    x0_left=None,
    x0_right=None,
    extension_length=0,
    extend_left=0,
    extend_right=0,
    routing_func=connect_strip,
    routing_func_args={},
    backward_port_side_split_index=0,
):
    """
     * ``list_ports``: reasonably well behaved list of ports
            i.e
            ports facing north ports are norther than any other ports
            ports facing south ports are souther ...
            ports facing west ports are the wester ...
            ports facing east ports are the easter ...

     * ``y``: float or string:
                if float: y coordinate to which the ports will be routed
                if string: "north" -> route to north
                if string: "south" -> route to south

     * ``backward_port_side_split_index``: integer
            this integer represents and index in the list of backwards ports
                (sorted from left to right)
            all ports with an index strictly larger are routed right
            all ports with an index lower or equal are routed left

    Returns:
        - a list of connectors which can be added to an element list
        - a list of the new optical ports

    """

    if y == "south" and extension_length > 0:
        extension_length = -extension_length

    da = 45
    north_ports = [p for p in list_ports if p.angle > 90 - da and p.angle < 90 + da]
    south_ports = [p for p in list_ports if p.angle > 270 - da and p.angle < 270 + da]
    east_ports = [p for p in list_ports if p.angle < da or p.angle > 360 - da]
    west_ports = [p for p in list_ports if p.angle < 180 + da and p.angle > 180 - da]

    epsilon = 1.0
    a = bend_radius + max(bend_radius, separation)
    xs = [p.x for p in list_ports]
    ys = [p.y for p in list_ports]

    x0_right = x0_right or max(xs) + a
    x0_right += extend_right
    x0_left = x0_left or min(xs) - a
    x0_left -= extend_left

    if y == "north":
        y = (
            max([p.y + a * np.abs(np.cos(p.angle * np.pi / 180)) for p in list_ports])
            + epsilon
        )
    elif y == "south":
        y = (
            min([p.y - a * np.abs(np.cos(p.angle * np.pi / 180)) for p in list_ports])
            - epsilon
        )
    elif type(y) == float:
        pass
    else:
        pass
        # raise ValueError('``y`` should be a float or "north" or "south"')

    sort_key_west_to_east = lambda p: p.x
    sort_key_east_to_west = lambda p: -p.x
    sort_key_south_to_north = lambda p: p.y
    sort_key_north_to_south = lambda p: -p.y

    if y <= min(ys):
        sort_key_east = sort_key_south_to_north
        sort_key_west = sort_key_south_to_north
        forward_ports = south_ports
        backward_ports = north_ports
        angle = 90.0

    elif y >= max(ys):
        sort_key_west = sort_key_north_to_south
        sort_key_east = sort_key_north_to_south
        forward_ports = north_ports
        backward_ports = south_ports
        angle = -90.0
    else:
        raise ValueError("y should be either to the north or to the south of all ports")
    """
    First route the bottom-half of the back ports
        (back ports are the one facing opposite side of x)
    Then route the south ports
    then the front ports
    then the north ports
    """

    west_ports.sort(key=sort_key_west)
    east_ports.sort(key=sort_key_east)
    forward_ports.sort(key=sort_key_west_to_east)
    backward_ports.sort(key=sort_key_east_to_west)

    backward_ports.sort(key=sort_key_west_to_east)
    backward_ports_thru_west = backward_ports[0:backward_port_side_split_index]
    backward_ports_thru_east = backward_ports[backward_port_side_split_index:]

    backward_ports_thru_west.sort(key=sort_key_west_to_east)
    backward_ports_thru_east.sort(key=sort_key_east_to_west)

    elements = []
    ports = []

    def add_port(p, x, l_elements, l_ports, start_straight=0.01):
        new_port = p._copy()
        new_port.angle = angle
        new_port.position = (x, y + extension_length)

        if np.sum(np.abs((new_port.position - p.position) ** 2)) < 1e-12:
            l_ports += [flipped(new_port)]
            return

        try:
            l_elements += [
                routing_func(
                    p,
                    new_port,
                    start_straight=start_straight,
                    bend_radius=bend_radius,
                    **routing_func_args
                )
            ]
            l_ports += [flipped(new_port)]

        except Exception as e:
            print("**************************")
            print("Could not connect")
            print(p)
            print(new_port)
            print("**************************")
            raise e

    x_optical_left = x0_left
    for p in west_ports:
        add_port(p, x_optical_left, elements, ports)
        x_optical_left -= separation

    for p in forward_ports:
        add_port(p, p.x, elements, ports)

    x_optical_right = x0_right
    for p in east_ports:
        add_port(p, x_optical_right, elements, ports)
        x_optical_right += separation

    start_straight = 0.01
    for p in backward_ports_thru_east:
        add_port(p, x_optical_right, elements, ports, start_straight=start_straight)
        x_optical_right += separation
        start_straight += separation

    start_straight = 0.01
    for p in backward_ports_thru_west:
        add_port(p, x_optical_left, elements, ports, start_straight=start_straight)
        x_optical_left -= separation
        start_straight += separation

    return elements, ports


def demo():
    from pp.component import Component
    from pp.layers import LAYER

    def dummy():
        cmp = Component()
        xs = [0.0, 10.0, 25.0, 50.0]
        ys = [0.0, 10.0, 25.0, 50.0]
        a = 5
        xl = min(xs) - a
        xr = max(xs) + a
        yb = min(ys) - a
        yt = max(ys) + a

        cmp.add_polygon([(xl, yb), (xl, yt), (xr, yt), (xr, yb)], LAYER.WG)

        for i, y in enumerate(ys):
            p0 = (xl, y)
            p1 = (xr, y)
            cmp.add_port(name="W{}".format(i), midpoint=p0, orientation=180, width=0.5)
            cmp.add_port(name="E{}".format(i), midpoint=p1, orientation=0, width=0.5)

        for i, x in enumerate(xs):
            p0 = (x, yb)
            p1 = (x, yt)
            cmp.add_port(name="S{}".format(i), midpoint=p0, orientation=270, width=0.5)
            cmp.add_port(name="N{}".format(i), midpoint=p1, orientation=90, width=0.5)

        return cmp

    def top_level():
        cmp = Component()
        _dummy_t = dummy()
        sides = ["north", "south", "east", "west"]
        positions = [(0, 0), (400, 0), (400, 400), (0, 400)]
        for pos, side in zip(positions, sides):
            dummy_ref = _dummy_t.ref(position=pos)
            cmp.add(dummy_ref)
            conns, ports = route_ports_to_side(dummy_ref, side)
            for e in conns:
                cmp.add(e)
            for i, p in enumerate(ports):
                cmp.add_port(name="{}{}".format(side[0], i), port=p)
        return cmp

    pp.show(top_level())


if __name__ == "__main__":
    demo()
