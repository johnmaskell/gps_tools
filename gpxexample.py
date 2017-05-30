from gpstools.gpxtools import GPX

print(GPX.__doc__)

optionals = {
    "kmltype" : "line", #marker
    "markerstyle" : "pin",
    "lineColour" : "yellow",
    "lineWidth" : 4,
    "timeInterval" : 0.25 #hours
    }

kwargs = optionals
filename = "Track_2017-05-23 133531.gpx"
newscan = GPX(filename,**kwargs)
lon, lat, elev, time = newscan.readGPX()
newscan.gpx2KML()
newscan.elevProfile()

