#!/usr/bin/env python

"""
.. module:: SLHATools
    :synopsis: A collection of tools needed for use and manipulation of SLHA files

.. moduleauthor:: Doris Proschofsky <Doris.Proschofsky@assoc.oeaw.ac.at>
.. moduleauthor:: Wolfgang Waltenberger <wolfgang.waltenberger@gmail.com>

"""

import pyslha2 as pyslha
import tempfile

def createSLHAFile(topo, masses = None, filename = None, branching = None, totalwidth = None):
   """ Creates an SLHA File for a certain Tx name and certain masses.

     :param topo: Tx name
     :type topo: str
     :param masses: a dictionary {pid: mass} where pid is an integer and mass is \
       an integer or float, all masses not included in the dictionary are set to 100000\
       (by default masses from initial SLHA file are taken).
     :param filename: by default a unique random filename will be generated.
     :type filenmame: str
     :param branching: a dictionary from a dictionary {pidmom: {"piddaugther1,piddaugther2,...": branching ratio, ...}...}\
       pidmom is an integer, pids of daugther particles are given as a string seperated by ',',\
       the branching ratio is a float or integer.
     :param totalwidth: a dictionary {pid: total width} where pid is an integer and total width is \
       an integer or float (by default total width from initial SLHA file is taken).
     :returns: the filename in string format
     """

   slha = pyslha.readSLHAFile('../slha/%s.slha' %topo)

   if masses:
      for pid in masses:
         slha[0]['MASS'].entries[pid] = masses[pid]

      for pid in slha[0]['MASS'].entries:
         if not masses.has_key(pid):
            slha[0]['MASS'].entries[pid] = 1.00000000e+05

   if branching:
      for pid in slha[1]:
         for k in range(len(slha[1][pid].decays)):
#            print 'deleting', slha[1][pid].decays[k]
            del slha[1][pid].decays[k]
      for pid in branching:
         if not slha[1].has_key(pid):
            slha[1][pid] = pyslha.Particle(pid)
            print "[SLHATools.py] Created new decay object for pid %d" %pid
#         print 'number of decays:', len(slha[1][pid].decays)
         for decay in branching[pid]:
            ids = decay.split(',')
            for i in ids:
               i.replace(' ','')
            slha[1][pid].add_decay(branching[pid][decay], len(ids), ids)

   if totalwidth:
      for pid in totalwidth:
         if not slha[1].has_key(pid):
            slha[1][pid] = pyslha.Particle(pid)
         slha[1][pid].totalwidth = totalwidth[pid]

   if filename:
      pyslha.writeSLHAFile(filename, slha[0], slha[1])
      return filename
   else:
      filename = tempfile.mkstemp()
      pyslha.writeSLHAFile(filename[1], slha[0], slha[1])
      return filename[1]

def writeXSecToSLHAFile( slhafile, nevts=10000,basedir=None, XsecsInfo=None, printLHE=True):
  """ calculates the production cross sections and writes it as XSECTION block in the SLHA file

      :param slhafile: path of SLHA file
      :type slhafile: str
      :param nevts: number of events generated by pythia, default 10000
      :type nevts: int
      :param XsecsInfo: optional information about cross-sections to be computed (sqrts, order and label) \
        If not defined and not found in CrossSection.XSectionInfo, use default values
      :type XsecsInfo: CrossSection.XSecInfoList
      :param printLHE: chooses if LHE event file is written to disk or not
  """
  import logging
  log = logging.getLogger(__name__)
  try:
    import tempfile
    import Theory.XSecComputer as XSEC
    import Tools.PhysicsUnits as UNIT

    fstate = "  " #final state, if necessary can be read out from DECAY block
    fstate = "# Nevts="+str(nevts) #additional information?

    fin = open(slhafile, 'r')
    lines = fin.readlines()
    fin.close()
    processesInFile = []
    for l in lines:
      if l.startswith("#") or len(l.replace('\n',''))<2: continue
      if 'XSECTION' in l:
        pids = [eval(l.split()[5]),eval(l.split()[6])]
        pids.sort()
        processesInFile.append(tuple(pids))

    if processesInFile: 
      log.warning ("XSecs found in file. Adding missing cross-sections")

    #computes production cross sections
    if XsecsInfo is None:
      try:
        XsecsInfo = CrossSection.XSectionInfo  #Check if cross-section information has been defined
      except:
        pass

    Tmp = tempfile.mkdtemp(dir=basedir)
    dic = XSEC.compute(nevts, slhafile, datadir = Tmp, basedir = basedir, XsecsInfo=XsecsInfo, printLHE=printLHE)
    XsecsInfo = dic.crossSectionsInfo()  #Get information about cross-sections

    #write production cross sections to XSECTION block in SLHA file.
    f = open(slhafile, 'a')
    XsecDic = dic.crossSections()
    if len(XsecDic.keys())==0:
      log.error ( "warning: I dont have keys in the cross section dictionary." )
      return
    allpids = XsecDic[XsecDic.keys()[0]].keys()
    for pids in allpids:
      newpids = list(pids)
      newpids.sort()
      newpids = tuple(newpids)
      if newpids in processesInFile: continue   #Ignore processes already present in file
      pid_xsecs = {}
  #Collect all cross-sections for the pid pair
      for xsec in XsecsInfo.xsecs:
        sqrtS = UNIT.rmvunit(xsec.sqrts,'TeV')
        cs_order = xsec.order
        cs = XsecDic[xsec.label][pids]
        cs = UNIT.rmvunit(cs,'fb')
        if not sqrtS in pid_xsecs.keys(): pid_xsecs[sqrtS] = []
        pid_xsecs[sqrtS].append([cs_order,cs])
  #Write cross-sections grouped by sqrtS:
      for sqrtS in pid_xsecs:
        if not sum([xsec[1] for xsec in pid_xsecs[sqrtS]]): continue  #Avoid blocks with no entries (zero xsecs)
        f.write("\nXSECTION  %f  %d  %d  %d  %d  %d  %s\n" %(sqrtS*1000, 2212, 2212, 2, pids[0], pids[1], fstate)) #sqrts in GeV
        for line_cs in pid_xsecs[sqrtS]:
          if not line_cs[1]: continue
          f.write("0  %d  0  0  0  0  %f SModelS 1.0\n" %(line_cs[0],line_cs[1]))


    f.close

    XSEC.clean(Tmp)
    return
  except Exception,e:
    log.error ( "could not write xsec: "+str(e) )

def num_in_base(val, base=62, min_digits=1, complement=False,
       digits="0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"):
    """Convert number to string in specified base
       If minimum number of digits is specified, pads result to at least
       that length.
       If complement is True, prints negative numbers in complement
       format based on the specified number of digits.
       Non-standard digits can be used. This can also allow bases greater
       than 36.
    """
    if base < 2: raise ValueError("Minimum base is 2")
    if base > len(digits): raise ValueError("Not enough digits for base")
    # Deal with negative numbers
    negative = val < 0
    val = abs(val)
    if complement:
        sign = ""
        max = base**min_digits
        if (val > max) or (not negative and val == max):
            raise ValueError("Value out of range for complemented format")
        if negative:
            val = (max - val)
    else:
        sign = "-" * negative
    # Calculate digits
    val_digits = []
    while val:
        val, digit = divmod(val, base)
        val_digits.append(digits[digit])
    result = "".join(reversed(val_digits))
    leading_digits = (digits[0] * (min_digits - len(result)))
    return sign + leading_digits + result

def uniqueName ( slhafile, blocks= { "MINPAR": [3], "EXTPAR": [ 31, 32, 33, 34, 35, 36, 41, 42, 43, 44, 45, 46, 47, 48, 49, 23, 26 ] } ):
  """ create a unique name for an slha file.

    :param blocks: dictionary of the slha blocks that are used; \
      values in dictionary are lists of indices, that are to be used, \
      or None if all indices are to be considered.
    :returns: unique name for slha file
  """

  ## for some values (e.g. angles, we want to multiply with a factor,
  ## before truncating them
  factors={}
  factors["MINPAR"]={ 3: 100. } ## tanbeta

  import logging
  log = logging.getLogger(__name__)
  name=""
  try:
    import pyslha2
    f=pyslha2.readSLHAFile ( slhafile, ignorenomass=True )
    if not f or len(f)==0:
      log.error ( "couldnt read %s." % ( slhafile ) )
      return None
    bnr=0 # block number
    for (key,block) in f[0].items():
      if not key in blocks.keys(): continue
      bnr+=1
      considerIndices=blocks[key]
      if considerIndices==None: # consider all indices, if none are given
        considerIndices=block.keys()
      for (index,value) in block.items():
        if index not in considerIndices: continue
        #print "block %s bnr %d, variable #%d %f" % ( block.name,bnr,index,value)
        if factors.has_key ( block.name ) and factors[block.name].has_key ( index ):
          value=value*factors[block.name][index]
        t=int(value)
        if t<0: t=1000000+abs(t)
        name+=str(t)

    ret=num_in_base ( long(name) )
    return ret
  except IOError,e:
    log.error ( "couldnt read %s: %s" % ( slhafile, e ) )
  return None

def xSecFromSLHAFile (  slhafile ):
  """ create the cross section info from the slha file.
    :returns: CrossSection object
  """
  import CrossSection
  XsecsInfo=None
  try:
     XsecsInfo = CrossSection.XSectionInfo 
  except:
     pass
  if not XsecsInfo: #If not, define default cross-sections
     XsecsInfo = CrossSection.XSecInfoList()
  from Tools.PhysicsUnits import addunit, rmvunit
  Xsec = {}
  slha = open(slhafile, 'r')
  lines = slha.readlines()
  slha.close()
  xsecblock = False
  for l in lines:
    if l.startswith("#") or len(l)<2: continue
    if 'XSECTION' in l:
      xsecblock = True
      sqrtS =  eval(l.split()[1])/1000.    #Values in the SLHA file are in GeV
      pids = (eval(l.split()[5]),eval(l.split()[6]))
      continue
    if not xsecblock: continue  #ignores other entries
    cs_order = eval(l.split()[1])
    cs = addunit(eval(l.split()[6]),'fb')
    wlabel = str(int(sqrtS))+' TeV'
    if cs_order == 0: wlabel += ' (LO)'
    elif cs_order == 1: wlabel += ' (NLO)'
    elif cs_order == 2: wlabel += ' (NLL)'
    else:
      print '[SLHADecomposer] unknown QCD order in XSECTION line', l
      return False
    xsInfo = CrossSection.SingleXSecInfo()
    xsInfo.sqrts = addunit(sqrtS,'TeV')
    xsInfo.order = cs_order
    xsInfo.label = wlabel
    if not wlabel in Xsec.keys():
      Xsec[wlabel] = {}
      # XsecsInfoFile.xsecs.append(xsInfo)
    Xsec[wlabel][pids] = cs
  return CrossSection.CrossSection ( { "Xsecdic": Xsec, "lhefile": None, "lhefiles": None, "XsecList": XsecsInfo } )
