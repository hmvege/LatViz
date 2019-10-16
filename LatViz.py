#!/usr/bin/python2

import os as os
from visitlqcd import plot_visit

if __name__ == "__main__":
    # # Visit plot setup
    visitBin = "/opt/visit/bin/visit"
    #visitBin = "/Applications/VisIt.app/Contents/Resources/bin/visit"

    bin_folder = os.path.abspath('example_data')

    plot_visit(
       bin_folder,  # path fo .bin folder
       "euclidean",       

       # # Energy settings
       32,                # size of lattice
       "energy",          # observable type
       1.0,              # min value of the scale
       2.5,               # max value of the scale

       # Topological charge settings
       # 32,                # size of lattice
       # "topc",            # observable type
       # -0.001,            # min value of the scale
       # 0.001,             # max value of the scale


       visitBin,          # Binary location of Visit
       euclideanTime=59,  # Euclidean time slice for flow
       NContours=10,      # number of contours
       pixelSize=1280,     # image size in pixels
       transparency=75,   # alpha channel (0-255)
       avi=True,          # avi output
       gif=True,          # gif output
       # delete temp files (frames and blocks)
       cleanUp=True,
       plotTitle=None     # title (default is the observable)
    )

