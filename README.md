# Transfer ShapeKeys via UVs (Blender Addon)

This is a Blender add-on to transfer ShapeKeys between objects using compatible UV maps for vertex matching.

With respect to the integrated Blender method, based on triangle search in the proximity, this method offers advantages and disadvantages:

* (GOOD) This method doesn't require the geometries to be of a similar shape or perfectly overlapped.
* (GOOD) If the UVs are well-made, it might work better in problematic concave areas like nose and ears.
* (BAD) UV editing is a pain!

## Installation

* Download a zip release (`sktransfer-x.y.zip`)
* Install the zip through the Menu `Edit -> Preferences ...` and the `Add-ons` tab.

## Usage

A short video tutorial can be found here: https://www.youtube.com/watch?v=DAWjtayuwE0

Transferring a ShapeKey from a Source to a Destination object works if both have active UV layers able to show the same texture correctly.

In Object mode:

* Select (`click`) the Source object
* Select (`click`) the ShapeKey to transfer
* Add to selection (`shift+Click`) the Destination object
* Search (`F3`) `Transfer ShapeKey via UV`
  * or, from the Python console: `bpy.ops.object.transfer_shapekey_via_uv()`


Done. The Destination object should have a new ShapeKey with the same name of the source one.

Actually, during transfer, a texture is not really needed. It is just for the user to check if the UVs are comparable.


Parameters:

* `buffer_size` (int) is the size of the intermediate buffer used to store ShapeKey deltas. By default it is set at 256. Increase it if you have a very dense topology and you notice bad transfer in areas with many close pixels.
* `save_debug_images` (bool) if True activates the creation of PNG images for visual debug (see later section).

## Examples

A short video showing the addon in action: <https://www.youtube.com/watch?v=IZ5r9AO-G30>


### ShapeKey transfer between spheres.

First example transferring SHapeKeys between UV spheres created with different segments and rings.
The ShapeKeys are displacing segments outward the sphere centers.

<table>
<tr><th></th><th>Source</th><th>Destination</th></tr>
<tr><td>Basis</td><td><img src="Pics/Earth-Source-Basis.png" alt="Earth-Source-Basis"></td><td><img src="Pics/Earth-Destination-Basis.png" alt="Earth-Destination-Basis"></td></tr>
<tr><td>UVs</td><td><img src="Pics/Earth-Source-UV.png" alt="Earth-Source-UV"></td><td><img src="Pics/Earth-Destination-UV.png" alt="Earth-Destination-UV"></td></tr>
<tr><td>ShapeKey: NorthPole</td><td><img src="Pics/Earth-Source-NorthPole.png" alt="Earth-Source-NorthPole"></td><td><img src="Pics/Earth-Destination-NorthPole.png" alt="Earth-Destination-NorthPole"></td></tr>
<tr><td>ShapeKey: WaterUp</td><td><img src="Pics/Earth-Source-WaterUp.png" alt="Earth-Source-WaterUp"></td><td><img src="Pics/Earth-Destination-WaterUp.png" alt="Earth-Destination-WaterUp"></td></tr>
</table>

### ShapeKey transfer between Monkeys

The Source is the default Suzanne. The destination is a Suzanne after some scalings and a subdivision, all of them applied to the geometry.

<table>
<tr><th></th><th>Source</th><th>Destination</th></tr>
<tr><td>Basis</td><td><img src="Pics/Monkey-Source-Basis.png" alt="Monkey-Source-Basis"></td><td><img src="Pics/Monkey-Destination-Basis.png" alt="Monkey-Destination-Basis"></td></tr>
<tr><td>UVs</td><td><img src="Pics/Monkey-Source-UV.png" alt="Monkey-Source-UV"></td><td><img src="Pics/Monkey-Destination-UV.png" alt="Monkey-Destination-UV"></td></tr>
<tr><td>ShapeKey: BigEars</td><td><img src="Pics/Monkey-Source-BigEars.png" alt="Monkey-Source-BigEars"></td><td><img src="Pics/Monkey-Destination-BigEars.png" alt="Monkey-Destination-BigEars"></td></tr>
<tr><td>ShapeKey: BrowsUp</td><td><img src="Pics/Monkey-Source-BrowsUp.png" alt="Monkey-Source-BrowsUp"></td><td><img src="Pics/Monkey-Destination-BrowsUp.png" alt="Monkey-Destination-BrowsUp"></td></tr>
</table>


### ShapeKey transfer between a Human head and a Monkey.

The source object is actually a [FLAME](https://github.com/TimoBolkart/FLAME-Blender-Add-on) model, automatically generated and textured. The destination is again Suzanne.

For this case, I edited the UV of the monkey and tried to match the texture returned by FLAME. Given the strong difference in the two models, I couldn't get anything useful on the upper part of the face, but I focussed on the mouth and the addon was able to transfer a smile. 

<table>
<tr><th></th><th>Source</th><th>Destination</th></tr>
<tr><td>Basis</td><td><img src="Pics/FLAME-Source-Basis.png" alt="FLAME-Source-Basis"></td><td><img src="Pics/FLAME-Destination-Basis.png" alt="FLAME-Destination-Basis"></td></tr>
<tr><td>UVs</td><td><img src="Pics/FLAME-Source-UV.png" alt="FLAME-Source-UV"></td><td><img src="Pics/FLAME-Destination-UV.png" alt="FLAME-Destination-UV">It's a mess! I focused mainly on the mouth.</td></tr>
<tr><td>ShapeKey: Smile</td><td><img src="Pics/FLAME-Source-Smile.png" alt="FLAME-Source-Smile"></td><td><img src="Pics/FLAME-Destination-Smile.png" alt="FLAME-Destination-Smile"></td></tr>
</table>


### ShapeKey transfer between EMOCA-generated FLAME models.

The source object is actually a [FLAME](https://github.com/TimoBolkart/FLAME-Blender-Add-on) model, automatically generated and textured.
The destination is a FLAME model (but without ShapeKeys) generated via the [EMOCA](https://github.com/radekd91/emoca/) framework (3D mesh is automatically generated from video analysis).

For this case, the UV maps are already perfectly compatible.

<table>
<tr><th></th><th>Source</th><th>Destination</th></tr>
<tr><td>Basis</td><td><img src="Pics/EMOCA-Source-Basis.png" alt="EMOCA-Source-Basis"></td><td><img src="Pics/EMOCA-Destination-Basis.png" alt="EMOCA-Destination-Basis"></td></tr>
<tr><td>UVs</td><td><img src="Pics/EMOCA-Source-UV.png" alt="EMOCA-Source-UV"></td><td><img src="Pics/EMOCA-Destination-UV.png" alt="EMOCA-Destination-UV"></td></tr>
<tr><td>ShapeKey: Exp1</td><td><img src="Pics/EMOCA-Source-Exp1.png" alt="EMOCA-Source-Exp1"></td><td><img src="Pics/EMOCA-Destination-Exp1.png" alt="EMOCA-Destination-Exp1"></td></tr>
</table>


## ChangeLog

* [0.2] - 2024-01-23
  * Optionally, ShapeKey deltas are computed relatively to vertex normals.

* [0.1] - 2024-01-13
  * First public release



## TODOs

* Fill corners of the transfer buffer
* Panel and buttons
* A scaling parameter to modulate delta transfer
* Move the visual debug as addon option rather than operator parameter


## For Developers

### Running from repository code

Option 1:

* Clone this repository
* Open a Terminal
* Set env variable: `export BLENDER_USER_SCRIPTS="path/to/Transfer-ShapeKeys-Via-UV-Blender-Addon/BlenderScripts"`
* Run Blender: `path/to/blender.app/Contents/MacOS/blender`

Option 2:

* Clone this repository
* Menu `Edit -> Preferences ...`
* Tab `File Paths`
* Panel `Script Directories`
* Add directory `Transfer-ShapeKeys-Via-UV-Blender-Addon/BlenderScripts`


### Creating a release

    cd BlenderScripts/addons
    zip -r sktransfer-x.y.zip sktransfer -x "**/.DS_Store" "**/__pycache__/*"


### Visual debugging

WARNING: if you use the `save_debug_images` option, the PIL module (`pip install pillow`) must be installed in the Blender internal Python interpreter.

E.g., on a Mac, from a Terminal:

    > /Applications/blender-3.6.7/Blender.app/Contents/Resources/3.6/python/bin/python3.10 -m pip install pillow

If the operator parameter `save_debug_images` is set to True, three images will be saved on disk in the current working directory:
* `{SourceObjectName}-sk{number}-uv{number}-{buffer_size}x{buffer_size}-counts.png`
  * Every pixel is colored grey if a vertex delta was saved. The brighter, more deltas were accumulated and averaged.
* `{SourceObjectName}-sk{number}-uv{number}-{buffer_size}x{buffer_size}-deltas.png`
  * The accumulated XYZ ShapeKey delta values visualized as RGB colors.
* `{SourceObjectName}-sk{number}-uv{number}-{buffer_size}x{buffer_size}-filled.png`
  * The delta buffer after triangulation and interpolated triangle filling.

## Credits and Links

* The project has been developed at the [Affective Computing group](https://affective.dfki.de) of the [German Research Center for Artificial Intelligence (DFKI)](https://www.dfki.de/)
* The development was funded by the following research projects:
  * [SocialWear](https://affective.dfki.de/socialwear-bmbf-2020-2024/) (BMBF, cost action 22132)
  * [BIGEKO](https://www.interaktive-technologien.de/projekte/bigeko) (BMBF, grant number 16SV9093)

* The `delaunay` module for triangularization is distributed under the MIT license (see `LICENSE-delaunay.txt`) and was originally retreieved from <https://github.com/mkirc/delaunay>. Many thanks to [mkirc](https://github.com/mkirc) for the bug fixes!
* Triangle filling routines were inspired by this page: <http://www.sunshine2k.de/coding/java/TriangleRasterization/TriangleRasterization.html>
  * My version includes vertex value interpolation
