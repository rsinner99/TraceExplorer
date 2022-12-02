import math
import time

from flask import (
    Blueprint, redirect, render_template,
    request, flash, url_for, send_from_directory
)

from trace_explorer.analysis import analyze_custom_time_range
from trace_explorer.cli import get_timedelta
from trace_explorer.config import REPORT_DIR

from .utils import rename_index_html, get_all_files, delete_dir
from .forms import SzenarioListForm

bp = Blueprint('web', __name__, url_prefix='')


@bp.route('/', methods=('GET',))
def list_files():
    files = get_all_files()
    return render_template('files.html', len=len(files), files=files)


@bp.route('/', methods=('GET',))
@bp.route('/delete/<path:path>', methods=('GET',))
def delete_file(path):
    delete_dir(path)
    return redirect(url_for('web.list_files'))


@bp.route('/analysis', methods=('GET', 'POST'))
def analysis():
    form  = SzenarioListForm()
    if form.validate_on_submit():
        error = None
        data = []
        for szenario in form.szenario.entries:
            name = szenario.name
            start = szenario.start.data
            end = szenario.end.data
            if not name:
                name = f"CustomSzenario - {current}"
            if not start:
                error = "Start time is missing."

            try:
                current = math.ceil(time.time_ns() / 1e3) # microseconds: rounded up
                start_delta = get_timedelta(start)
                start_time = current - start_delta
                if end:
                    end_delta = get_timedelta(end)
                    end_time = current - end_delta
                else:
                    end_time = current
            except Exception as e:
                error = str(e)
                raise e

            if error:
                flash(error)

            data.append({
                "start_time": start_time,
                "end_time": end_time,
                "name": name
            })

        analyze_custom_time_range(data)
        path = rename_index_html()
        return redirect(url_for('web.report', path=f'{path}/index.html'))

    return render_template('analysis.html', form=form)


@bp.route('/report/<path:path>', methods=('GET',))
def report(path):
    return send_from_directory(REPORT_DIR, path)
