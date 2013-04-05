#!/usr/bin/python

""" centralized facility to access the results """

import SMSHelpers

def ResultsForSqrts ( sqrts ):
  import SMSResultsCollector
  """ If this is called, only results for a
      center of mass energy of sqrts will be retrieved.
      if sqrts is None or 0, then all results will be made available """
  if sqrts==7:
    SMSHelpers.runs=[ "2012", "2011" ]
    SMSResultsCollector.alldirectories=[ "2011", "2012" ]
    return
  if sqrts==8:
    SMSHelpers.runs=[ "8TeV", "ATLAS8TeV" ]
    SMSResultsCollector.alldirectories=[ "8TeV", "ATLAS8TeV" ]
    return
  if sqrts==0 or sqrts==None:
    SMSHelpers.runs=[ "8TeV", "2012", "2011", "ATLAS8TeV" ]
    SMSResultsCollector.alldirectories=[ "8TeV", "2012", "2011", "ATLAS8TeV" ]
    return
  print "[SMSResults.py:ResultsForSqrts] error: dont have any results for",sqrts

def verbosity ( level="error" ):
  if level=="error":
    SMSHelpers.verbose=False
  else:
    SMSHelpers.verbose=True

def getExclusion ( analysis, topo, run=None ):
  """ get the exclusions on the mother particles,
      for the summary plots """
  run=SMSHelpers.getRun ( analysis, run )
  ex=SMSHelpers.motherParticleExclusions ( analysis, run )
  if not ex.has_key ( topo ): return None
  return ex[topo]

def getExclusionLine(topo,ana,expected=False,plusminussigma=0,extendedinfo=True,xvalue=None,factor=1.0):
  """ get the exclusion line, as a TGraph """
  if xvalue==None: xvalue=''
  import SMSResultsCollector
  ex=SMSResultsCollector.exclusionline(topo,ana,xvalue,expected,plusminussigma)
  return ex

def getTopologies ( analysis, run=None ):
  """ return all topologies that this analysis has results for """
  run=SMSHelpers.getRun ( analysis, run )
  # we used the exclusion info to get the list
  x=SMSHelpers.motherParticleExclusions ( analysis, run )
  return x.keys()

def getRun ( analysis, run=None ):
  """ tell us, which run the results will be fetched for.
      None if the request cannot be met """
  run=SMSHelpers.getRun ( analysis, run )
  return run

def getAnalyses ( topo, run=None ):
  import os
  """ return all analyses that have results for topo """
  runs=SMSHelpers.runs
  if run: runs= [ run ]
  analyses={}
  for r in runs:
    ## so thats the runs I really have to think about
    dirs=os.listdir ( "%s/%s/" % ( SMSHelpers.Base, r ) )
    for ana in dirs:
      if os.path.exists ( "%s/%s/%s/info.txt" % ( SMSHelpers.Base, r, ana ) ):
        e=getExclusion ( ana, topo, r )
        if e: analyses[ana]=True

  return analyses.keys()

def getUpperLimit ( analysis, topo, mx=None, my=None, run=None, png=None ):
  """ get the upper limit for run/analysis/topo.
      return none if it doesnt exist.
      if mx and my are none, return the entire histogram,
      if mx and my are floats, return the upper limit at this
      point
      if png==True, return path of pngfile containing the histogram"""
  run=SMSHelpers.getRun ( analysis, run )
  histo=SMSHelpers.getUpperLimitHisto ( analysis, topo, run )
  if png==True:
    pngfile=SMSHelpers.getUpperLimitPng(analysis,topo,run)
    return pngfile
  if mx==None:
    return histo
  value=SMSHelpers.getUpperLimitAtPoint ( histo, mx, my )
  return value

def getEfficiency ( analysis, topo, mx=None, my=None, run=None ):
  """ get the efficiency for run/analysis/topo.
      return none if it doesnt exist.
      if mx and my are none, return the entire histogram,
      if mx and my are floats, return the upper limit at this
      point """
  run=SMSHelpers.getRun ( analysis, run )
  histo=SMSHelpers.getEfficiencyHisto ( analysis, topo, run )
  if mx==None:
    return histo
  value=SMSHelpers.getEfficiencyAtPoint ( histo, mx, my )
  return value

def getExplanationForLackOfUpperLimit ( analysis, topo, mx=None, my=None, \
                                        run=None, number=False ):
  """ if there's no upper limit, we want to know what's wrong.
      If number is false, return a text, if number is true
      return the error code """
  value=getUpperLimit ( analysis, topo, run=run )
  msg=SMSHelpers.getErrorMessage ( value, mx, my )
  if number: return msg[0]
  return msg[1]

def isPublic ( analysis, run=None ):
  """ is the result from this analysis public? """
  value=SMSHelpers.getMetaInfoField ( analysis, "private", run )
  if not value:
    return None
  try:
    d=not bool ( int ( value ) )
    return d
  except Exception:
    print "[SMSNewResults.py] couldnt parse ``private'' field"
  return None

def getLumi ( analysis, run=None ):
  """ get the integrated luminosity for this analysis """
  return SMSHelpers.getMetaInfoField ( analysis, "lumi", run )

def getSqrts ( analysis, run=None ):
  """ get s_hat for this analysis """
  return SMSHelpers.getMetaInfoField ( analysis, "sqrts", run )

def getPAS ( analysis, run=None ):
  """ get the PAS for this analysis """
  return SMSHelpers.getMetaInfoField ( analysis, "pas", run )

def getx ( analysis, topo=None, run=None ):
  """ get the description of the x-values for this analysis, if you supply a
      topo, then the return value is the x-values only for this topo """
  if topo:
    tmp=getx ( analysis, run )
    if tmp.has_key ( topo ): return tmp[topo]
    return None
  st = SMSHelpers.getMetaInfoField ( analysis, "x", run )
  if not st:
     return None
  st = st.split(',')
  d = {}
  for i in range(len(st)):
     l = st[i].split(':')
     x = l[1].split()
     d[l[0]] = x
  return d

def getFigures ( analysis, run=None ):
  """ get the figure number for this analysis """
  return SMSHelpers.getMetaInfoField ( analysis, "figures", run )

def getConditions ( analysis, run=None ):
  """ get the figure number for this analysis """
  run=SMSHelpers.getRun ( analysis, run )
  ret = SMSHelpers.conditions ( analysis, run )
  return ret

def getRequirement ( analysis, run=None ):
  """ any requirements that come with this analysis? (e.g. onshellness) """
  return SMSHelpers.getMetaInfoField ( analysis, "requires", run )

def getCheckedBy ( analysis, run=None ):
  """ has the result been validated? """
  return SMSHelpers.getMetaInfoField ( analysis, "checked", run )

def getJournal ( analysis, run=None ):
  """ get the journal of this analysis """
  return SMSHelpers.getMetaInfoField ( analysis, "journal", run )

def getBibtex ( analysis, run=None ):
  """ get the inspire page with the bibtex entry for this analysis """
  return SMSHelpers.getMetaInfoField ( analysis, "bibtex", run )

def getURL ( analysis, run=None ):
  """ get the URL for this analysis """
  return SMSHelpers.getMetaInfoField ( analysis, "url", run )

def hasURL ( analysis, run=None ):
  """ see if an URL is known """
  return SMSHelpers.hasMetaInfoField ( analysis, "url", run )

def getContact ( analysis, run=None ):
  """ get the contact for this analysis """
  return SMSHelpers.getMetaInfoField ( analysis, "contact", run )

def getPerturbationOrder ( analysis, run=None ):
  """ get the contact for this analysis """
  return SMSHelpers.getMetaInfoField ( analysis, "order", run )

def particles(topo,plot = 'ROOT'):
  """return the production mode for a given topology:
     latex code either compatible to ROOT or Python"""
  if SMSHelpers.dicparticle.has_key(topo):
    part = SMSHelpers.dicparticle[topo]
    if plot == 'ROOT':
      #print "[SMSResults.py] debug",part
      return part
    if plot == 'python':
      return part.replace('#','\\')
  else:
    return None

def particleName(topo):
  """return the production mode for a given topology:
     write out the name in plain letters, no latex """
  if topo[:2]=="TGQ": return "associate"
  if topo=="TChiSlep" or topo=="TChiNuSlep": return "chargino neutralino"
  if topo=="TChiSlepSlep": return "chargino neutralino"
  if topo=="TChiwz": return "chargino neutralino"
  if not SMSHelpers.dicparticle.has_key(topo):
    return "???"
  part = SMSHelpers.dicparticle[topo].replace("#tilde","").replace("{","").replace("}","")
  if part=="g": part="gluino"
  if part=="b": part="sbottom"
  if part=="t": part="stop"
  if part=="q": part="squark"
  return part

def massDecoupling_ ( topo ):
  if topo=="T2tt":
    return "m(#tilde{g},#tilde{q})>>m(#tilde{t})"
  if topo=="T2FVttcc":
    return "m(#tilde{g},#tilde{q})>>m(#tilde{t})"
  if topo=="T2bb":
    return "m(#tilde{g},#tilde{q})>>m(#tilde{b})"
  if topo=="TChiSlep":
    #return "m(#tilde{g}),m(#tilde{q})>>m(#tilde{#chi}^{0}_{2}),m(#tilde{#chi}^{#pm})"
    return "m(#tilde{g},m(#tilde{q})>>m(#tilde{#chi}^{0}_{2},#tilde{#chi}^{#pm})"
  if topo=="TChiSlepSlep":
#return "m(#tilde{g}),m(#tilde{q})>>m(#tilde{#chi}^{0}_{2})"
    return "m(#tilde{g},#tilde{q})>>m(#tilde{#chi}^{0}_{2},#tilde{#chi}^{#pm})"
  if topo=="TChiNuSlep":
    return "m(#tilde{g},#tilde{q})>>m(#tilde{#chi}^{0}_{2},#tilde{#chi}^{#pm})"
    #return "m(#tilde{g}),m(#tilde{q})>>m(#tilde{#chi}^{0}_{2}),m(#tilde{#chi}^{#pm})"
  if topo=="TChiwz":
    return "m(#tilde{g},#tilde{q})>>m(#tilde{#chi}^{0}_{2},#tilde{#chi}^{#pm})"
  T2=topo[:2]
  if T2=="T1" or T2=="T3" or T2=="T5":
    return "m(#tilde{q})>>m(#tilde{g})"
  if T2=="T2" or T2=="T4" or T2=="T6":
    return "m(#tilde{g})>>m(#tilde{q})"
  return ""

def massDecoupling ( topo, plot='ROOT',kerning=True ):
  """ describe the assumed mass decoupling """
  md=massDecoupling_ ( topo )
  if kerning:
    md=md.replace(">>",">#kern[-.2]{>}")
  if plot!='ROOT':
    md = '$' + md.replace('#','\\') + '$'
  return md

