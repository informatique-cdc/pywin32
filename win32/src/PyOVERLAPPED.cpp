//
// @doc

#include "windows.h"
#include "Python.h"
#include "structmember.h"
#include "PyWinTypes.h"
#include "PyWinObjects.h"

// @pymethod <o PyOVERLAPPED>|pywintypes|OVERLAPPED|Creates a new OVERLAPPED object
PyObject *PyWinMethod_NewOVERLAPPED(PyObject *self, PyObject *args)
{
	if (!PyArg_ParseTuple(args, ":OVERLAPPED"))
		return NULL;
	return new PyOVERLAPPED();
}

// @object PyOVERLAPPED|A Python object, representing an overlapped structure
// @comm Typically you create a PyOVERLAPPED object, and set its hEvent property.
// The object can then be passed to any function which takes an OVERLAPPED object, and
// the object attributes will be automatically updated.
PYWINTYPES_EXPORT BOOL PyWinObject_AsOVERLAPPED(PyObject *ob, OVERLAPPED **ppOverlapped, BOOL bNoneOK /*= TRUE*/)
{
	if (bNoneOK && ob==Py_None) {
		*ppOverlapped = NULL;
	} else if (!PyOVERLAPPED_Check(ob)) {
		PyErr_SetString(PyExc_TypeError, "The object is not a PyOVERLAPPED object");
		return FALSE;
	} else {
		*ppOverlapped = ((PyOVERLAPPED *)ob)->GetOverlapped();
	}
	return TRUE;
}

PYWINTYPES_EXPORT PyObject *PyWinObject_FromOVERLAPPED(const OVERLAPPED *pOverlapped)
{
	if (pOverlapped==NULL) {
		Py_INCREF(Py_None);
		return Py_None;
	}
	PyObject *ret = new PyOVERLAPPED(pOverlapped);
	if(ret==NULL)
		PyErr_SetString(PyExc_MemoryError, "Allocating pOverlapped");
	return ret;
}

PYWINTYPES_EXPORT PyTypeObject PyOVERLAPPEDType =
{
	PyObject_HEAD_INIT(&PyType_Type)
	0,
	"PyOVERLAPPED",
	sizeof(PyOVERLAPPED),
	0,
	PyOVERLAPPED::deallocFunc,		/* tp_dealloc */
	0,		/* tp_print */
	PyOVERLAPPED::getattr,				/* tp_getattr */
	PyOVERLAPPED::setattr,				/* tp_setattr */
	// @pymeth __cmp__|Used when OVERLAPPED objects are compared.
	PyOVERLAPPED::compareFunc,	/* tp_compare */
	0,						/* tp_repr */
	0,						/* tp_as_number */
	0,	/* tp_as_sequence */
	0,						/* tp_as_mapping */
	0,
	0,						/* tp_call */
	0,		/* tp_str */
};

#define OFF(e) offsetof(PyOVERLAPPED, e)

/*static*/ struct memberlist PyOVERLAPPED::memberlist[] = {
	{"Internal",    T_INT,      OFF(m_overlapped.Internal)}, // @prop integer|Internal|Reserved for operating system use.
	{"InternalHigh",T_INT,      OFF(m_overlapped.InternalHigh)}, // @prop integer|InternalHigh|Reserved for operating system use.
	{"Offset",      T_INT,      OFF(m_overlapped.Offset)}, // @prop integer|Offset|Specifies a file position at which to start the transfer. The file position is a byte offset from the start of the file. The calling process sets this member before calling the ReadFile or WriteFile function. This member is ignored when reading from or writing to named pipes and communications devices.
	{"OffsetHigh",  T_INT,      OFF(m_overlapped.OffsetHigh)}, // @prop integer|OffsetHigh|Specifies the high word of the byte offset at which to start the transfer.
	{NULL}
};
// @prop integer/<o PyHANDLE>|hEvent|Identifies an event set to the signaled state when the transfer has been completed. The calling process sets this member before calling the <om win32file.ReadFile>, <om win32file.WriteFile>, <om win32pipe.ConnectNamedPipe>, or <om win32pipe.TransactNamedPipe> function.

PyOVERLAPPED::PyOVERLAPPED(void)
{
	ob_type = &PyOVERLAPPEDType;
	_Py_NewReference(this);
	memset(&m_overlapped, 0, sizeof(m_overlapped));
	m_obHandle = NULL;
}

PyOVERLAPPED::PyOVERLAPPED(const OVERLAPPED *pO)
{
	ob_type = &PyOVERLAPPEDType;
	_Py_NewReference(this);
	m_overlapped = *pO;
	m_obHandle = NULL;
}

PyOVERLAPPED::~PyOVERLAPPED(void)
{
	Py_XDECREF(m_obHandle);
}

int PyOVERLAPPED::compare(PyObject *ob)
{
	return memcmp(&m_overlapped, &((PyOVERLAPPED *)ob)->m_overlapped, sizeof(m_overlapped));
}

// @pymethod int|PyOVERLAPPED|__cmp__|Used when objects are compared.
int PyOVERLAPPED::compareFunc(PyObject *ob1, PyObject *ob2)
{
	return ((PyOVERLAPPED *)ob1)->compare(ob2);
}

PyObject *PyOVERLAPPED::getattr(PyObject *self, char *name)
{
/*	PyObject *res;

	res = findmethod(PyOVERLAPPED_methods, self, name);
	if (res != NULL)
		return res;
	PyErr_Clear();*/
	// @prop integer/<o PyHANDLE>|hEvent|Identifies an event set to the signaled state when the transfer has been completed. The calling process sets this member before calling the <om win32file.ReadFile>, <om win32file.WriteFile>, <om win32pipe.ConnectNamedPipe>, or <om win32pipe.TransactNamedPipe> function.
	if (strcmp("hEvent", name)==0) {
		PyOVERLAPPED *pO = (PyOVERLAPPED *)self;
		if (pO->m_obHandle) {
			Py_INCREF(pO->m_obHandle);
			return pO->m_obHandle;
		}
		return PyInt_FromLong((long)pO->m_overlapped.hEvent);
	}
	return PyMember_Get((char *)self, memberlist, name);
}

int PyOVERLAPPED::setattr(PyObject *self, char *name, PyObject *v)
{
	if (v == NULL) {
		PyErr_SetString(PyExc_AttributeError, "can't delete OVERLAPPED attributes");
		return -1;
	}
	if (strcmp("hEvent", name)==0) {
		PyOVERLAPPED *pO = (PyOVERLAPPED *)self;
		Py_XDECREF(pO->m_obHandle);
		pO->m_obHandle = NULL;
		if (PyHANDLE_Check(v)) {
			pO->m_obHandle = v;
			PyWinObject_AsHANDLE(v, &pO->m_overlapped.hEvent, FALSE);
			Py_INCREF(v);
		} else if (PyInt_Check(v)) {
			pO->m_overlapped.hEvent = (HANDLE)PyInt_AsLong(v);
		}
		return 0;
	}
	return PyMember_Set((char *)self, memberlist, name, v);
}

/*static*/ void PyOVERLAPPED::deallocFunc(PyObject *ob)
{
	delete (PyOVERLAPPED *)ob;
}

