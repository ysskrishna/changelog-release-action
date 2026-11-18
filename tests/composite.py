"""Execute this single-step action's metadata against a controlled fixture context."""
from pathlib import Path
import re
import subprocess

import yaml


def run_composite(metadata_path, overrides, env, workspace, workflow_token):
    action = yaml.safe_load(metadata_path.read_text())
    assert action["runs"]["using"] == "composite"
    assert len(action["runs"]["steps"]) == 1, "Update the fixture runner for additional steps"
    assert set(overrides) <= set(action["inputs"])
    context = {
        "inputs": {name: overrides.get(name, definition.get("default", ""))
                   for name, definition in action["inputs"].items()},
        "env": env,
        "github": {"action_path": str(metadata_path.parent), "token": workflow_token},
    }

    def resolve(value):
        expression = re.fullmatch(r"\$\{\{\s*(.*?)\s*\}\}", value)
        if not expression:
            assert "${{" not in value, "Unsupported expression in fixture runner"
            return value
        for term in expression[1].split("||"):
            term = term.strip()
            assert re.fullmatch(r"[\w.-]+", term), "Unsupported expression in fixture runner"
            result = context
            for key in term.split("."):
                result = result.get(key, "") if isinstance(result, dict) else ""
            if result:
                return result
        return ""

    step = action["runs"]["steps"][0]
    assert step["shell"] == "bash"
    assert "${{" not in step["run"], "Update the fixture runner for run expressions"
    step_env = {key: value for key, value in env.items()
                if not key.startswith("RELEASE_") and key != "ACTION_PATH"}
    step_env.update({key: resolve(value) for key, value in step["env"].items()})
    result = subprocess.run(
        ["bash", "--noprofile", "--norc", "-e", "-o", "pipefail", "-c", step["run"]],
        cwd=workspace, env=step_env, capture_output=True, text=True)
    if result.returncode:
        return result, {}
    step_outputs = dict(line.split("=", 1)
                        for line in Path(env["GITHUB_OUTPUT"]).read_text().splitlines())
    context["steps"] = {step["id"]: {"outputs": step_outputs}}
    return result, {name: resolve(definition["value"])
                    for name, definition in action["outputs"].items()}
