import os
import matplotlib.pyplot as plt
import numpy as np
import utm
from pyproj import Proj, transform
from datetime import datetime, timedelta
class GPX():
    '''Parsing gpx files for plotting and use in other programs'''
    def __init__(self,fileName,**kwargs):
        self.fileName = fileName
        self.userOpts = kwargs        
        for key in self.userOpts:
            print(self.userOpts[key])

    def readGPX(self):
        fIn = open(self.fileName,'r')
        line = fIn.readline()        
        time_stamp = []; lon = []; lat = []; elev = [];
        splitline = line.split('"')
        for i in range(len(splitline)):
            if "ele" in splitline[i]:
                substring = splitline[i].split("<ele>")                
                elev.append((substring[1].split("</ele>"))[0])
            if "time" in splitline[i]:
                substring = splitline[i].split("<time>")                
                time_stamp.append((substring[1].split("</time>"))[0])
            if " lat" in splitline[i]:
                lat.append(splitline[i+1])
            if " lon" in splitline[i]:
                lon.append(splitline[i+1])
                
        return lon, lat, elev, time_stamp[1:]

                
    def gpx2KML(self):
        lon, lat, elev, time = self.readGPX()
        kml_path = "../kml/"
        if not os.path.isdir(kml_path):
            os.makedirs(kml_path)
        kml_file = (self.fileName.split("/")[-1])[:-3] + "kml"
        kml_out = kml_path + kml_file
        colour = self.colour2KML()
        f = open(kml_out,'w')
        content = ''
        coordinates = ''
        hdr_string = ('''<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2" xmlns:gx="http://www.google.com/kml/ext/2.2" xmlns:kml="http://www.opengis.net/kml/2.2" xmlns:atom="http://www.w3.org/2005/Atom">
<Document>
	<name>myLine.kml</name>
	<Style id="s_ylw-pushpin">
		<IconStyle>
			<scale>1.1</scale>
			<Icon>
				<href>http://maps.google.com/mapfiles/kml/pushpin/ylw-pushpin.png</href>
			</Icon>
			<hotSpot x="20" y="2" xunits="pixels" yunits="pixels"/>
		</IconStyle>
	</Style>
	<Style id="s_ylw-pushpin_hl">
		<IconStyle>
			<scale>1.3</scale>
			<Icon>
				<href>http://maps.google.com/mapfiles/kml/pushpin/ylw-pushpin.png</href>
			</Icon>
			<hotSpot x="20" y="2" xunits="pixels" yunits="pixels"/>
		</IconStyle>
	</Style>
	<StyleMap id="m_ylw-pushpin">
		<Pair>
			<key>normal</key>
			<styleUrl>#s_ylw-pushpin</styleUrl>
		</Pair>
		<Pair>
			<key>highlight</key>
			<styleUrl>#s_ylw-pushpin_hl</styleUrl>
		</Pair>
	</StyleMap>
	<Placemark>
		<name>myLine</name>
		<styleUrl>#m_ylw-pushpin</styleUrl>
                 <Style> 
                <LineStyle><color>%s</color><width>%d</width></LineStyle>
                </Style>
		<LineString>
			<tessellate>1</tessellate>
			<coordinates>''' % (colour,self.userOpts["lineWidth"]))
        tail_string = '''				</coordinates>
			</LineString>
		</Placemark>
</Document>
</kml>'''

        for i in range(len(lon)-1):
            
            coord_string = lon[i] + "," + lat[i] + ",0 "
            coordinates += coord_string
        content += hdr_string
        content += coordinates
        content += tail_string
        f.write(content)
        f.close()
        
                
    def colour2KML(self):
        colours = {
            "red" : "501400FF",
            "green" : "5014B400",
            "blue" : "50FF7800",
            "yellow" : "5014F0FF",
            "black" : "50000014",
            "white" : "50FFFFFF"
            }
        return colours[self.userOpts["lineColour"]]

        
    def elevProfile(self):
        lon, lat, elev, time = self.readGPX()
        index = self.subSample(time)
        lonarr = np.asarray(lon,dtype=float)
        latarr = np.asarray(lat,dtype=float)
        elevarr = np.asarray(elev,dtype=float)        
        userutm = utm.from_latlon(np.mean(latarr),np.mean(lonarr))        
        utmstring = ''
        utmstring += str(userutm[2])
        utmstring += userutm[3]   
        projOut = self.getEPSG(utmstring)        
        projIn = "epsg:4326"
        inProj = Proj(init=projIn)
        outProj = Proj(init=projOut)
        xutm,yutm = transform(inProj,outProj,lonarr,latarr)
        dist = np.zeros(len(xutm))
        for i in range(1, len(xutm)):
            dist[i] = dist[i-1] + ((xutm[i]-xutm[i-1])**2+(yutm[i]-yutm[i-1])**2)**0.5    
        
        profPlot, = plt.plot(dist[index],elevarr[index])
        totDist, = plt.plot(0,0,'w')
        totTime, = plt.plot(0,0,'w')
        intTime, = plt.plot(0,0,'w')
        aveSpeed, = plt.plot(0,0,'w')
        distance =  dist[-1]/1000.
        start_time = datetime.strptime(time[0],'%Y-%m-%dT%H:%M:%SZ')
        end_time = datetime.strptime(time[-1],'%Y-%m-%dT%H:%M:%SZ')
        duration =  ((end_time-start_time).total_seconds())/3600.
        meanspeed = distance/duration        
        idx = 1
        for i in range(1, len(dist)):            
            if idx<len(index):
                if i==int(index[idx]):
                    sections, = plt.plot([dist[i],dist[i]],[0,elevarr[i]],'r')
                    idx = idx + 1
        plt.ylabel("Elevation (m)")
        plt.xlabel("Distance (m)")
        plt.legend([profPlot,sections,totDist,totTime,intTime,aveSpeed],["Profile","Interval distance","Distance - " + str("%.2f" % round(distance,2)) + " km","Time - " + str("%.2f" % round(duration,2)) + " Hrs","Time interval - " + str(self.userOpts['timeInterval']) + " Hrs","Average speed - " + str("%.2f" % round(meanspeed,2)) + " km/h"])
        plt.show()
        plt.close()


    def getEPSG(self,utmstring):
        utmzones = {
            "30U" : "epsg:32630"
            #need to add full UTM/EPSG dictionary
            }
        return utmzones[utmstring]

    def subSample(self,time):
        index = []
        index.append(0)       
        current_time = datetime.strptime(time[0],'%Y-%m-%dT%H:%M:%SZ')
        dtmin = self.userOpts['timeInterval']*60.0
        future_time = current_time + timedelta(minutes = int(dtmin))
        for i in range(1,len(time)):
            timestamp = datetime.strptime(time[i],'%Y-%m-%dT%H:%M:%SZ')
            time_delta = (future_time-timestamp).total_seconds()
            
            if time_delta<=0.0:
                index.append(i)
                future_time = timestamp + timedelta(minutes = int(dtmin))
        if index[-1]!=len(time)-1:
            index.append(len(time)-1)
        return index    

        
 
        
