#!/usr/bin/env bash
set -u

PASS=0
WARN=0
FAIL=0

green() { printf '\033[32m%s\033[0m\n' "$*"; }
yellow() { printf '\033[33m%s\033[0m\n' "$*"; }
red() { printf '\033[31m%s\033[0m\n' "$*"; }

pass() { PASS=$((PASS+1)); green "[PASS] $*"; }
warn() { WARN=$((WARN+1)); yellow "[WARN] $*"; }
fail() { FAIL=$((FAIL+1)); red "[FAIL] $*"; }

section() {
  echo
  echo "============================================================"
  echo "$1"
  echo "============================================================"
}

command -v kubectl >/dev/null 2>&1 || {
  echo "kubectl is required."
  exit 1
}

section "1. Cluster access"

if kubectl cluster-info >/dev/null 2>&1; then
  pass "kubectl can reach the cluster"
else
  fail "kubectl cannot reach the cluster"
fi

section "2. Beamdata workloads"

kubectl get pods -n beamdata -o wide || fail "Could not list beamdata pods"

for app in flux2-klein z-image-turbo gradio; do
  ready="$(kubectl get deploy "$app" -n beamdata -o jsonpath='{.status.readyReplicas}' 2>/dev/null || true)"
  desired="$(kubectl get deploy "$app" -n beamdata -o jsonpath='{.spec.replicas}' 2>/dev/null || true)"

  if [[ -n "$ready" && "$ready" == "$desired" ]]; then
    pass "$app deployment ready ($ready/$desired)"
  else
    fail "$app deployment not fully ready (ready=${ready:-0}, desired=${desired:-unknown})"
  fi
done

section "3. Monitoring workloads"

kubectl get pods -n monitoring -o wide || fail "Could not list monitoring pods"

for app in prometheus grafana; do
  ready="$(kubectl get deploy "$app" -n monitoring -o jsonpath='{.status.readyReplicas}' 2>/dev/null || true)"
  desired="$(kubectl get deploy "$app" -n monitoring -o jsonpath='{.spec.replicas}' 2>/dev/null || true)"

  if [[ -n "$ready" && "$ready" == "$desired" ]]; then
    pass "$app deployment ready ($ready/$desired)"
  else
    fail "$app deployment not fully ready (ready=${ready:-0}, desired=${desired:-unknown})"
  fi
done

section "4. Services and Ingress"

kubectl get svc -n beamdata
kubectl get ingress -n beamdata

for svc in flux2-klein z-image-turbo gradio; do
  if kubectl get svc "$svc" -n beamdata >/dev/null 2>&1; then
    pass "Service exists: $svc"
  else
    fail "Missing Service: $svc"
  fi
done

if kubectl get ingress gradio -n beamdata >/dev/null 2>&1; then
  ingress_addr="$(kubectl get ingress gradio -n beamdata -o jsonpath='{.status.loadBalancer.ingress[0].ip}' 2>/dev/null || true)"
  pass "Gradio Ingress exists${ingress_addr:+ (address: $ingress_addr)}"
else
  fail "Gradio Ingress missing"
fi

section "5. GPU scheduling and runtime"

node="$(kubectl get nodes -o jsonpath='{.items[0].metadata.name}' 2>/dev/null || true)"

if [[ -n "$node" ]]; then
  capacity="$(kubectl get node "$node" -o jsonpath='{.status.capacity.nvidia\.com/gpu}' 2>/dev/null || true)"
  allocatable="$(kubectl get node "$node" -o jsonpath='{.status.allocatable.nvidia\.com/gpu}' 2>/dev/null || true)"

  echo "Node: $node"
  echo "nvidia.com/gpu capacity: ${capacity:-not-reported}"
  echo "nvidia.com/gpu allocatable: ${allocatable:-not-reported}"

  if [[ "$capacity" == "2" && "$allocatable" == "2" ]]; then
    pass "GPU time-slicing exposes 2 logical GPU slots"
  else
    warn "Expected 2 logical GPU slots; observed capacity=${capacity:-?}, allocatable=${allocatable:-?}"
  fi
else
  fail "Could not determine node name"
fi

if command -v nvidia-smi >/dev/null 2>&1; then
  echo
  nvidia-smi
  pass "nvidia-smi available"
else
  warn "nvidia-smi not available on host"
fi

section "6. Model health from Gradio pod"

gradio_pod="$(kubectl get pod -n beamdata -l app=gradio -o jsonpath='{.items[0].metadata.name}' 2>/dev/null || true)"

if [[ -z "$gradio_pod" ]]; then
  fail "Could not find Gradio pod"
else
  echo "Using pod: $gradio_pod"

  kubectl exec -n beamdata "$gradio_pod" -- python - <<'PY'
import os
import urllib.request
import urllib.error

checks = [
    ("FLUX", "http://flux2-klein:8000/health", os.environ.get("FLUX_TOKEN")),
    ("Z-Image", "http://z-image-turbo:8000/health", os.environ.get("ZIMAGE_TOKEN")),
]

failed = False

for name, url, token in checks:
    req = urllib.request.Request(url)
    if token:
        req.add_header("Authorization", f"Bearer {token}")

    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            print(f"{name}: HTTP {response.status}")
            if response.status != 200:
                failed = True
    except Exception as exc:
        print(f"{name}: FAILED: {exc}")
        failed = True

raise SystemExit(1 if failed else 0)
PY

  if [[ $? -eq 0 ]]; then
    pass "Both model health endpoints reachable from Gradio"
  else
    fail "One or more model health checks failed from Gradio"
  fi
fi

section "7. Local Traefik route"

if command -v curl >/dev/null 2>&1; then
  http_code="$(curl -sS -o /dev/null -w '%{http_code}' http://127.0.0.1/proxy/7860/ 2>/dev/null || true)"

  if [[ "$http_code" == "200" ]]; then
    pass "Traefik route /proxy/7860/ returns HTTP 200"
  else
    warn "Traefik route returned HTTP ${http_code:-no-response}"
  fi
else
  warn "curl not installed; skipping local Ingress check"
fi

section "8. NetworkPolicy"

if kubectl get networkpolicy -n beamdata >/dev/null 2>&1; then
  kubectl get networkpolicy -n beamdata
  count="$(kubectl get networkpolicy -n beamdata --no-headers 2>/dev/null | wc -l | tr -d ' ')"

  if [[ "$count" -gt 0 ]]; then
    pass "$count NetworkPolicy resource(s) present"
  else
    warn "No NetworkPolicy resources present"
  fi
else
  warn "Could not query NetworkPolicy resources"
fi

section "9. Disk usage"

df -h /data 2>/dev/null || df -h /

usage="$(df -P /data 2>/dev/null | awk 'NR==2 {gsub("%","",$5); print $5}')"

if [[ -n "${usage:-}" ]]; then
  if (( usage >= 90 )); then
    fail "/data usage is ${usage}% — high risk of DiskPressure"
  elif (( usage >= 80 )); then
    warn "/data usage is ${usage}% — monitor before pulling/importing large images"
  else
    pass "/data usage is ${usage}%"
  fi
fi

section "10. YAML client-side validation"

yaml_fail=0

while IFS= read -r file; do
  if [[ "$file" == *"nvidia-device-plugin-patch.yaml" ]]; then
    echo "SKIP (patch file): $file"
    continue
  fi

  if kubectl apply --dry-run=client -f "$file" >/dev/null 2>&1; then
    echo "OK: $file"
  else
    echo "FAILED: $file"
    yaml_fail=$((yaml_fail+1))
  fi
done < <(find deployment/k3s -type f -name '*.yaml' | sort)

if (( yaml_fail == 0 )); then
  pass "All standalone Kubernetes YAML files passed client-side validation"
else
  fail "$yaml_fail YAML file(s) failed client-side validation"
fi

section "Summary"

echo "PASS: $PASS"
echo "WARN: $WARN"
echo "FAIL: $FAIL"

if (( FAIL > 0 )); then
  red "Verification completed with failures."
  exit 1
elif (( WARN > 0 )); then
  yellow "Verification completed with warnings."
  exit 0
else
  green "Verification completed successfully."
  exit 0
fi
