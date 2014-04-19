"""
.. module:: theory.theoryPrediction
   :synopsis: Classes encapsulating the results of the computation of reference
   cross sections and related methods
        
.. moduleauthor:: Andre Lessa <lessa.a.p@gmail.com>
        
"""

import copy
from . import clusterTools
from . import crossSection
from . import element
import logging
from theory.particleNames import elementsInStr
from .auxiliaryFunctions import cSim
from .auxiliaryFunctions import cGtr
from .analysis import SRanalysis, ULanalysis

logger = logging.getLogger(__name__)


class TheoryPrediction(object):
    """
    Main class to store the results of the theory prediction for a given
    analysis.
    
    """    
    def __init__(self):
        self.analysis = None
        self.value = None
        self.conditions = None
        self.mass = None


def theoryPredictionFor(analysis, smsTopList, maxMassDist=0.2):
    """
    Main method to compute theory predictions. Collects the elements and
    efficiencies, combine the masses (if needed) and compute the conditions (if
    any). Returns a list of TheoryPrediction objects.
    
    """
    # Select elements constrained by analysis and apply efficiencies
    elements = getElementsFrom(smsTopList, analysis)   
    if len(elements) == 0:
        return None      
    # Combine masses
    clusters = combineElements(elements, analysis, maxDist=maxMassDist)    
    # Collect results and evaluate conditions:
    predictions = []
    for cluster in clusters:
        theoPrediction = TheoryPrediction()
        theoPrediction.value = cluster.getTotalXSec()
        theoPrediction.conditions = evalConditions(cluster, analysis)
        theoPrediction.mass = cluster.getAvgMass()
        predictions.append(theoPrediction)

    if len(predictions) == 0:
        return None
    return predictions


def getElementsFrom(smsTopList, analysis):
    """
    Loops over all elements in smsTopList and returns the elements which are
    constrained by the analysis (have efficiency != 0). The elements weights
    are multiplied by their respective efficiency and the cross-sections not
    matching the analysis sqrts are removed.
    
    """    
    elements = []
    for el in smsTopList.getElements():
        eff = analysis.getEfficiencyFor(el)
        if eff == 0.:
            continue
        element = el.copy()
        element.weight = crossSection.XSectionList()
        for xsec in el.weight:
            if xsec.info.sqrts == analysis.sqrts:
                element.weight.add(copy.deepcopy(xsec*eff))
        if len(element.weight) > 0:
            elements.append(element)
            
    return elements


def combineElements(elements, analysis, maxDist):
    """
    Combines elements according to the analysis type. If analysis = upper limit
    type, group elements into mass clusters. If analysis = signal region type,
    group all elements into a single cluster.
    
    """    
    if type(analysis) == type(SRanalysis()):
        clusters = [clusterTools.groupAll(elements)]
    elif type(analysis) == type(ULanalysis()):
        clusters = clusterTools.clusterElements(elements, analysis, maxDist)
    return clusters


def evalConditions(cluster, analysis):
    """
    If analysis type = upper limit, evaluates the analysis conditions inside an
    element cluster. If  analysis type = signal region, returns None.
    
    """        
    if type(analysis) == type(SRanalysis()):
        return None
    elif type(analysis) == type(ULanalysis()):
        if not analysis.conditions:
            return analysis.conditions
        conditions = {}
        # Loop over conditions        
        for cond in analysis.conditions:
            # Get elements appearing in conditions            
            condElements = [element.Element(elStr) \
                            for elStr in elementsInStr(cond)]
            newcond = cond
            for iel, el in enumerate(condElements):
                newcond = newcond.replace(str(el), "condElements["+str(iel)+
                                          "].weight")
                for el1 in cluster.elements:   
                    if el1.particlesMatch(el):                        
                        el.weight.combineWith(el1.weight)
                        
            
            if newcond.find("Cgtr") >= 0:
                newcond = newcond.replace("Cgtr", "cGtr")
                logger.warning(analysis.label + " using deprecated function "
                        "'Cgtr'. Auto-replacing with 'cGtr'.")
                
            if newcond.find("Csim") >= 0:
                newcond = newcond.replace("Csim", "cSim")
                logger.warning(analysis.label + " using deprecated function "
                        "'Csim'. Auto-replacing with 'cSim'.")
            
            conditions[cond] = eval(newcond)
            
        return conditions
