import gdspy

from phidl.device_layout import DeviceReference

import pp
from pp.component import Component
from pp.name import NAME_TO_DEVICE


def import_gds(
    filename: str,
    cellname: None = None,
    flatten: bool = False,
    overwrite_cache: bool = False,
    snap_to_grid_nm: bool = False,
) -> Component:
    """ returns a Componenent from a GDS file
    """
    filename = str(filename)
    gdsii_lib = gdspy.GdsLibrary()
    gdsii_lib.read_gds(filename)
    top_level_cells = gdsii_lib.top_level()

    if cellname is not None:
        if cellname not in gdsii_lib.cell_dict:
            raise ValueError(
                f"import_gds() The requested cell {cellname} is not present in file {filename}"
            )
        topcell = gdsii_lib.cell_dict[cellname]
    elif cellname is None and len(top_level_cells) == 1:
        topcell = top_level_cells[0]
    elif cellname is None and len(top_level_cells) > 1:
        raise ValueError(
            "import_gds() There are multiple top-level cells in {}, you must specify `cellname` to select of one of them among {}".format(
                filename, [_c.name for _c in top_level_cells]
            )
        )

    if flatten:
        D = pp.Component()
        polygons = topcell.get_polygons(by_spec=True)

        for layer_in_gds, polys in polygons.items():
            D.add_polygon(polys, layer=layer_in_gds)
        return D

    else:
        D_list = []
        c2dmap = {}
        all_cells = topcell.get_dependencies(True)
        all_cells.update([topcell])

        for cell in all_cells:
            cell_name = cell.name
            if overwrite_cache or cell_name not in NAME_TO_DEVICE:
                D = pp.Component()
                D.name = cell.name
                D.polygons = cell.polygons
                D.references = cell.references
                D.name = cell_name
                D.labels = cell.labels
            else:
                D = NAME_TO_DEVICE[cell_name]

            c2dmap.update({cell_name: D})
            D_list += [D]

        for D in D_list:
            # First convert each reference so it points to the right Device
            converted_references = []
            for e in D.references:
                try:
                    ref_device = c2dmap[e.ref_cell.name]

                    dr = DeviceReference(
                        device=ref_device,
                        origin=e.origin,
                        rotation=e.rotation,
                        magnification=e.magnification,
                        x_reflection=e.x_reflection,
                    )
                    converted_references.append(dr)
                except Exception:
                    print("WARNING - Could not import", e.ref_cell.name)

            D.references = converted_references
            # Next convert each Polygon
            temp_polygons = list(D.polygons)
            D.polygons = []
            for p in temp_polygons:
                if snap_to_grid_nm:
                    points_on_grid = pp.drc.snap_to_grid(
                        p.polygons[0], nm=snap_to_grid_nm
                    )
                    p = gdspy.Polygon(
                        points_on_grid, layer=p.layers[0], datatype=p.datatypes[0]
                    )
                D.add_polygon(p)
                # else:
                #     warnings.warn('[PHIDL] import_gds(). Warning an element which was not a ' \
                #         'polygon or reference exists in the GDS, and was not able to be imported. ' \
                #         'The element was a: "%s"' % e)

        topdevice = c2dmap[topcell.name]
        return topdevice


def test_import_gds_flat():
    gdspath = pp.CONFIG["gdslib"] / "gds" / "mzi2x2.gds"
    c = import_gds(gdspath, snap_to_grid_nm=5)
    assert len(c.get_polygons()) == 54

    for x, y in c.get_polygons()[0]:
        assert pp.drc.on_grid(x, 5)
        assert pp.drc.on_grid(y, 5)


def test_import_gds_hierarchy():
    c0 = pp.c.mzi2x2()
    gdspath = pp.write_gds(c0)
    c = import_gds(gdspath)
    assert len(c.get_dependencies()) == 3


if __name__ == "__main__":

    filename = pp.CONFIG["gdslib"] / "gds" / "mzi2x2.gds"
    c = import_gds(filename, snap_to_grid_nm=5)
    print(c)
    pp.show(c)
