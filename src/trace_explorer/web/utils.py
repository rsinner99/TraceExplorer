import os
import glob
import shutil
import time

from trace_explorer.config import REPORT_DIR

def rename_index_html():
    src = os.path.join(REPORT_DIR, 'index.html')
    dst_name = str(time.time_ns())
    dst = os.path.join(REPORT_DIR, dst_name)
    os.mkdir(dst)
    os.rename(src, os.path.join(dst, 'index.html'))
    trace_files = glob.glob(os.path.join(REPORT_DIR, 'trace*.html'))
    for f in trace_files:
        new = os.path.join(dst, os.path.basename(f))
        os.rename(f, new)
    return dst_name

def get_all_files():
    files = glob.glob(os.path.join(REPORT_DIR, "./**/index.html"), recursive=True)
    result = []
    for fn in files:
        name = fn.split('/')[-2]
        result.append(name)
    return result

def delete_dir(name):
    files = glob.glob(os.path.join(REPORT_DIR, name, '/*.html'))
    for f in files:
        os.remove(f)
    shutil.rmtree(os.path.join(REPORT_DIR, name))
