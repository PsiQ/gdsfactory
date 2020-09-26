"""
Ports define where each port has:

- name
- midpoint: (x, y)
- width:
- orientation: (deg) 0, 90, 180, 270. where 0 faces east, 90 (north), 180 (west), 270 (south)
- Type:
    - optical
    - electrical (DC)
    - rf (high frequency)
    - detector (Superconducting)
"""


import pp


@pp.autoname
def test_component_with_port(length=5, wg_width=0.5):
    """
    component with one port on the west side
    """

    y = wg_width
    x = length

    c = pp.Component()
    c.add_polygon([(0, 0), (x, 0), (x, y), (0, y)], layer=1)
    c.add_port(
        name="W0",
        midpoint=(0, y / 2),
        width=y,
        orientation=180,
        layer=1,
        port_type="optical",
    )
    assert len(c.ports) == 1
    return c


if __name__ == "__main__":
    c = test_component_with_port()
    pp.show(c)
