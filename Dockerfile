# quoted — a verification service with no dependencies to install.
#
# There is no `pip install` step because there is nothing to install. That is
# the whole argument of this project rendered as a build file: a service whose
# claim is "it refuses what it cannot verify" should not itself rest on a
# hundred packages nobody has read.
FROM python:3.12-slim

WORKDIR /app
COPY src/ /app/src/

ENV PYTHONPATH=/app/src \
    PYTHONUNBUFFERED=1 \
    PORT=8080

# Run as nobody. The service reads request bodies and writes nothing to disk.
USER 65534:65534

EXPOSE 8080
# **Read PORT, do not assume 8080.** Every managed host injects its own port;
# a healthcheck hardcoded to 8080 marks a perfectly healthy container unhealthy
# and the platform kills it. Verified 2026-08-23: the service answered on 7788
# while the old check got nothing on 8080.
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s \
  CMD python3 -c "import os,sys,urllib.request;\
sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:'+os.environ.get('PORT','8080')+'/health',timeout=2).status==200 else 1)"

CMD ["python3", "-m", "quoted.serve"]
