"""
Compile SMIv2 MIBs
++++++++++++++++++

Invoke user callback function to provide MIB text,
compile given text string into pysnmp MIB form and pass
results to another user callback function for storing.

Here we expect to deal only with SMIv2-valid MIBs.

We use noDeps flag to prevent MIB compiler from attemping
to compile IMPORT'ed MIBs as well.
"""  #
import zipfile
from pathlib import Path

from pysmi.codegen import JsonCodeGen
from pysmi.compiler import MibCompiler, MibStatus
from pysmi.parser import SmiV2Parser
from pysmi.reader import getReadersFromUrls
from pysmi.writer import FileWriter

from settings import BASE_URL


def mibs_list(file):
    if zipfile.is_zipfile(file.open("rb")):
        with zipfile.ZipFile(file) as f:
            return f.namelist()
    return [file.name]


def compile(filename):
    file = BASE_URL.joinpath("uploads", "mibs", filename)

    files = mibs_list(file)

    mibcompiler = MibCompiler(
        SmiV2Parser(),
        JsonCodeGen(),
        # out own callback function stores results in its own way
        FileWriter(BASE_URL.joinpath("uploads", "parsed")).setOptions(suffix='.json')
    )

    mibcompiler.addSources(
        *getReadersFromUrls(
            *[
                file.as_uri()
                if zipfile.is_zipfile(file)
                else BASE_URL.joinpath("uploads", "mibs").as_uri(),
                BASE_URL.joinpath("mibs", "rfc").as_uri(),
                "https://bestmonitoringtools.com/mibdb/mibs/@mib@"
            ],
            **dict(fuzzyMatching=True)
        )
    )

    results = mibcompiler.compile(*files, **dict(noDeps=True,
                                              rebuild=True,
                                              genTexts=True))

    mibcompiler.buildIndex(results, ignoreErrors=False)

    return results


if __name__ == '__main__':
    print()
