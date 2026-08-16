# LUMINA Wearables

This repository owns wearable-provider ingestion, normalization, mapping, and
Archive promotion policy. The initial service intentionally exposes only a
health endpoint so the LUMINA Core stack can orchestrate it without placing
wearable semantics in the core repository.

Current release: `1.0.0`.

```bash
docker build -t lumina-wearables .
docker run --rm -p 8300:8300 lumina-wearables
curl http://localhost:8300/health
```

Provider integrations and Open Wearables credentials are not implemented by
this minimal scaffold.
