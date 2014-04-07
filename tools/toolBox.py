#!/usr/bin/env python

"""
.. module:: toolBox
   :synopsis: Contains a singleton-like class that keeps track of all external tools

.. moduleauthor:: Wolfgang Waltenberger <wolfgang.waltenberger@gmail.com>

"""

import logging
FORMAT = '%(levelname)s in %(module)s.%(funcName)s(): %(message)s'
logging.basicConfig(format=FORMAT)
logger = logging.getLogger(__name__)
logger.setLevel ( level=logging.INFO )

class ToolBox:
    """
    A singleton-like class that keeps track of all external tools.
    
    """
    __shared_state = {"tools" : {}}
    
    def __init__(self):
        # instead of making this a singleton, we introduce
        self.__dict__ = self.__shared_state
        if len(self.__shared_state["tools"]) == 0:
            self.initSingleton()

    def initSingleton(self):
        """
        Intialize singleton instance (done only once for the entire class).
        
        """
        import externalPythia6
        import externalNllFast
        self.add(externalPythia6.ExternalPythia6())
        for(sqrts, tool) in externalNllFast.nllFastTools.items():
                self.add(tool)

    def add(self, instance):
        """
        Adds a tool by passing an instance to this method.
        
        """
        self.tools[instance.name]=instance

    def listOfTools(self):
        """
        Returns a simple list with the tool names.
        
        """
        return self.tools.keys()

    def installationOk(self, ok, colors):
        import types
        green = '\033[0;32m'
        red = '\033[0;31m'
        reset = '\033[;0m'
        if ok == True:
            ret = "installation ok!"
            if colors:
                ret="%s%s%s" % (green, ret, reset)
            return ret
        ret = "problem with installation"
        if type(ok) == types.StringType:
            ret += " (%s)" % ok
        if colors:
            ret = "%s%s%s" % (red, ret, reset)
        return ret

    def checkInstallation(self, colors=True, make=False):
        ret = "The following tools are found in the Toolbox:\n"
        hasMade = False
        for(name, instance) in self.tools.items():
            ok = instance.checkInstallation()
            exe = instance.pathOfExecutable()
            maxl = 45
            if len(exe) > maxl + 4:
                exe = "... " + instance.pathOfExecutable()[-maxl:]
            ret += "%-12s [%-50s]:    %s\n" % (name, exe,
                                               self.installationOk(ok, colors))
            if not ok and make: 
                hasMade = True
                instance.compile()
        if make and hasMade:
            ret += "Check again:\n"
            ret += self.checkInstallation(self, colors, make=False)
        ## logger.info(ret)
        print (ret)

    def compile(self):
        for(name, instance) in self.tools.items():
            installOk = instance.checkInstallation()
            if installOk == True:
                continue
            logger.info("Installation of " + str(name) + " not correct. \
                        Trying to compile.")
            instance.compile()

    def get(self, tool, verbose=True):
        """
        Gets instance of tool from the toolbox.
        
        """
        if not tool in self.tools:
            if verbose:
                logger.error("Asking for non-existent tool ``%s''" % tool)
            return None
        return self.tools[tool]

if __name__ == "__main__":
    import argparse
    argparser = argparse.ArgumentParser(description='simple script to check \
            if the tools are installed and compiled')
    argparser.add_argument('-n', '--nocolors', help='turn off colors',
                           action='store_true')
    argparser.add_argument('-m', '--make', help='compile packages if needed',
                           action='store_true')
    args = argparser.parse_args()
    tmp = ToolBox()
    if args.make:
        tmp.compile()
    tmp.checkInstallation(colors=not args.nocolors)
