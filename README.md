# salty-polaris

salty-polaris scrapes AIS data for Northern California ports to discover what ships have called.

## Installation

Install postgresql schema by using infra/psql/add_schema.sh

```bash
docker build -t polaris:latest .
```

## Usage

### Command line

```bash
docker run -v /var/polaris:/mnt/polaris --name polaris porlaris:latest
```
