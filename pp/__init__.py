""" pp Photonics package

functions:

    - pp.show(): writes and shows the GDS in Klayout using klive
    - pp.plotgds(): plots GDS in matplotlib
    - pp.import_gds(): returns a Component from a GDS

classes:

    - pp.Component
    - pp.Port
    - CONFIG

modules:

    - c: components
    - routing
    - layer: GDS layers
"""
from phidl import quickplot as qp
import phidl.geometry as pg

# NOTE: import order matters. Only change the order if you know what you are doing
from pp.config import CONFIG, call_if_func, conf
from pp.component import Component, ComponentReference
from pp.port import Port
from pp.name import autoname
from pp.layers import LAYER
from pp.load_component import load_component
from pp.load_csv import load_csv

from pp.write_component import get_component_type
from pp.write_component import show
from pp.write_component import write_gds
from pp.write_component import write_component_type
from pp.write_component import write_component
from pp.write_doe import write_doe

import pp.components as c
import pp.routing as routing
import pp.bias as bias
import pp.klive as klive
import pp.sp as sp
import pp.port as port
import pp.units as units

from pp.component_from_yaml import component_from_yaml

from pp.components import component_factory
from pp.components.extension import extend_port
from pp.components.extension import extend_ports
from pp.add_padding import add_padding
from pp.add_pins import add_pins
from pp.import_gds import import_gds
from pp.import_phidl_component import import_phidl_component
from pp.plotgds import plotgds
from pp.pack import pack
from pp.boolean import boolean


__all__ = [
    "CONFIG",
    "LAYER",
    "Component",
    "ComponentReference",
    "bias",
    "autoname",
    "add_padding",
    "add_pins",
    "import_gds",
    "import_phidl_component",
    "c",
    "conf",
    "component_factory",
    "call_if_func",
    "extend_port",
    "extend_ports",
    "boolean",
    "get_component_type",
    "klive",
    "load_component",
    "load_csv",
    "plotgds",
    "pack",
    "qp",
    "pg",
    "port",
    "routing",
    "show",
    "sp",
    "write_component",
    "write_component_type",
    "write_doe",
    "write_gds",
    "Port",
    "component_from_yaml",
    "units",
]
__version__ = "1.4.2"


if __name__ == "__main__":
    print(__all__)
