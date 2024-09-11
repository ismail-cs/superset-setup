FROM apache/superset:2.1.0
USER root
RUN pip install pymssql
USER superset
COPY --chown=superset:superset superset_config.py /app/pythonpath/superset_config.py


