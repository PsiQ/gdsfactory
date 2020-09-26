"""
Lets create a new component.

We create a function which returns a pp.Component instance.

Lets build waveguide crossing out of a vertical and horizonal arm


- Create a component instance that we will return from a component_factory function. We will use a autoname decorator to define the name
- Define a polygon
- Create ports
"""

from phidl import quickplot as qp
import pp
from pp import LAYER


@pp.autoname
def test_crossing_arm(wg_width=0.5, r1=3.0, r2=1.1, taper_width=1.2, taper_length=3.4):
    """ crossing arm
    """
    c = pp.Component()
    c << pp.c.ellipse(radii=(r1, r2), layer=LAYER.SLAB150)

    xmax = taper_length + taper_width / 2
    h = wg_width / 2
    taper_points = [
        (-xmax, h),
        (-taper_width / 2, taper_width / 2),
        (taper_width / 2, taper_width / 2),
        (xmax, h),
        (xmax, -h),
        (taper_width / 2, -taper_width / 2),
        (-taper_width / 2, -taper_width / 2),
        (-xmax, -h),
    ]

    c.add_polygon(taper_points, layer=LAYER.WG)

    c.add_port(
        name="W0", midpoint=(-xmax, 0), orientation=180, width=wg_width, layer=LAYER.WG
    )

    c.add_port(
        name="E0", midpoint=(xmax, 0), orientation=0, width=wg_width, layer=LAYER.WG
    )
    return c


if __name__ == "__main__":
    c = test_crossing_arm()
    pp.show(c)
    qp(c)
