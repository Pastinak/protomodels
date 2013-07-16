#!/usr/bin/env python

"""
.. module:: ClusterTools
   :synopsis: methods that deal with clustering masses and finding average masses

.. moduleauthor:: Andre Lessa <lessa.a.p@gmail.com>
.. moduleauthor:: Wolfgang Waltenberger <wolfgang.waltenberger@gmail.com>

"""

CMdic={} # This stores a dictionary to relate the weight labels to their respective sqrts values ( '7 TeV (NLL)' : 7 TeV, '8 TeV (LO)' : 8 TeV, etc)

def DoCluster(objlist,Distfunc,dmin):
  """Cluster algorithm (generic for any type of object, as long as the distance function is given) 
     :returns: FIXME
  """
  from Tools.PhysicsUnits import addunit
  import copy
  MD = []
#Compute distance matrix
  for i in range(len(objlist)):
    line = []
    for j in range(len(objlist)):
      if j >= i:
        line.append(Distfunc(objlist[i],objlist[j]))
      else:
        line.append(addunit(0.,'GeV'))
    MD.append(line)

  for i in range(len(objlist)):
    for j in range(len(objlist)):
      if j < i: MD[i][j] = MD[j][i]

#Begin clustering
  ClusterList = []
  for i in range(len(objlist)):
    cluster = set([])
    for j in range(len(objlist)):
      if MD[i][j] == None: continue
      if MD[i][j] <= dmin: cluster.add(j)
    if not cluster in ClusterList: ClusterList.append(cluster)   #Zero level clusters (individual masses)


  FinalCluster = []
  newClusters = [0]
  while len(newClusters) > 0:
    newClusters = []
    for cluster in ClusterList:
      split = False
      if len(cluster) > 2:
        for i in cluster:
          ClDist = ClusterDist(set([i]),cluster,MD)
          if  ClDist == None or ClDist > dmin:
            newcluster = copy.deepcopy(cluster)
            newcluster.remove(i)
            split = True
            if not newcluster in newClusters:
              newClusters.append(newcluster)

      if not split and not cluster in FinalCluster: FinalCluster.append(cluster)

    ClusterList = newClusters
    if len(ClusterList) > 2000:  #Check for oversized list of cluster (too time consuming)
      print "DoCluster: Error clustering. ClusterList >",len(ClusterList)
      return None


#Clean up clusters
  FinalCluster = FinalCluster + ClusterList
  i = 0
  for i in range(len(FinalCluster)):
    clusterA = FinalCluster[i]
    for j in range(len(FinalCluster)):
      clusterB = FinalCluster[j]
      if i != j and clusterB.issubset(clusterA):
        FinalCluster[j] = set([])

  while FinalCluster.count(set([])) > 0: FinalCluster.remove(set([]))

  return FinalCluster

def GoodMass(mass,Distfunc,dmin):
  """Test if a mass array is "good"
     = have similar branch masses if branch topologies are equal
     = have similar mother and LSP masses if branch topologies are different
     If it is, return an equivalent array with equal masses (= mass avg)"""

  if mass[0] == mass[1]: return mass
  if len(mass[0]) == len(mass[1]):
    mass1 = [mass[0],mass[0]]
    mass2 = [mass[1],mass[1]]
    MD = Distfunc(mass1,mass2)
    if MD == None or MD > dmin:
      return False
    else:
      return MassAvg([mass1,mass2],"harmonic")
  else:
    mass1 = mass
    mass2 = mass
    mass1[1][0] = mass1[0][0]   #Force mothers and daughters to be equal in each branch
    mass1[1][len(mass1)-1] = mass1[0][len(mass1)-1]
    mass2[0][0] = mass2[1][0]
    mass2[0][len(mass2)-1] = mass2[1][len(mass2)-1]
    MD = Distfunc(mass1,mass2)
    if MD == None or MD > dmin:
      return False
    else:
      return MassAvg([mass1,mass2],"harmonic")

def MassAvg(equivin, method = "mean"):
  """For a list of equivalent masses, compute an average mass (or mass array)
     using the defined method.
     :param method: the method employed: "harmonic" = harmonic means, "mean" = algebaric (standard) mean

     :returns: the average mass
  """
  import numpy
  from Tools.PhysicsUnits import rmvunit

  N = len(equivin)
  if N == 0:
    print "MassAvg: Empty array"
    return False
  if N == 1: return equivin[0]

  if type(equivin[0]) != type(list()):
    equivinBr = [equivin]
#In case the input has 2 branches of different sizes, average
#each one individually
  elif len(equivin[0]) == 2 and type(equivin[0][0]) == type(list()):
    if len(equivin[0][0]) != len(equivin[0][1]):
      equivinBr = [[],[]]
      for mass in equivin:
        equivinBr[0].append(mass[0])
        equivinBr[1].append(mass[1])
    else:
      equivinBr = [equivin]

  massout = []
  for ib in range(len(equivinBr)):
    equivmasses = numpy.array(equivinBr[ib])  #Generate numpy array

#Sanity checks:
    for mass in equivmasses.flat:
      if rmvunit(mass,'GeV') == 0.:
        print "MassAvg: Zero mass!"
        return False
      if rmvunit(mass,'GeV') < 0.:
        print "MassAvg: Negative mass!",mass
        return False

    if method == "mean":
      massavg = equivmasses[0]
    elif method == "harmonic":
      massavg = 1./equivmasses[0]
    else:
      print "MassAvg: Unknown method"
      return False

    for imass in range(1,N):
      mass = equivmasses[imass]
      if mass.shape != massavg.shape:    #Sanity check
        print "MassAvg: Wrong input"
        return False
      if method == "mean":
        massavg = massavg + mass
      elif method == "harmonic":
        massavg = massavg + 1./mass

    if method == "mean":
      massavg = massavg/float(N)
    elif method == "harmonic":
      massavg = float(N)/massavg

    if massavg.shape != equivmasses[0].shape:
      print "MassAvg: Error computing average"
      return False

    massout.append(massavg.tolist())

  if len(massout) == 1:
    return massout[0]
  else:
    return massout

def sumweights(wlist):
  """Sum a list of weights"""
  from Tools.PhysicsUnits import addunit
  neweight = {}
  for wk in wlist[0].keys(): neweight[wk]=addunit(0.,'fb')# .update({wk : addunit(0.,'fb')})
  for wk in wlist[0].keys():
    wsum = addunit(0.,'fb')
    for weight in wlist: wsum = wsum + weight[wk]
    # neweight.update({wk : wsum})
    neweight[wk]=wsum
  return neweight


def ClusterDist(cluster1,cluster2,MD):
  """Definition of distance two clusters, MD = square matrix of distances"""
  d = 0.
  if type(cluster1) != type(set()) or type(cluster2) != type(set()):
    print "ClusterDist: unknown format input"
    return False

  for ic in cluster1:
    for jc in cluster2:
      if MD[ic][jc] == None: return None
      d = max(d,MD[ic][jc])
  return d

