# Deployment B - Kubernetes GPU Time-Slicing

## Purpose

The AIDC server has one physical NVIDIA RTX A6000 GPU.

Without GPU sharing, Kubernetes advertises:

nvidia.com/gpu: 1

This prevents two separate model Pods from each requesting one GPU at the same time.

The goal of this configuration is to enable NVIDIA CUDA time-slicing with two logical GPU replicas so that:

- FLUX can request one logical GPU
- Z-Image can request one logical GPU
- both Pods can run on the same physical RTX A6000

## Important

Time-slicing does NOT partition VRAM.

Both workloads still share the same physical GPU memory.

The two logical resources are scheduling/access slots, not two independent GPUs.

The current target is:

Physical GPU:
- 1x NVIDIA RTX A6000
- ~48 GB VRAM

Logical Kubernetes resources after configuration:
- nvidia.com/gpu: 2

## Apply

Create the NVIDIA time-slicing ConfigMap:

kubectl apply -f deployment/k8s/gpu-sharing/nvidia-time-slicing-configmap.yaml

Patch the existing NVIDIA device plugin:

kubectl patch daemonset \
  -n kube-system \
  nvidia-device-plugin-daemonset \
  --type strategic \
  --patch-file deployment/k8s/gpu-sharing/nvidia-device-plugin-patch.yaml

Wait for the plugin to restart:

kubectl rollout status daemonset/nvidia-device-plugin-daemonset \
  -n kube-system

## Validation

Check plugin status:

kubectl get pods -n kube-system | grep nvidia

Check GPU resources:

kubectl get node aidc-t09 \
-o jsonpath='{.status.capacity.nvidia\.com/gpu}{" capacity\n"}{.status.allocatable.nvidia\.com/gpu}{" allocatable\n"}'

Expected result:

2 capacity
2 allocatable

Also inspect:

kubectl describe node aidc-t09 | grep -A10 -B5 'nvidia.com/gpu'

## Rollback

If time-slicing causes problems:

kubectl rollout undo daemonset/nvidia-device-plugin-daemonset \
  -n kube-system

kubectl delete configmap nvidia-device-plugin-config \
  -n kube-system

Then verify that Kubernetes returns to:

1 capacity
1 allocatable

## Next Test

After GPU sharing is confirmed:

1. Deploy FLUX Pod requesting nvidia.com/gpu: 1
2. Deploy Z-Image Pod requesting nvidia.com/gpu: 1
3. Verify both Pods are Running
4. Verify both see the RTX A6000
5. Generate using each model independently
6. Generate using both simultaneously
7. Measure:
   - peak VRAM
   - GPU utilization
   - generation latency
   - failures / OOM
