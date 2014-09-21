"""
.. module:: theory.branch
   :synopsis: Module holding the branch class and methods.
        
.. moduleauthor:: Andre Lessa <lessa.a.p@gmail.com>
        
"""

from smodels.theory.particleNames import simParticles, elementsInStr
from smodels.tools.physicsUnits import addunit
import logging
from smodels.particles import rEven, ptcDic

logger = logging.getLogger(__name__)


class Branch(object):
    """
    An instance of this class represents a branch.
    
    A branch-element can be constructed from a string (e.g., ('[b,b],[W]').
    
    """
    def __init__(self, info=None):
        """
        Initializes the branch. If info is defined, tries to generate
        the branch using it. info must be a string description of the branch.
        """
        self.masses = []
        self.particles = []
        self.momID = None
        self.daughterID = None
        self.maxWeight = None
        if type(info) == type(str()):
            branch = elementsInStr(info)
            if not branch or len(branch) > 1:
                logger.error("Wrong input string " + info)
                import sys
                sys.exit()
            else:
                branch = branch[0]
                vertices = elementsInStr(branch[1:-1])
                for vertex in vertices:
                    ptcs = vertex[1:-1].split(',')
                    # Syntax check:
                    for ptc in ptcs:
                        if not ptc in rEven.values() \
                                and not ptc in ptcDic:
                            logger.error("Unknown particle " + ptc)
                            import sys
                            sys.exit()
                    self.particles.append(ptcs)


    def __str__(self):
        """
        Create the canonical SModels description of the Branch.        
        """
        st = str(self.particles).replace("'", "")
        st = st.replace(" ", "")
        return st


    def __eq__(self, other):
        """
        Use the branch isEqual function to compare two branches.
        """
        return self.isEqual(other)


    def __ne__(self, other):
        """
        Use the branch isEqual function to compare two branches.
        """
        return not self.isEqual(other)


    def isEqual(self, other, useDict=True):
        """ Compare the branch with other. If particles are similar
        and masses are equal, return True. Otherwise, return False.        
        """
        if type (other) != type(self):
            return False
        if not simParticles(self.particles, other.particles, useDict):
            return False
        if self.masses != other.masses:
            return False
        return True


    def copy(self):
        """
        Generate an independent copy of self.
        
        Faster than deepcopy.
        
        """
        newbranch = Branch()
        newbranch.masses = self.masses[:]
        newbranch.particles = self.particles[:]
        newbranch.momID = self.momID
        newbranch.daughterID = self.daughterID
        if not self.maxWeight is None:
            newbranch.maxWeight = self.maxWeight.copy()
        return newbranch


    def getLength(self):
        """
        Returns the branch length (= number of R-odd masses).
        
        """
        return len(self.masses)


    def _addDecay(self, br, massDictionary):
        """
        Generate a new branch adding a 1-step cascade decay.
        
        This is described by the br object, with particle masses given by
        massDictionary.
        
        """
        newBranch = self.copy()
        newparticles = []
        newmass = []
        newBranch.daughterID = None

        for partID in br.ids:
            # Add R-even particles to final state
            if partID in rEven:
                newparticles.append(rEven[partID])
            else:
                # Add masses of non R-even particles to mass vector
                newmass.append(massDictionary[partID])
                newBranch.daughterID = partID

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
        
        """
        if not self.daughterID:
            # Do nothing if there is no R-odd daughter (relevant for RPV decays
            # of the LSP)
            return []
        # List of possible decays (brs) for R-odd daughter in branch
        brs = brDictionary[self.daughterID]
        if len(brs) == 0:
            # Daughter is stable, there are no new branches
            return []
        newBranches = []
        for br in brs:
            # Generate a new branch for each possible decay
            newBranches.append(self._addDecay(br, massDictionary))
        return newBranches


def decayBranches(branchList, brDictionary, massDictionary,
                  sigcut=addunit(0., 'fb')):
    """
    Decay all branches from branchList until all R-odd particles have decayed.
    
    :param branchList: list of Branch() objects containing the initial mothers
    :param brDictionary: branching ratio dictionary for all particles appearing
                         in the decays
    :param massDictionary: mass dictionary for all particles appearing in the
                           decays
    :param sigcut: minimum sigma*BR to be generated, by default sigcut = 0.
                   (all branches are kept)
    
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
    return finalBranchList
