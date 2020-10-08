import numpy as np
from pp.routing.route_ports_to_side import route_ports_to_side
from pp.routing.connect import connect_strip_way_points
from pp.routing.manhattan import generate_manhattan_waypoints
from pp.routing.manhattan import remove_flat_angles
from pp.geo_utils import remove_identicals


def _groups(ports, cut, axis="X"):
    if axis == "Y":
        group1 = [p for p in ports if p.x <= cut]
        group2 = [p for p in ports if p.x > cut]
    else:
        group1 = [p for p in ports if p.y <= cut]
        group2 = [p for p in ports if p.y > cut]
    return group1, group2


def u_bundle_direct(
    start_ports,
    end_ports,
    route_filter=connect_strip_way_points,
    separation=5.0,
    start_straight=0.01,
    end_straight=0.01,
    start_straight_offset=0.0,
    end_straight_offset=0.0,
    **routing_params
):
    r"""
    Args:
        start_ports: list of start ports
        end_ports: list of end ports
        route_filter: filter to apply to the manhattan waypoints
            e.g `connect_strip_way_points` for deep etch strip waveguide

    Returns:
        `[route_filter(r) for r in routes]` where routes is a list of lists of coordinates
        e.g with default `connect_strip_way_points`, returns a list of elements which can be added to a component


    Used for routing multiple ports back to a bundled input in a component

    ::

        X: start ports
        D: End ports

        On this example bellow, the axis is along X

                           X------\
                                  |
                           X----\ |
                          ...   | |
                           X--\ | |
                              | | |
          D-------------------/ | |
          ...                   | |
          D---------------------/ |
          D-----------------------
          D-----------------------\
          D---------------------\ |
          ...                   | |
          D-------------------\ | |
                              | | |
                           X--/ | |
                          ...   | |
                           X----/ |
                                  |
                           X------/
    """

    routes = u_bundle_direct_routes(
        start_ports,
        end_ports,
        separation=separation,
        start_straight=start_straight,
        end_straight=end_straight,
        start_straight_offset=start_straight_offset,
        end_straight_offset=end_straight_offset,
        routing_func=generate_manhattan_waypoints,
        **routing_params
    )

    return [route_filter(route, **routing_params) for route in routes]


def u_bundle_direct_routes(
    start_ports,
    end_ports,
    routing_func=generate_manhattan_waypoints,
    separation=5.0,
    start_straight=0.01,
    end_straight=0.01,
    end_straight_offset=0.0,
    start_straight_offset=0.0,
    **routing_func_params
):

    nb_ports = len(start_ports)
    for p in start_ports:
        p.angle = p.angle % 360

    for p in end_ports:
        p.angle = p.angle % 360

    if len(end_ports) != nb_ports:
        raise ValueError(
            "Number of start ports should match number of end ports.\
        Got {} {}".format(
                len(start_ports), len(end_ports)
            )
        )
    if len(set([p.angle for p in start_ports + end_ports])) > 1:
        raise ValueError(
            "All ports should have the same angle\
        , got \n{}\n{}".format(
                start_ports, end_ports
            )
        )

    xs_end = [p.x for p in end_ports]
    ys_end = [p.y for p in end_ports]

    x_cut = 0.5 * (min(xs_end) + max(xs_end))
    y_cut = 0.5 * (min(ys_end) + max(ys_end))

    # Find axis
    angle_start = start_ports[0].angle
    if angle_start in [0, 180]:
        axis = "X"
        cut = y_cut
    else:
        axis = "Y"
        cut = x_cut

    # Get groups (below, above) or (left, right)
    group1, group2 = _groups(start_ports, cut, axis=axis)

    # Sort ports to make them easy to connect
    if axis == "X":
        group1.sort(key=lambda p: -p.y)
        group2.sort(key=lambda p: p.y)

        end_ports.sort(key=lambda p: p.y)
        end_group1 = end_ports[: len(group1)]
        end_group2 = end_ports[len(group1) :]
        end_group2.sort(key=lambda p: -p.y)

        xs_start = [p.x for p in start_ports]

        if angle_start == 0:
            dx = xs_start[0] - xs_end[0]
        elif angle_start == 180:
            dx = xs_end[0] - xs_start[0]
        end_straight = max(end_straight, dx)

    if axis == "Y":
        group1.sort(key=lambda p: -p.x)
        group2.sort(key=lambda p: p.x)

        end_ports.sort(key=lambda p: p.x)
        end_group1 = end_ports[: len(group1)]
        end_group2 = end_ports[len(group1) :]
        end_group2.sort(key=lambda p: -p.x)

        ys_start = [p.y for p in start_ports]

        if angle_start == 90:
            dy = ys_start[0] - ys_end[0]
        elif angle_start == 270:
            dy = ys_end[0] - ys_start[0]
        end_straight = max(end_straight, dy)

    # add offsets
    start_straight += start_straight_offset
    end_straight += end_straight_offset

    connections = []
    straight_len_end = end_straight
    straight_len_start = start_straight
    for p_start, p_end in zip(group1, end_group1):
        _c = routing_func(
            p_start,
            p_end,
            start_straight=straight_len_start,
            end_straight=straight_len_end,
            **routing_func_params
        )
        connections += [_c]
        straight_len_end += separation
        straight_len_start += separation

    straight_len_end = end_straight
    straight_len_start = start_straight
    for p_start, p_end in zip(group2, end_group2):
        _c = routing_func(
            p_start,
            p_end,
            start_straight=straight_len_start,
            end_straight=straight_len_end,
            **routing_func_params
        )
        connections += [_c]
        straight_len_end += separation
        straight_len_start += separation

    return connections


def u_bundle_indirect(
    start_ports,
    end_ports,
    route_filter=connect_strip_way_points,
    separation=5.0,
    extension_length=0.0,
    start_straight=0.01,
    end_straight=0.01,
    end_straight_offset=0.0,
    start_straight_offset=0.0,
    **routing_params
):
    """
    Args:
        start_ports: list of start ports
        end_ports: list of end ports
        route_filter: filter to apply to the manhattan waypoints
            e.g `connect_strip_way_points` for deep etch strip waveguide
    Returns:
        `[route_filter(r) for r in routes]` where routes is a list of lists of coordinates
        e.g with default `connect_strip_way_points`, returns a list of elements which can be added to a component


    Used for routing multiple ports back to a bundled input in a component


    ::

        X: start ports
        D: End ports


                                    X------
                                    X----  |
                                   ...   | |
                                    X--\ | |
                                       | | |
            /--------------------------/ | |
            |                            | |
            | /--------------------------/ |
            | |                            |
            | | /--------------------------/
            | | |
            | | \--D
            | \----D
            |     ...
            \------D
            /------D
            |     ...
            | /----D
            | | /--D
            | | |
            | | \--------------------------
            | |                            |
            | \--------------------------\ |
            |                            | |
            \--------------------------\ | |
                                       | | |
                                    X--/ | |
                                   ...   | |
                                    X----/ |
                                    X------/
        '''

    """

    routes = u_bundle_indirect_routes(
        start_ports,
        end_ports,
        separation=separation,
        start_straight=start_straight,
        end_straight=end_straight,
        start_straight_offset=start_straight_offset,
        end_straight_offset=end_straight_offset,
        routing_func=generate_manhattan_waypoints,
        extension_length=extension_length,
        **routing_params
    )

    return [route_filter(route, **routing_params) for route in routes]


def u_bundle_indirect_routes(
    start_ports,
    end_ports,
    routing_func=generate_manhattan_waypoints,
    separation=5.0,
    extension_length=0.0,
    start_straight=0.01,
    end_straight=0.01,
    end_straight_offset=0.0,
    start_straight_offset=0.0,
    **routing_func_params
):

    nb_ports = len(start_ports)

    for p in start_ports:
        p.angle = p.angle % 360

    for p in end_ports:
        p.angle = p.angle % 360

    if len(end_ports) != nb_ports:
        raise ValueError(
            "Number of start ports should match number of end ports.\
        Got {} {}".format(
                len(start_ports), len(end_ports)
            )
        )

    if len(set([p.angle for p in start_ports])) > 1:
        raise ValueError(
            "All start port angles should be the same.\
        Got {}".format(
                start_ports
            )
        )

    if len(set([p.angle for p in end_ports])) > 1:
        raise ValueError(
            "All end port angles should be the same.\
        Got {}".format(
                end_ports
            )
        )

    xs_end = [p.x for p in end_ports]
    ys_end = [p.y for p in end_ports]

    """
    # Compute the bundle axis
    """

    if start_ports[0].angle in [0, 180]:
        axis = "X"
    else:
        axis = "Y"

    """
     Split start ports in two groups:
        - the ones on the south/west of end ports (depending on bundle axis)
        - the ones on the north/east of end ports (depending on bundle axis)
    """

    if axis == "X":
        y_cut = 0.5 * (min(ys_end) + max(ys_end))
        group1 = [p for p in start_ports if p.y <= y_cut]
        group2 = [p for p in start_ports if p.y > y_cut]

        if start_ports[0].angle == 0 and end_ports[0].angle == 180:
            """
                    X->
               <-D
                    X->
            """
            # To go back to a U bundle
            group1_route_directives = ["north", "west"]
            group2_route_directives = ["south", "west"]

        elif start_ports[0].angle == 180 and end_ports[0].angle == 0:
            """
               <-X
                    D->
               <-X
            """
            # To go back to a U bundle
            group1_route_directives = ["north", "east"]
            group2_route_directives = ["south", "east"]

        else:
            print("u_undirect_bundle not designed to work in this case")

    if axis == "Y":
        x_cut = 0.5 * (min(xs_end) + max(xs_end))
        group1 = [p for p in start_ports if p.x <= x_cut]
        group2 = [p for p in start_ports if p.x > x_cut]

        if start_ports[0].angle == 90 and end_ports[0].angle == 270:
            """

              ^     ^
              |     |
              X     X
                 D
                 |

            """
            # To go back to a U bundle
            group1_route_directives = ["east", "south"]
            group2_route_directives = ["west", "south"]

        elif start_ports[0].angle == 270 and end_ports[0].angle == 90:
            """
                 ^
                 |
                 D
              X     X
              |     |

            """
            # To go back to a U bundle
            group1_route_directives = ["east", "north"]
            group2_route_directives = ["west", "north"]

        else:
            print("u_undirect_bundle not designed to work in this case")

    """
    Do the routing directives to get back to a u_bundle direct case
    """

    routing_param = {
        "routing_func": routing_func,
        "separation": separation,
        **routing_func_params,
    }

    # Multiple sections of different routes are generated in different places.
    # At the output, we want a list of routes. (not a list of portions of route)
    # dict_connections keeps track of these sections

    dict_connections = {i: [] for i in range(nb_ports)}

    def add_connections(conns):
        """
        Ensure that each section in a batch of connection
        is added to the correct route. Also we don't know in which order the
        routes are given (from beginning to end or vice versa)
        """

        end_prev_conns = [(k, v[-1][-1]) for k, v in dict_connections.items()]
        for c in conns:
            p = c[0]
            for i, q in end_prev_conns:
                if np.abs(p - q).sum() < 1e-9:
                    dict_connections[i] += [c]
                    break

    # First part
    print(group1_route_directives)
    conn1, tmp_ports1 = route_ports_to_side(
        group1,
        group1_route_directives[0],
        extension_length=extension_length,
        **routing_param
    )

    conn2, tmp_ports2 = route_ports_to_side(
        group2,
        group2_route_directives[0],
        extension_length=extension_length,
        **routing_param
    )
    conn = conn1 + conn2
    dict_connections = {i: [c] for i, c in enumerate(conn)}

    # Second part
    conn1, tmp_ports1 = route_ports_to_side(
        tmp_ports1, group1_route_directives[1], **routing_param
    )

    conn2, tmp_ports2 = route_ports_to_side(
        tmp_ports2, group2_route_directives[1], **routing_param
    )

    add_connections(conn1 + conn2)
    # conn2)

    bundle_params = {
        **routing_param,
        "start_straight": start_straight,
        "end_straight": end_straight,
        "start_straight_offset": start_straight_offset,
        "end_straight_offset": end_straight_offset,
    }

    end_ports.sort(key=lambda p: p.y)
    conn1 = u_bundle_direct_routes(
        tmp_ports1, end_ports[: len(tmp_ports1)], **bundle_params
    )
    conn2 = u_bundle_direct_routes(
        tmp_ports2, end_ports[len(tmp_ports1) :], **bundle_params
    )

    add_connections(conn1 + conn2)

    def _merge_connections(list_of_points):

        a = [list_of_points[0]]
        a = a + [point[1:] for point in list_of_points[1:]]
        b = np.vstack(a)
        b = remove_identicals(b)
        b = remove_flat_angles(b)
        return b

    connections = [_merge_connections(c) for c in dict_connections.values()]
    return connections
