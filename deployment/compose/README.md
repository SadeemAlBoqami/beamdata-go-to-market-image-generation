# Docker Compose deployment on aidc-t09

Run the five services in the repository-root `compose.yaml`: Gradio, FLUX,
Z-Image Turbo, Prometheus, and Grafana. The model and Prometheus containers have
no published ports. Gradio stays on host loopback port 7860 for the existing
`/proxy/7860/` reverse proxy. Grafana defaults to host loopback port 3000 for
an SSH tunnel or protected admin proxy.

## Before the first start

Use Docker Compose v2 with NVIDIA Container Toolkit GPU support. Confirm that
the two named model images already exist locally. The model services use
`pull_policy: never`; Compose will fail rather than download another copy.

```bash
docker compose version
docker image inspect ghcr.io/sadeemalboqami/flux2-klein:latest ghcr.io/sadeemalboqami/z-image-turbo:latest >/dev/null
test -f /data/models/flux2-klein-gguf/flux-2-klein-4b-Q4_K_M.gguf
test -d /var/lib/hf-cache/hub
df -h /data
```

Both model containers mount `/var/lib/hf-cache` at the same path and set
`HF_HOME` to that path. `HF_HUB_OFFLINE=1` prevents fresh model downloads; check
that the FLUX base model and Z-Image snapshots are in this cache before
switching. FLUX mounts its GGUF directory read-only. The existing benchmark
folder is mounted read-only in Gradio, so its images are not copied into the
frontend image. Prometheus retains blocks for up to 7 days or 1 GB; its WAL
and temporary data can use additional space. Monitor its named volume alongside
the small Grafana volume.

If repository-root `.env` already exists, keep its current values and add the
variables from `deployment/compose/.env.example`. Otherwise copy that template.
Set unique FLUX and Z-Image API tokens and a Grafana admin password, then
restrict the file's permissions. `.env` is gitignored. Do not print the
resolved Compose config while it contains tokens.

```bash
test -e .env || cp deployment/compose/.env.example .env
chmod 600 .env
# Edit .env with local secrets.
docker compose config -q
```

## Existing exporter access

Prometheus maps `host.docker.internal` to Docker's host gateway and scrapes the
already-running `dcgm-exporter` on port 9400 and `node-exporter` on port 9100.
No exporter container is started by this stack. The exporters must listen on
an address reachable from the Docker bridge. Listening only on `127.0.0.1`
does **not** make them reachable through the host gateway. On aidc-t09, both
listeners were confirmed on `*` (ports 9400 and 9100). Recheck before rollout:

```bash
sudo ss -ltnp '( sport = :9400 or sport = :9100 )'
```

If either exporter listens only on loopback, adjust that existing exporter's
bind address to the Docker bridge gateway or another host address reachable
from containers, and restrict access with the host firewall. Keep the exporter
containers themselves; do not start duplicates. Start only Prometheus first;
this cannot start a second model container. Then test both exporter URLs from
inside the Prometheus container. Each command must exit successfully:

```bash
docker compose up -d prometheus
docker compose exec -T prometheus wget -q -O /dev/null http://host.docker.internal:9400/metrics
docker compose exec -T prometheus wget -q -O /dev/null http://host.docker.internal:9100/metrics
```

For the `/data` panel, confirm the existing node exporter actually reports the
host mount as `mountpoint="/data"`:

```bash
curl -fsS http://127.0.0.1:9100/metrics | grep 'node_filesystem_size_bytes.*mountpoint="/data"'
```

## Migrate the current containers

Check the old containers' mounts before stopping them. Leave their stopped
containers available for rollback while the new stack is verified. The Compose
model containers intentionally reuse the current names, so an accidental
second pair cannot start alongside the old pair. Also stop the current Gradio
process that occupies host port 7860.

```bash
docker inspect flux2-klein z-image-turbo --format '{{.Name}} {{json .Mounts}}'
docker stop flux2-klein z-image-turbo
docker rename flux2-klein flux2-klein-precompose
docker rename z-image-turbo z-image-turbo-precompose
sudo ss -ltnp 'sport = :7860'
# Stop the existing Gradio process or service identified above.
docker compose up -d --build
docker compose ps
```

The frontend uses `http://flux:8000` and `http://zimage:8000` over Compose
DNS. The host's former 8005/8006 loopback mappings are intentionally absent.
Gradio retains `root_path=/proxy/7860` and serves CSS through the same proxy.
Run generation and the saved Benchmark Comparison tab through the reverse
proxy after startup. Avoid `docker compose down -v`: that would remove the
Grafana and Prometheus data volumes.

## Monitoring checks

Grafana's provisioned **Beamdata host and GPU** dashboard shows GPU usage,
VRAM used/free and installed capacity, temperature, power, host CPU and RAM,
`/data` disk utilization, and Prometheus scrape health. The live exporter was
checked for `DCGM_FI_DEV_GPU_UTIL`, `DCGM_FI_DEV_FB_USED`,
`DCGM_FI_DEV_FB_FREE`, `DCGM_FI_DEV_GPU_TEMP`, and
`DCGM_FI_DEV_POWER_USAGE`, including sample values. It does not expose a total
or reserved framebuffer series. The 49,140 MiB capacity line is a static
reference from the verified A6000 specification; update it if the GPU changes.
Prometheus also scrapes the models' native `/metrics` endpoints; both current
model containers returned HTTP 200 there. Individual inference series depend
on what those pinned vLLM-Omni images emit. Docker health checks cover Gradio
and both model APIs. Check `docker compose ps` for application health and Grafana's scrape
health panel for exporter/model metrics reachability.

Grafana is at `http://127.0.0.1:3000/` on aidc-t09. Leave
`GRAFANA_BIND_IP=127.0.0.1` unless a protected team/admin route is in place.
Prometheus has no host port. No Kubernetes, extra exporters, model startup
switching, or permanent generated-image storage are part of this deployment.
