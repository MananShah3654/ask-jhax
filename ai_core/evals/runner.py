"""
Eval harness: run cases through your answer fn, score with hard rules + an
LLM judge (cheap model). Gate deploys on the aggregate. Usage:

    from ai_core.evals.runner import run_evals
    report = await run_evals(cases_path, answer_fn)   # answer_fn: async (q)->str
    assert report["pass_rate"] >= 0.8
"""
import json

from ..llm import cheap_llm
from ..utils import extract_json

_JUDGE = """You are a strict evaluator. Given a QUESTION, an ANSWER, and a RUBRIC,
score 1-5 for: correctness, uses_real_data, actionability, tone, no_hallucination.
Return ONLY JSON: {"scores":{...}, "avg":x.x, "pass":true/false, "reason":"..."}
Fail (pass=false) if the answer hallucinates or ignores the rubric."""


def _hard_rules(ans: str, case: dict):
    low = (ans or "").lower()
    for phrase in case.get("must_include", []):
        if phrase.lower() not in low:
            return False, f"missing required phrase: {phrase}"
    for phrase in case.get("must_not", []):
        if phrase.lower() in low:
            return False, f"contains forbidden phrase: {phrase}"
    return True, ""


async def judge(question, answer, rubric):
    raw = await cheap_llm(_JUDGE, f"QUESTION: {question}\n\nANSWER: {answer}\n\nRUBRIC: {rubric}")
    return extract_json(raw)


def load_cases(path):
    cases = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if line:
                cases.append(json.loads(line))
    return cases


async def run_evals(cases_path, answer_fn):
    cases = load_cases(cases_path)
    results, passed = [], 0
    for c in cases:
        ans = await answer_fn(c["q"])
        ok, why = _hard_rules(ans, c)
        j = await judge(c["q"], ans, c.get("rubric", "")) if ok else {"pass": False, "reason": why, "avg": 0}
        case_pass = bool(ok and j.get("pass"))
        passed += int(case_pass)
        results.append({"id": c.get("id"), "pass": case_pass, "judge": j, "hard_rule": why})
    return {
        "total": len(cases),
        "passed": passed,
        "pass_rate": (passed / len(cases)) if cases else 0.0,
        "results": results,
    }
