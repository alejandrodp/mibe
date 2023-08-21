"""
Compile SMIv2 MIBs
++++++++++++++++++

Invoke user callback function to provide MIB text,
compile given text string into pysnmp MIB form and pass
results to another user callback function for storing.

Here we expect to deal only with SMIv2-valid MIBs.

We use noDeps flag to prevent MIB compiler from attemping
to compile IMPORT'ed MIBs as well.
"""#
import os

from pysmi.codegen import PySnmpCodeGen, JsonCodeGen
from pysmi.compiler import MibCompiler
from pysmi.parser import SmiV2Parser
from pysmi.reader import getReadersFromUrls
from pysmi.searcher import StubSearcher
from pysmi.writer import FileWriter

inputMibs = ['ARUBAWIRED-MVRP-MIB']
srcDir = ['mibs.zip']  # we will read MIBs from here

# Initialize compiler infrastructure

mibCompiler = MibCompiler(
    SmiV2Parser(),
    JsonCodeGen(),
    # out own callback function stores results in its own way
    FileWriter(os.path.join('./parsed')).setOptions(suffix='.json')
)

# our own callback function serves as a MIB source here

mibCompiler.addSources(
            *getReadersFromUrls(
                *srcDir, **dict(fuzzyMatching=True)
            )
        )

# mibCompiler.addSources(
#   CallbackReader(lambda m, c: open(srcDir+'/'+m+'.mib').read())
# )

# never recompile MIBs with MACROs
mibCompiler.addSearchers(StubSearcher(*PySnmpCodeGen.baseMibs))

# run non-recursive MIB compilation
results = mibCompiler.compile(*inputMibs, **dict(noDeps=False,
                                                 rebuild=True,
                                                 genTexts=True))

mibCompiler.buildIndex(results, ignoreErrors=True)

print(results)