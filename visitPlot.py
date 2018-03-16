#!/Users/hansmathiasmamenvege/Programming/visit/python/2.7.11/i386-apple-darwin16_clang/bin/python

import os
import numpy as np
# import mayavi

def initVisit(visitPyPath, visitBinPath):
    '''
    Function initVisit:
    opens and launches the VisIt backend. For info about VisIt see:
    
    https://wci.llnl.gov/simulation/computer-codes/visit/ 

    Parameters:
    visitPyPath  (string) -> the location of the python library of VisIt
    visitBinPath (string) -> the location of the binary executables of VisIt
    '''
    # Import Packages
    import sys
    sys.path.insert(0,visitPyPath)
    global visit
    import visit

    # Init Visit
    visit.Launch(vdir=visitBinPath)


def makeVideoAndGif(folder, outFileName):
    '''
    Function makeVideoAndGif:
    uses ffmpeg and imagemagic to create a .mp4 and a .gif file out of the 
    frames in a folder.

    Parameters:
    folder      (string) -> the path of the folder containing the frames
    outFileName (string) -> the name of the output file
    '''
    # Create mp4 file
    os.system("ffmpeg -r 1 -i " + folder + "/%02d.png -vcodec mpeg4 -r 10 -y " + outFileName)
    
    # Create gif file
    # some command...


def closeVisit():    
    '''
    Function closeVisit:
    closes the VisIt backend
    '''
    visit.CloseComputeEngine()


def makeFrame(fileName, observable, outputFile, minVal, maxVal):

    # Open DataFile
    visit.OpenDatabase(fileName)
    
    # Set Plot Title
    if observable == "energy":
        plotTitle = "Energy Density"
    elif observable == "topc":
        plotTitle = "Topological Charge"
    

    # Draw Contour Plot
    if observable == "energy":
        visit.DefineScalarExpression("scaledField", "field/(-64)")
        visit.AddPlot("Contour", "scaledField")
        p = visit.ContourAttributes()
        p.scaling = 1 # logscale
        
    elif observable == "topc":
        visit.AddPlot("Contour", "field")
        p = visit.ContourAttributes()

    # Set min and max values
    p.min = minVal
    p.max = maxVal
    p.minFlag = 1
    p.maxFlag = 1
    p.contourNLevels = 15
    
    # Define Color Scheme ? perhaps manually to get transparency?
    p.colorType = 2
    p.colorTableName = "hot"
    visit.SetPlotOptions(p)

    # Title
    plottitle=visit.CreateAnnotationObject("Text2D")
    plottitle.position=(0.35,0.91)
    plottitle.fontFamily = plottitle.Times
    plottitle.text=plotTitle

    # Figure Dimension and Parameters
    s = visit.SaveWindowAttributes()
    s.format = s.PNG
    s.outputDirectory = ""
    s.width, s.height = (640,640)
    s.resConstraint = s.EqualWidthHeight
    s.screenCapture = 0
    s.family = 0
    s.fileName = outputFile
    visit.SetSaveWindowAttributes(s)

    # View Angle
    visit.ResetView()
    v = visit.GetView3D()
    v.viewNormal = (-0.505893, 0.32034, 0.800909)
    v.viewUp = (0.1314, 0.946269, -0.295482)
    v.parallelScale = 14.5472
    v.nearPlane = -34.641
    v.farPlane = 34.641
    v.perspective = 1
    visit.SetView3D(v) # Set the view

    # Set Background
    a = visit.AnnotationAttributes()
    a.backgroundColor = (192,192,192, 0)
    visit.SetAnnotationAttributes(a)
    
    # Antialiasing
    r = visit.RenderingAttributes()
    r.antialiasing = 1
    visit.SetRenderingAttributes(r)    

    # Draw
    visit.DrawPlots()
    visit.SaveWindow()

    # Close Files
    visit.DeleteAllPlots()
    visit.CloseDatabase(fileName)

if __name__ == "__main__":
    # Initialize Visit
    visitBinPath = "/home/giovanni/Desktop/visit2_13_0.linux-x86_64/bin"
    visitPyPath = "/home/giovanni/Desktop/visit2_13_0.linux-x86_64/2.13.0/linux-x86_64/lib/site-packages"
    
    visitBinPath = "/Users/hansmathiasmamenvege/Programming/visit2.13.0/src/bin"
    visitPyPath = "/Users/hansmathiasmamenvege/Programming/visit2.13.0/src/lib/site-packages/" 
    initVisit(visitPyPath, visitBinPath)

    # Plot Frames
    makeFrame("00.bov","energy", "00", 0.01, 0.1)
    makeFrame("01.bov","energy","01", 0.01, 0.1)
    makeFrame("02.bov","energy","02", 0.01, 0.1)
    makeFrame("03.bov","energy","03", 0.01, 0.1)

    # Close Visit
    closeVisit()

    # Make Video
    makeVideoAndGif(".", "a.mp4")
