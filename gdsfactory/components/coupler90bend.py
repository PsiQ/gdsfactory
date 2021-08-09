import gdsfactory as gf
from gdsfactory.component import Component
from gdsfactory.components.bend_euler import bend_euler
from gdsfactory.cross_section import strip
from gdsfactory.types import ComponentFactory, CrossSectionFactory


@gf.cell
def coupler90bend(
    radius: float = 10.0,
    gap: float = 0.2,
    bend: ComponentFactory = bend_euler,
    cross_section_inner: CrossSectionFactory = strip,
    cross_section_outer: CrossSectionFactory = strip,
) -> Component:
    r"""Returns 2 coupled bends.

    Args:
        radius: um
        gap: um
        bend: for bend
        cross_section_inner:
        cross_section_outer:


    .. code::

            r  N1 N0
            |   | |
            |  / /
            | / /
       W1____/ /
       W0_____/

    """

    c = Component()

    xi = cross_section_inner()
    xo = cross_section_outer()

    width = xo.info["width"] / 2 + xi.info["width"] / 2
    spacing = gap + width

    bend90_inner = bend(radius=radius, cross_section=cross_section_inner)
    bend90_outer = bend(radius=radius + spacing, cross_section=cross_section_outer)
    bend_inner_ref = c << bend90_inner
    bend_outer_ref = c << bend90_outer

    pbw = bend_inner_ref.ports["W0"]
    bend_inner_ref.movey(pbw.midpoint[1] + spacing)

    # This component is a leaf cell => using absorb
    c.absorb(bend_outer_ref)
    c.absorb(bend_inner_ref)

    c.add_port("N0", port=bend_outer_ref.ports["N0"])
    c.add_port("N1", port=bend_inner_ref.ports["N0"])
    c.add_port("W0", port=bend_outer_ref.ports["W0"])
    c.add_port("W1", port=bend_inner_ref.ports["W0"])

    return c


if __name__ == "__main__":
    c = coupler90bend(radius=3)
    c.show()