# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import numpy as np


# Support class associating a 2d vertex to the value that will be interpolated
class ValuedVertex:
    def __init__(self, x: int, y: int, val):
        self.x: int = x
        self.y: int = y
        self.val: int = val


def _drawHorizontalLine(dest_raster: np.ndarray, x1: int, x2: int, y: int, val1, val2) -> None:
    # 1-pixel only
    if x1 == x2:
        # assert (val1==val2).all()
        dest_raster[y, x1] = val1  # (val1 + val2) / 2
        return

    # We draw only from left to right
    if x1 > x2:
        x1, x2 = x2, x1
        val1, val2 = val2, val1

    # Fill the raster by interpolating val1 to val2 from left to right (x1 to x2 inclusive)
    dx = x2 - x1
    dval = val2 - val1
    for x in range(x1, x2 + 1):
        k = (x - x1) / dx
        assert 0.0 <= k <= 1.0
        v = val1 + dval * k
        dest_raster[y, x] = v


def _fillBottomFlatTriangle(dest_raster: np.ndarray, v1: ValuedVertex, v2: ValuedVertex, v3: ValuedVertex) -> None:
    # The flat bottom is between v2 and v3
    assert v2.y == v3.y
    # v1 is at the top
    assert v1.y <= v2.y
    assert v1.y <= v3.y

    invslope1: float = (v2.x - v1.x) / (v2.y - v1.y)
    invslope2: float = (v3.x - v1.x) / (v3.y - v1.y)

    curx1: float = v1.x  # between v1 and v2
    curx2: float = v1.x  # between v1 and v3

    dy = v2.y - v1.y
    assert dy > 0

    for scanlineY in range(v1.y, v2.y + 1):
        assert type(scanlineY) == int

        # Compute pixel values
        ky = (scanlineY - v1.y) / dy
        assert 0.0 <= ky <= 1.0
        val1 = v1.val + (v2.val - v1.val) * ky  # between v1 and v2
        val2 = v1.val + (v3.val - v1.val) * ky  # between v1 and v3

        _drawHorizontalLine(dest_raster=dest_raster, x1=int(curx1), x2=int(curx2), y=scanlineY, val1=val1, val2=val2)
        curx1 += invslope1
        curx2 += invslope2


def _fillTopFlatTriangle(dest_raster: np.ndarray, v1: ValuedVertex, v2: ValuedVertex, v3: ValuedVertex) -> None:
    # The flat top is between v1 and v2
    assert v1.y == v2.y
    # v3 is at the bottom
    assert v1.y <= v3.y
    assert v2.y <= v3.y

    invslope1: float = (v3.x - v1.x) / (v3.y - v1.y)
    invslope2: float = (v3.x - v2.x) / (v3.y - v2.y)

    curx1: float = v3.x  # between v1 and v3 (backwards)
    curx2: float = v3.x  # between v2 and v3 (backwards)

    dy = v3.y - v1.y
    assert dy > 0

    for scanlineY in range(v3.y, v1.y - 1, -1):
        assert type(scanlineY) == int

        # Compute pixel values
        ky = (scanlineY - v1.y) / dy
        assert 0.0 <= ky <= 1.0
        val1 = v1.val + (v3.val - v1.val) * ky  # between v1 and v3
        val2 = v2.val + (v3.val - v2.val) * ky  # between v2 and v3

        _drawHorizontalLine(dest_raster=dest_raster, x1=int(curx1), x2=int(curx2), y=scanlineY, val1=val1, val2=val2)
        curx1 -= invslope1
        curx2 -= invslope2


def _drawTriangle(dest_raster: np.ndarray, v1: ValuedVertex, v2: ValuedVertex, v3: ValuedVertex) -> None:
    # Sort vertices by increasing y coordinate
    sorted_vertices = sorted((v1, v2, v3), key=lambda v: v.y)
    v1, v2, v3 = sorted_vertices
    # print(f"Sorted: {v1}   {v2}   {v3}")

    assert v1.y <= v2.y <= v3.y

    # case of bottom-flat triangle
    if v2.y == v3.y:
        _fillBottomFlatTriangle(dest_raster, v1, v2, v3)

    # case of top-flat triangle
    elif v1.y == v2.y:
        _fillTopFlatTriangle(dest_raster, v1, v2, v3)

    # general case: split the triangle in a top-flat and bottom-flat
    else:
        assert v1.y < v2.y < v3.y
        dx3 = v3.x - v1.x
        dy2 = v2.y - v1.y
        dy3 = v3.y - v1.y
        # print("{dx3} {dy2} {dy3}")
        dval3 = v3.val - v1.val
        k4 = (v2.y - v1.y) / (dy3 + 1)
        assert 0.0 <= k4 <= 1.0
        v4_val = v1.val + dval3 * k4
        v4 = ValuedVertex(
            x=int(v1.x + (dy2 / dy3) * dx3),
            y=v2.y,
            val=v4_val
        )
        _fillBottomFlatTriangle(dest_raster, v1, v2, v4)
        _fillTopFlatTriangle(dest_raster, v2, v4, v3)


def fillTriangles(polygons: list, values_map: np.ndarray) -> np.ndarray:
    """
    Given a list of triangles (polygons with 3 vertices and with integer coordinates)
    and a map (np.ndarray) containing the values to be associated to the vertices
    creates a new raster np.ndarray of the same dimension, where each triangle is filled by interpolating the values.

    :param polygons: The polygons, where each polygon is assumed to have 3 vertices and integer coordinates.
    :param values_map: The maps containing the source values of the vertices that we want to interpolate
    :return: A new array, with the same dimension of the values, where the pixels inside the triangles are interpolated
     according to the values at the vertices.
    """

    out = np.zeros_like(values_map)

    for poly in polygons:
        assert len(poly.vertices) == 3

        # print(f"Fill triangle {poly}")
        # for v in poly.vertices:
        #    print(f"{v} {v.x} {type(v.x)}")
        val_vertices = [ValuedVertex(x=v.x, y=v.y, val=values_map[v.y, v.x]) for v in poly.vertices]
        _drawTriangle(dest_raster=out, v1=val_vertices[0], v2=val_vertices[1], v3=val_vertices[2])

    return out
