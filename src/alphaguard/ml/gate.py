"""Agent 2 downside-risk gate + deterministic policy (ARCHITECTURE §7.4 / §7.6)."""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path

import numpy as np
import xgboost as xgb

from alphaguard.contracts.decisions import FEATURE_NAMES, Agent2Decision
from alphaguard.contracts.manifest import ModelBundleManifest
from alphaguard.contracts.proposals import Agent1Action, Agent1Proposal
from alphaguard.ml.features import FeatureRow

logger = logging.getLogger(__name__)


class GateLoadError(RuntimeError):
    """Fail-closed gate load / skew error."""


class DownsideRiskGate:
    def __init__(self, bundle_dir: Path) -> None:
        self.bundle_dir = bundle_dir
        self.manifest = self._load_manifest(bundle_dir)
        self.model = self._load_model(bundle_dir, self.manifest)

    @staticmethod
    def _load_manifest(bundle_dir: Path) -> ModelBundleManifest:
        path = bundle_dir / "manifest.json"
        if not path.exists():
            raise GateLoadError(
                f"gate manifest missing at {path}. "
                "Train a bundle or point MODEL_BUNDLE_DIR at data/fixtures/model_bundle_fixture."
            )
        try:
            manifest = ModelBundleManifest.model_validate_json(path.read_text(encoding="utf-8"))
        except Exception as exc:  # noqa: BLE001
            raise GateLoadError(f"gate manifest invalid/skewed at {path}: {exc}") from exc
        if list(manifest.feature_names) != list(FEATURE_NAMES):
            raise GateLoadError(
                f"feature_names skew: expected {list(FEATURE_NAMES)}, "
                f"got {manifest.feature_names}. Retrain or use fixture bundle."
            )
        if manifest.score_kind != "proba_high_risk":
            raise GateLoadError(
                f"unsupported score_kind={manifest.score_kind!r}; expected proba_high_risk"
            )
        required = os.environ.get("ALPHAGUARD_REQUIRE_BUNDLE_KIND", "").strip()
        if required and manifest.bundle_kind != required:
            raise GateLoadError(
                f"bundle_kind mismatch: required {required!r} via "
                f"ALPHAGUARD_REQUIRE_BUNDLE_KIND, got {manifest.bundle_kind!r} "
                f"from {path}. Point MODEL_BUNDLE_DIR at an Option B bundle "
                "or unset ALPHAGUARD_REQUIRE_BUNDLE_KIND."
            )
        return manifest

    @staticmethod
    def _load_model(bundle_dir: Path, manifest: ModelBundleManifest) -> xgb.Booster:
        model_path = bundle_dir / manifest.model_filename
        if not model_path.exists():
            raise GateLoadError(
                f"model file missing at {model_path}. "
                "Use fixture bundle or run scripts/build_fixture_bundle.py."
            )
        booster = xgb.Booster()
        booster.load_model(str(model_path))
        return booster

    def score(self, row: FeatureRow) -> float:
        vector = row.ordered_vector(self.manifest.feature_names)
        dmatrix = xgb.DMatrix(
            np.asarray([vector], dtype=float),
            feature_names=list(self.manifest.feature_names),
        )
        proba = float(self.model.predict(dmatrix)[0])
        return max(0.0, min(1.0, proba))

    def apply_policy(
        self,
        action: Agent1Action,
        downside_risk_score: float,
        volatility_20d: float,
    ) -> tuple[str, str]:
        """Return (decision, reason) for AG1 policy table."""
        threshold = self.manifest.score_threshold
        if action in ("HOLD", "PASS"):
            return "approve", f"{action} always approve under policy_version=v1"

        # BUY
        if downside_risk_score >= threshold:
            return (
                "reject",
                f"BUY rejected: downside_risk_score={downside_risk_score:.4f} "
                f">= score_threshold={threshold:.4f}",
            )
        if self.manifest.vol_veto_enabled:
            veto = self.manifest.vol_veto_threshold
            if veto is None:
                raise GateLoadError("vol_veto_enabled but vol_veto_threshold missing")
            if volatility_20d >= veto:
                return (
                    "reject",
                    f"BUY rejected by vol veto: volatility_20d={volatility_20d:.4f} "
                    f">= vol_veto_threshold={veto:.4f}",
                )
        return (
            "approve",
            f"BUY approved: downside_risk_score={downside_risk_score:.4f} "
            f"< score_threshold={threshold:.4f}",
        )

    def decide(self, proposal: Agent1Proposal, row: FeatureRow) -> Agent2Decision:
        score = self.score(row)
        decision, reason = self.apply_policy(
            action=proposal.action,
            downside_risk_score=score,
            volatility_20d=float(row.values["volatility_20d"]),
        )
        return Agent2Decision(
            event_id=proposal.event_id,
            ticker=proposal.ticker,
            action=proposal.action,
            downside_risk_score=score,
            decision=decision,  # type: ignore[arg-type]
            decision_reason=reason,
            model_version=self.manifest.model_version,
            bundle_id=self.manifest.bundle_id,
            features_used=list(self.manifest.feature_names),
            feature_as_of=row.feature_as_of,
            policy_version=self.manifest.policy_version,
        )


def write_manifest(path: Path, manifest: ModelBundleManifest) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(manifest.model_dump(mode="json"), indent=2) + "\n",
        encoding="utf-8",
    )
