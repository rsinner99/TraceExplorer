FROM python:3.10-buster

#ENV ENV RCA_DB_URL=localhost:9200
ENV RCA_CSV_PATH="/data/eval_results.csv"
ENV RCA_REPORT_DIR="/data/output"

WORKDIR /code

RUN useradd rca

RUN mkdir /data /data/input /data/output
RUN chown -R rca:rca /data

COPY ./requirements.txt ./
RUN python3 -m pip install -r requirements.txt

COPY --chown=rca:rca src/trace_explorer /code/trace_explorer
RUN rm -f /etc/nginx/conf.d/default.conf

USER rca

EXPOSE 8000
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "trace_explorer.web.app:app"]