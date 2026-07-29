#!/usr/bin/env python3
"""构建耗时度量脚本（Docker 镜像构建优化）。

度量 Cold_Build（``--no-cache`` + 清理可复用层）与 Incremental_Build（复用缓存层）
两种场景的构建耗时，每种场景至少连续执行 3 次，逐次以秒（≥2 位小数）计时，并将
基线记录追加写入 JSON 文件。

设计要点（见 design.md 第 7 节、Data Models 节）：
- **纯逻辑与构建执行解耦**：平均计算、阈值判定、记录构造、基线 JSON 读写等均为不依赖
  真实构建的纯函数，便于单元测试（任务 8.2）直接覆盖。
- **构建执行**：``run_single_build`` / ``run_benchmark`` 通过 subprocess 先构建共享
  基础镜像 ``jonex/python-base:local``，再以 ``COMPOSE_BAKE=1 docker compose build``
  并行构建 deploy-* 镜像，用 ``time.perf_counter`` 计时；单次失败/中断被捕获并标记为
  invalid，不计入平均、不覆盖已有有效记录。

CLI 用法::

    python deploy/scripts/build_benchmark.py \
        --scenario cold \
        --repeat 3 \
        --baseline deploy/build-baseline.json

需求对应：6.1, 6.2, 6.3, 6.4
"""

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

# ---------------------------------------------------------------------------
# 常量
# ---------------------------------------------------------------------------

#: 场景标识
SCENARIO_COLD = "cold"
SCENARIO_INCREMENTAL = "incremental"
VALID_SCENARIOS = (SCENARIO_COLD, SCENARIO_INCREMENTAL)

#: 耗时保留小数位（需求 6.1：秒，精度至少 2 位小数）
DURATION_PRECISION = 2

#: Incremental 单次 ≤ Cold 平均的比例阈值（需求 6.2）
INCREMENTAL_THRESHOLD_RATIO = 0.5

#: 构建入口：compose 流程（先构建共享 python-base，再 COMPOSE_BAKE 并行 compose build）
DEFAULT_COMPOSE_FILE = "deploy/docker-compose.yml"
PYTHON_BASE_TAG = "jonex/python-base:local"
PYTHON_BASE_DOCKERFILE = "deploy/docker/python-base.Dockerfile"


# ===========================================================================
# 纯逻辑函数（不触发真实构建，单元测试可直接覆盖）
# ===========================================================================


def round_duration(seconds: float) -> float:
    """将耗时四舍五入到约定的小数精度（秒，≥2 位小数）。"""
    return round(float(seconds), DURATION_PRECISION)


def compute_average(durations: Sequence[float]) -> Optional[float]:
    """计算平均耗时，**仅基于传入的有效耗时**（需求 6.3）。

    传入的 ``durations`` 约定为有效次数的耗时列表（invalid 次数不在其中）。

    Args:
        durations: 有效构建耗时序列（秒）。

    Returns:
        平均耗时（保留约定小数位）；当没有任何有效次数时返回 ``None``。
    """
    valid = [float(d) for d in durations if d is not None]
    if not valid:
        return None
    return round_duration(sum(valid) / len(valid))


def is_incremental_within_threshold(
    incremental_duration: float,
    cold_average: float,
    ratio: float = INCREMENTAL_THRESHOLD_RATIO,
) -> bool:
    """判定 Incremental 单次耗时是否 ≤ Cold 平均耗时的指定比例（需求 6.2）。

    Args:
        incremental_duration: Incremental_Build 单次耗时（秒）。
        cold_average: 同环境 Cold_Build 平均耗时（秒）。
        ratio: 比例阈值，默认 0.5（即 50%）。

    Returns:
        当 ``incremental_duration <= cold_average * ratio`` 时返回 ``True``。

    Raises:
        ValueError: 当 ``cold_average`` 非正数（无法作为有效基准）时。
    """
    if cold_average is None or cold_average <= 0:
        raise ValueError("cold_average 必须为正数才能进行阈值判定")
    return float(incremental_duration) <= cold_average * ratio


def collect_environment() -> Dict[str, Any]:
    """采集度量环境信息（如逻辑核心数），用于基线记录的 ``environment`` 字段。"""
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
    """构造一条结构完整的基线记录（纯函数）。

    字段遵循 design.md Data Models 节示例：``scenario`` / ``durations`` / ``average``
    / ``invalid_runs`` / ``timestamp`` / ``environment``。``average`` 仅基于有效次数
    （即 ``durations`` 中的耗时）计算。

    Args:
        scenario: 场景类型（``cold`` 或 ``incremental``）。
        durations: 有效构建耗时序列（秒）。
        invalid_runs: 失败/中断的次数记录，形如 ``[{"index": int, "reason": str}]``。
        environment: 度量环境信息；为 ``None`` 时不采集（保持纯函数特性，由调用方注入）。
        timestamp: ISO8601 时间戳；为 ``None`` 时使用当前本地时间。

    Returns:
        基线记录字典。
    """
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
    """返回一个空的基线结构（``{"records": []}``）。"""
    return {"records": []}


def append_record(
    baseline: Dict[str, Any],
    record: Dict[str, Any],
) -> Dict[str, Any]:
    """将一条记录**追加**到基线中，返回新的基线对象（纯函数）。

    采用追加语义而非覆盖：已有的有效记录不会被新记录替换/删除（需求 6.4——
    保留已记录的有效度量数据不被覆盖）。

    Args:
        baseline: 现有基线结构（含 ``records`` 列表）。
        record: 待追加的记录。

    Returns:
        追加后的新基线对象（原 ``baseline`` 不被原地修改）。
    """
    existing = list(baseline.get("records", []))
    existing.append(record)
    merged = dict(baseline)
    merged["records"] = existing
    return merged


def split_runs(
    run_results: Sequence[Dict[str, Any]],
) -> Dict[str, List[Any]]:
    """将逐次构建结果拆分为有效耗时列表与无效次数记录列表（纯函数）。

    每个 ``run_result`` 形如::

        {"index": int, "duration": Optional[float], "error": Optional[str]}

    其中 ``duration`` 为 ``None`` 或存在 ``error`` 视为无效次数（不计入平均）。

    Returns:
        ``{"durations": [...有效耗时...], "invalid_runs": [{"index", "reason"}...]}``
    """
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


# ---------------------------------------------------------------------------
# 基线 JSON 读写（IO 边界，仍尽量保持简单可测）
# ---------------------------------------------------------------------------


def load_baseline(path: str | Path) -> Dict[str, Any]:
    """从磁盘加载基线 JSON；文件不存在或为空时返回空基线结构。"""
    p = Path(path)
    if not p.exists() or p.stat().st_size == 0:
        return empty_baseline()
    with p.open("r", encoding="utf-8") as f:
        data = json.load(f)
    if "records" not in data or not isinstance(data.get("records"), list):
        data["records"] = []
    return data


def save_baseline(path: str | Path, baseline: Dict[str, Any]) -> None:
    """将基线结构写回磁盘（UTF-8、缩进 2、保留非 ASCII）。"""
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("w", encoding="utf-8") as f:
        json.dump(baseline, f, ensure_ascii=False, indent=2)
        f.write("\n")


def append_record_to_file(
    path: str | Path,
    record: Dict[str, Any],
) -> Dict[str, Any]:
    """加载现有基线、追加一条记录并写回，返回更新后的基线（不覆盖已有有效记录）。"""
    baseline = load_baseline(path)
    updated = append_record(baseline, record)
    save_baseline(path, updated)
    return updated


# ===========================================================================
# 构建执行（IO / subprocess，单元测试通过注入 runner 旁路）
# ===========================================================================


def _build_env() -> Dict[str, str]:
    """构建用环境变量：启用 BuildKit + COMPOSE_BAKE（compose build 委托 buildx bake 并行）。"""
    env = dict(os.environ)
    env["DOCKER_BUILDKIT"] = "1"
    env["COMPOSE_BAKE"] = "1"
    env.setdefault("BUILDX_BAKE_ENTITLEMENTS_FS", "0")
    return env


def _python_base_command(no_cache: bool) -> List[str]:
    """构建共享基础镜像 jonex/python-base:local 并 --load 进本地镜像库。"""
    cmd = ["docker", "buildx", "build", "--load"]
    if no_cache:
        cmd.append("--no-cache")
    cmd += ["-t", PYTHON_BASE_TAG, "-f", PYTHON_BASE_DOCKERFILE, "."]
    return cmd


def _compose_build_command(compose_file: str, no_cache: bool) -> List[str]:
    """并行 compose 构建（产出 deploy-* 镜像）。"""
    cmd = ["docker", "compose", "-f", compose_file, "build"]
    if no_cache:
        cmd.append("--no-cache")
    return cmd


def _prune_reusable_layers() -> None:
    """Cold_Build 前清理可复用层（builder 缓存），确保无缓存可用。

    失败不致命（例如无 buildx builder 时），仅输出提示。
    """
    try:
        subprocess.run(
            ["docker", "buildx", "prune", "-f"],
            check=False,
            capture_output=True,
        )
    except OSError as exc:  # pragma: no cover - 取决于本机 docker 可用性
        print(f"[warn] 清理可复用层失败（忽略）：{exc}", file=sys.stderr)


def run_single_build(
    scenario: str,
    compose_file: str = DEFAULT_COMPOSE_FILE,
) -> Dict[str, Any]:
    """触发单次构建并用 ``perf_counter`` 计时（秒，≥2 位小数）。

    构建分两步：① 构建共享基础镜像 python-base；② COMPOSE_BAKE 并行 compose build。
    Cold 场景两步均 ``--no-cache`` 并先清理可复用层；Incremental 复用缓存层。

    单次构建失败/中断（非零退出码、异常、被 Ctrl-C 中断）会被捕获，返回携带
    ``error`` 的结果，由上层标记该次为 invalid（不计入平均、不覆盖已有有效记录）。

    Returns:
        ``{"duration": Optional[float], "error": Optional[str]}``
    """
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
    """连续执行 ``repeat`` 次构建并构造一条基线记录。

    Args:
        scenario: 场景类型。
        repeat: 重复次数（应 ≥3，见需求 6.1）。
        runner: 单次构建执行器（默认 :func:`run_single_build`）；测试可注入桩。
        environment: 注入的环境信息；默认调用 :func:`collect_environment`。

    Returns:
        基线记录（含 ``durations`` / ``average`` / ``invalid_runs`` 等）。
    """
    if scenario not in VALID_SCENARIOS:
        raise ValueError(f"非法 scenario: {scenario!r}，应为 {VALID_SCENARIOS}")

    actual_runner = runner or (lambda s: run_single_build(s))
    run_results: List[Dict[str, Any]] = []
    for i in range(repeat):
        print(f"[info] {scenario} 第 {i + 1}/{repeat} 次构建开始……")
        result = actual_runner(scenario)
        result["index"] = i
        if result.get("error"):
            # 需求 6.4：输出指示失败原因的错误信息
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


# ===========================================================================
# CLI
# ===========================================================================


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

    runner = lambda s: run_single_build(  # noqa: E731
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

    # 需求 6.2：若本次为 incremental 且基线中存在 cold 平均，给出阈值判定提示
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

    # 全部失败视为度量未取得有效数据
    if not record["durations"]:
        print("[error] 本次度量未获得任何有效耗时。", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
