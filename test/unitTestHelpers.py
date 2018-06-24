"""
.. module:: unitTestHelpers
   :synopsis: helper functions for the unit tests
 
.. moduleauthor:: Andre Lessa <lessa.a.p@gmail.com>
.. moduleauthor:: Wolfgang Waltenberger <wolfgang.waltenberger@gmail.com>
 
"""

import unum
 
def equalObjs(obj1,obj2,allowedDiff,ignore=[], where=None ):
    """
    Compare two objects.
    The numerical values are compared up to the precision defined by allowedDiff.
 
    :param obj1: First python object to be compared
    :param obj2: Second python object to be compared
    :param allowedDiff: Allowed % difference between two numerical values
    :param ignore: List of keys to be ignored
    :param where: keep track of where we are, for easier debugging.
    :return: True/False
    """
    if type(obj1) in [ float, int ] and type ( obj2) in [ float, int ]:
        obj1,obj2=float(obj1),float(obj2)
 
    if type(obj1) != type(obj2):
        logger.warning("Data types differ (%s,%s)" %(type(obj1),type(obj2)))
        return False
 
    if isinstance(obj1,unum.Unum):
        if obj1 == obj2:
            return True
        diff = 2.*abs(obj1-obj2)/abs(obj1+obj2)
        return diff.asNumber() < allowedDiff
    elif isinstance(obj1,float):
        if obj1 == obj2:
            return True
        diff = 2.*abs(obj1-obj2)/abs(obj1+obj2)
        return diff < allowedDiff
    elif isinstance(obj1,str):
        return obj1 == obj2
    elif isinstance(obj1,dict):
        for key in obj1:
            if key in ignore: continue
            if not key in obj2:
                logger.warning("Key %s missing" %key)
                return False
            if not equalObjs(obj1[key],obj2[key],allowedDiff, ignore=ignore, where=key ):
                logger.warning('Objects differ in %s:\n   %s\n and\n   %s' %(where, str(obj1[key]),str(obj2[key])))
                #s1,s2 = str(obj1[key]),str(obj2[key]) 
                #if False: # len(s1) + len(s2) > 200:
                #    logger.warning ( "The values are too long to print." )
                #else:
                #    logger.warning( 'The values are: >>%s<< (this run) versus >>%s<< (default)'%\
                #                ( s1[:20],s2[:20] ) )
                return False
    elif isinstance(obj1,list):
        if len(obj1) != len(obj2):
            logger.warning('Lists differ in length:\n   %i (this run)\n and\n   %i (default)' %\
                                (len(obj1),len(obj2)))
            return False
        for ival,val in enumerate(obj1):
            if not equalObjs(val,obj2[ival],allowedDiff):
                logger.warning('Lists differ:\n   %s (this run)\n and\n   %s (default)' %\
                                (str(val),str(obj2[ival])))
                return False
    else:
        return obj1 == obj2
 
    return True
 
 
