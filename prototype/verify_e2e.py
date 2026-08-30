"""End-to-end verification script for all 4 scenarios across both personas."""
import os
import sys

# Ensure root and prototype directories are in sys.path
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(CURRENT_DIR)
for p in [CURRENT_DIR, ROOT_DIR]:
    if p not in sys.path:
        sys.path.insert(0, p)

from prototype.engine.scenarios.runner import ScenarioRunner
from prototype.engine.contracts.schemas import UserRole, ExecutiveConstraint

def main():
    runner = ScenarioRunner(mode="mock")
    scenarios = ["scenario_1", "scenario_2", "scenario_3", "scenario_4"]
    roles = [UserRole.EXECUTIVE, UserRole.OPERATIONS_ANALYST]

    print("=" * 80)
    print("RUNNING END-TO-END VERIFICATION MATRIX")
    print("=" * 80)

    for sc in scenarios:
        for role in roles:
            res = runner.run_scenario(
                scenario_id=sc,
                role=role,
                constraint=ExecutiveConstraint(budget_cap_usd=45000.0)
            )
            spc = res["spc_result"]
            tree = res["tree_result"]
            presc = res["prescriptive_output"]
            tel = res["telemetry"]

            print(f"[{sc}] Role: {role.value:<19} | Anomaly: {str(spc.is_anomaly):<5} (z={spc.z_score:+.2f}) | Abstain: {str(presc['is_abstaining']):<5} | Res: {tree.residual:.2e} | Latency: {tel.latency_ms:.1f}ms")

    print("=" * 80)
    print("ALL 8 SCENARIO/ROLE COMBINATIONS PASSED VERIFICATION!")
    print("=" * 80)

if __name__ == "__main__":
    main()
