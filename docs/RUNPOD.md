# Strata on RunPod Serverless

Deployment preparation checked on 2026-10-02. This configuration has not yet been built or tested on RunPod hardware.

## Repository and image

- Repository: TommyTheGreatExplorer/Strata
- Branch: main
- Dockerfile path: Dockerfile (repository root)
- Endpoint type: Load Balancer, for the existing OpenAI/Anthropic HTTP API and streaming.
- Keep the image's existing entrypoint.

The existing server exposes /health. Current RunPod supports HEALTH_CHECK_PATH, so a /ping code patch is unnecessary.

## Endpoint settings

| Setting | Initial value |
| --- | --- |
| Health check endpoint | /health |
| Expose HTTP port | 8080 |
| Minimum / active workers | 0 |
| Maximum workers | 1 |
| Network volume | Attach before first model setup |

Keep maximum workers at 1 while the model and packs are prepared: concurrent setup writes to one volume can corrupt data.

## Environment variables

| Name | Value |
| --- | --- |
| PORT | 8080 |
| PORT_HEALTH | 8080 |
| HEALTH_CHECK_PATH | /health |
| HOST | 0.0.0.0 |
| STRATA_DATA | /runpod-volume/strata |
| FAMILY | qwen |
| MODEL | IQ2_XS |
| CONTEXT | 32768 |
| VISION | no |
| GPU | 0 |
| API_KEY | Supply a long random secret through RunPod configuration; never commit it |

RunPod mounts Serverless network volumes at /runpod-volume. STRATA_DATA points model files, packs, draft layer and install configuration at that persistent volume instead of the container's /data directory.

## Hardware and storage checks

A starting target is a supported 24 GB NVIDIA GPU, at least 64 GB allocated system RAM, an x86-64 AVX2 CPU and a 150 GB standard network volume. These are planning values, not measured RunPod results. Verify allocated RAM and available disk before setup. Strata also uses CPU and system RAM, not just GPU VRAM.

The Dockerfile uses CUDA 13.0 and requires NVIDIA driver 580 or newer. Its default GPU architectures are 75, 80, 86, 89 and 120; other GPUs need the correct CUDA_ARCHITECTURES build argument. Confirm the chosen worker is compatible before paying for model setup.

The upstream entrypoint detects host RAM rather than a container memory cap. If the assigned memory is insufficient, choose a suitable smaller model or evaluate LOW_RAM=on; that mode can depend heavily on storage throughput. Do not assume a small GPU tier supplies 64 GB system RAM.

## First start and validation

1. Build the image and read build logs.
2. Confirm the network volume is attached and API_KEY is configured.
3. First start downloads roughly 70 GB of model data, prepares artifacts and loads the engine. GPU compute is billed throughout startup.
4. Watch worker logs. The server's HTTP port opens after engine loading. The initial download may exceed RunPod startup/health limits; if it repeatedly restarts, pre-populate the same model directory using a controlled bootstrap workload before serving requests.
5. Verify /health, then /v1/models and a small /v1/chat/completions request. Test streaming separately and confirm client and platform authentication requirements.
6. Let the worker scale to zero and verify files persist and the next start skips downloading.

RunPod's documented Load Balancer limits include a 2-minute wait when no worker is available and a 5.5-minute processing timeout. Cold starts may need client retries; this setup is not yet validated for long agent requests.

Settings such as host, API key, context and vision are saved in the model configuration. Upstream documents REINSTALL=1 for changing saved settings; use it for reconfiguration and remove it afterward.

## Cost

A 150 GB standard network volume is approximately USD 10.50/month at USD 0.07/GB/month. Storage continues billing when workers stop. Flex compute scales to zero; startup, inference and idle timeout are billed while a worker runs. Container disk is a separate storage component.

## References

- [Strata Docker installation](INSTALL.md#docker-linux)
- [RunPod GitHub builds](https://docs.runpod.io/serverless/workers/github-integration)
- [RunPod Load Balancer configuration and limits](https://docs.runpod.io/serverless/load-balancing/overview)
- [RunPod network volumes](https://docs.runpod.io/storage/network-volumes)
- [RunPod Serverless billing](https://docs.runpod.io/serverless/pricing)
