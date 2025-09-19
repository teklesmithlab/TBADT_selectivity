from pymol.cgo import *
from pymol import cmd

sphere = [
   SPHERE, 0.000, 0.000, 0.000, 4.400
]
cmd.load_cgo(sphere, "0_sphere_4.400")

cylinder = [
]
cmd.load_cgo(cylinder, "axes")

cmd.load("/Users/mimis_stuff/PycharmProjects/PythonProject/TBADT_selectivity_old/xyz_files/p2_11_transform.xyz")
cmd.show_as("spheres", "p2_11_transform")
cmd.set("sphere_transparency", 0.5)
cmd.set("orthoscopic", "on")
