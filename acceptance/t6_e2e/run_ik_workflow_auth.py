# SPDX-License-Identifier: AGPL-3.0-or-later
# T6 端到端验收：带 auth 的 IK 工作流运行器（临时验收脚本，不改动 Phase 1 基线 client）
# 复用 yuanze_client.YuanzeClient 逻辑，仅注入 Authorization Bearer token。
import json
import os
import sys

sys.path.insert(0, r"D:\yuanze-demos\client")
from yuanze_client import YuanzeClient, _resolve_path  # noqa: E402


class AuthYuanzeClient(YuanzeClient):
    def __init__(self, base_url: str, token: str):
        super().__init__(base_url)
        self._http.headers["Authorization"] = f"Bearer {token}"


def build_workflow(target_pose: dict, max_residual: float = 0.001) -> dict:
    return {
        "type": "sequence",
        "params": {
            "instructions": [
                {
                    "type": "compute_ik",
                    "params": {
                        "service_name": "inverse_kinematics_solver",
                        "target_pose": target_pose,
                        "solver_type": "LMA",
                        "tolerance": 0.001,
                        "max_iterations": 1000,
                        "timestamp": 1719990000,
                    },
                },
                {
                    "type": "robot_move",
                    "params": {
                        "service_name": "robot_move_joints",
                        "speed": 0.5,
                        "timestamp": 1719990001,
                    },
                },
                {
                    "type": "validate_precision",
                    "params": {"max_allowed_residual": max_residual, "timestamp": 1719990002},
                },
                {
                    "type": "conditional",
                    "params": {
                        "domain": {
                            "type": "not",
                            "inner": {
                                "type": "eq",
                                "path": "payload.audit.pending_alert",
                                "value": None,
                            },
                        },
                        "then": {"type": "audit_alert", "params": {"model": "gpt-4o-mini"}},
                        "else": {"type": "noop"},
                    },
                },
            ]
        },
    }


def main() -> int:
    base_url = os.environ.get("EVORULE_SERVER_URL", "http://127.0.0.1:18080")
    token = os.environ.get("EVORULE_SERVER_TOKEN", "evorule-acceptance-secret")
    target_pose = {"x": 0.5, "y": 0.3, "z": 0.2}

    with AuthYuanzeClient(base_url, token) as client:
        print(f"[1] 创建会话 -> {base_url}")
        session_id = client.create_session()
        print(f"    session_id = {session_id}")

        print("[2] 提交 sequence 工作流")
        workflow = build_workflow(target_pose)
        client.send_command(session_id, workflow)

        print("[3] 等待执行完成（轮询 /state）...")
        state = client.wait_for_field(session_id, "service_result", timeout=30.0)
        payload = state.get("payload", {})

        print("\n=== 最终 payload ===")
        print(json.dumps(payload, indent=2, ensure_ascii=False, default=str))

        print("\n=== 审计报告（session 级哈希链）===")
        audit = client.get_session_audit(session_id)
        print(f"  fact_count: {audit.get('fact_count')}")
        print(f"  last_hash:  {(audit.get('last_hash') or '')[:16]}...")
        print(f"  verified:   {audit.get('verified')}")

        svc = payload.get("service_result", {})
        alert = payload.get("audit", {}).get("pending_alert")
        print(f"\n结论：converged_ok={svc.get('converged_ok')}, "
              f"residual={svc.get('residual')}, "
              f"pending_alert={'无' if alert is None else '有'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
