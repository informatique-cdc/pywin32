# A tool to setup the Python registry.

error = "Registry Setup Error"

import sys # at least we can count on this!

def FileExists(fname):
	"""Check if a file exists.  Returns true or false.
	"""
	import os
	try:
		os.stat(fname)
		return 1
	except os.error, details:
		return 0

def IsPackageDir(path, packageName, knownFileName):
	"""Given a path, a ni package name, and possibly a known file name in
           the root of the package, see if this path is good.
      """
	import os
	if knownFileName is None:
		knownFileName = "."
	return FileExists(os.path.join(os.path.join(path, packageName),knownFileName))


def FindPackagePath(packageName, knownFileName, searchPaths):
	"""Find a package.

           Given a ni style package name, check the package is registered.

           First place looked is the registry for an existing entry.  Then
           the searchPaths are searched.
      """
	import win32api, win32con, regutil
	pathLook = regutil.GetRegisteredNamedPath(packageName)
	if pathLook and IsPackageDir(pathLook, packageName, knownFileName):
		return pathLook, None # The currently registered one is good.
	# Search down the search paths.
	for pathLook in searchPaths:
		if IsPackageDir(pathLook, packageName, knownFileName):
			# Found it
			ret = win32api.GetFullPathName(pathLook)
			return ret, ret
	raise error, "The package %s can not be located" % packageName

def FindHelpPath(helpFile, helpDesc, searchPaths):
	# See if the current registry entry is OK
	import win32api, win32con, os
	try:
		key = win32api.RegOpenKey(win32con.HKEY_LOCAL_MACHINE, "Software\\Microsoft\\Windows\\Help", 0, win32con.KEY_ALL_ACCESS)
		try:
			try:
				path = win32api.RegQueryValueEx(key, helpDesc)[0]
				print "Looking in", path
				if FileExists(os.path.join(path, helpFile)):
					return win32api.GetFullPathName(path)
			except win32api.error:
				pass # no registry entry.
		finally:
			win32api.RegCloseKey(key)
	except win32api.error:
		pass
	for pathLook in searchPaths:
		if FileExists(os.path.join(pathLook, helpFile)):
			return win32api.GetFullPathName(pathLook)
		pathLook = os.path.join(pathLook, "Help")
		if FileExists(os.path.join( pathLook, helpFile)):
			return win32api.GetFullPathName(pathLook)
	raise error, "The help file %s can not be located" % helpFile

def FindAppPath(appName, knownFileName, searchPaths):
	"""Find an application.

         First place looked is the registry for an existing entry.  Then
         the searchPaths are searched.
      """
	# Look in the first path.
	import win32api, win32con, regutil, string, os
	regPath = regutil.GetRegisteredNamedPath(appName)
	if regPath:
		pathLook = string.split(regPath,";")[0]
	if regPath and FileExists(os.path.join(pathLook, knownFileName)):
		return None # The currently registered one is good.
	# Search down the search paths.
	for pathLook in searchPaths:
		if FileExists(os.path.join(pathLook, knownFileName)):
			# Found it
			return win32api.GetFullPathName(pathLook)
	raise error, "The file %s can not be located for application %s" % (knownFileName, appName)

def FindRegisteredModule(moduleName, possibleRealNames, searchPaths):
	"""Find a registered module.

         First place looked is the registry for an existing entry.  Then
         the searchPaths are searched.
         
	   Returns the full path to the .exe or None if the current registered entry is OK.
      """
	import win32api, win32con, regutil, string
	try:
		fname = win32api.RegQueryValue(regutil.GetRootKey(), \
		               regutil.BuildDefaultPythonKey() + "\\Modules\\%s" % moduleName)

		if FileExists(fname):
			return None # Nothing extra needed

	except win32api.error:
		pass
	return LocateFileName(possibleRealNames, searchPaths)

def FindPythonExe(exeAlias, possibleRealNames, searchPaths):
	"""Find an exe.

         First place looked is the registry for an existing entry.  Then
         the searchPaths are searched.
         
	   Returns the full path to the .exe, and a boolean indicating if the current 
	   registered entry is OK.
      """
	import win32api, win32con, regutil, string
	if possibleRealNames is None:
		possibleRealNames = exeAlias
	try:
		fname = win32api.RegQueryValue(regutil.GetRootKey(), regutil.GetAppPathsKey() + "\\" + exeAlias)
		if FileExists(fname):
			return fname, 1 # Registered entry OK

	except win32api.error:
		pass
	return LocateFileName(possibleRealNames, searchPaths), 0

def QuotedFileName(fname):
	"""Given a filename, return a quoted version if necessary
      """
	import win32api, win32con, regutil, string
	try:
		string.index(fname, " ") # Other chars forcing quote?
		return '"%s"' % fname
	except ValueError:
		# No space in name.
		return fname

def LocateFileName(fileNamesString, searchPaths):
	"""Locate a file name, anywhere on the search path.

	   If the file can not be located, prompt the user to find it for us
	   (using a common OpenFile dialog)

	   Raises KeyboardInterrupt if the user cancels.
	"""
	import win32api, win32con, regutil, string, os
	fileNames = string.split(fileNamesString,";")
	for path in searchPaths:
		for fileName in fileNames:
			try:
				retPath = os.path.join(path, fileName)
				os.stat(retPath)
				break
			except os.error:
				retPath = None
		if retPath:
			break
	else:
		fileName = fileNames[0]
		try:
			import win32ui
		except ImportError:
			raise error, "Need to locate the file %s, but the win32ui module is not available\nPlease run the program again, passing as a parameter the path to this file." % fileName
		# Display a common dialog to locate the file.
		flags=win32con.OFN_FILEMUSTEXIST
		ext = os.path.splitext(fileName)[1]
		filter = "Files of requested type (*%s)|*%s||" % (ext,ext)
		dlg = win32ui.CreateFileDialog(1,None,fileName,flags,filter,None)
		dlg.SetOFNTitle("Locate " + fileName)
		if dlg.DoModal() <> win32con.IDOK:
			raise KeyboardInterrupt, "User cancelled the process"
		retPath = dlg.GetPathName()
	return win32api.GetFullPathName(retPath)

def LocatePath(fileName, searchPaths):
	"""Like LocateFileName, but returns a directory only.
	"""
	import os, win32api
	return win32api.GetFullPathName(os.path.split(LocateFileName(fileName, searchPaths))[0])

def LocateOptionalPath(fileName, searchPaths):
	"""Like LocatePath, but returns None if the user cancels.
	"""
	try:
		return LocatePath(fileName, searchPaths)
	except KeyboardInterrupt:
		return None


def LocateOptionalFileName(fileName, searchPaths = None):
	"""Like LocateFileName, but returns None if the user cancels.
	"""
	try:
		return LocateFileName(fileName, searchPaths)
	except KeyboardInterrupt:
		return None

def LocatePythonCore(searchPaths):
	"""Locate and validate the core Python directories.  Returns a list
         of paths that should be used as the core (ie, un-named) portion of
         the Python path.
	"""
	import win32api, win32con, string, os, regutil
	currentPath = regutil.GetRegisteredNamedPath(None)
	if currentPath:
		presearchPaths = string.split(currentPath, ";")
	else:
		presearchPaths = [win32api.GetFullPathName(".")]
	libPath = None
	for path in presearchPaths:
		if FileExists(os.path.join(path, "os.py")):
			libPath = path
			break
	if libPath is None and searchPaths is not None:
		libPath = LocatePath("os.py", searchPaths)
	if libPath is None:
		raise error, "The core Python library could not be located."

	corePath = None
	for path in presearchPaths:
		if FileExists(os.path.join(path, "parser.dll")):
			corePath = path
			break
	if corePath is None and searchPaths is not None:
		corePath = LocatePath("parser.dll", searchPaths)
	if corePath is None:
		raise error, "The core Python path could not be located."

	installPath = win32api.GetFullPathName(os.path.join(libPath, ".."))
	return installPath, [libPath, corePath]

def FindRegisterPackage(packageName, knownFile, searchPaths):
	"""Find and Register a package.

	   Assumes the core registry setup correctly.

	   In addition, if the location located by the package is already
           in the **core** path, then an entry is registered, but no path.
	   (no other paths are checked, as the application whose path was used
	   may later be uninstalled.  This should not happen with the core)
	"""
	import win32api, win32con, regutil, string
	if not packageName: raise error, "A package name must be supplied"
	corePaths = string.split(regutil.GetRegisteredNamedPath(None),";")
	if not searchPaths: searchPaths = corePaths
	try:
		pathLook, pathAdd = FindPackagePath(packageName, knownFile, searchPaths)
		if pathAdd is not None:
			if pathAdd in corePaths:
				pathAdd = ""
			regutil.RegisterNamedPath(packageName, pathAdd)
		return pathLook
	except error, details:
		print "*** The %s package could not be registered - %s" % (packageName, details)
		print "*** Please ensure you have passed the correct paths on the command line."
		print "*** - For packages, you should pass a path to the packages parent directory,"
		print "*** - and not the package directory itself..."


def FindRegisterApp(appName, knownFiles, searchPaths):
	"""Find and Register a package.

	   Assumes the core registry setup correctly.

	"""
	import win32api, win32con, regutil, string
	if type(knownFiles)==type(''):
		knownFiles = [knownFiles]
	paths=[]
	try:
		for knownFile in knownFiles:
			pathLook = FindAppPath(appName, knownFile, searchPaths)
			if pathLook:
				paths.append(pathLook)
	except error, details:
		print "*** ", details
		return

	regutil.RegisterNamedPath(appName, string.join(paths,";"))

def FindRegisterModule(modName, actualFileNames, searchPaths):
	"""Find and Register a module.

	   Assumes the core registry setup correctly.
	"""
	import regutil
	try:
		fname = FindRegisteredModule(modName, actualFileNames, searchPaths)
		if fname is not None:
			regutil.RegisterModule(modName, fname)
	except error, details:
		print "*** ", details

def FindRegisterPythonExe(exeAlias, searchPaths, actualFileNames = None):
	"""Find and Register a Python exe (not necessarily *the* python.exe)

	   Assumes the core registry setup correctly.
	"""
	import win32api, win32con, regutil, string
	fname, ok = FindPythonExe(exeAlias, actualFileNames, searchPaths)
	if not ok:
		regutil.RegisterPythonExe(fname, exeAlias)
	return fname


def FindRegisterHelpFile(helpFile, searchPaths, helpDesc = None ):
	import regutil
	
	try:
		pathLook = FindHelpPath(helpFile, helpDesc, searchPaths)
	except error, details:
		print "*** ", details
		return
#	print "%s found at %s" % (helpFile, pathLook)
	regutil.RegisterHelpFile(helpFile, pathLook, helpDesc)
	
def SetupCore(searchPaths):
	"""Setup the core Python information in the registry.

	   This function makes no assumptions about the current state of sys.path.

	   After this function has completed, you should have access to the standard
	   Python library, and the standard Win32 extensions
	"""

	import sys	
	for path in searchPaths:
		sys.path.append(path)

	import string, os
	import regutil, win32api, win32con
	
	installPath, corePaths = LocatePythonCore(searchPaths)
	# Register the core Pythonpath.
	print corePaths
	regutil.RegisterNamedPath(None, string.join(corePaths,";"))

	# Register the install path.
	hKey = win32api.RegCreateKey(regutil.GetRootKey() , regutil.BuildDefaultPythonKey())
	try:
		# Core Paths.
		win32api.RegSetValue(hKey, "InstallPath", win32con.REG_SZ, installPath)
	finally:
		win32api.RegCloseKey(hKey)
	# The core DLL.
	regutil.RegisterCoreDLL()

	# Register the win32 extensions, as some of them are pretty much core!
	# Why doesnt win32con.__file__ give me a path? (ahh - because only the .pyc exists?)

	# Register the win32 core paths.
	win32paths = win32api.GetFullPathName( os.path.split(win32api.__file__)[0]) + ";" + \
	             win32api.GetFullPathName( os.path.split(LocateFileName("win32con.py;win32con.pyc", sys.path ) )[0] )
	             
	FindRegisterModule("pywintypes", "pywintypes15.dll", [".", win32api.GetSystemDirectory()])
	regutil.RegisterNamedPath("win32",win32paths)


def RegisterShellInfo(searchPaths):
	"""Registers key parts of the Python installation with the Windows Shell.

	   Assumes a valid, minimal Python installation exists
	   (ie, SetupCore() has been previously successfully run)
	"""
	import regutil, win32con
	# Set up a pointer to the .exe's
	exePath = FindRegisterPythonExe("Python.exe", searchPaths)
	regutil.SetRegistryDefaultValue(".py", "Python.File", win32con.HKEY_CLASSES_ROOT)
	regutil.RegisterShellCommand("Open", QuotedFileName(exePath)+" %1 %*", "&Run")
	regutil.SetRegistryDefaultValue("Python.File\\DefaultIcon", "%s,0" % exePath, win32con.HKEY_CLASSES_ROOT)
	
	FindRegisterHelpFile("Python.hlp", searchPaths, "Main Python Documentation")

	# We consider the win32 core, as it contains all the win32 api type
	# stuff we need.
#	FindRegisterApp("win32", ["win32con.pyc", "win32api.pyd"], searchPaths)

def RegisterPythonwin(searchPaths):
	"""Knows how to register Pythonwin components
	"""
	import regutil
	FindRegisterApp("Pythonwin", "docview.py", searchPaths)
	FindRegisterHelpFile("Pythonwin.hlp", searchPaths, "Pythonwin Reference")
	
	FindRegisterPythonExe("pythonwin.exe", searchPaths, "Pythonwin.exe")
	regutil.RegisterShellCommand("Edit", QuotedFileName("pythonwin.exe")+" /edit %1")
	regutil.RegisterDDECommand("Edit", "Pythonwin", "System", '[self.OpenDocumentFile(r"%1")]')

	FindRegisterModule("win32ui", "win32ui.pyd", searchPaths)
	FindRegisterModule("win32uiole", "win32uiole.pyd", searchPaths)

	fnamePythonwin = regutil.GetRegisteredExe("Pythonwin.exe")
	fnamePython = regutil.GetRegisteredExe("Python.exe")
	
	regutil.RegisterFileExtensions(defPyIcon=fnamePythonwin+",0", 
	                               defPycIcon = fnamePythonwin+",5",
	                               runCommand = QuotedFileName(fnamePython)+" %1 %*")

def UnregisterPythonwin():
	"""Knows how to unregister Pythonwin components
	"""
	import regutil
	regutil.UnregisterNamedPath("Pythonwin")
	regutil.UnregisterHelpFile("Pythonwin.hlp")

	regutil.UnregisterPythonExe("pythonwin.exe")
	
	#regutil.UnregisterShellCommand("Edit")

	regutil.UnregisterModule("win32ui")
	regutil.UnregisterModule("win32uiole")
	

def RegisterWin32com(searchPaths):
	"""Knows how to register win32com components
	"""
	import win32api
#	import ni,win32dbg;win32dbg.brk()
	corePath = FindRegisterPackage("win32com", "olectl.py", searchPaths)
	if corePath:
		FindRegisterHelpFile("win32com.hlp", searchPaths + [corePath+"\\win32com"], "Python COM Reference")
		FindRegisterModule("pythoncom", "pythoncom15.dll", [win32api.GetSystemDirectory(), '.'])

usage = """\
regsetup.py - Setup/maintain the registry for Python apps.

Run without options, (but possibly search paths) to repair a totally broken
python registry setup.  This should allow other options to work.

Usage:   %s [options ...] paths ...
-p packageName  -- Find and register a package.  Looks in the paths for
                   a sub-directory with the name of the package, and
                   adds a path entry for the package.
-a appName      -- Unconditionally add an application name to the path.
                   A new path entry is create with the app name, and the
                   paths specified are added to the registry.
-c              -- Add the specified paths to the core Pythonpath.
                   If a path appears on the core path, and a package also 
                   needs that same path, the package will not bother 
                   registering it.  Therefore, By adding paths to the 
                   core path, you can avoid packages re-registering the same path.  
-m filename     -- Find and register the specific file name as a module.
                   Do not include a path on the filename!
--shell         -- Register everything with the Win95/NT shell.
--pythonwin     -- Find and register all Pythonwin components.
--unpythonwin   -- Unregister Pythonwin
--win32com      -- Find and register all win32com components
--upackage name -- Unregister the package
--uapp name     -- Unregister the app (identical to --upackage)
--umodule name  -- Unregister the module

--description   -- Print a description of the usage.
--examples      -- Print examples of usage.
""" % sys.argv[0]

description="""\
If no options are processed, the program attempts to validate and set 
the standard Python path to the point where the standard library is
available.  This can be handy if you move Python to a new drive/sub-directory,
in which case most of the options would fail (as they need at least string.py,
os.py etc to function.)
Running without options should repair Python well enough to run with 
the other options.

paths are search paths that the program will use to seek out a file.
For example, when registering the core Python, you may wish to
provide paths to non-standard places to look for the Python help files,
library files, etc.  When registering win32com, you should pass paths
specific to win32com.

See also the "regcheck.py" utility which will check and dump the contents
of the registry.
"""

examples="""\
Examples:
"regsetup c:\\wierd\\spot\\1 c:\\wierd\\spot\\2"
Attempts to setup the core Python.  Looks in some standard places,
as well as the 2 wierd spots to locate the core Python files (eg, Python.exe,
python14.dll, the standard library and Win32 Extensions.

"regsetup --win32com"
Attempts to register win32com.  No options are passed, so this is only
likely to succeed if win32com is already successfully registered, or the
win32com directory is current.  If neither of these are true, you should pass
the path to the win32com directory.

"regsetup -a myappname . .\subdir"
Registers a new Pythonpath entry named myappname, with "C:\\I\\AM\\HERE" and
"C:\\I\\AM\\HERE\subdir" added to the path (ie, all args are converted to
absolute paths)

"regsetup -c c:\\my\\python\\files"
Unconditionally add "c:\\my\\python\\files" to the 'core' Python path.

"regsetup -m some.pyd \\windows\\system"
Register the module some.pyd in \\windows\\system as a registered
module.  This will allow some.pyd to be imported, even though the
windows system directory is not (usually!) on the Python Path.

"regsetup --umodule some"
Unregister the module "some".  This means normal import rules then apply
for that module.
"""

if __name__=='__main__':
	if len(sys.argv)>1 and sys.argv[1] in ['/?','-?','-help','-h']:
		print usage
	elif len(sys.argv)==1 or not sys.argv[1][0] in ['/','-']:
		# No args, or useful args.
		searchPath = sys.path[:]
		for arg in sys.argv[1:]:
			searchPath.append(arg)
		# Good chance we are being run from the "regsetup.py" directory.
		# Typically this will be "\somewhere\win32\lib" and the "somewhere"
		# should also be searched.
		searchPath.append("..\\..")
		print "Attempting to setup/repair the Python core"
		
		SetupCore(searchPath)
		RegisterShellInfo(searchPath)	
		# Check the registry.
		print "Registration complete - checking the registry..."
		import regcheck
		regcheck.CheckRegistry()
	else:
		searchPaths = []
		import getopt, string
		opts, args = getopt.getopt(sys.argv[1:], 'p:a:m:c', 
			['pythonwin','unpythonwin','win32com','shell','upackage=','uapp=','umodule=','description','examples'])
		for arg in args:
			searchPaths.append(arg)
		for o,a in opts:
			if o=='--description':
				print description
			if o=='--examples':
				print examples
			if o=='--shell':
				print "Registering the Python core."
				RegisterShellInfo(searchPaths)
			if o=='--pythonwin':
				print "Registering Pythonwin"
				RegisterPythonwin(searchPaths)
			if o=='--win32com':
				print "Registering win32com"
				RegisterWin32com(searchPaths)
			if o=='--unpythonwin':
				print "Unregistering Pythonwin"
				UnregisterPythonwin()
			if o=='-m':
				import os
				print "Registering module",a
				FindRegisterModule(os.path.splitext(a)[0],a, searchPaths)
			if o=='--umodule':
				import os, regutil
				print "Unregistering module",a
				regutil.UnregisterModule(os.path.splitext(a)[0])
			if o=='-p':
				print "Registering package", a
				FindRegisterPackage(a,None,searchPaths)
			if o in ['--upackage', '--uapp']:
				import regutil
				print "Unregistering application/package", a
				regutil.UnregisterNamedPath(a)
			if o=='-a':
				import regutil
				path = string.join(searchPaths,";")
				print "Registering application", a,"to path",path
				regutil.RegisterNamedPath(a,path)
			if o=='-c':
				if not len(searchPaths):
					raise error, "-c option must provide at least one additional path"
				import win32api, regutil
				currentPaths = string.split(regutil.GetRegisteredNamedPath(None),";")
				oldLen = len(currentPaths)
				for newPath in searchPaths:
					if newPath not in currentPaths:
						currentPaths.append(newPath)
				if len(currentPaths)<>oldLen:
					print "Registering %d new core paths" % (len(currentPaths)-oldLen)
					regutil.RegisterNamedPath(None,string.join(currentPaths,";"))
				else:
					print "All specified paths are already registered."
