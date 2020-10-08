from pp.container import container
from pp.component import Component
from pp.routing.route_pad_array import route_pad_array
from pp.rotate import rotate


@container
def add_electrical_pads(component: Component, rotation=180, **kwargs):
    """add compnent with top electrical pads and routes
    Args:
        component: Component,
        pad_spacing: float = 150.,
        pad: Callable = pad,
        fanout_length: Optional[int] = None,
        max_y0_optical: None = None,
        waveguide_separation: float = 4.0,
        bend_radius: float = 0.1,
        connected_port_list_ids: None = None,
        n_ports: int = 1,
        excluded_ports: List[Any] = [],
        pad_indices: None = None,
        route_filter: Callable = connect_elec_waypoints,
        port_name: str = "W",
        pad_rotation: int = -90,
        x_pad_offset: int = 0,
        port_labels: None = None,
        select_ports: Callable = select_electrical_ports,

    """

    c = Component(f"{component.name}_pad")

    cr = component.rotate(rotation)

    elements, pads, _ = route_pad_array(component=cr, **kwargs,)

    c << cr
    for e in elements:
        c.add(e)
    for e in pads:
        c.add(e)

    for pname, p in cr.ports.items():
        if p.port_type == "optical":
            c.add_port(pname, port=p)

    return rotate(c, -rotation)


if __name__ == "__main__":
    import pp

    c = pp.c.cross(length=100, layer=pp.LAYER.M3, port_type="dc")
    c = pp.c.mzi2x2(with_elec_connections=True)
    c = pp.c.waveguide_heater()
    c.move((20, 50))
    cc = add_electrical_pads(c, fanout_length=100)
    print(cc.ports)

    ccc = pp.routing.add_fiber_array(cc)
    pp.show(ccc)
