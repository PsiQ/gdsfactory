import pp


def test_netlist_with_routes():
    """Needs FIX
    routes are not connected using connect,
    Using a hack we add the route to the netlist inside function round_corners
    from pp.routing.manhattan
    ideally we would extract the exact route composition (bends, tapers and waveguides)
    """
    c = pp.Component()
    w = c << pp.c.waveguide(length=3)
    b = c << pp.c.bend_circular()
    w.xmax = 0
    b.xmin = 10

    routes = pp.routing.connect_bundle(w.ports["E0"], b.ports["W0"])
    c.add(routes)

    # print(routes[0].get_settings())
    # print(c.get_netlist().connections)
    print(c.get_netlist().instances)

    assert len(c.get_dependencies()) == 3
    assert len(c.get_netlist().connections) == 2
    return c


if __name__ == "__main__":
    c = test_netlist_with_routes()
    pp.show(c)