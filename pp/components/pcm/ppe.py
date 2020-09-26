""" based on https://github.com/niladri18/Phidl/blob/master/src/ppe.py
"""

import math
import pp
from omegaconf.listconfig import ListConfig
from pp.component import Component
from typing import List, Union


@pp.autoname
def line(
    x0: Union[float, int],
    y0: Union[float, int],
    width: Union[float, int],
    height: int,
    layer: ListConfig,
) -> Component:
    L = pp.Component()
    L.add_polygon(
        [(x0, y0), (x0 + width, y0), (x0 + width, y0 + height), (x0, y0 + height)],
        layer=layer,
    )
    return L


@pp.autoname
def linespace(
    x0: Union[float, int],
    y0: Union[float, int],
    width: Union[float, int],
    height: int,
    pitch: int,
    ymax: Union[float, int],
    layer: ListConfig,
) -> Component:
    """ # Creates a line space pattern in y-direction
    Args:
        x0: x coordinate of the lower left line
        y0: y coordinate of the lower left line
        width: width of each line
        height: height of each line
        pitch: pitch of each line
        pitch > height
    """
    if abs(pitch) < abs(height):
        print("pitch must be greater then height")
        return
    LS = pp.Component()
    if pitch > 0:
        while y0 + height <= ymax:
            Li = line(x0=x0, y0=y0, width=width, height=height, layer=layer)
            LS.add_ref(Li)
            y0 += pitch
    elif pitch < 0:
        while y0 + height >= -ymax:
            Li = line(x0=x0, y0=y0, width=width, heigh=height, layer=layer)
            LS.add_ref(Li)
            y0 += pitch
    return LS


def y0linespace(y0: float, height: int, pitch: int, ymax: float) -> float:
    if pitch > 0:
        while y0 + height <= ymax:
            y0 += pitch
    elif pitch < 0:
        while y0 + height >= -ymax:
            y0 += pitch
    return y0


@pp.autoname
def cross(x0: float, y0: float, width: int, lw: int, layer: ListConfig) -> Component:
    """ cross

    Args:
        x0,y0 : center
        width: width of the bounding box
        lw: linewidth
    """
    cross = pp.Component()
    cross.add_polygon(
        [
            (x0 - width / 2, y0 - lw / 2),
            (x0 - width / 2, y0 + lw / 2),
            (x0 + width / 2, y0 + lw / 2),
            (x0 + width / 2, y0 - lw / 2),
        ],
        layer=layer,
    )
    cross.add_polygon(
        [
            (x0 - lw / 2, y0 - width / 2),
            (x0 - lw / 2, y0 + width / 2),
            (x0 + lw / 2, y0 + width / 2),
            (x0 + lw / 2, y0 - width / 2),
        ],
        layer=layer,
    )
    return cross


@pp.autoname
def ppe(
    layer: ListConfig = pp.LAYER.WG,
    layers_cladding: List[ListConfig] = [pp.LAYER.WGCLAD],
    cladding_offset: int = 3,
) -> Component:
    """
    pattern placement error
    """
    D = pp.Component()

    # Define global variables
    xmax = 500
    ymax = 500
    xmin = 0
    ymin = 0
    xm = (xmax - xmin) / 2.0
    ym = (ymax - ymin) / 2.0
    o = cladding_offset

    # Cover the entire macro
    for layer_cladding in layers_cladding:
        D.add_polygon(
            [(0, -o), (xmax + o, -o), (xmax + o, ymax + o), (0, ymax + o)],
            layer=layer_cladding,
        )

    # Place the pattern rec
    Cross = cross(x0=xm, y0=ym, width=100, lw=10, layer=layer)
    Cross.rotate(45, center=[xm, ym])
    D.add_ref(Cross)

    # calculate offset due to the cross
    xoff = math.sqrt(100 * 50)
    yoff = math.sqrt(100 * 50)

    # Top left 1
    x0 = 10
    y0 = ym
    pitch = 20
    LS1 = linespace(
        x0=x0,
        y0=y0,
        width=240 - xoff,
        height=10,
        pitch=pitch,
        ymax=ym + yoff,
        layer=layer,
    )
    y0 = y0linespace(y0=y0, height=10, pitch=pitch, ymax=ym + yoff)
    D.add_ref(LS1)

    # Top left 2
    x0 = 10
    y0 = y0
    LS1 = linespace(x0=x0, y0=y0, width=240, height=10, pitch=20, ymax=500, layer=layer)
    D.add_ref(LS1)

    # Top right 1
    x0 = xm + xoff
    y0 = ym
    pitch = 30
    LS2 = linespace(
        x0=x0,
        y0=y0,
        width=240 - xoff + 10,
        height=10,
        pitch=pitch,
        ymax=ym + yoff,
        layer=layer,
    )
    y0 = y0linespace(y0=y0, height=10, pitch=pitch, ymax=ym + yoff)
    D.add_ref(LS2)

    # Top right 2
    x0 = xm + 10
    LS2 = linespace(x0=x0, y0=y0, width=240, height=10, pitch=30, ymax=500, layer=layer)
    D.add_ref(LS2)

    # Lower left 1
    x0 = 10
    y0 = 0
    pitch = 30
    LS3 = linespace(
        x0=x0, y0=y0, width=240, height=10, pitch=30, ymax=xm - yoff, layer=layer
    )
    D.add_ref(LS3)

    # Lower left 2
    x0 = 10
    y0 += pitch
    LS3 = linespace(
        x0=x0, y0=y0, width=240 - xoff, height=10, pitch=30, ymax=240, layer=layer
    )
    D.add_ref(LS3)

    # Lower right 1
    x0 = xm + 10
    y0 = 0
    pitch = 20
    LS4 = linespace(
        x0=x0, y0=y0, width=240, height=10, pitch=20, ymax=xm - yoff, layer=layer
    )
    D.add_ref(LS4)

    # Lower right 2
    x0 = xm + xoff
    y0 += pitch
    LS4 = linespace(
        x0=x0, y0=y0, width=240 - xoff + 10, height=10, pitch=20, ymax=240, layer=layer
    )
    D.add_ref(LS4)

    # Add NOOPC cover on the pattern rec
    xt = xoff - 10
    yt = yoff - 10

    for layer_cladding in layers_cladding:
        D.add_polygon(
            [
                (xm - xt, ym - yt),
                (xm - xt, ym + yt),
                (xm + xt, ym + yt),
                (xm + xt, ym - yt),
            ],
            layer=layer_cladding,
        )
    return D


if __name__ == "__main__":
    c = ppe()
    pp.show(c)
