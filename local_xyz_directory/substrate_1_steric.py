from pymol.cgo import *
from pymol import cmd

sphere = [
   SPHERE, 0.000, 0.000, 0.000, 2.700
]
cmd.load_cgo(sphere, "0_sphere_2.700")

cylinder = [
]
cmd.load_cgo(cylinder, "axes")

cmd.load("/Users/mimis_stuff/PycharmProjects/PythonProject/TBADT_selectivity/local_xyz_directory/substrate_1_transform.xyz")
cmd.show_as("spheres", "substrate_1_transform")
cmd.set("sphere_transparency", 0.5)
cmd.set("orthoscopic", "on")
