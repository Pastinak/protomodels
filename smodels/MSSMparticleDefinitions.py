"""
.. module:: particles
   :synopsis: Defines the particles to be used.
              All particles appearing in the model as well as the SM particles
              must be defined here.

.. moduleauthor:: Alicia Wongel <alicia.wongel@gmail.com>
.. moduleauthor:: Andre Lessa <lessa.a.p@gmail.com>


   Properties not defined here and defined by the LHE or SLHA input file 
   (such as masses, width and BRs) are automatically added later.
"""

from smodels.tools.physicsUnits import MeV, GeV
from smodels.theory.particleClass import Particles, ParticleList


# MSSM particles

####  R-odd   ##########
#1st generation squarks and its conjugates:
sdl = Particles(Z2parity='odd', label='sd_L', pdg=1000001, mass=None, eCharge=-1./3, colordim=3, spin=0, width=None, branches=None)
sul = Particles(Z2parity='odd', label='su_L', pdg=1000002, mass=None, eCharge=2./3, colordim=3, spin=0, width=None, branches=None)
sdr = Particles(Z2parity='odd', label='sd_R', pdg=2000001, mass=None, eCharge=-1./3, colordim=3, spin=0, width=None, branches=None)
sur = Particles(Z2parity='odd', label='su_R', pdg=2000002, mass=None, eCharge=2./3, colordim=3, spin=0, width=None, branches=None)

#2nd generation squarks and its conjugates:
ssl = Particles(Z2parity='odd', label='ss_L', pdg=1000003, mass=None, eCharge=-1./3, colordim=3, spin=0, width=None, branches=None)
scl = Particles(Z2parity='odd', label='sc_L', pdg=1000004, mass=None, eCharge=2./3, colordim=3, spin=0, width=None, branches=None)
ssr = Particles(Z2parity='odd', label='ss_R', pdg=2000003, mass=None, eCharge=-1./3, colordim=3, spin=0, width=None, branches=None)
scr = Particles(Z2parity='odd', label='sc_R', pdg=2000004, mass=None, eCharge=2./3, colordim=3, spin=0, width=None, branches=None)

#3rd generation squarks and its conjugates:
sb1 = Particles(Z2parity='odd', label='sb_1', pdg=1000005, mass=None, eCharge=2./3, colordim=3, spin=0, width=None, branches=None)
st1 = Particles(Z2parity='odd', label='st_1', pdg=1000006, mass=None, eCharge=-1./3, colordim=3, spin=0, width=None, branches=None)
sb2 = Particles(Z2parity='odd', label='sb_2', pdg=2000005, mass=None, eCharge=2./3, colordim=3, spin=0, width=None, branches=None)
st2 = Particles(Z2parity='odd', label='st_2', pdg=2000006, mass=None, eCharge=-1./3, colordim=3, spin=0, width=None, branches=None)

#1st generation sleptons and its conjugates:
sel = Particles(Z2parity='odd', label='se_L', pdg=1000011, mass=None, eCharge=-1, colordim=0, spin=0, width=None, branches=None)
snel = Particles(Z2parity='odd', label='sne_L', pdg=1000012, mass=None, eCharge=0, colordim=0, spin=0, width=None, branches=None)
ser = Particles(Z2parity='odd', label='se_R', pdg=2000011, mass=None, eCharge=0, colordim=0, spin=0, width=None, branches=None)

#2nd generation sleptons and its conjugates:
smul = Particles(Z2parity='odd', label='smu_L', pdg=1000013, mass=None, eCharge=-1, colordim=0, spin=0, width=None, branches=None)
snmul = Particles(Z2parity='odd', label='snmu_L', pdg=1000014, mass=None, eCharge=0, colordim=0, spin=0, width=None, branches=None)
smur = Particles(Z2parity='odd', label='smu_R', pdg=2000013, mass=None, eCharge=-1, colordim=0, spin=0, width=None, branches=None)

#3rd generation sleptons and its conjugates:
sta1 = Particles(Z2parity='odd', label='sta_1', pdg=1000015, mass=None, eCharge=-1, colordim=0, spin=0, width=None, branches=None)
sntal = Particles(Z2parity='odd', label='snta_L', pdg=1000016, mass=None, eCharge=0, colordim=0, spin=0, width=None, branches=None)
sta2 = Particles(Z2parity='odd', label='sta_2', pdg=2000015, mass=None, eCharge=-1, colordim=0, spin=0, width=None, branches=None)

#Gluino:
gluino = Particles(Z2parity='odd', label='gluino', pdg=1000021, mass=None, eCharge=0, colordim=8, spin=1./2, width=None, branches=None)
#Neutralinos
n1 = Particles(Z2parity='odd', label='N1', pdg=1000022, mass=None, eCharge=0, colordim=0, spin=1./2, width=None, branches=None)  
n2 = Particles(Z2parity='odd', label='N2', pdg=1000023, mass=None, eCharge=0, colordim=0, spin=1./2, width=None, branches=None)  
n3 = Particles(Z2parity='odd', label='N3', pdg=1000025, mass=None, eCharge=0, colordim=0, spin=1./2, width=None, branches=None)  
n4 = Particles(Z2parity='odd', label='N4', pdg=1000035, mass=None, eCharge=0, colordim=0, spin=1./2, width=None, branches=None)  

#Charginos
c1 = Particles(Z2parity='odd', label='C1+', pdg=1000024, mass=None, eCharge=1, colordim=0, spin=1./2, width=None, branches=None)  
c2 = Particles(Z2parity='odd', label='C2+', pdg=1000037, mass=None, eCharge=1, colordim=0, spin=1./2, width=None, branches=None)  

##### R-even  ###############
#Higgs
H = Particles(Z2parity='even', label='H+', pdg=37, mass=None, eCharge=+1, colordim=0, spin=0, width=None, branches=None)  
A0 = Particles(Z2parity='even', label='A0', pdg=36, mass=None, eCharge=0, colordim=0, spin=0, width=None, branches=None)  
H0 = Particles(Z2parity='even', label='H0', pdg=35, mass=None, eCharge=0, colordim=0, spin=0, width=None, branches=None)  


squarks = [sdl,sul,sdr,sur] + [ssl,scl,ssr,scr] + [sb1,st1,sb2,st2]
sleptons = [sel,snel,ser] + [smul,snmul,smur] + [sta1,sntal,sta2]
inos = [gluino] + [n1,n2,n3,n4] + [c1,c2]
higgs = [H,A0,H0]

sparticles = squarks + sleptons + inos + higgs
sparticlesC = [p.chargeConjugate() for p in sparticles]  #Define the charge conjugates



BSMList = sparticles + sparticlesC

BSMparticleList = ParticleList('BSM', BSMList)
BSMpdgs = BSMparticleList.getPdgs()
BSMparticles = BSMparticleList.getNames()



