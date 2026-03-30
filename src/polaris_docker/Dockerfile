#
# docker build -t polaris:latest .
# docker run -v /var/polaris:/mnt/polaris --name polaris polaris:latest
# docker run -e stuntbox=net -v /var/polaris:/mnt/polaris --name polaris polaris:latest
# docker run -e stuntbox=net -e limit=5 -v /var/polaris:/mnt/polaris --name polaris polaris:latest
#
FROM python:3.11-slim

WORKDIR /app

# Create and activate virtualenv first
RUN python -m venv /app/venv
ENV VIRTUAL_ENV=/app/venv
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

# Copy requirements and install them inside the venv
COPY requirements.txt ./
RUN $VIRTUAL_ENV/bin/pip install --no-cache-dir -r requirements.txt

COPY polaris_app.py ./
COPY ports.py ./
COPY vessels.py ./
COPY postgres.py ./
COPY sql_table.py ./
COPY vessels.py ./

RUN mkdir -p /mnt/polaris
CMD ["python", "polaris_app.py"]
