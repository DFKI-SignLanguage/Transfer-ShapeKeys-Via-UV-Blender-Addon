import bpy
from mathutils import Vector

import numpy as np

from sktransfer.triangle_filling import fillTriangles
from sktransfer.delaunay.quadedge.mesh import Mesh
from sktransfer.delaunay.quadedge.point import Vertex
from sktransfer.delaunay.delaunay import delaunay


from typing import Tuple


def export_shapekey_info(mesh: bpy.types.Mesh, shape_key_idx: int, uv_layer_idx: int, resolution: Tuple[int, int] = (256, 256)) -> np.ndarray:
    """
    Given a mesh, a ShapeKey index and a UV layer, uses the UV vertex coordinates to produce a 3D map storing the offset of each vertex with respect to the base ShapeKey.
    The function returns a "ShapeKey Info" 4D array storing the ShapeKey offset and a counter info.
    sk_info.shape == (resolution[0], resolution[1], 4)
    For each element of the output x/y coordinate has 4 elements. The first three are the offset of the vertex
    xyz_map = sk_info[:, :, :3]
    The last element is a counter of how many times the same cell has been written.
    counts_map = sk_info[:, :, 3]
    The routine works by iterating the polygons and, for each polygon, retrieves the shape_key offset and stores it according to the UV coordinate.
    In so doing, the same map "pixel" can be written multiple times. The counts_map stores how many times the same location was written.
    The stored xyz result is the mean of all written values.
    """

    shape_key: bpy.types.ShapeKey = mesh.shape_keys.key_blocks[shape_key_idx]
    uv_layer: bpy.types.MeshUVLoopLayer = mesh.uv_layers[uv_layer_idx]
    
    out_w, out_h = resolution[0], resolution[1]

    # Preparing the output matrix
    out = np.zeros(shape=(out_h, out_w, 4))

    reference_shape_key: bpy.types.ShapeKey = mesh.shape_keys.reference_key

    #
    # Iterate over the polygons of the uv layer
    for poly in mesh.polygons:
        assert type(poly) == bpy.types.MeshPolygon
        
        assert len(poly.vertices) == len(poly.loop_indices)

        # For each vertex of the polygon
        for v_idx, loop_idx in zip(poly.vertices, poly.loop_indices):
            # print(v_idx)
            assert type(v_idx) == int
            assert type(loop_idx) == int
            
            # Get the UV coords
            # U increases on width (left to right), and V increases on height (bottom to top!)
            uv_coords = uv_layer.uv[loop_idx].vector
            # print(uv_coords)

            assert 0.0 <= uv_coords.x <= 1.0
            assert 0.0 <= uv_coords.y <= 1.0
            
            # Approximate to int pixel coord
            out_x = round(uv_coords.x * (out_w - 1))
            out_y = round(uv_coords.y * (out_h - 1))
            # print(uv_pixel_coords)
            assert 0 <= out_x <= out_w - 1
            assert 0 <= out_y <= out_h - 1

            # Get the blendshape offset value
            sk_vertex_coords = shape_key.data[v_idx].co
            # sk_base_vertex_coords = shape_key.relative_key.data[v_idx].co
            sk_base_vertex_coords = reference_shape_key.data[v_idx].co
            delta = sk_vertex_coords - sk_base_vertex_coords
            # print(sk_vertex_coords, sk_base_vertex_coords, delta)

            # Accumulate the delta into the output picture
            if out[out_y, out_x, 3] == 0.0:
                out[out_y, out_x, :] = delta.x, delta.y, delta.z, 1
            else:
                current_mean = Vector(out[out_y, out_x, :3])
                count = out[out_y, out_x, 3]
                new_mean = ((current_mean * count) + delta) / (count + 1)

                out[out_y, out_x, :] = new_mean.x, new_mean.y, new_mean.z, count + 1

    return out


def create_shapekey(obj: bpy.types.Object, uv_layer_idx: int, xyz_map: np.ndarray, src_sk: str) -> None:

    if obj.type != 'MESH':
        raise Exception("obj must be of type MESH")

    mesh = obj.data
    assert type(mesh) == bpy.types.Mesh
    
    map_h, map_w, map_d = xyz_map.shape
    if map_d != 3:
        raise Exception(f"Invalid ShapeKey info map. Expected depth 3. Found {map_d}")

    #
    # If there were no ShapeKeys already, create the first
    if mesh.shape_keys is None:
        basis_sk = obj.shape_key_add(name='Basis')
        basis_sk.interpolation = 'KEY_LINEAR'

    assert mesh.shape_keys is not None

    # Create the destination ShapeKey
    new_sk: bpy.types.ShapeKey = obj.shape_key_add(name=src_sk.name)
    new_sk.slider_min = src_sk.slider_min
    new_sk.slider_max = src_sk.slider_max
    key_blocks = mesh.shape_keys.key_blocks
    assert new_sk.name in key_blocks
    
    # Retrieve the target UV
    uv_layer: bpy.types.MeshUVLoopLayer = mesh.uv_layers[uv_layer_idx]
    reference_shape_key: bpy.types.ShapeKey = mesh.shape_keys.reference_key

    # For each polygon
    for poly in mesh.polygons:
        # For each vertex and loop index
        for v_idx, loop_idx in zip(poly.vertices, poly.loop_indices):
            # get the UV coordinates
            uv_coords = uv_layer.uv[loop_idx].vector
            # convert the coordinates in pixel space
            uv_x = round(uv_coords.x * (map_w - 1))
            uv_y = round(uv_coords.y * (map_h - 1))
            
            # Take the delta from the map
            delta = Vector(xyz_map[uv_y, uv_x])
            # print(f"For poly {poly.index} coords {uv_x},{uv_y} --> delta {delta}")

            # Adds the delta to the vertex position in the reference ShapeKey
            reference_coords: Vector = reference_shape_key.data[v_idx].co
            absolute_coords = reference_coords + delta

            # Store the new coordinate in the ShapeKey
            new_sk.data[v_idx].co = absolute_coords


def _save_buffer_as_image(buffer: np.ndarray, save_name: str) -> None:
    """
    Support function to save a numpy array as image, for visual debugging.
    Requires the PIL module!!!

    :param buffer: The numpy array to save. Supports 2D arrays (Grey images) or 3D arrays with depth==3 (RGB images).
    Values are arbitrary and will be normalized in range 0-255 according to min and max values in the array.
    :param save_name: The name used for saving the file.
    :return: None
    """

    import PIL.Image

    # For 3D arrays, we try to create an RGB image.
    # For 2D arrays we go for a greyscale image.
    color_scheme = None
    if len(buffer.shape) == 3:
        _, _, depth = buffer.shape
        if depth == 3:
            color_scheme = 'RGB'
    elif len(buffer.shape) == 2:
        color_scheme = 'L'

    if color_scheme is None:
        raise Exception(f"Unsupported color buffer shape {buffer.shape}")

    # Normalize the buffer range in [0.0-255.0]
    buffer_255 = 255.0 * (buffer - buffer.min()) / (buffer.max() - buffer.min())
    # And convert it into unsigned bytes for PIL
    buffer_255 = buffer_255.astype(np.uint8)
    # Creates the PIL.Image.Image
    counts_img = PIL.Image.fromarray(buffer_255, color_scheme)
    print(f"Saving '{save_name}'...")
    counts_img.save(save_name)


def transfer_shapekey_via_uv(src_obj: bpy.types.Object, src_sk_idx: int, src_uv_idx: int,
                             dst_obj: bpy.types.Object, dst_uv_idx: int,
                             resolution: Tuple[int, int],
                             save_debug_images: bool = False) -> None:
    """
    The main function that: i) retrieves the ShapeKey deltas from the source mesh,
     ii) triangulates the delta points and fills the gaps between the points, and
     iii) creates the ShapeKey on the destination object.

    :param src_obj:
    :param src_sk_idx:
    :param src_uv_idx:
    :param dst_obj:
    :param dst_uv_idx:
    :param resolution:
    :param save_debug_images: If True, the intermediate buffers (counts, deltas and triangulates deltas)
     will be saved as PNG images for visual debugging.
    :return:
    """

    map_width, map_height = resolution

    src_mesh: bpy.types.Mesh = src_obj.data
    src_active_sk: bpy.types.ShapeKey = src_mesh.shape_keys.key_blocks[src_sk_idx]

    #
    # Extract ShapeKey info
    sk_info = export_shapekey_info(mesh=src_mesh, shape_key_idx=src_sk_idx, uv_layer_idx=src_uv_idx,
                                   resolution=resolution)

    # Convert counts ShapeKey Info into a grey image and save
    print(f"sk_info_map shape:{sk_info.shape}")
    counts_map = sk_info[:, :, 3]
    print(f"Counts map shape: {counts_map.shape}, min/max={counts_map.min()}/{counts_map.max()}")
    unique_values, unique_counts = np.unique(counts_map, return_counts=True)
    print("Counts stats:")
    for v, c in zip(unique_values, unique_counts):
        print(f"{v}\t{c}")

    if save_debug_images:
        _save_buffer_as_image(buffer=counts_map,
                              save_name=f"{src_obj.name}-sk{src_sk_idx}-uv{src_uv_idx}-{map_width}x{map_height}-counts.png")

    # Convert XYZ ShapeKey Info into an RGB image and save
    xyz_map = sk_info[:, :, :3]

    if save_debug_images:
        _save_buffer_as_image(buffer=xyz_map,
                              save_name=f"{src_obj.name}-sk{src_sk_idx}-uv{src_uv_idx}-{map_width}x{map_height}-deltas.png")

    #
    # Triangulate and Fill the ShapeKey deltas
    vertices = []
    for y in range(map_height):
        for x in range(map_width):
            c = counts_map[y, x]
            if c != 0.0:
                vertices.append(Vertex(x, y))

    n_vertices = len(vertices)
    print(f"Found {n_vertices} vertices.")

    print("Triangulating...")
    m = Mesh()  # this object holds the edges and vertices
    m.loadVertices(vertices)
    res = delaunay(m, 0, n_vertices - 1)
    print(f"Delaunay result:", f"{res}")

    polygons = m.listPolygons()
    print(f"Num Polygons {len(polygons)}")
    # Filter out polygons with more or less than 3 vertices
    polygons = [p for p in polygons if len(p.vertices) == 3]
    print(f"Polygons with 3 vertices: {len(polygons)}")

    # Fill all the triangles
    filled_xyz_map = fillTriangles(polygons=polygons, values_map=xyz_map)
    print(f"Filled xyz_map shape {filled_xyz_map.shape}")

    if save_debug_images:
        # Save the resulting map
        _save_buffer_as_image(buffer=filled_xyz_map,
                              save_name=f"{src_obj.name}-sk{src_sk_idx}-uv{src_uv_idx}-{map_width}x{map_height}-filled.png")

    #
    # Rebuild the ShapeKey on the destination object
    print(f"Creating ShapeKey '{src_active_sk.name}' on object '{dst_obj.name}' using UV layer {dst_uv_idx} ...")
    create_shapekey(obj=dst_obj, uv_layer_idx=dst_uv_idx, xyz_map=filled_xyz_map, src_sk=src_active_sk)
