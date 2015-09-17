import logging
import zipfile
import StringIO

logger = logging.getLogger(__name__)


def unzip(raw_str):
    '''
    Unzip file like object and return a dictionary where keys are filenames
    and values are file content strings
    '''
    ret = {}
    try:
        buf = StringIO.StringIO(raw_str)
        zipf = zipfile.ZipFile(buf)
        for name in zipf.namelist():
            ret[name] = zipf.read(name)
    except Exception, ex:
        logger.exception('Could not unzip file')
        print ex
    return ret
