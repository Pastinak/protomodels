#!/usr/bin/env python3

"""
.. module:: tools.modelTester
   :synopsis: Functions to test (a set of) points, handling decomposition,
              result and coverage checks, parallelisation.

.. moduleauthor:: Ursula Laa <ursula.laa@lpsc.in2p3.fr>
.. moduleauthor:: Wolfgang Waltenberger <wolfgang.waltenberger@gmail.com>

"""

from smodels.tools import ioObjects
from smodels.tools import coverage, runtime
from smodels.theory import decomposer
from smodels.theory import theoryPrediction
from smodels.share.models.SMparticles import SMList
from smodels.theory.model import Model
from smodels.theory.theoryPrediction import theoryPredictionsFor
from smodels.theory.exceptions import SModelSTheoryError as SModelSError
from smodels.tools import crashReport, timeOut
from smodels.tools.printer import MPrinter
import multiprocessing
import os
import sys
import time
try:
    from ConfigParser import SafeConfigParser
except ImportError as e:
    from configparser import ConfigParser
from smodels.tools.physicsUnits import GeV, fb, TeV
from smodels.experiment.exceptions import DatabaseNotFoundException
from smodels.experiment.databaseObj import Database, ExpResultList
from smodels.tools.smodelsLogging import logger
import logging

def testPoint(inputFile, outputDir, parser, databaseVersion, listOfExpRes):
    """
    Test model point defined in input file (running decomposition, check
    results, test coverage)

    :parameter inputFile: path to input file
    :parameter outputDir: path to directory where output is be stored
    :parameter parser: ConfigParser storing information from parameters file
    :parameter databaseVersion: Database version (printed to output file)
    :parameter listOfExpRes: list of ExpResult objects to be considered
    :returns: output of printers
    """

    """Get run parameters and options from the parser"""
    sigmacut = parser.getfloat("parameters", "sigmacut") * fb
    minmassgap = parser.getfloat("parameters", "minmassgap") * GeV


    """Setup output printers"""
    masterPrinter = MPrinter()
    masterPrinter.setPrinterOptions(parser)
    masterPrinter.setOutPutFiles(os.path.join(outputDir, os.path.basename(inputFile)))

    """ Add list of analyses loaded to printer"""
    masterPrinter.addObj(ExpResultList(listOfExpRes))

    """Check input file for errors"""
    inputStatus = ioObjects.FileStatus()
    if parser.getboolean("options", "checkInput"):
        inputStatus.checkFile(inputFile, sigmacut)
    """Initialize output status and exit if there were errors in the input"""
    outputStatus = ioObjects.OutputStatus(inputStatus.status, inputFile,
            dict(parser.items("parameters")), databaseVersion)
    masterPrinter.addObj(outputStatus)
    if outputStatus.status < 0:
        return masterPrinter.flush()
    
    """
    Load the input model
    ==================== 
    """    
    try:
        """
        Load the input model and  update it with the information from the input file
        """
        from smodels.particlesLoader import BSMList
        model = Model(inputFile=inputFile, BSMparticles=BSMList, SMparticles=SMList)
        model.updateParticles()
    except SModelSError as e:
        print("Exception %s %s" %(e, type(e)))
        """ Update status to fail, print error message and exit """
        outputStatus.updateStatus(-1)
        return masterPrinter.flush()        


    """
    Decompose input model
    =====================
    """

    try:

        """ Decompose the input model, store the output elements in smstoplist """
        smstoplist = decomposer.decompose(model, sigmacut,
                    doCompress=parser.getboolean("options", "doCompress"),
                    doInvisible=parser.getboolean("options", "doInvisible"),
                    minmassgap=minmassgap)
    except SModelSError as e:
        print("Exception %s %s" %(e, type(e)))
        """ Update status to fail, print error message and exit """
        outputStatus.updateStatus(-1)
        return masterPrinter.flush()

    """ Print Decomposition output.
        If no topologies with sigma > sigmacut are found, update status, write
        output file, stop running """
    if not smstoplist:
        outputStatus.updateStatus(-3)
        return masterPrinter.flush()

    masterPrinter.addObj(smstoplist)


    """
    Compute theory predictions
    ====================================================
    """

    """ Get theory prediction for each analysis and print basic output """
    allPredictions = []
    combineResults=False
    try:
        combineResults = parser.getboolean("options","combineSRs")
    except Exception as e:
        pass
    for expResult in listOfExpRes:
        theorypredictions = theoryPredictionsFor(expResult, smstoplist,
                    useBestDataset=True, combinedResults=combineResults,
                    marginalize=False)
        if not theorypredictions:
            continue
        allPredictions += theorypredictions._theoryPredictions

    """Compute chi-square and likelihood"""
    if parser.getboolean("options","computeStatistics"):
        for theoPred in allPredictions:
            theoPred.computeStatistics()

    """ Define theory predictions list that collects all theoryPrediction objects which satisfy max condition."""
    maxcond = parser.getfloat("parameters", "maxcond")           
    theoryPredictions = theoryPrediction.TheoryPredictionList(allPredictions, maxcond)

    if len(theoryPredictions) != 0:
        outputStatus.updateStatus(1)
        masterPrinter.addObj(theoryPredictions)
    else:
        outputStatus.updateStatus(0) # no results after enforcing maxcond

    if parser.getboolean("options", "testCoverage"):
        """ Testing coverage of model point, add results to the output file """
        if  parser.has_option("options","coverageSqrts"):
            sqrts = parser.getfloat("options", "coverageSqrts")*TeV
        else:
            sqrts = None
        uncovered = coverage.Uncovered(smstoplist,sigmacut,sqrts=sqrts)
        masterPrinter.addObj(uncovered)

    return masterPrinter.flush()

def runSingleFile(inputFile, outputDir, parser, databaseVersion, listOfExpRes,
                    timeout, development, parameterFile):
    """
    Call testPoint on inputFile, write crash report in case of problems

    :parameter inputFile: path to input file
    :parameter outputDir: path to directory where output is be stored
    :parameter parser: ConfigParser storing information from parameter.ini file
    :parameter databaseVersion: Database version (printed to output file)
    :parameter listOfExpRes: list of ExpResult objects to be considered
    :parameter crashReport: if True, write crash report in case of problems
    :param timeout: set a timeout for one model point (0 means no timeout)
    :returns: output of printers
    """
    try:
        with timeOut.Timeout(timeout):
            return testPoint(inputFile, outputDir, parser, databaseVersion,
                             listOfExpRes)
    except Exception as e:
        crashReportFacility = crashReport.CrashReport()

        if development:
            print(crashReport.createStackTrace())
            raise e
        else:
            print(crashReport.createStackTrace())
            crashReportFacility.createCrashReportFile(inputFile, parameterFile)
            print(crashReportFacility.createUnknownErrorMessage())
    return None

def _cleanList(fileList, inDir):
    """ clean up list of files """
    cleanedList = []
    for f in fileList:
        tmp = os.path.join(inDir, f)
        if not os.path.isfile(tmp):
            logger.info("%s does not exist or is not a file. Skipping it." % tmp)
            continue
        cleanedList.append(tmp)
    return cleanedList

def _determineNCPus(cpus_wanted, n_files):
    """ determine the number of CPUs that are to be used.
    :param cpus_wanted: number of CPUs specified in parameter file
    :param n_files: number of files to be run on
    :returns: number of CPUs that are to be used
    """
    ncpusAll = runtime.nCPUs()
    # ncpus = parser.getint("parameters", "ncpus")
    ncpus = cpus_wanted
    if ncpus == 0 or ncpus < -1:
        logger.error("Weird number of ncpus given in ini file: %d" % ncpus)
        sys.exit()
    if ncpus == -1 or ncpus > ncpusAll: ncpus = ncpusAll
    ncpus = min(n_files, ncpus)
    return ncpus

def testPoints(fileList, inDir, outputDir, parser, databaseVersion,
                 listOfExpRes, timeout, development, parameterFile):
    """
    Loop over all input files in fileList with testPoint, using ncpus CPUs
    defined in parser

    :param fileList: list of input files to be tested
    :param inDir: path to directory where input files are stored
    :param outputDir: path to directory where output is stored
    :param parser: ConfigParser storing information from parameter.ini file
    :param databaseVersion: Database version (printed to output files)
    :param listOfExpRes: list of ExpResult objects to be considered
    :param timeout: set a timeout for one model point (0 means no timeout)
    :param development: turn on development mode (e.g. no crash report)
    :param parameterFile: parameter file, for crash reports
    :returns: printer(s) output, if not run in parallel mode
    """
    
    t0 = time.time()
    if len(fileList) == 0:
        logger.error("no files given.")
        return None

    cleanedList = _cleanList(fileList, inDir)
    ncpus = _determineNCPus(parser.getint("parameters", "ncpus"), len(cleanedList))
    
    if len(cleanedList) == 0:
        logger.error("No valid input files found")
        return None
    elif len(cleanedList) == 1:        
        logger.info("Running SModelS for a single file")
        runSingleFile(cleanedList[0], outputDir, parser, 
                        databaseVersion, listOfExpRes, timeout, 
                        development, parameterFile)
    else:
        logger.info("Running SModelS for %i files with %i processes. Messages will be redirected to smodels.log" 
                    %(len(cleanedList),ncpus))
        for hdlr in logger.handlers[:]:
            logger.removeHandler(hdlr)
        fileLog = logging.FileHandler('./smodels.log')
        logger.addHandler(fileLog)
    
        pool = multiprocessing.Pool(processes=ncpus)
        children = []
        for inputFile in cleanedList:
            p = pool.apply_async(runSingleFile, args=(inputFile, outputDir, parser, 
                                                      databaseVersion, listOfExpRes, timeout, 
                                                  development, parameterFile,))
            children.append(p)
    
        for i,p in enumerate(children):
            out = p.get()
            logger.debug("child %i terminated: %s" %(i,out))
            if float(i)/len(children)
        logger.debug("All children terminated")
        
    logger.info("Done in %3.2f min"%((time.time()-t0)/60.))
    
    return None

def checkForSemicolon(strng, section, var):
    if ";" in strng:
        logger.warning("A semicolon(;) has been found in [%s] %s, in your config file. If this was meant as comment, then please a space before it." %(section, var))

def loadDatabase(parser, db):
    """
    Load database

    :parameter parser: ConfigParser with path to database
    :parameter db: binary database object. If None, then database is loaded,
                   according to databasePath. If True, then database is loaded,
                   and text mode is forced.
    :returns: database object, database version

    """
    try:
        dp = parser.get("path", "databasePath")
        logger.error("``[path] databasePath'' in ini file is deprecated; " \
           "use ``[database] path'' instead.(See e.g. smodels/etc/parameters_default.ini)")
        parser.set("database", "path", dp)
    except Exception as e:
        ## path.databasePath not set. This is good.
        pass
    try:
        database = db
        # logger.error("database=db: %s" % database)
        if database in [ None, True ]:
            databasePath = parser.get("database", "path")
            checkForSemicolon(databasePath, "database", "path")
            discard_zeroes = True
            try:
                discard_zeroes = parser.getboolean("database", "discardZeroes")
            except Exception as e: ## too complicated to be more specific
                logger.info("database:discardZeroes is not given in config file. Defaulting to 'True'.")
            force_load=None
            if database == True: force_load="txt"
            if os.path.isfile(databasePath):
                force_load="pcl"
            database = Database(databasePath, force_load=force_load, \
                                 discard_zeroes = discard_zeroes)
        databaseVersion = database.databaseVersion
    except DatabaseNotFoundException:
        logger.error("Database not found in ``%s''" % os.path.realpath(databasePath))
        sys.exit()
    return database, databaseVersion

def loadDatabaseResults(parser, database):
    """
    Load database entries specified in parser

    :parameter parser: ConfigParser, containing analysis and txnames selection
    :parameter database: Database object
    :returns: List of experimental results

    """
    """ In case that a list of analyses or txnames are given, retrieve list """
    tmp = parser.get("database", "analyses").split(",")
    analyses = [ x.strip() for x in tmp ]
    tmp_tx = parser.get("database", "txnames").split(",")
    txnames = [ x.strip() for x in tmp_tx ]
    if parser.get("database", "dataselector") == "efficiencyMap":
        dataTypes = ['efficiencyMap']
        datasetIDs = ['all']
    elif parser.get("database", "dataselector") == "upperLimit":
        dataTypes = ['upperLimit']
        datasetIDs = ['all']
    else:
        dataTypes = ['all']
        tmp_dIDs = parser.get("database", "dataselector").split(",")
        datasetIDs = [ x.strip() for x in tmp_dIDs ]

    useSuperseded=False
    useNonValidated=False
    if parser.has_option("database","useSuperseded"):
        useSuperseded = parser.getboolean("database", "usesuperseded")
    if parser.has_option("database","useNonValidated"):
        useNonValidated = parser.getboolean("database", "usenonvalidated")
    if useSuperseded:
        logger.info('Including superseded results')
    if useNonValidated:
        logger.info('Including non-validated results')


    """ Load analyses """

    ret = database.getExpResults(analysisIDs=analyses, txnames=txnames,
                                 datasetIDs=datasetIDs, dataTypes=dataTypes,
                                 useSuperseded=useSuperseded, useNonValidated=useNonValidated)
    return ret

def getParameters(parameterFile):
    """
    Read parameter file, exit in case of errors

    :parameter parameterFile: Path to parameter File
    :returns: ConfigParser read from parameterFile

    """
    try:
        parser = ConfigParser(inline_comment_prefixes=(';',))
    except Exception as e:
        parser = SafeConfigParser()
    ret=parser.read(parameterFile)
    if ret == []:
        logger.error("No such file or directory: '%s'" % parameterFile)
        sys.exit()
    return parser

def getAllInputFiles(inFile):
    """
    Given inFile, return list of all input files

    :parameter inFile: Path to input file or directory containing input files
    :returns: List of all input files, and the directory name

    """
    if os.path.isdir(inFile):
        fileList = os.listdir(inFile)
        return fileList, inFile
    fileList = [ os.path.basename(inFile) ]
    return fileList, os.path.dirname(inFile)
