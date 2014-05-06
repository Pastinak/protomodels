#!/usr/bin/env python

"""
.. module:: theory.Topology
   :synopsis: Provides a Topology class and a TopologyList collection type.
    
.. moduleauthor:: Wolfgang Magerl <wolfgang.magerl@gmail.com>
    
"""

from smodels.theory import crossSection
from smodels.theory.element import Element
from smodels.theory.printer import Printer
import logging

logger = logging.getLogger(__name__)


class Topology(object):
    """
    An instance of this class represents a topology.
    
    """
    def __init__(self, elements=None):
        """
        Constructor.
        
        If elements is defined, create the topology from it. If elements it is
        a list, all elements must share a common global topology.
        
        """
        self.vertnumb = []
        self.vertparts = []
        self.elementList = []

        if elements:
            if type(elements) == type(Element()):
                self.addElement(elements)
            elif type(elements) == type([]):
                for element in elements:
                    self.addElement(element)


    def __eq__(self, other):
        return self.isEqual(other)


    def __ne__(self, other):
        return not self.isEqual(other)


    def isEqual(self, other, order=False):
        """
        Check for equality of two topologies.
        
        If order == False and each topology has two branches, ignore branch
        ordering.
        
        :returns: True, if both topologies have the same number of vertices and
        particles.
        
        """
        if type(self) != type(other):
            return False
        if order or len(self.vertnumb) != 2 or len(other.vertnumb) != 2:
            if self.vertnumb != other.vertnumb:
                return False
            if self.vertparts != other.vertparts:
                return False
            return True
        else:
            x1 = [self.vertnumb[0], self.vertparts[0]]
            x2 = [self.vertnumb[1], self.vertparts[1]]
            xA = [other.vertnumb[0], other.vertparts[0]]
            xB = [other.vertnumb[1], other.vertparts[1]]
            if x1 == xA and x2 == xB:
                return True
            if x1 == xB and x2 == xA:
                return True
            return False


    def checkConsistency(self):
        """
        Perform a consistency check.
        
        The number of vertices and insertions per vertex is redundant
        information in a topology, so we can perform an internal consistency
        check.
        
        """
        for element in self.elementList:
            info = element.getEinfo()
            if self.vertnumb != info["vertnumb"]:
                logger.error("Inconsistent topology.")
                return False
            if self.vertparts != info["vertparts"]:
                logger.error("Inconsistent topology.")
                return False
        logger.info("Consistent topology.")
        return True


    def describe(self):
        """
        Create a detailed description of the topology.
        
        """
        ret = ("number of vertices: %s, number of vertex particles: %s, "
               "number of elements: %d" % \
               (self.vertnumb, self.vertparts, len(self.elementList)))
        return ret


    def getElements(self):
        """
        Get list of elements of the topology.
        
        """
        return self.elementList


    def addElement(self, newelement):
        """
        Add an Element object to the elementList.
        
        For all the pre-existing elements, which match the new element, add
        weight. If no pre-existing elements match the new one, add it to the
        list. If order == False, try both branch orderings.
        
        """
        # If the topology info has not been set yet, set it using the element
        # info
        if not self.vertparts:
            self.vertparts = newelement.getEinfo()["vertparts"]
        if not self.vertnumb:
            self.vertnumb = newelement.getEinfo()["vertnumb"]

        # Check if newelement matches the topology structure
        info = newelement.getEinfo()
        infoB = newelement.switchBranches().getEinfo()
        if info != self._getTinfo() and infoB != self._getTinfo():
            logger.warning('Element to be added does not match topology')
            return False


        added = False
        # Include element to elementList
        for element in self.elementList:
            if element == newelement:
                added = True
                element.weight.combineWith(newelement.weight)
                # When combining elements with different mothers, erase mother
                # info
                if element.getMothers() != newelement.getMothers():
                    element.branches[0].momID = None
                    element.branches[1].momID = None
                # When combining elements with different daughters, erase
                # daughter info
                if element.getDaughters() != newelement.getDaughters():
                    element.branches[0].daughterID = None
                    element.branches[1].daughterID = None


        if added:
            return True
        # If element has not been found add to list (OBS: if both branch
        # orderings are good, add the original one)
        # Check both branch orderings
        tryelements = [newelement, newelement.switchBranches()]
        for newel in tryelements:
            info = newel.getEinfo()
            if info["vertnumb"] != self.vertnumb or info["vertparts"] != \
                    self.vertparts:
                continue
            self.elementList.append(newel)
            return True

        # If element does not match topology info, return False
        return False


    def _getTinfo(self):
        """
        Return a dictionary with the topology number of vertices and vertparts.
        
        """
        return {'vertnumb' : self.vertnumb, 'vertparts' : self.vertparts}


    def getTotalWeight(self):
        """
        Return the sum of all elements weights.
        
        """
        if len(self.elementList) == 0:
            return None

        sumw = crossSection.XSectionList()
        for element in self.elementList:
            sumw.combineWith(element.weight)

        return sumw


class TopologyList(Printer):
    """
    An instance of this class represents an iterable collection of topologies.
    
    """
    def __init__(self, topologies=[]):
        """
        Add topologies sequentially, if provided.
        
        """
        super(TopologyList, self).__init__()
        self.topos = []
        for topo in topologies:
            self.add(topo)


    def __len__(self):
        return len(self.topos)


    def __getitem__(self, index):
        return self.topos[index]


    def __iter__(self):
        return iter(self.topos)


    def __str__(self):
        s = "TopologyList:\n"
        for topo in self.topos:
            s += str(topo) + "\n"
        return s


    def addList(self, parList):
        """
        TODO: write docstring
        
        """
        for topo in parList:
            self.add(topo)


    def describe(self):
        """
        TODO: write docstring
        
        """
        s = "TopologyList:\n"
        for topo in self.topos:
            s += str(topo) + "\n"
        return s


    def add(self, newTopology):
        """
        Check if elements in newTopology matches an entry in self.topos.
        
        If it does, add weight. If the same topology exists, but not the same
        element, add element. If neither element nor topology exist, add the
        new topology and all its elements.

        :type topo: Topology    
        
        """
        topmatch = False
        for itopo, topo in enumerate(self.topos):
            if topo == newTopology:
                topmatch = itopo
        # If no pre-existing topologies match, append it to list of topologies
        if topmatch is False:
            self.topos.append(newTopology)
        else:
            for newelement in newTopology.elementList:
                self.topos[topmatch].addElement(newelement)


    def getTotalWeight(self):
        """
        Return the sum of all topologies total weights.
        
        """
        sumw = crossSection.XSectionList()
        for topo in self:
            topoweight = topo.getTotalWeight()
            if topoweight:
                sumw.combineWith(topoweight)
        return sumw


    def getElements(self):
        """
        Return a list with all the elements in all the topologies.
        
        """
        elements = []
        for top in self.topos:
            elements.extend(top.elementList)
        return elements


    def prepareData(self):
        """
        Select data preparation method through dynamic binding.
        
        """
        return Printer.prepareTopologyListData(self)

