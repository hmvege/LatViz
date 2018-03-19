import sys
import json
import subprocess

def makeVideoAndGif(folder, outFileName, avi=True, gif=True):
    '''
    Function makeVideoAndGif:
    uses ffmpeg and imagemagic to create a .mp4 and a .gif file out of the 
    frames in a folder.

    Parameters:
    folder      (string) -> the path of the folder containing the frames
    outFileName (string) -> the name of the output file
    avi         (bool)   -> bool to set the avi output default=True
    gif         (bool)   -> bool to set the gif output default=True
    '''
    
    # Create mp4 file
    if avi:
        cmd = ["ffmpeg", "-r", "8", "-i", folder + "temp/%03d.png", 
                        "-qscale:v", "0", "-r", "8", "-y", outFileName + ".avi"]
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE)
        read_out = proc.stdout.read()
    
    # Create gif file
    if gif:
        cmd = ["convert", "-delay", "10", "-loop", "0", 
                        folder + "temp/*.png", outFileName +".gif"]
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE)
        read_out = proc.stdout.read()

def makeFrame(fileName, observable, outputFile, minVal, maxVal, colors, 
              NContours=15, plotTitle=None, pixelSize=640):
    '''
    Function makeFrame:
    creates a frame given a sub-block of the lattice. Uses Visit to set view, 
    colorscheme and saves the frame in the temp folder.

    Parameters:
    fileName    (string) -> path to the sub-block .bov file
    outputFile  (string) -> the name of the output .png file
    observable  (string) -> either "energy" or "topc", used to set the scale 
                            and the title
    minVal      (float)  -> the minimum value of the scale to use
    maxVal      (float)  -> the maximum value of the scale to use
    NContours   (int)    -> the number of contour surfaces to draw default=15
    plotTitle   (string) -> title for the plot default is observable name
    pixelSize   (int)    -> size of the output image in pixels, default=640
    colors      (list)   -> list of colors for palette
    '''
    # Open DataFile
    visit.OpenDatabase(fileName)
    
    # Set Plot Title
    if not plotTitle:
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
        p.scaling = 0 # logscale

    # Set min and max values
    p.min = minVal
    p.max = maxVal
    p.minFlag = 1
    p.maxFlag = 1
    p.contourNLevels = NContours
    
    # Define Color Scheme 
    for i, color in enumerate(colors):
        p.SetMultiColor(i, tuple(color))
    p.colorType = 1
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
    s.width, s.height = (pixelSize,pixelSize)
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
    visit.SetView3D(v) 

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

def plotConf(folder, files, size, observable, outpuFileName, 
             minVal, maxVal, colors, NContours=15, pixelSize=640, 
             avi=True, gif=True, plotTitle=None):
    '''
    Function plotConf:
    given a folder and a configuration file, generates the frames, a gif and
    and avi file.

    Parameters:
    folder    (string) -> the path of the configuration (will be the path of
                          the temp folder as well)
    files     (list)   -> list of .bov files
    size      (int)    -> the number of points per spatial dimension
    observable(string) -> either "energy" or "topc", used to set the scale 
                          and the title of the frame
    outpuFileName (string) -> the name of the .avi and .gif files
    minVal      (float)  -> the minimum value of the scale to use
    maxVal      (float)  -> the maximum value of the scale to use
    avi       (bool)     -> bool to set the avi output default=True
    gif       (bool)     -> bool to set the gif output default=True
    NContours   (int)    -> the number of contour surfaces to draw default=15
    plotTitle   (string) -> title for the plot default is observable name
    pixelSize   (int)    -> size of the output image in pixels, default=640
    '''    
    # Plot Frames
    for i, file in enumerate(files):
        makeFrame(file, observable, folder + "temp/" + str(i).zfill(3), 
            minVal, maxVal, colors, NContours=NContours, plotTitle=plotTitle,
            pixelSize=pixelSize)

    # Make Video
    if avi or gif:
        makeVideoAndGif(folder, folder + outpuFileName, avi=avi, gif=gif)
    

if __name__ == "__main__":
    with open(sys.argv[1], "r") as jsonParams:
        params = json.load(jsonParams)

    # Plot
    plotConf(params["folder"],       # path fo .bin folder
             params["files"],        # the .bov file
             params["size"],         # size of lattice
             params["observable"],   # observable type
             params["outputFile"],   # outputfile name
             params["minValue"],     # min value of the scale
             params["maxValue"],     # max value of the scale
             params["palette"],      # color palette liste
             params["NContours"],    # number of contours
             params["pixelSize"],    # image size in pixels
             params["avi"],          # avi output
             params["gif"],          # gif output
             params["plotTitle"]     # title (default is the observable)
            )

    exit()
