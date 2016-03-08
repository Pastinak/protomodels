"""
.. module:: theory.branch
   :synopsis: Module holding the branch class and methods.
        
.. moduleauthor:: Andre Lessa <lessa.a.p@gmail.com>
        
"""

from smodels.theory.particleNames import simParticles, elementsInStr
from smodels.tools.physicsUnits import fb
import logging
from smodels.particles import rEven, ptcDic
import sys
from smodels.theory.exceptions import SModelSTheoryError as SModelSError

logger = logging.getLogger(__name__)


class Branch(object):
    """
    An instance of this class represents a branch.    
    A branch-element can be constructed from a string (e.g., ('[b,b],[W]').
    
    :ivar masses: list of masses for the intermediate states
    :ivar particles: list of particles (strings) for the final states
    :ivar PIDs: a list of the pdg numbers of the intermediate states appearing in the branch.
                If the branch represents more than one possible pdg list, PIDs will correspond
                to a nested list (PIDs = [[pid1,pid2,...],[pidA,pidB,...])
    :ivar maxWeight: weight of the branch (XSection object)
    """
    def __init__(self, info=None):
        """
        Initializes the branch. If info is defined, tries to generate
        the branch using it.
        
        :parameter info: string describing the branch in bracket notation
                         (e.g. [[e+],[jet]])
        """
        self.masses = []
        self.particles = []
        self.PIDs = []
        self.maxWeight = None
        self.vertnumb = None
        self.vertparts = None
        if type(info) == type(str()):
            branch = elementsInStr(info)
            if not branch or len(branch) > 1:
                logger.error("Wrong input string " + info)
                raise SModelSError()
            else:
                branch = branch[0]
                vertices = elementsInStr(branch[1:-1])
                for vertex in vertices:
                    ptcs = vertex[1:-1].split(',')
                    # Syntax check:
                    for ptc in ptcs:
                        if not ptc in rEven.values() \
                                and not ptc in ptcDic:
                            logger.error("Unknown particle. Add " + ptc + " to smodels/particle.py")
                            raise SModelSError()
                    self.particles.append(ptcs)
            self.vertnumb = len(self.particles)
            self.vertparts = [len(v) for v in self.particles]


    def __str__(self):
        """
        Create the branch bracket notation string, e.g. [[e+],[jet]].
        
        :returns: string representation of the branch (in bracket notation)    
        """
        st = str(self.particles).replace("'", "")
        st = st.replace(" ", "")
        return st


    def __eq__(self, other):
        """
        Check if branches are equal, allowing for inclusive particle labels.
        
        :parameter other: branch to be compared (Branch object)
        :returns: True if branches are equal (particles and masses match); False otherwise.
        """
        
        return self.isEqual(other)


    def __ne__(self, other):
        """
        Check if branches are different, allowing for inclusive particle labels.
        
        :parameter other: branch to be compared (Branch object)
        :returns: False if branches are equal (particles and masses match); True otherwise.
        """
        
        return not self.isEqual(other)


    def setInfo(self):
        """
        Defines the number of vertices (vertnumb) and number of
        particles in each vertex (vertpats) properties, if they have not
        been defined yet.
        """

        self.vertnumb = len(self.particles)
        self.vertparts = [len(v) for v in self.particles]


    def particlesMatch(self, other, useDict=True):
        """
        Compare two Branches for matching particles (same as isEqual, but ignores
        mass differences)
        
        :parameter other: branch to be compared (Branch object)
        :parameter useDict: if True, allow for inclusive particle labels
        :returns: True if branches are equal (particles and masses match); False otherwise.              
        """
        
        if type (other) != type(self):
            return False
        
        #Make sure number of vertices and particles have been defined
        self.setInfo()
        other.setInfo()
        if self.vertnumb != other.vertnumb:
            return False
        if self.vertparts != other.vertparts:
            return False

        for iv,vertex in enumerate(self.particles):
            if not simParticles(vertex,other.particles[iv]):
                return False                        
        return True


    def isEqual(self, other, useDict=True):
        """
        Compares two branches. If particles are similar
        and masses are equal, return True. Otherwise, return False.  
        
        :parameter other: branch to be compared (Branch object)
        :parameter useDict: if True, allow for inclusive particle labels
        :returns: True if branches are equal (particles and masses match); False otherwise.              
        """
        
        if not self.particlesMatch(other, useDict):
            return False
        elif self.masses != other.masses:
            return False
        
        return True    

    def copy(self):
        """
        Generate an independent copy of self.        
        Faster than deepcopy.
        
        :returns: Branch object
        """
        newbranch = Branch()
        newbranch.masses = self.masses[:]
        newbranch.particles = self.particles[:]
        newbranch.PIDs = []
        self.setInfo()
        newbranch.vertnumb = self.vertnumb
        newbranch.vertparts = self.vertparts[:]
        for pidList in self.PIDs:
            newbranch.PIDs.append(pidList[:])
        if not self.maxWeight is None:
            newbranch.maxWeight = self.maxWeight.copy()
        return newbranch


    def getLength(self):
        """
        Returns the branch length (number of R-odd particles).
        
        :returns: length of branch (number of R-odd particles)
        """
        
        return len(self.masses)


    def _addDecay(self, br, massDictionary):
        """
        Generate a new branch adding a 1-step cascade decay        
        This is described by the br object, with particle masses given by
        massDictionary.
        
        :parameter br: branching ratio object (see pyslha). Contains information about the decay.
        :parameter massDictionary: dictionary containing the masses for all intermediate states.
        :returns: extended branch (Branch object). False if there was an error.
        """
        newBranch = self.copy()
        newparticles = []
        newmass = []
        
        if len(self.PIDs) != 1:
            logger.error("During decay the branch should \
                            not have multiple PID lists!")
            return False   

        for partID in br.ids:
            # Add R-even particles to final state
            if partID in rEven:
                newparticles.append(rEven[partID])
            else:
                # Add masses of non R-even particles to mass vector
                newmass.append(massDictionary[partID])
                newBranch.PIDs[0].append(partID)

        if len(newmass) > 1:
            logger.warning("Multiple R-odd particles in the final state: " +
                           str(br.ids))
            return False

        if newparticles:
            newBranch.particles.append(newparticles)
        if newmass:
            newBranch.masses.append(newmass[0])
        if not self.maxWeight is None:
            newBranch.maxWeight = self.maxWeight * br.br

        return newBranch


    def decayDaughter(self, brDictionary, massDictionary):
        """
        Generate a list of all new branches generated by the 1-step cascade
        decay of the current branch daughter.
        
        :parameter brDictionary: dictionary with the decay information
                                 for all intermediate states (values are br objects, see pyslha)
        :parameter massDictionary: dictionary containing the masses for all intermediate states.
        :returns: list of extended branches (Branch objects). Empty list if daughter is stable or
                  if daughterID was not defined.
        """

        if len(self.PIDs) != 1:
            logger.error("Can not decay branch with multiple PID lists")
            return False                
        if not self.PIDs[0][-1]:
            # Do nothing if there is no R-odd daughter (relevant for RPV decays
            # of the LSP)
            return []
        #If decay table is not defined, assume daughter is stable:
        if not self.PIDs[0][-1] in brDictionary: return []
        # List of possible decays (brs) for R-odd daughter in branch        
        brs = brDictionary[self.PIDs[0][-1]]
        if len(brs) == 0:
            # Daughter is stable, there are no new branches
            return []
        newBranches = []
        for br in brs:
            if not br.br: continue  #Skip zero BRs
            # Generate a new branch for each possible decay
            newBranches.append(self._addDecay(br, massDictionary))
        return newBranches


def decayBranches(branchList, brDictionary, massDictionary,
                  sigcut=0. *fb):
    """
    Decay all branches from branchList until all unstable intermediate states have decayed.
    
    :parameter branchList: list of Branch() objects containing the initial mothers
    :parameter brDictionary: dictionary with the decay information
                                 for all intermediate states (values are br objects, see pyslha)
    :parameter massDictionary: dictionary containing the masses for all intermediate states.
    :parameter sigcut: minimum sigma*BR to be generated, by default sigcut = 0.
                   (all branches are kept)
    :returns: list of branches (Branch objects)    
    """

    finalBranchList = []
    while branchList:
        # Store branches after adding one step cascade decay
        newBranchList = []
        for inbranch in branchList:
            if sigcut.asNumber() > 0. and inbranch.maxWeight < sigcut:
                # Remove the branches above sigcut and with length > topmax
                continue
            # Add all possible decays of the R-odd daughter to the original
            # branch (if any)
            newBranches = inbranch.decayDaughter(brDictionary, massDictionary)
            if newBranches:
                # New branches were generated, add them for next iteration
                newBranchList.extend(newBranches)
            else:
                # All particles have already decayed, store final branch
                finalBranchList.append(inbranch)
        # Use new branches (if any) for next iteration step
        branchList = newBranchList
        
    #Sort list by initial branch PID:
    finalBranchList = sorted(finalBranchList, key=lambda branch: branch.PIDs)
    return finalBranchList
