FROM python:3.10.6-slim-bullseye@sha256:dff7fd9200421a8c65e020af221a21c8aab784c5c8a8d55c64a095b645209d77
WORKDIR /opt/glitch
COPY baselines/sources/glitch/ /opt/glitch/
COPY .runtime/glitch-wheels/ /wheels/
COPY baselines/glitch/requirements.lock /requirements.lock
RUN pip install --no-index --find-links /wheels -r /requirements.lock grapheme==0.6.0 \
    && pip install --use-pep517 --no-deps --no-build-isolation -e .
ENTRYPOINT ["glitch"]
