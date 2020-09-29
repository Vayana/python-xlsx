# -*- coding: utf-8 -*-
__author__="Ståle Undheim <staale@staale.org>"

import re
import zipfile

from xml.dom import minidom

class DomZip(object):
    def __init__(self, filename):
        self.filename = filename

    def __getitem__(self, key):
        # @type ziphandle ZipFile
        try:
            ziphandle = zipfile.ZipFile(self.filename)
            dom = minidom.parseString(ziphandle.read(key))
            ziphandle.close()
            return dom
        except KeyError:
            return None

class Workbook(object):

    def __init__(self, filename):
        self.sheetsByName = {}
        self.sheetsByIndex = []
        self.filename = filename
        self.domzip = DomZip(filename)
        self.sharedStrings = SharedStrings(self)
        workbookDoc = self.domzip["xl/workbook.xml"]
        sheets = workbookDoc.firstChild.getElementsByTagName("sheets")[0]
        for sheetNode in sheets.childNodes:
            name = sheetNode._attrs["name"].value
            id = int(sheetNode._attrs["r:id"].value[3:])

            sheet = Sheet(self, id, name)
            self.sheetsByIndex.append(sheet)
            self.sheetsByName[name] = sheet
            assert sheet.name in self.sheetsByName
        
        self._has_signature = False
        self.signatureEntry = None
        try :
            self.signatureEntry = self.domzip["_xmlsignatures/sig1.xml"]
            if self.signatureEntry :
                self._has_signature = True
            else:
                self.signatureEntry = self.domzip["_xmlsignatures/sig2.xml"]
                if self.signatureEntry:
                    self._has_signature = True
        except KeyError as ex :
            pass
        
    def keys(self):
        return self.sheetsByName.keys()

    def __len__(self):
        return len(self.sheetsByName)

    def __getitem__(self, key):
        if isinstance(key, int):
            return self.sheetsByIndex[key]
        else:
            return self.sheetsByName[key]


    def has_signatures(self):
        return self._has_signature
    
    
    def verify_signatures(self):
        if self._has_signature :
            keyInfo = data = cert = None
            keyInfo = self.signatureEntry.firstChild.getElementsByTagName('KeyInfo')
            if keyInfo :
                data = keyInfo[0].getElementsByTagName('X509Data')
                if data :
                    cert = data[0].getElementsByTagName('X509Certificate')
                    
            if cert :
                from M2Crypto.X509 import load_cert_string
                x509_cert = load_cert_string(cert[0].nodeValue)
                print "X509 Certificate Created: {0}".format(x509_cert)
                if x509_cert : 
                    result = x509_cert.verify(pkey=None)
                    print "X509 Certificate Verified: {0}".format(result)
                    if result : 
                        return True
        return False
                

class SharedStrings(list):
    def __init__(self, workbook):
        sharedStringsDom = workbook.domzip["xl/sharedStrings.xml"]
        nodes = sharedStringsDom.firstChild.childNodes
        for text in [n.firstChild.firstChild for n in nodes]:
            self.append(text.nodeValue if text != None else "")

class Sheet(object):

    def __init__(self, workbook, id, name):
        self.workbook = workbook
        self.id = id
        self.name = name
        self.loaded = False
        self.addrPattern = re.compile("([a-zA-Z]*)(\d*)")
        self.cells = {}
        self.cols = {}
        self.rows = {}

    def __load(self):
        sheetDoc = self.workbook.domzip["xl/worksheets/sheet%d.xml"%self.id]
        sheetData = sheetDoc.firstChild.getElementsByTagName("sheetData")[0]
        # @type sheetData Element
        rows = {}
        columns = {}
        for rowNode in sheetData.childNodes:
            rowNum = rowNode.getAttribute("r")
            for columnNode in rowNode.childNodes:
                colType = columnNode.getAttribute("t")
                cellId = columnNode.getAttribute("r")
                colNum = cellId[:len(cellId)-len(rowNum)]
                formula = None
                if colType == "s":
                    stringIndex = columnNode.firstChild.firstChild.nodeValue
                    data = self.workbook.sharedStrings[int(stringIndex)]
                elif columnNode.firstChild:
                    data = getattr(columnNode.getElementsByTagName("v")[0].firstChild, "nodeValue", None)
                else:
                    data = ""
                if columnNode.getElementsByTagName("f"):
                    formula = getattr(columnNode.getElementsByTagName("f")[0].firstChild, "nodeValue", None)
                if not rowNum in rows:
                    rows[rowNum] = []
                if not colNum in columns:
                    columns[colNum] = []
                cell = Cell(rowNum, colNum, data,formula=formula)
                rows[rowNum].append(cell)
                columns[colNum].append(cell)
                self.cells[cellId] = cell
        for rowNum in rows.keys():
            self.rows[rowNum] = sorted(rows[rowNum])
        self.cols = columns
        self.loaded=True

    def __getitem__(self, key):
        if not self.loaded:
            self.__load()
        (column, row) = self.addrPattern.match(key).groups()
        if column and row:
            if not key in self.cells:
                return None
            return self.cells[key]
        if column:
            return self.cols[key]
        if row:
            return self.rows[key]

    def __iter__(self):
        if not self.loaded:
            self.__load()
        return self.cells.__iter__()

class Cell(object):
    def __init__(self, row, column, value, formula=None):
        self.row = int(row)
        self.column = column
        self.value = value
	self.formula = formula
        self.id = "%s%s"%(column, row)

    def __cmp__(self, other):
        if other.column == self.column:
            return self.row - other.row
        else:
            if self.column < other.column:
                return -1
            elif self.column > other.column:
                return 1
            else:
                return 0

    def __str__(self):
        return "<Cell [%s] : \"%s\" (%s)>"%(self.id, self.value, self.formula)
