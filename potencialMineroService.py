import arcpy
import os
import json
import zipfile
import uuid

arcpy.env.overwriteOutput = True



# IMPORT CONFIG JSON ::::::::::::::::::::::::::::::::::::::::::::::::::::::

fileserver = r'E:\arcgisserver\config-store\services\complementos'
config = os.path.join(fileserver, 'potencialMinero\config.json')

#config = os.path.join(os.path.dirname(__file__), 'config.json')
jsondata = json.load(open(config))

# :::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::



class potencialMinero:
	def __init__(self):
		self.filezip_tmp = arcpy.GetParameterAsText(0)
		self.filezip = jsondata['demo'] if self.filezip_tmp in [None, "#", ""] else self.filezip_tmp
		self.pixel_tmp = arcpy.GetParameterAsText(1)
		self.pixel = jsondata['pixel'] if self.pixel_tmp in (None, '', "#") else self.pixel_tmp
		self.pathoutput = ""
		self.listfcs = []
		self.listRaster = []
		self.listfcs = []
		self.ws = jsondata['workspace']
		self.namefiles = jsondata['nameFiles']
		self.geometria = jsondata['geometria']
		self.campo = jsondata['campo']
		self.tipocampo = jsondata['tipocampo']
		self.ponderacion = jsondata['ponderacion']
		self.errores = jsondata['errores']
		self.namefolder = str(uuid.uuid4())
		self.directorio = os.path.join(self.ws, self.namefolder)
		self.nameZip = jsondata['nameZip']
		arcpy.env.workspace = self.directorio


	def descomprimir(self):
		os.mkdir(self.directorio)
		zf = zipfile.ZipFile(self.filezip)
		zf.extractall(self.directorio)


	def consistencia01(self):
		fcs = [os.path.join(self.directorio, x) for x in arcpy.ListFeatureClasses() if x in self.namefiles]
		if len(fcs) == 6:
			self.listfcs = fcs
		else:
			raise RuntimeError(self.errores['1'])



	def consistencia02(self):
		for x in self.listfcs:
			desc = arcpy.Describe(x)
			if desc.shapeType == self.geometria:
				pass
			else:
				raise RuntimeError(self.errores['2'])				
		



	def consistencia03(self):
		for x in self.listfcs:
			camposfc = [m for m in arcpy.ListFields(x) if m.name == self.campo]
			if len(camposfc) == 1 and camposfc[0].type in self.tipocampo:
				pass
			else:
				raise RuntimeError(self.errores['3'])


	def ejecutarPotencial(self):
		listRaster = []
		count = 0
		self.listfcs.sort()
		for x in self.listfcs:
			raster = arcpy.PolygonToRaster_conversion(x, self.campo, os.path.join(arcpy.env.scratchFolder, 'var_{}'.format(count)), "CELL_CENTER", self.campo, self.pixel)
			listRaster.append(arcpy.sa.Raster(raster)*self.ponderacion[count])
			count = count + 1
		pm = sum(listRaster)
		self.extentRaster = pm.extent.projectAs(arcpy.SpatialReference(jsondata["sr"])).JSON
		self.pathoutput = os.path.join(arcpy.env.scratchFolder, 'PotencialMinero.tif')
		pm.save(self.pathoutput)
		self.dirPm = pm.path
		arcpy.Delete_management(self.directorio)
		return pm


	@property
	def comprimirTif(self):
	    zf = zipfile.ZipFile(os.path.join(self.dirPm, self.nameZip), "w", zipfile.ZIP_DEFLATED)
	    a = [x for x in os.listdir(os.path.dirname(self.pathoutput)) if x[0: 15] == 'PotencialMinero']
	    for i in a:
	        zf.write(os.path.join(os.path.dirname(self.pathoutput), i), i)
	    zf.close()
	    return zf.filename


	def main(self):
		try:
			self.descomprimir()
			self.consistencia01()
			self.consistencia02()
			self.consistencia03()
			rasterOut = self.ejecutarPotencial()
			stringOut = self.comprimirTif
			arcpy.SetParameterAsText(2, rasterOut)
			arcpy.SetParameterAsText(3, stringOut)
			arcpy.SetParameterAsText(4, self.extentRaster)
		except Exception as e:
			arcpy.AddMessage(e)



if __name__ == "__main__":
	obj = potencialMinero()
	obj.main()






