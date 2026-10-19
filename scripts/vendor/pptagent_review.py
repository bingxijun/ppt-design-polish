# Adapted from ICIP-CAS PPTAgent; MIT. See licenses/PPTAgent.txt.
from typing import Any

def validate_review(payload: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(payload, dict) or payload.get("verdict") not in {
        "pass",
        "fail",
        "unjudgeable",
    }:
        raise ValueError("review must contain a valid verdict")
    if not isinstance(payload.get("summary"), str) or not payload["summary"].strip():
        raise ValueError("review summary must be nonempty text")
    if not isinstance(payload.get("issues"), list):
        raise TypeError("review issues must be a list")
    for issue in payload["issues"]:
        if not isinstance(issue, dict) or issue.get("severity") not in {
            "blocker",
            "major",
            "minor",
        }:
            raise ValueError("each issue must contain a valid severity")
        if type(issue.get("slide")) is not int or issue["slide"] < 1:
            raise ValueError("each issue must identify a positive slide number")
        if any(
            not isinstance(issue.get(key), str) or not issue[key].strip()
            for key in ("description", "suggested_fix")
        ):
            raise ValueError("each issue must contain a description and suggested_fix")
        if payload["verdict"] == "pass" and issue["severity"] in {"blocker", "major"}:
            raise ValueError("a review with blocker or major issues cannot pass")
    return {**payload, "ok": payload["verdict"] == "pass"}
