"""Audit and add verified summary semantics to existing MLflow runs.

The script never creates runs or experiments. It correlates completed FCOS
refinement runs with project artifacts that embed their exact MLflow run IDs.
Original metrics, parameters, tags, timestamps, and artifacts are preserved.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import sqlite3
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

NORMALIZATION_VERSION = "1"
SUMMARY_STEP = 0
METRIC_MAP = {
    "best/val_map50_95": "mAP50_95",
    "best/val_map50": "mAP50",
    "best/val_mar100": "recall",
    "last/val_map50_95": "mAP50_95",
    "last/val_map50": "mAP50",
    "last/val_mar100": "recall",
}
SUMMARY_TAGS = {
    "normalization/version": NORMALIZATION_VERSION,
    "normalization/status": "verified",
    "normalization/source": "project_artifacts",
}


@dataclass(frozen=True)
class VerifiedRun:
    run_id: str
    run_name: str
    category: str
    history_path: Path
    metrics_path: Path
    values: dict[str, float]
    best_epoch: int
    last_epoch: int


def find_project_root(start: Path | None = None) -> Path:
    current = (start or Path.cwd()).resolve()
    for candidate in (current, *current.parents):
        if (candidate / ".git").exists() and (candidate / ".dvc").exists():
            return candidate
    raise FileNotFoundError("Could not locate project root containing .git and .dvc")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sqlite_uri(path: Path, *, read_only: bool = False) -> str:
    suffix = "?mode=ro" if read_only else ""
    return f"file:{path.resolve().as_posix()}{suffix}"


def tracking_uri(path: Path) -> str:
    return f"sqlite:///{path.resolve().as_posix()}"


def connect_read_only(path: Path) -> sqlite3.Connection:
    connection = sqlite3.connect(sqlite_uri(path, read_only=True), uri=True)
    connection.row_factory = sqlite3.Row
    return connection


def database_counts(connection: sqlite3.Connection) -> dict[str, int]:
    counts = {
        table: connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        for table in ("experiments", "runs", "metrics", "latest_metrics", "params", "tags")
    }
    counts["finished_runs"] = connection.execute(
        "SELECT COUNT(*) FROM runs WHERE status='FINISHED'"
    ).fetchone()[0]
    counts["failed_runs"] = connection.execute(
        "SELECT COUNT(*) FROM runs WHERE status='FAILED'"
    ).fetchone()[0]
    return counts


def logical_database_diff(before_path: Path, after_path: Path) -> dict[str, dict[str, int]]:
    connection = sqlite3.connect(after_path)
    try:
        connection.execute("ATTACH DATABASE ? AS old", (str(before_path),))
        tables = [
            row[0]
            for row in connection.execute(
                "SELECT name FROM main.sqlite_master "
                "WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name"
            )
        ]
        changes: dict[str, dict[str, int]] = {}
        for table in tables:
            columns = [row[1] for row in connection.execute(f'PRAGMA main.table_info("{table}")')]
            if not columns:
                continue
            selection = ",".join(f'"{column}"' for column in columns)
            added = connection.execute(
                f'SELECT COUNT(*) FROM (SELECT {selection} FROM main."{table}" '
                f'EXCEPT SELECT {selection} FROM old."{table}")'
            ).fetchone()[0]
            deleted = connection.execute(
                f'SELECT COUNT(*) FROM (SELECT {selection} FROM old."{table}" '
                f'EXCEPT SELECT {selection} FROM main."{table}")'
            ).fetchone()[0]
            if added or deleted:
                changes[table] = {
                    "rows_added_or_modified": added,
                    "rows_deleted_or_modified": deleted,
                }
        return changes
    finally:
        connection.close()


def classify_run(run_name: str) -> str:
    if run_name == "E0_yolo26n_640_baseline":
        return "historical_yolo_baseline"
    if run_name == "E1_ssd300":
        return "ssd_architecture_screening"
    if run_name == "E2_fcos_640":
        return "fcos_architecture_screening"
    if run_name.startswith("E3_fasterrcnn"):
        return "faster_rcnn_architecture_screening"
    if run_name.startswith("E4_detr"):
        return "detr_architecture_screening"
    if run_name.startswith("A"):
        return "optimizer_learning_rate_refinement"
    if run_name.startswith("B"):
        return "scheduler_refinement"
    if run_name.startswith("R"):
        return "regularization_refinement"
    if run_name.startswith("G"):
        return "gradient_clipping_refinement"
    if run_name.startswith("C"):
        return "augmentation_refinement"
    if run_name.startswith("V"):
        return "resolution_refinement"
    if run_name.startswith("D"):
        return "backbone_refinement"
    if run_name.startswith("E1_full") or run_name.startswith("E2_freeze") or run_name.startswith("E3_freeze"):
        return "fine_tuning_freezing_refinement"
    if run_name == "F_final_fcos_tuned":
        return "final_selected_fcos"
    return "unknown"


def load_runs(connection: sqlite3.Connection) -> list[dict[str, Any]]:
    query = """
        SELECT r.run_uuid AS run_id, r.experiment_id, e.name AS experiment_name,
               r.status, r.start_time, r.end_time, r.artifact_uri,
               COALESCE(name.value, '') AS run_name,
               COALESCE(parent.value, '') AS parent_run_id
        FROM runs r
        JOIN experiments e ON e.experiment_id = r.experiment_id
        LEFT JOIN tags name
          ON name.run_uuid = r.run_uuid AND name.key = 'mlflow.runName'
        LEFT JOIN tags parent
          ON parent.run_uuid = r.run_uuid AND parent.key = 'mlflow.parentRunId'
        ORDER BY r.start_time, r.run_uuid
    """
    return [dict(row) for row in connection.execute(query)]


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def original_epoch_values(
    connection: sqlite3.Connection, run_id: str, metric_key: str
) -> dict[int, float]:
    rows = connection.execute(
        "SELECT step, value FROM metrics WHERE run_uuid=? AND key=? ORDER BY timestamp",
        (run_id, metric_key),
    )
    values: dict[int, float] = {}
    for row in rows:
        # Legacy runs append a best-summary value at step 0. The first value at
        # each step is the epoch record written during training.
        values.setdefault(int(row["step"]), float(row["value"]))
    return values


def verify_refinement_runs(
    root: Path, connection: sqlite3.Connection, runs: list[dict[str, Any]]
) -> tuple[dict[str, VerifiedRun], dict[str, str]]:
    runs_by_id = {run["run_id"]: run for run in runs}
    verified: dict[str, VerifiedRun] = {}
    rejected: dict[str, str] = {}
    refinement_root = root / "artifacts" / "refinement" / "fcos"

    for metrics_path in sorted(refinement_root.glob("*/metrics.json")):
        summary = json.loads(metrics_path.read_text(encoding="utf-8"))
        run_id = summary.get("mlflow_run_id")
        run_name = summary.get("experiment_id")
        history_path = metrics_path.with_name("history.csv")
        if not run_id or not run_name or not history_path.exists():
            continue
        run = runs_by_id.get(run_id)
        if not run or run["run_name"] != run_name or run["status"] != "FINISHED":
            rejected[run_id] = "embedded run identity does not match a finished MLflow run"
            continue

        rows = read_csv(history_path)
        if not rows:
            rejected[run_id] = "history is empty"
            continue
        for expected_step, row in enumerate(rows):
            if int(float(row["epoch"])) != expected_step:
                rejected[run_id] = "history epochs are not contiguous and zero-based"
                break
        if run_id in rejected:
            continue

        for legacy_key in ("mAP50_95", "mAP50", "recall"):
            historical = original_epoch_values(connection, run_id, legacy_key)
            for row in rows:
                step = int(float(row["epoch"]))
                if step not in historical or not math.isclose(
                    float(row[legacy_key]), historical[step], rel_tol=0.0, abs_tol=1e-12
                ):
                    rejected[run_id] = f"history disagrees with MLflow {legacy_key} at step {step}"
                    break
            if run_id in rejected:
                break
        if run_id in rejected:
            continue

        best_index = max(range(len(rows)), key=lambda i: float(rows[i]["mAP50_95"]))
        best_epoch = best_index + 1
        last_epoch = len(rows)
        if int(summary["best_epoch"]) != best_epoch:
            rejected[run_id] = "metrics.json best_epoch disagrees with history"
            continue
        for key in ("mAP50_95", "mAP50"):
            if not math.isclose(
                float(summary[key]), float(rows[best_index][key]), rel_tol=0.0, abs_tol=1e-12
            ):
                rejected[run_id] = f"metrics.json {key} disagrees with best history row"
                break
        if run_id in rejected:
            continue

        values = {
            "best/val_map50_95": float(rows[best_index]["mAP50_95"]),
            "best/val_map50": float(rows[best_index]["mAP50"]),
            "best/val_mar100": float(rows[best_index]["recall"]),
            "best/epoch": float(best_epoch),
            "last/val_map50_95": float(rows[-1]["mAP50_95"]),
            "last/val_map50": float(rows[-1]["mAP50"]),
            "last/val_mar100": float(rows[-1]["recall"]),
            "last/epoch": float(last_epoch),
        }
        verified[run_id] = VerifiedRun(
            run_id=run_id,
            run_name=run_name,
            category=classify_run(run_name),
            history_path=history_path,
            metrics_path=metrics_path,
            values=values,
            best_epoch=best_epoch,
            last_epoch=last_epoch,
        )
    return verified, rejected


def existing_normalized_state(
    connection: sqlite3.Connection, run_id: str
) -> tuple[dict[str, float], dict[str, str]]:
    metrics = {
        row["key"]: float(row["value"])
        for row in connection.execute(
            "SELECT key, value FROM latest_metrics WHERE run_uuid=? AND (key LIKE 'best/%' OR key LIKE 'last/%')",
            (run_id,),
        )
    }
    tags = {
        row["key"]: row["value"]
        for row in connection.execute(
            "SELECT key, value FROM tags WHERE run_uuid=? AND key LIKE 'normalization/%'",
            (run_id,),
        )
    }
    return metrics, tags


def build_plan(
    connection: sqlite3.Connection, verified: dict[str, VerifiedRun]
) -> list[dict[str, Any]]:
    plan: list[dict[str, Any]] = []
    for run_id, item in sorted(verified.items(), key=lambda pair: pair[1].run_name):
        existing_metrics, existing_tags = existing_normalized_state(connection, run_id)
        for key, value in item.values.items():
            if key in existing_metrics:
                if not math.isclose(existing_metrics[key], value, rel_tol=0.0, abs_tol=1e-12):
                    raise RuntimeError(f"Conflicting normalized metric {key} for run {run_id}")
                action = "UNCHANGED"
            else:
                action = "ADD"
            plan.append(
                {
                    "run_id": run_id,
                    "run_name": item.run_name,
                    "source": item.history_path.relative_to(item.history_path.parents[3]).as_posix(),
                    "key": key,
                    "value": value,
                    "kind": "metric",
                    "confidence": "VERIFIED",
                    "action": action,
                }
            )
        for key, value in SUMMARY_TAGS.items():
            if key in existing_tags:
                if existing_tags[key] != value:
                    raise RuntimeError(f"Conflicting normalization tag {key} for run {run_id}")
                action = "UNCHANGED"
            else:
                action = "ADD"
            plan.append(
                {
                    "run_id": run_id,
                    "run_name": item.run_name,
                    "source": "normalization policy version 1",
                    "key": key,
                    "value": value,
                    "kind": "tag",
                    "confidence": "VERIFIED",
                    "action": action,
                }
            )
    return plan


def apply_plan(db_path: Path, plan: list[dict[str, Any]]) -> int:
    additions = [entry for entry in plan if entry["action"] == "ADD"]
    if not additions:
        return 0
    from mlflow.tracking import MlflowClient

    client = MlflowClient(tracking_uri=tracking_uri(db_path))
    for entry in additions:
        if entry["kind"] == "metric":
            client.log_metric(
                entry["run_id"], entry["key"], float(entry["value"]), step=SUMMARY_STEP
            )
        else:
            client.set_tag(entry["run_id"], entry["key"], str(entry["value"]))
    return len(additions)


def milliseconds_to_iso(value: int | None) -> str | None:
    if value is None:
        return None
    return datetime.fromtimestamp(value / 1000, tz=timezone.utc).isoformat()


def build_inventory(
    root: Path,
    runs: list[dict[str, Any]],
    verified: dict[str, VerifiedRun],
    rejected: dict[str, str],
) -> list[dict[str, Any]]:
    inventory = []
    for run in runs:
        run_id = run["run_id"]
        item = verified.get(run_id)
        if item:
            correlation = "VERIFIED"
            normalization_status = "NORMALIZED"
            sources = ";".join(
                [
                    item.metrics_path.relative_to(root).as_posix(),
                    item.history_path.relative_to(root).as_posix(),
                ]
            )
            normalized_keys = ";".join((*item.values.keys(), *SUMMARY_TAGS.keys()))
            notes = "Exact embedded run_id and row-level history agreement"
        else:
            correlation = "PARTIAL" if run["status"] == "FINISHED" else "SKIP"
            normalization_status = "SKIP"
            sources = ""
            normalized_keys = ""
            if run_id in rejected:
                notes = rejected[run_id]
            elif run["status"] != "FINISHED":
                notes = "Failed run preserved; no complete verified summary applied"
            elif run["run_name"].endswith("_mlflow_smoke"):
                notes = "Setup smoke run; not a modeling result"
            else:
                notes = "No project artifact with an embedded exact MLflow run_id"
        inventory.append(
            {
                "run_id": run_id,
                "experiment_id": run["experiment_id"],
                "experiment_name": run["experiment_name"],
                "run_name": run["run_name"],
                "status": run["status"],
                "start_time_utc": milliseconds_to_iso(run["start_time"]),
                "end_time_utc": milliseconds_to_iso(run["end_time"]),
                "parent_run_id": run["parent_run_id"],
                "category": classify_run(run["run_name"]),
                "artifact_uri": run["artifact_uri"],
                "correlation_status": correlation,
                "normalization_status": normalization_status,
                "source_artifacts": sources,
                "normalized_keys": normalized_keys,
                "uncertainty_notes": notes,
            }
        )
    return inventory


def write_inventory(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def write_report(path: Path, report: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true", help="Apply only verified missing summaries")
    parser.add_argument("--backup", type=Path, required=True, help="Verified pre-normalization DB backup")
    parser.add_argument("--report", type=Path)
    parser.add_argument("--inventory", type=Path)
    args = parser.parse_args()

    root = find_project_root()
    db_path = root / "artifacts" / "modeling" / "mlflow.db"
    backup_path = args.backup.resolve()
    if not backup_path.exists():
        raise FileNotFoundError(backup_path)
    backup_hash = sha256(backup_path)
    before_hash = sha256(db_path)
    if not args.apply and before_hash != backup_hash:
        # A post-normalization dry run is valid only when the DB already carries
        # version-1 summaries, checked below through the idempotent plan.
        pass

    with connect_read_only(backup_path) as backup_connection:
        if backup_connection.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
            raise RuntimeError("Backup MLflow SQLite integrity check failed")
        pre_normalization_counts = database_counts(backup_connection)

    with connect_read_only(db_path) as connection:
        if connection.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
            raise RuntimeError("MLflow SQLite integrity check failed")
        before_counts = database_counts(connection)
        runs = load_runs(connection)
        verified, rejected = verify_refinement_runs(root, connection, runs)
        if len(runs) != 49 or len(verified) != 36:
            raise RuntimeError(
                f"Unexpected forensic inventory: runs={len(runs)}, verified={len(verified)}"
            )
        plan = build_plan(connection, verified)

    planned_additions = sum(entry["action"] == "ADD" for entry in plan)
    applied_additions = apply_plan(db_path, plan) if args.apply else 0

    with connect_read_only(db_path) as connection:
        if connection.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
            raise RuntimeError("Post-operation SQLite integrity check failed")
        after_counts = database_counts(connection)
        runs_after = load_runs(connection)
        verified_after, rejected_after = verify_refinement_runs(root, connection, runs_after)
        remaining_plan = build_plan(connection, verified_after)
        remaining_additions = sum(entry["action"] == "ADD" for entry in remaining_plan)

    if args.apply and remaining_additions:
        raise RuntimeError(f"Normalization is not idempotent: {remaining_additions} additions remain")

    inventory = build_inventory(root, runs_after, verified_after, rejected_after)
    final = verified_after["5b2630950f384adeb9c68bacc44764bb"]
    logical_diff = logical_database_diff(backup_path, db_path)
    normalized_entries_present = sum(
        table_change["rows_added_or_modified"]
        for table, table_change in logical_diff.items()
        if table in {"metrics", "tags"}
    )
    report = {
        "normalization": {
            "version": NORMALIZATION_VERSION,
            "mode": "apply" if args.apply else "dry-run",
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "summary_step": SUMMARY_STEP,
            "historical_timestamp_policy": "New summaries use normalization time; original timestamps are unchanged",
            "verified_runs": len(verified_after),
            "skipped_runs": len(runs_after) - len(verified_after),
            "planned_additions_at_start": planned_additions,
            "applied_additions_this_invocation": applied_additions,
            "normalized_entries_present": normalized_entries_present,
            "remaining_additions": remaining_additions,
        },
        "database": {
            "path": db_path.relative_to(root).as_posix(),
            "sha256_before_normalization": backup_hash,
            "sha256_before_current_invocation": before_hash,
            "sha256_after_normalization": sha256(db_path),
            "backup_path": str(backup_path),
            "backup_sha256": backup_hash,
            "counts_before_normalization": pre_normalization_counts,
            "counts_before_current_invocation": before_counts,
            "counts_after_normalization": after_counts,
            "logical_diff_from_backup": logical_diff,
        },
        "semantics": {
            "epoch_metrics": "Original historical keys and rows are preserved",
            "summary_metrics": list(final.values),
            "summary_tags": SUMMARY_TAGS,
            "mar100_scope": "Applied only to verified TorchMetrics FCOS histories; YOLO recall is not relabeled",
        },
        "final_model": {
            "run_id": final.run_id,
            "run_name": final.run_name,
            "history_path": final.history_path.relative_to(root).as_posix(),
            "history_length": final.last_epoch,
            "best_zero_based_index": final.best_epoch - 1,
            "best_human_epoch": final.best_epoch,
            "best_checkpoint_sha256": sha256(
                root / "artifacts/refinement/fcos/F_final_fcos_tuned/best.pth"
            ),
            "normalized_values": final.values,
        },
        "classification_counts": dict(Counter(row["category"] for row in inventory)),
        "status_counts": dict(Counter(row["status"] for row in inventory)),
        "correlation_counts": dict(Counter(row["correlation_status"] for row in inventory)),
        "dry_run_plan": plan,
    }
    if args.inventory:
        write_inventory(args.inventory.resolve(), inventory)
    if args.report:
        write_report(args.report.resolve(), report)

    print(json.dumps({
        "mode": report["normalization"]["mode"],
        "runs": len(runs_after),
        "verified_runs": len(verified_after),
        "skipped_runs": len(runs_after) - len(verified_after),
        "planned_additions_at_start": planned_additions,
        "applied_additions_this_invocation": applied_additions,
        "normalized_entries_present": normalized_entries_present,
        "remaining_additions": remaining_additions,
        "database_counts": after_counts,
        "final_model": report["final_model"],
    }, indent=2))


if __name__ == "__main__":
    main()
