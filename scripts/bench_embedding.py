

import asyncio
import os
import statistics
import time

import httpx

HOST = os.getenv("OLLAMA_HOST", "http://127.0.0.1:11434").rstrip("/")
MODEL = os.getenv("EMBED_MODEL", "qwen3-embedding:8b")
ENDPOINT = f"{HOST}/api/embed"


REQUESTS_PER_LEVEL = int(os.getenv("BENCH_REQ", "48"))
CONCURRENCY_LEVELS = [int(x) for x in os.getenv("BENCH_LEVELS", "1,2,4,8,16").split(",")]


_TEXT_MUL = int(os.getenv("BENCH_TEXT_MUL", "3"))


SAMPLE_TEXT = (
    "Jonex平台是一个插件化 AI 能力平台框架，通过可组合的 capability 对外提供业务服务。"
    "知识库能力封装 RAG 检索，向量检索经 Milvus，本体图谱存储于 Neo4j，"
    "所有 LLM 与 embedding 调用统一经 llm-gateway 出口。"
) * _TEXT_MUL



BATCH_NUM = int(os.getenv("BENCH_BATCH", "1"))


async def one_request(client: httpx.AsyncClient, idx: int) -> tuple[bool, float, int, str]:

    inp = SAMPLE_TEXT if BATCH_NUM <= 1 else [SAMPLE_TEXT] * BATCH_NUM
    payload = {"model": MODEL, "input": inp}
    t0 = time.perf_counter()
    try:
        resp = await client.post(ENDPOINT, json=payload)
        dt = time.perf_counter() - t0
        if resp.status_code != 200:
            return False, dt, 0, f"HTTP {resp.status_code}: {resp.text[:120]}"
        data = resp.json()
        embs = data.get("embeddings") or []
        dim = len(embs[0]) if embs and isinstance(embs[0], list) else 0
        return True, dt, dim, ""
    except Exception as e:
        return False, time.perf_counter() - t0, 0, repr(e)[:120]


async def run_level(concurrency: int, total: int) -> None:
    sem = asyncio.Semaphore(concurrency)
    latencies: list[float] = []
    ok = 0
    errors: list[str] = []
    dim_seen = 0

    limits = httpx.Limits(max_connections=concurrency + 4, max_keepalive_connections=concurrency + 4)
    async with httpx.AsyncClient(timeout=httpx.Timeout(600.0), limits=limits) as client:

        async def guarded(i: int):
            nonlocal ok, dim_seen
            async with sem:
                success, dt, dim, err = await one_request(client, i)
                latencies.append(dt)
                if success:
                    ok += 1
                    dim_seen = dim or dim_seen
                elif len(errors) < 3:
                    errors.append(err)

        wall0 = time.perf_counter()
        await asyncio.gather(*(guarded(i) for i in range(total)))
        wall = time.perf_counter() - wall0

    lat_sorted = sorted(latencies)

    def pct(p: float) -> float:
        if not lat_sorted:
            return 0.0
        k = min(len(lat_sorted) - 1, int(round(p * (len(lat_sorted) - 1))))
        return lat_sorted[k]

    thr = ok / wall if wall > 0 else 0.0
    chunk_thr = ok * BATCH_NUM / wall if wall > 0 else 0.0
    print(
        f"并发={concurrency:<3} batch={BATCH_NUM:<2} 请求={total:<3} 成功={ok:<3} "
        f"墙钟={wall:6.1f}s | 请求吞吐={thr:5.2f} req/s chunk吞吐={chunk_thr:6.2f} chunk/s | "
        f"单请求 p50={pct(0.5):5.2f}s p95={pct(0.95):5.2f}s "
        f"max={max(latencies):5.2f}s | dim={dim_seen}"
    )
    if errors:
        print(f"    示例错误: {errors}")


async def main() -> None:
    print(f"目标: {ENDPOINT}  模型: {MODEL}")
    print(f"样本文本长度: {len(SAMPLE_TEXT)} 字符; 每档请求数: {REQUESTS_PER_LEVEL}\n")


    print("预热中（加载模型）...")
    async with httpx.AsyncClient(timeout=httpx.Timeout(600.0)) as client:
        ok, dt, dim, err = await one_request(client, -1)
        print(f"预热: 成功={ok} 延迟={dt:.2f}s dim={dim} {err}\n")

    for level in CONCURRENCY_LEVELS:
        await run_level(level, REQUESTS_PER_LEVEL)


if __name__ == "__main__":
    asyncio.run(main())
