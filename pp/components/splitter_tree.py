from typing import Callable
import pp

from pp.components.mmi1x2 import mmi1x2
from pp.components.waveguide import waveguide
from pp.routing.connect import connect_strip
from pp.port import get_ports_facing


@pp.autoname
def splitter_tree(
    coupler: Callable = mmi1x2,
    n_o_outputs: int = 4,
    bend_radius: float = 10.0,
    spacing: float = 50.0,
    termination_component=None,
):
    """tree of 1x2 splitters

    Args:
        coupler: 1x2 coupler factory
        n_o_outputs:
        bend_radius: for routing
        spacing: 2X spacing
        termination_component: factory or component for EAST termination

    .. code::

             __|
          __|  |__
        _|  |__
         |__       spacing


    .. plot::
      :include-source:

      import pp

      c = pp.c.splitter_tree(coupler=pp.c.mmi1x2(), n_o_outputs=4, spacing=50, bend_radius=10)
      pp.plotgds(c)

    """
    n_o_outputs = n_o_outputs
    c = pp.Component()

    coupler = pp.call_if_func(coupler)
    _coupler = c.add_ref(coupler)
    coupler_sep = coupler.ports["E1"].y - coupler.ports["E0"].y

    if n_o_outputs > 2:
        _cmp = splitter_tree(
            coupler=coupler,
            n_o_outputs=n_o_outputs // 2,
            bend_radius=bend_radius,
            spacing=spacing / 2,
        )
    else:
        termination_component = (
            termination_component
            if termination_component is not None
            else waveguide(length=0.1)
        )
        _cmp = pp.call_if_func(termination_component)

    spacing = (
        spacing
        if spacing is not None
        else _cmp.ports["W0"].y - _coupler.size_info.south
    )
    if spacing < coupler_sep:
        tree_top = _cmp.ref(port_id="W0", position=_coupler.ports["E1"])
        tree_bot = _cmp.ref(
            port_id="W0", position=_coupler.ports["E0"], v_mirror=False  # True
        )

    else:
        d = 2 * bend_radius + 1
        spacing = max(spacing, d)

        tree_top = _cmp.ref(
            port_id="W0", position=_coupler.ports["E1"].position + (d, spacing)
        )
        tree_bot = _cmp.ref(
            port_id="W0",
            position=_coupler.ports["E0"].position + (d, -spacing),
            v_mirror=False,  # True,
        )

        c.add(connect_strip(coupler.ports["E1"], tree_top.ports["W0"]))
        c.add(connect_strip(coupler.ports["E0"], tree_bot.ports["W0"]))

    i = 0
    for p in get_ports_facing(tree_bot, "E"):
        c.add_port(name="{}".format(i), port=p)
        i += 1

    for p in get_ports_facing(tree_top, "E"):
        c.add_port(name="{}".format(i), port=p)
        i += 1

    c.add(tree_bot)
    c.add(tree_top)
    c.add_port(name="W0", port=_coupler.ports["W0"])

    return c


if __name__ == "__main__":
    c = splitter_tree(coupler=pp.c.mmi1x2())
    pp.show(c)
