/* File : win32pipe.i */
// @doc

%module win32pipe // An interface to the win32 pipe API's

%{
  /* Used to validate access modes in win32pipe.win32pipe() */
#include "fcntl.h"
%}

%include "typemaps.i"
%include "pywin32.i"

%init %{
	// All errors raised by this module are of this type.
	Py_INCREF(PyWinExc_ApiError);
	PyDict_SetItemString(d, "error", PyWinExc_ApiError);
%}

%{
extern PyObject *PyPopen(PyObject *self, PyObject  *args);
extern PyObject *PyPopen2(PyObject *self, PyObject  *args);
extern PyObject *PyPopen3(PyObject *self, PyObject  *args);
extern PyObject *PyPopen4(PyObject *self, PyObject  *args);

%}
// @pymeth popen|Version of popen that works in a GUI
%native(popen) PyPopen;

// @pymeth popen2|Variation on popen - returns 2 pipes
%native(popen2) PyPopen2;

// @pymeth popen3|Variation on popen - returns 3 pipes
%native(popen3) PyPopen3;

// @pymeth popen4|Like popen2, but stdout/err are combined.
%native(popen4) PyPopen4;

// @pymeth GetNamedPipeHandleState|Returns the state of a named pipe.
%native(GetNamedPipeHandleState) MyGetNamedPipeHandleState;

// @pymeth ConnectNamedPipe|Connects to a named pipe
%native(ConnectNamedPipe) MyConnectNamedPipe;

// @pymeth CallNamedPipe|Calls a named pipe
%native(CallNamedPipe) MyCallNamedPipe;

%name(CreatePipe)
PyObject *MyCreatePipe(SECURITY_ATTRIBUTES *INPUT, DWORD nSize);
PyObject *FdCreatePipe(SECURITY_ATTRIBUTES *INPUT, DWORD nSize, int mode);


#define PIPE_ACCESS_DUPLEX PIPE_ACCESS_DUPLEX
#define PIPE_ACCESS_INBOUND PIPE_ACCESS_INBOUND
#define PIPE_ACCESS_OUTBOUND PIPE_ACCESS_OUTBOUND
#define PIPE_TYPE_BYTE PIPE_TYPE_BYTE
#define PIPE_TYPE_MESSAGE PIPE_TYPE_MESSAGE
#define PIPE_READMODE_BYTE PIPE_READMODE_BYTE
#define PIPE_READMODE_MESSAGE PIPE_READMODE_MESSAGE
#define PIPE_WAIT PIPE_WAIT
#define PIPE_NOWAIT PIPE_NOWAIT
#define NMPWAIT_NOWAIT NMPWAIT_NOWAIT
#define NMPWAIT_WAIT_FOREVER NMPWAIT_WAIT_FOREVER
#define NMPWAIT_USE_DEFAULT_WAIT NMPWAIT_USE_DEFAULT_WAIT
#define PIPE_UNLIMITED_INSTANCES PIPE_UNLIMITED_INSTANCES

%{
// @pyswig (int, int, int/None, int/None, <o PyUnicode>|GetNamedPipeHandleState|Determines the state of the named pipe.
PyObject *MyGetNamedPipeHandleState(PyObject *self, PyObject *args)
{
	HANDLE hNamedPipe;
	PyObject *obhNamedPipe;
	unsigned long State;
	unsigned long CurInstances;
	unsigned long MaxCollectionCount;
	unsigned long CollectDataTimeout;
	unsigned long *pMaxCollectionCount;
	unsigned long *pCollectDataTimeout;
	PyObject *obMaxCollectionCount;
	PyObject *obCollectDataTimeout;

	BOOL getCollectData = FALSE;
	// @pyparm <o PyHANDLE>|hPipe||The handle to the pipe.
	// @pyparm int|bGetCollectionData|0|Determines of the collection data should be returned.  If not, None is returned in their place.

	if (!PyArg_ParseTuple(args, "O|i:GetNamedPipeHandleState", &obhNamedPipe, &getCollectData))
		return NULL;
	if (!PyWinObject_AsHANDLE(obhNamedPipe, &hNamedPipe))
		return NULL;
	TCHAR buf[512];
	if (getCollectData) {
		pMaxCollectionCount = &MaxCollectionCount;
		pCollectDataTimeout = &CollectDataTimeout;
	} else
		pMaxCollectionCount = pCollectDataTimeout = NULL;

	if (!GetNamedPipeHandleState(hNamedPipe, &State, &CurInstances, pMaxCollectionCount, pCollectDataTimeout, buf, 512))
		return PyWin_SetAPIError("GetNamedPipeHandleState");
	PyObject *obName = PyWinObject_FromTCHAR(buf);
	if (getCollectData) {
		obMaxCollectionCount = PyInt_FromLong(MaxCollectionCount);
		obCollectDataTimeout = PyInt_FromLong(CollectDataTimeout);
	} else {
		obMaxCollectionCount = Py_None; Py_INCREF(Py_None);
		obCollectDataTimeout = Py_None; Py_INCREF(Py_None);
	}
	PyObject *rc = Py_BuildValue("iiOOO", State, CurInstances, obMaxCollectionCount, obCollectDataTimeout, obName);
	Py_DECREF(obMaxCollectionCount);
	Py_DECREF(obCollectDataTimeout);
	Py_DECREF(obName);
	return rc;
}

// @pyswig int|ConnectNamedPipe|Connects to a named pipe
// @comm The result is the HRESULT from the underlying function.
// If an overlapped object is passed, the result may be ERROR_IO_PENDING or ERROR_PIPE_CONNECTED.
PyObject *MyConnectNamedPipe(PyObject *self, PyObject *args)
{
	HANDLE hNamedPipe;
	PyObject *obhNamedPipe;
	OVERLAPPED *pOverlapped;
	PyObject *obOverlapped = NULL;
	// @pyparm <o PyHANDLE>|hPipe||The handle to the pipe.
	// @pyparm <o PyOVERLAPPED>|overlapped|None|An overlapped object to use, else None
	if (!PyArg_ParseTuple(args, "O|O:ConnectNamedPipe", &obhNamedPipe, &obOverlapped))
		return NULL;
	if (!PyWinObject_AsHANDLE(obhNamedPipe, &hNamedPipe))
		return NULL;
	if (obOverlapped==NULL)
		pOverlapped = NULL;
	else {
		if (!PyWinObject_AsOVERLAPPED(obOverlapped, &pOverlapped))
			return NULL;
	}
	BOOL ok;
    Py_BEGIN_ALLOW_THREADS
	ok = ConnectNamedPipe(hNamedPipe, pOverlapped);
    Py_END_ALLOW_THREADS
	DWORD rc = GetLastError();
	// These error conditions are documented as "acceptable" - ie,
	// the function has still worked.
	if (rc!= 0 && rc != ERROR_IO_PENDING && rc != ERROR_PIPE_CONNECTED)
		return PyWin_SetAPIError("ConnectNamedPipe");
	return PyInt_FromLong(rc);
}

// @pyswig string|CallNamedPipe|Opens and performs a transaction on a named pipe.
PyObject *MyCallNamedPipe(PyObject *self, PyObject *args)
{
	PyObject *obPipeName;
	char *data;
	int dataSize;
	DWORD timeOut;
	int readBufSize;
	TCHAR *szPipeName;
	if (!PyArg_ParseTuple(args, "Os#il:CallNamedPipe", 
		&obPipeName, // @pyparm <o PyUNICODE>|pipeName||The name of the pipe.
		&data, &dataSize, // @pyparm string|data||The data to write.
		&readBufSize, // @pyparm int|bufSize||The size of the result buffer to allocate for the read.
		&timeOut)) // @pyparm int|timeOut||The timeout
		return NULL;

	if (!PyWinObject_AsTCHAR(obPipeName, &szPipeName))
		return NULL;

	void *readBuf = malloc(readBufSize);

	DWORD numRead = 0;
	BOOL ok;
    Py_BEGIN_ALLOW_THREADS
	ok = CallNamedPipe(szPipeName, (void *)data, dataSize, readBuf, readBufSize, &numRead, timeOut);
    Py_END_ALLOW_THREADS
	if (!ok) {
		PyWinObject_FreeTCHAR(szPipeName);
		free(readBuf);
		return PyWin_SetAPIError("CallNamedPipe");
	}
	PyObject *rc = PyString_FromStringAndSize( (char *)readBuf, numRead);
	PyWinObject_FreeTCHAR(szPipeName);
	free(readBuf);
	return rc;
}

// @pyswig (<o PyHANDLE>, <o PyHANDLE>)|CreatePipe|Creates an anonymous pipe, and returns handles to the read and write ends of the pipe
PyObject *MyCreatePipe(
		       SECURITY_ATTRIBUTES *INPUT, // @pyparm <o PySECURITY_ATTRIBUTES>|sa||
		       DWORD nSize // @pyparm int|nSize||
		       )
{
  HANDLE hReadPipe;		// variable for read handle 
  HANDLE hWritePipe;		// variable for write handle 
  BOOL   ok;			// did CreatePipe work?

  ok = CreatePipe(&hReadPipe, &hWritePipe, INPUT, nSize);
  if (!ok)
    return PyWin_SetAPIError("CreatePipe");

  PyObject *read_obj = PyWinObject_FromHANDLE(hReadPipe);
  PyObject *write_obj = PyWinObject_FromHANDLE(hWritePipe);
  PyObject *result = Py_BuildValue("OO", read_obj, write_obj);
  Py_DECREF(read_obj);
  Py_DECREF(write_obj);
  return result;
}

// @pyswig (int, int)|FdCreatePipe|As CreatePipe but returns file descriptors
PyObject *FdCreatePipe(
		    SECURITY_ATTRIBUTES *INPUT, // @pyparm <o PySECURITY_ATTRIBUTES>|sa||
		    DWORD nSize, // @pyparm int|nSize||
		    int mode // @pyparm int|mode||
		    )
{
  HANDLE hReadPipe;		// variable for read handle 
  HANDLE hWritePipe;		// variable for write handle 
  BOOL   ok;			// did CreatePipe work?
  if (mode != _O_TEXT && mode != _O_BINARY)
    {
      PyErr_SetString(PyExc_ValueError, "mode must be O_TEXT or O_BINARY");
      return NULL;
    }

  ok = CreatePipe(&hReadPipe, &hWritePipe, INPUT, nSize);
  if (!ok)
    return PyWin_SetAPIError("CreatePipe");

  int read_fd = _open_osfhandle ((long) hReadPipe, mode);
  int write_fd = _open_osfhandle ((long) hWritePipe, mode);
  PyObject *result = Py_BuildValue("ii", read_fd, write_fd);
  return result;
}

%}

// @pyswig <o PyHANDLE>|CreateNamedPipe|Creates an instance of a named pipe and returns a handle for subsequent pipe operations
PyHANDLE CreateNamedPipe( 
	TCHAR *lpName,	// @pyparm <o PyUnicode>|pipeName||The name of the pipe
	unsigned long dwOpenMode, // @pyparm int|openMode||OpenMode of the pipe
	unsigned long dwPipeMode, // @pyparm int|pipeMode||
	unsigned long nMaxInstances, // @pyparm int|nMaxInstances||
	unsigned long nOutBufferSize,// @pyparm int|nOutBufferSize||
	unsigned long nInBufferSize, // @pyparm int|nInBufferSize||
	unsigned long nDefaultTimeOut, // @pyparm int|nDefaultTimeOut||
	SECURITY_ATTRIBUTES *INPUT // @pyparm <o PySECURITY_ATTRIBUTES>|sa||
);
// @pyswig |DisconnectNamedPipe|Disconnects the server end of a named pipe instance from a client process. 
BOOLAPI DisconnectNamedPipe(
	PyHANDLE hFile // @pyparm <o PyHANDLE>|hFile||The handle to the pipe to disconnect.
);

// @pyswig int|GetOverlappedResult|Determines the result of the most recent call with an OVERLAPPED object.
// @comm The result is the number of bytes transferred.  The overlapped object's attributes will be changed during this call.
BOOLAPI GetOverlappedResult(
	PyHANDLE hFile, 	// @pyparm <o PyHANDLE>|hFile||The handle to the pipe or file
	OVERLAPPED *lpOverlapped, // @pyparm <o PyOVERLAPPED>|overlapped||The overlapped object to check.
	unsigned long *OUTPUT, // lpNumberOfBytesTransferred
	BOOL bWait	// @pyparm int|bWait||Indicates if the function should wait for data to become available.
);

 
