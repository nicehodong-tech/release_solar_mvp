FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONHASHSEED=0 \
    PORT=8080

WORKDIR /app

RUN addgroup --system --gid 10001 saju \
    && adduser --system --uid 10001 --ingroup saju --home /home/saju saju

COPY requirements.txt ./requirements.txt
RUN python -m pip install --no-cache-dir --disable-pip-version-check -r requirements.txt

COPY --chown=saju:saju saju_analysis_engine ./saju_analysis_engine
COPY --chown=saju:saju saju_birth_engine ./saju_birth_engine
COPY --chown=saju:saju saju_web ./saju_web
COPY --chown=saju:saju scripts ./scripts

RUN python -m compileall -q saju_analysis_engine saju_birth_engine saju_web scripts

USER saju
EXPOSE 8080
STOPSIGNAL SIGTERM

CMD ["python", "-m", "saju_web.app", "--host", "0.0.0.0"]
