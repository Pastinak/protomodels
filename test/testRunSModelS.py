#!/usr/bin/env python

"""
.. module:: testRunSModelS
   :synopsis: Tests runSModelS

.. moduleauthor:: Ursula Laa <Ursula.Laa@assoc.oeaw.ac.at>

"""

import sys
sys.path.insert(0,"../")
import unittest
import os
from smodels.installation import installDirectory
from smodels.tools import summaryReader
from runSModelS import main

class RunSModelSTest(unittest.TestCase):
    def main(self, filename ):
        a=sys.stdout
        sys.stdout = open ( "stdout.log", "w" )
        out = "%s/test/unitTestOutput.txt" % installDirectory()
        if os.path.exists ( out ): 
            os.unlink ( out )
        main(filename, 
             parameterFile="%s/test/testParameters.ini" %installDirectory(), 
             outputFile= out )
        outputfile = summaryReader.Summary(
                "%s/test/unitTestOutput.txt" % installDirectory())
        sys.stdout = a
        return outputfile

    def testGoodFile(self):

        filename = "%s/inputFiles/slha/gluino_squarks.slha" % (installDirectory() )
        outputfile = self.main(filename )
        sample = summaryReader.Summary(
                "%s/test/summary_default.txt" %installDirectory())
        self.assertEquals(sample, outputfile)

    def testBadFile(self):

        filename = "%s/inputFiles/slha/I_dont_exist.slha" % (installDirectory() )
        outputfile = self.main (filename ) 
        sample = summaryReader.Summary(
                "%s/test/summary_bad_default.txt" %installDirectory())
        self.assertEquals(sample, outputfile)

if __name__ == "__main__":
    unittest.main()
