#!/usr/bin/env python3


from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Sequence






SCENARIO_COLD = "cold"
SCENARIO_INCREMENTAL = "incremental"
VALID_SCENARIOS = (SCENARIO_COLD, SCENARIO_INCREMENTAL)


DURATION_PRECISION = 2


INCREMENTAL_THRESHOLD_RATIO = 0.5


DEFAULT_COMPOSE_FILE = "deploy/docker-compose.yml"
PYTHON_BASE_TAG = "jonex/python-base:local"
PYTHON_BASE_DOCKERFILE = "deploy/docker/python-base.Dockerfile"







def round_duration(seconds: float) -> float:

    return round(float(seconds), DURATION_PRECISION)


def compute_average(durations: Sequence[float]) -> Optional[float]:

    valid = [float(d) for d in durations if d is not None]
    if not valid:
        return None
    return round_duration(sum(valid) / len(valid))


def is_incremental_within_threshold(
    incremental_duration: float,
    cold_average: float,
    ratio: float = INCREMENTAL_THRESHOLD_RATIO,
) -> bool:

    if cold_average is None or cold_average <= 0:
        raise ValueError("cold_average 必须为正数才能进行阈值判定")
    return float(incremental_duration) <= cold_average * ratio


def collect_environment() -> Dict[str, Any]:

    return {
        "cpu_logical": os.cpu_count(),
        "platform": sys.platform,
    }


def build_baseline_record(
    scenario: str,
    durations: Sequence[float],
    invalid_runs: Optional[Sequence[Dict[str, Any]]] = None,
    environment: Optional[Dict[str, Any]] = None,
    timestamp: Optional[str] = None,
) -> Dict[str, Any]:

    if scenario not in VALID_SCENARIOS:
        raise ValueError(f"非法 scenario: {scenario!r}，应为 {VALID_SCENARIOS}")

    rounded = [round_duration(d) for d in durations]
    record: Dict[str, Any] = {
        "scenario": scenario,
        "durations": rounded,
        "average": compute_average(rounded),
        "invalid_runs": list(invalid_runs or []),
        "timestamp": timestamp or datetime.now().astimezone().isoformat(),
    }
    if environment is not None:
        record["environment"] = environment
    return record


def empty_baseline() -> Dict[str, Any]:

    return {"records": []}


def append_record(
    baseline: Dict[str, Any],
    record: Dict[str, Any],
) -> Dict[str, Any]:

    existing = list(baseline.get("records", []))
    existing.append(record)
    merged = dict(baseline)
    merged["records"] = existing
    return merged


def split_runs(
    run_results: Sequence[Dict[str, Any]],
) -> Dict[str, List[Any]]:

    durations: List[float] = []
    invalid_runs: List[Dict[str, Any]] = []
    for result in run_results:
        duration = result.get("duration")
        error = result.get("error")
        if error is not None or duration is None:
            invalid_runs.append(
                {
                    "index": result.get("index"),
                    "reason": error or "构建未返回有效耗时",
                }
            )
        else:
            durations.append(round_duration(duration))
    return {"durations": durations, "invalid_runs": invalid_runs}







def load_baseline(path: str | Path) -> Dict[str, Any]:

    p = Path(path)
    if not p.exists() or p.stat().st_size == 0:
        return empty_baseline()
    with p.open("r", encoding="utf-8") as f:
        data = json.load(f)
    if "records" not in data or not isinstance(data.get("records"), list):
        data["records"] = []
    return data


def save_baseline(path: str | Path, baseline: Dict[str, Any]) -> None:

    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("w", encoding="utf-8") as f:
        json.dump(baseline, f, ensure_ascii=False, indent=2)
        f.write("\n")


def append_record_to_file(
    path: str | Path,
    record: Dict[str, Any],
) -> Dict[str, Any]:

    baseline = load_baseline(path)
    updated = append_record(baseline, record)
    save_baseline(path, updated)
    return updated







def _build_env() -> Dict[str, str]:

    env = dict(os.environ)
    env["DOCKER_BUILDKIT"] = "1"
    env["COMPOSE_BAKE"] = "1"
    env.setdefault("BUILDX_BAKE_ENTITLEMENTS_FS", "0")
    return env


def _python_base_command(no_cache: bool) -> List[str]:

    cmd = ["docker", "buildx", "build", "--load"]
    if no_cache:
        cmd.append("--no-cache")
    cmd += ["-t", PYTHON_BASE_TAG, "-f", PYTHON_BASE_DOCKERFILE, "."]
    return cmd


def _compose_build_command(compose_file: str, no_cache: bool) -> List[str]:

    cmd = ["docker", "compose", "-f", compose_file, "build"]
    if no_cache:
        cmd.append("--no-cache")
    return cmd


def _prune_reusable_layers() -> None:

    try:
        subprocess.run(
            ["docker", "buildx", "prune", "-f"],
            check=False,
            capture_output=True,
        )
    except OSError as exc:
        print(f"[warn] 清理可复用层失败（忽略）：{exc}", file=sys.stderr)


def run_single_build(
    scenario: str,
    compose_file: str = DEFAULT_COMPOSE_FILE,
) -> Dict[str, Any]:

    if scenario == SCENARIO_COLD:
        no_cache = True
        _prune_reusable_layers()
    elif scenario == SCENARIO_INCREMENTAL:
        no_cache = False
    else:
        raise ValueError(f"非法 scenario: {scenario!r}")

    env = _build_env()
    steps = [
        _python_base_command(no_cache),
        _compose_build_command(compose_file, no_cache),
    ]

    start = time.perf_counter()
    try:
        for cmd in steps:
            completed = subprocess.run(cmd, check=False, env=env)
            if completed.returncode != 0:
                return {
                    "duration": None,
                    "error": f"构建失败：命令 {' '.join(cmd)} 退出码 {completed.returncode}",
                }
        elapsed = time.perf_counter() - start
        return {"duration": round_duration(elapsed), "error": None}
    except KeyboardInterrupt:
        return {"duration": None, "error": "构建被中断（KeyboardInterrupt）"}
    except OSError as exc:
        return {"duration": None, "error": f"构建启动失败：{exc}"}


def run_benchmark(
    scenario: str,
    repeat: int,
    runner: Optional[Callable[[str], Dict[str, Any]]] = None,
    environment: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:

    if scenario not in VALID_SCENARIOS:
        raise ValueError(f"非法 scenario: {scenario!r}，应为 {VALID_SCENARIOS}")

    actual_runner = runner or (lambda s: run_single_build(s))
    run_results: List[Dict[str, Any]] = []
    for i in range(repeat):
        print(f"[info] {scenario} 第 {i + 1}/{repeat} 次构建开始……")
        result = actual_runner(scenario)
        result["index"] = i
        if result.get("error"):

            print(f"[error] 第 {i + 1} 次构建无效：{result['error']}", file=sys.stderr)
        else:
            print(f"[info] 第 {i + 1} 次构建耗时 {result['duration']:.2f}s")
        run_results.append(result)

    split = split_runs(run_results)
    return build_baseline_record(
        scenario=scenario,
        durations=split["durations"],
        invalid_runs=split["invalid_runs"],
        environment=environment if environment is not None else collect_environment(),
    )







def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Docker 镜像构建耗时度量（Cold / Incremental）",
    )
    parser.add_argument(
        "--scenario",
        choices=list(VALID_SCENARIOS),
        required=True,
        help="度量场景：cold（无缓存全量）或 incremental（复用缓存层）",
    )
    parser.add_argument(
        "--repeat",
        type=int,
        default=3,
        help="连续执行次数（需求 6.1 要求 ≥3，默认 3）",
    )
    parser.add_argument(
        "--baseline",
        default="deploy/build-baseline.json",
        help="基线 JSON 文件路径（追加写入，不覆盖已有有效记录）",
    )
    parser.add_argument(
        "--compose-file",
        default=DEFAULT_COMPOSE_FILE,
        help="docker compose 配置文件路径（默认 deploy/docker-compose.yml）",
    )
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = build_arg_parser()
    args = parser.parse_args(argv)

    if args.repeat < 3:
        print(
            f"[warn] repeat={args.repeat} 少于需求要求的 3 次，仍按指定次数执行。",
            file=sys.stderr,
        )

    runner = lambda s: run_single_build(
        s, compose_file=args.compose_file
    )
    record = run_benchmark(args.scenario, args.repeat, runner=runner)

    updated = append_record_to_file(args.baseline, record)
    print(
        f"[info] 已写入基线 {args.baseline}："
        f"scenario={record['scenario']} "
        f"有效次数={len(record['durations'])} "
        f"无效次数={len(record['invalid_runs'])} "
        f"average={record['average']}"
    )


    if args.scenario == SCENARIO_INCREMENTAL and record["durations"]:
        cold_averages = [
            r["average"]
            for r in updated.get("records", [])
            if r.get("scenario") == SCENARIO_COLD and r.get("average")
        ]
        if cold_averages:
            latest_cold_avg = cold_averages[-1]
            single = record["durations"][-1]
            within = is_incremental_within_threshold(single, latest_cold_avg)
            verdict = "达标" if within else "未达标"
            print(
                f"[info] 阈值判定（Incremental 单次 ≤ Cold 平均 50%）：{verdict} "
                f"（单次 {single:.2f}s vs Cold 平均 {latest_cold_avg:.2f}s）"
            )


    if not record["durations"]:
        print("[error] 本次度量未获得任何有效耗时。", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
