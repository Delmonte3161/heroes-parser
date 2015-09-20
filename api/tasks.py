from __future__ import absolute_import

import os

from celery import shared_task

from stormreplay import *

import boto
import StringIO
import cStringIO

import json
import gzip

from celery.utils.log import get_task_logger
log = get_task_logger(__name__)

from boto.s3.key import Key

def AnalyzeReplayFile (replayFile, fieldNames):

    stormReader = StormReplayReader(replayFile)
    log.info("Created StormReplayReader") 

    stormAnalyzer = StormReplayAnalyzer(stormReader)
    log.info("Created StormReplayAnalyzer") 

    fieldMapping = StormReplayAnalyzer.getFieldMappingForNames(fieldNames) if len(fieldNames) > 0 else None

    retval = stormAnalyzer.analyze(fieldMapping)

    return retval

@shared_task
def LocallyStoredReplayParsingTask(fileName, debug):
    log.info('File name='+fileName+', debug='+str(debug))
    replayFile = open(fileName)
    retval = AnalyzeReplayFile(replayFile, debug)
    replayFile.close()
    os.remove(replayFile.name)
    return retval

