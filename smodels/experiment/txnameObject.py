"""
.. module:: dataObjects
   :synopsis: Holds the classes and methods used to read and store the information in the
              txname.txt files. Also contains the interpolation methods

.. moduleauthor:: Veronika Magerl <v.magerl@gmx.at>
.. moduleauthor:: Andre Lessa <lessa.a.p@gmail.com>
.. moduleauthor:: Wolfgang Waltenberger <wolfgang.waltenberger@gmail.com>

"""

import logging,os,sys
from smodels.tools.physicsUnits import GeV, fb, TeV, pb
from smodels.theory.particleNames import elementsInStr
from smodels.tools.stringTools import concatenateLines
from smodels.theory.element import Element
from smodels.theory.topology import Topology
from smodels.experiment.exceptions import SModelSExperimentError as SModelSError
from smodels.theory.auxiliaryFunctions import _memoize
from scipy.interpolate import griddata
from scipy.linalg import svd
import numpy as np
import unum
import copy
import math

FORMAT = '%(levelname)s in %(module)s.%(funcName)s() in %(lineno)s: %(message)s'
logging.basicConfig(format=FORMAT)
logger = logging.getLogger(__name__)

logger.setLevel(level=logging.ERROR)


class TxName(object):
    """Holds the information related to one txname in the Txname.txt
    file (constraint, condition,...) as well as the data.
    """
    
    
    def __init__(self, path, infoObj):
        self.path = path
        self.globalInfo = infoObj
        self.txnameData = None
        self._elements = []
        self._topologies = []
        
        logger.debug('Creating object based on txname file: %s' %self.path)        
        #Open the info file and get the information:
        if not os.path.isfile(path):
            logger.error("Txname file %s not found" % path)
            raise SModelSError()
        txtFile = open(path,'r')
        txdata = txtFile.read()
        if not "txName" in txdata: raise TypeError
        if not 'upperLimits' in txdata and not 'efficiencyMap' in txdata:
            raise TypeError
        txfile = open(self.path)
        content = concatenateLines (  txfile.readlines() )
        txfile.close()
        
        #Get tags in info file:
        tags = [line.split(':', 1)[0].strip() for line in content]
        for i,tag in enumerate(tags):
            if not tag: continue
            line = content[i]
            value = line.split(':',1)[1].strip()            
            if tags.count(tag) == 1:
                if ';' in value: value = value.split(';')                
                if tag == 'upperLimits' or tag == 'efficiencyMap':
                    self.txnameData = TxNameData(value)
                else: self.addInfo(tag,value)
            else:
                logger.info("Ignoring unknown field %s found in file %s" % (tag, self.infopath))
                continue
        
        #Builds up a list of _elements appearing in constraints:        
        if hasattr(self,'constraint'):             
            self._elements = [Element(el) for el in elementsInStr(self.constraint)]
        if hasattr(self,'condition') and self.condition:
            conds = self.condition
            if not isinstance(conds,list): conds = [conds]
            for cond in conds:                
                for el in elementsInStr(cond):
                    if not el in self._elements: self._elements.append(Element(el))
        
        #Builds up a list of _topologies appearing in constraints:
        for el in self._elements:
            top = Topology(el)
            if not top in self._topologies: self._topologies.append(top)

        
    def __str__(self):
        return self.txName
        
    def addInfo(self,tag,value):
        """
        Adds the info field labeled by tag with value value to the object.
        :param tag: information label (string)
        :param value: value for the field in string format 
        """
        
        if tag == 'constraint' or tag == 'condition':
            if isinstance(value,list):
                value = [val.replace("'","") for val in value]
            else: value = value.replace("'","")            
        
        try:
            setattr(self,tag,eval(value, {'fb' : fb, 'pb' : pb, 'GeV' : GeV, 'TeV' : TeV}))
        except SyntaxError:          
            setattr(self,tag,value)
        except NameError:
            setattr(self,tag,value)
        except TypeError:
            setattr(self,tag,value)            
    
    def getInfo(self, infoLabel):
        """Returns the value of info field.
        :param infoLabel: label of the info field (string). It must be an attribute of
                          the TxNameInfo object
        """
        
        if hasattr(self,infoLabel): return getattr(self,infoLabel)
        else: return False
    
    def hasElementAs(self,element):
        """
        Check if the conditions or constraint in Txname contains the element.
        :param element: Element object
        :param order: If False will test both branch orderings.
        :return: A copy of the element on the correct branch ordering appearing
                in the Txname constraint or condition.
        """
        
        elementB = element.switchBranches()
        for el in self._elements:
            if element.particlesMatch(el,order=True):
                return element.copy()
            elif elementB.particlesMatch(el,order=True):
                return elementB
        return False
        

    def getEfficiencyFor(self,element):
        """
        For upper limit results, checks if the input element appears in the constraints
        and falls inside the upper limit grid.
        If it does, returns efficiency = 1, else returns efficiency = 0.
        For efficiency map results, checks if the input element appears in the constraints.
        and falls inside the efficiency map grid.
        If it does, returns the corresponding efficiency value, else returns efficiency = 0.
        
        :param element: Element object
        :return: efficiency (float)
        """
        
        #Check if the element appears in Txname:
        hasEl = self.hasElementAs(element)        
        if not hasEl: return 0.
        mass = hasEl.getMasses()
        val = self.txnameData.getValueFor(mass)
        if type(val) == type(fb):  
            return 1.  #The element has an UL, return 1        
        elif val is None or math.isnan(val):
            return 0.  #The element mass is outside the data grid
        elif type(val) == type(1.):
            return val  #The element has an eff
        else:
            logger.error("Unknown txnameData value: %s" % (str(type(val))))
            raise SModelSError()
            
class TxNameData(object):
    """Holds the data for the Txname object.  It holds Upper limit values or efficiencies."""
    
    def __init__(self,value,accept_errors_upto=.05):
        """
        
        :param value: data in string format
        :param accept_errors_upto: If None, do not allow extrapolations outside of convex hull.
            If float value given, allow that much relative uncertainty on the upper limit / efficiency
            when extrapolating outside convex hull.
            This method can be used to loosen the equal branches assumption.
        """

        self.accept_errors_upto=accept_errors_upto
        self.store_value = value
        self.data = None
        
    def loadData(self):
        """
        Uses the information in store_value to generate the data grid used for interpolation.
        """
        
        if type(self.store_value)==str:
            self.data = eval(self.store_value, {'fb' : fb, 'pb' : pb, 'GeV' : GeV, 'TeV' : TeV})
        else: ## the data can also be given as lists, for debugging
            self.data = self.store_value
        self.unit = 1.0 ## store the unit so that we can take arbitrary units for the "z" values.
                        ## default is unitless, which we use for efficiency maps
        if len(self.data) < 1 or len(self.data[0]) < 2:
                logger.error ( "input data not in correct format. expecting sth like " \
         " [ [ [[ 300.*GeV,100.*GeV], [ 300.*GeV,100.*GeV] ], 10.*fb ], ... ] for upper " \
         " limits or [ [ [[ 300.*GeV,100.*GeV], [ 300.*GeV,100.*GeV] ], .1 ], ... ] for efficiency maps" )
        if type(self.data[0][1])==unum.Unum:
            ## if its a unum, we store 1.0 * unit
            self.unit=self.data[0][1] / ( self.data[0][1].asNumber() )
       
        self.computeV()



    @_memoize       
    def getValueFor(self,massarray):
        """
        Interpolates the data and returns the UL or efficiency for the respective massarray
        :param massarray: mass array values (with units), i.e. [[100*GeV,10*GeV],[100*GeV,10*GeV]]
        """
        
        if not self.data: self.loadData()
        
        porig=self.flattenMassArray ( massarray ) ## flatten
        self.massarray = massarray
        if len(porig)!=self.full_dimensionality:
            logger.error ( "dimensional error. I have been asked to compare a %d-dimensional mass vector with " \
                    "%d-dimensional data!" % ( len(porig), self.full_dimensionality ) )
            return None
#         print "porig=",porig
        p= ( (np.matrix(porig)[0] - self.delta_x ) ).tolist()[0]
#         print "pafter=",p
        P=np.dot(p,self.V)  ## rotate
#         print "P=",P
        dp=self.countNonZeros ( P )
#         print 'Pp=',P[:self.dimensionality]

#         #Check which points are being used in interpolation
#         from scipy import spatial
#         delaun = spatial.Delaunay(self.Mp)
#         isimplex = delaun.find_simplex([P[:self.dimensionality] ])[0]
#         for ipt in delaun.simplices[isimplex]:
#             pt = self.Mp[ipt] + [0.]*(len(porig)-len(self.Mp[ipt]))
#             pt = np.dot(pt,np.transpose(self.V))
#             pt = pt + self.delta_x[0]
#             print pt,self.xsec[ipt]
        
        self.projected_value = griddata( self.Mp, self.xsec, [ P[:self.dimensionality] ], method="linear")[0]
        self.projected_value = float(self.projected_value)        
        if dp != self.dimensionality: ## we have data in different dimensions
            if self.accept_errors_upto == None:
                return None
            logger.debug ( "attempting to interpolate outside of convex hull (d=%d,dp=%d,masses=%s)" %
                     ( self.dimensionality, dp, str(massarray) ) )
            return self._interpolateOutsideConvexHull ( massarray )

        return self._returnProjectedValue()
        
    def flattenMassArray ( self, data ):
        """ flatten mass array and remove units """
        ret=[]
        for i in data:
            for j in i:
                ret.append ( j.asNumber(GeV) )
        return ret
    def _estimateExtrapolationError ( self, massarray ):
        """ when projecting a point p from n to the point P in m dimensions,
            we estimate the expected extrapolation error with the following strategy: 
            we compute the gradient at point P, and let alpha be the distance between
            p and P. We then walk one step of length alpha in the direction of the greatest ascent,
            and the opposite direction. Whichever relative change is greater is 
            reported as the expected extrapolation error.
        """
        #p=self.flattenMassArray ( massarray ) ## point p in n dimensions
        porig=self.flattenMassArray ( massarray ) ## flatten
        p= ( (np.matrix(porig)[0] - self.delta_x ) ).tolist()[0]
        P=np.dot(p,self.V)                    ## projected point p in n dimensions
        ## P[self.dimensionality:] is project point p in m dimensions
        # m=self.countNonZeros ( P ) ## dimensionality of input
        ## how far are we away from the "plane": distance alpha
        alpha = float ( np.sqrt ( np.dot ( P[self.dimensionality:], P[self.dimensionality:] ) ) )
        ## the value of the grid at the point projected to the "plane"
        ##projected_value=griddata( self.Mp, self.xsec, [ P[:self.dimensionality] ], method="linear")[0]
        
        ## compute gradient
        gradient=[]
        # print ",,,,,,,,,,,"
        for i in range ( self.dimensionality ):
            #print "i=",i
            P2=copy.deepcopy(P)
            #print "now adding alpha"
            P2[i]+=alpha
            #print "before griddata"
            g=float ( ( griddata( self.Mp, self.xsec, [ P2[:self.dimensionality]], method="linear")[0] - self.projected_value ) / alpha )
            #print "g=",g
            if math.isnan ( g ):
                ## if we cannot compute a gradient, we return nan
                return float("nan")
            gradient.append ( g )
        ## normalize gradient
        # print "gradient=",gradient
        C= float ( np.sqrt ( np.dot ( gradient, gradient ) ) )
        if C == 0.:
            ## zero gradient? we return 0.
            return 0.
        for i,j in enumerate(gradient):
            #print "i=",i
            #print "j=",j
            #print "C=",C
            #print "alpha=",alpha
            #print "gradient[i]=",gradient[i]
            #print "type(gradient[i])=",type(gradient[i])
            #print "type(C)=",type(C)
            #print "type(alpha)=",type(alpha)
            gradient[i]=gradient[i]/C*alpha
            #print "gradient after=",gradient[i]
        #print "^^^^^^"
        ## walk one alpha along gradient
        P3=copy.deepcopy(P)
        P4=copy.deepcopy(P)
        for i,j in enumerate(gradient):
            P3[i]+=gradient[i]
            P4[i]-=gradient[i]
        # print "projected value", projected_value
        ag=griddata( self.Mp, self.xsec, [ P3[:self.dimensionality] ], method="linear")[0]
        #print "along gradient", ag
        agm=griddata( self.Mp, self.xsec, [ P4[:self.dimensionality] ], method="linear")[0]
        #print "along negative gradient",agm
        dep=abs ( ag - self.projected_value) / self.projected_value
        dem=abs ( agm - self.projected_value ) / self.projected_value
        de=dep
        if dem > de: de=dem
        return de

    def _interpolateOutsideConvexHull ( self, massarray ):
        """ experimental routine, meant to check if we can interpolate outside convex hull """
        porig=self.flattenMassArray ( massarray ) ## flatten
        p= ( (np.matrix(porig)[0] - self.delta_x ) ).tolist()[0]
        P=np.dot(p,self.V)
        # projected_value=griddata( self.Mp, self.xsec, [ P[:self.dimensionality] ], method="linear")[0]
        de = self._estimateExtrapolationError ( massarray ) 
        if de < self.accept_errors_upto:
            return self._returnProjectedValue()
        if not math.isnan(de):
            logger.debug ( "Expected propagation error of %f too large to propagate." % de )
        return None

    def _returnProjectedValue ( self ):
        ## None is returned without units'
        if self.projected_value is None or math.isnan(self.projected_value):
            logger.debug ( "projected value is None. Projected point not in convex hull? original point=%s" % self.massarray )
            return None
        return self.projected_value * self.unit 

    def countNonZeros ( self, mp ):
        """ count the nonzeros in a vector """
        nz=0
        for i in mp:
            if abs(i)>10**-5:
                nz+=1
        return nz

    def computeV ( self ):
        """ compute rotation matrix V, rotate and truncate also
            'data' points and store in self.Mp """
        Morig=[]
        self.xsec=[]
     
        for x,y in self.data:
            self.xsec.append ( y / self.unit )
            xp = self.flattenMassArray ( x )
            Morig.append ( xp )
        aM=np.matrix ( Morig )
        MT=aM.T.tolist()
        self.delta_x = np.matrix ( [ sum (x)/len(Morig) for x in MT ] )[0]
        # self.delta_x = [1]*len(MT)
        #print "delta_x=",self.delta_x
        M = []
        #print "Morig=",Morig
        for Mx in Morig:
            M.append ( ( np.matrix ( Mx ) - self.delta_x ).tolist()[0] )
        #print "M=",M

        U,s,Vt=svd(M)
        V=Vt.T
        self.V=V
        Mp=[]

        ## the dimensionality of the whole mass space, disrespecting equal branches assumption
        self.full_dimensionality = len(xp)
        self.dimensionality=0
        for m in M:
            mp=np.dot(m,V)
            Mp.append ( mp )
            nz=self.countNonZeros ( mp )
            if nz>self.dimensionality:
                self.dimensionality=nz
        self.MpCut=[]
        MpCut=[]
        for i in Mp:
            MpCut.append ( i[:self.dimensionality].tolist() )
        self.Mp=MpCut ## also keep the rotated points, with truncated zeros
