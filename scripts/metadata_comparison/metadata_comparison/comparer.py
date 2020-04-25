#!/usr/bin/env python3
#
# comparer.py
#
# Purpose: Compare performance metadata JSON files produced by Digester and produce result in CSV format
#
# Usage: python3 comparer.py [-h] [-v] [--json_paths JSONPATH [JSONPATH ...]] [--output_path OUTPUTPATH]
#
# Python Prereqs (at least, the ones which I needed to manually install... YMMV):
#
#   * pip3 install --upgrade pandas
#

import argparse
import json
import pandas
from pathlib import Path
from metadata_comparison.lib.logging import *

logger = log.getLogger('metadata_comparison.comparer')

def read_json_files(*paths):
    """
    Produces list of tuples: [[path, json], [path, json], ...]
    """
    jsons = []
    for path in paths:
        with open(path,) as file:
            jsons.append([path, json.load(file)])

    return jsons


def compare_jsons(*pathsAndJsons):
    """
    Uses pandas library to convert JSONs into dataframes, and concatenate those dataframes into a single one.
    Performs sanity check, producing exception, if at least one of the JSONs doesn't have matching subset of keys.
    """
    columnToCompareNameEnding = ".overallRuntimeSeconds"
    versionColumnName = "version"
    result = pandas.DataFrame()
    lastCols = []
    for pathAndJson in pathsAndJsons:
        df = pandas.json_normalize(pathAndJson[1])
        cols = [c for c in df.columns if c.endswith(columnToCompareNameEnding)]
        cols.sort()
        cols.insert(0, versionColumnName)

        if lastCols and lastCols != cols:
            raise Exception(f"JSON data at {pathAndJson[0]} doesn't have matching subset of columns. Expected: {lastCols} but got {cols}")

        lastCols = cols
        df.index = [pathAndJson[0]]
        result = pandas.concat([result, df[cols]])

    renameVersionColumnTo = "digester format version"
    result.rename(columns = {versionColumnName: renameVersionColumnTo}, inplace = True)
    result.index.name = "input file name"

    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='Compare performance metadata JSONs and produce CSV result')
    parser.add_argument('-v', '--verbose', action='store_true')
    parser.add_argument('--json_paths', metavar='JSONPATH', type=Path, nargs='+', help='Paths to JSON files')
    parser.add_argument('--output_path', metavar='OUTPUTPATH', type=Path, nargs=1, help='Path to output CSV file')

    args = parser.parse_args()
    set_log_verbosity(args.verbose)
    logger.info("Starting Comparer operation.")

    pathsAndJsons = read_json_files(*args.json_paths)
    comparisonResultDf = compare_jsons(*pathsAndJsons)
    comparisonResultDf.to_csv(args.output_path[0])

    logger.info('Comparer operation completed successfully.')
