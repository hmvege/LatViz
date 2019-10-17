import visit as vs
import os as os

def make_video_and_gif(folder, outFileName, avi=True, gif=True):
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
        cmd = 'ffmpeg -r 8 -i ' + folder + '/temp/%03d.png qscale:v 0 -y ' + outFileName + '.avi'
        os.system(cmd)
    
    # Create gif file
    if gif:
        cmd = 'convert -delay 10 -loop 0 ' + folder + '/temp/*.png ' + outFileName +'.gif'
        os.system(cmd)

class Contour3DFrame:
    def __init__(self, params):

        self.params = params
        
        # Set Plot Title
        if not self.params["plotTitle"]:
            if self.params["observable"] == "energy":
                self.params["plotTitle"] = "Energy Density"
            elif self.params["observable"] == "topc":
                self.params["plotTitle"] = "Topological Charge"
        pass

    def draw(self, fileName):
        # Open DataFile
        vs.OpenDatabase(fileName)
        
        # Draw Contour Plot
        p = vs.ContourAttributes()
        if self.params["observable"] == "energy":
            vs.DefineScalarExpression("scaledField", "(-1)*field")
            vs.AddPlot("Contour", "scaledField")
            p.scaling = 1 # logscale
            
        elif self.params["observable"] == "topc":
            vs.AddPlot("Contour", "field")
            p = visit.ContourAttributes()
            p.scaling = 0 # logscale

        # Set min and max values
        p.min = self.params["minValue"]
        p.max = self.params["maxValue"]
        p.minFlag = 1
        p.maxFlag = 1
        p.contourNLevels = self.params["NContours"]
        
        # Define Color Scheme 
        for i, color in enumerate(self.params["palette"]):
            p.SetMultiColor(i, tuple(color))
        p.colorType = 1
        vs.SetPlotOptions(p)

        
        # Title
        title = vs.CreateAnnotationObject("Text2D")
        title.position = (0.35,0.91)
        title.fontFamily = title.Times
        title.text = self.params["plotTitle"]

        # Figure Dimension and Parameters
        s = vs.SaveWindowAttributes()
        s.format = s.PNG
        s.outputDirectory = ""
        s.width, s.height = (self.params["pixelSize"], self.params["pixelSize"])
        s.resConstraint = s.EqualWidthHeight
        s.screenCapture = 0
        s.family = 0
        s.fileName = self.params["outputFile"]
        vs.SetSaveWindowAttributes(s)

        # View Angle
        vs.ResetView()
        v = vs.GetView3D()
        v.viewNormal = (-0.505893, 0.32034, 0.800909)
        v.viewUp = (0.1314, 0.946269, -0.295482)
        v.parallelScale = 14.5472
        v.nearPlane = -34.641
        v.farPlane = 34.641
        v.perspective = 1
        vs.SetView3D(v) 

        # Set Background
        a = vs.AnnotationAttributes()
        a.backgroundColor = (192,192,192, 0)
        vs.SetAnnotationAttributes(a)
        
        # Antialiasing
        r = vs.RenderingAttributes()
        r.antialiasing = 1
        vs.SetRenderingAttributes(r)    

        # Draw
        vs.DrawPlots()
        vs.SaveWindow()

        # Close Files
        vs.DeleteAllPlots()
        vs.CloseDatabase(fileName)

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
