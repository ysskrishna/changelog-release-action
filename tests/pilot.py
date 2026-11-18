"""Exercise a consumer's actual changelog without creating a real release."""
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile

from composite import run_composite

root = Path(__file__).resolve().parents[1]
consumer = Path(sys.argv[1]).resolve()
changelog = (consumer / "CHANGELOG.md").read_text()
section = re.search(r"^## \[(\d+\.\d+\.\d+[^]]*)\][^\n]*\n(.*?)(?=^## |^\[[^]]+\]:|\Z)",
                    changelog, flags=re.MULTILINE | re.DOTALL)
if not section or not section[2].strip():
    sys.exit("Consumer has no nonempty version section to test.")
tag = "v" + section[1]

with tempfile.TemporaryDirectory() as directory:
    fixture = Path(directory)
    def git(*args):
        subprocess.run(["git", *args], cwd=fixture, check=True, capture_output=True)

    git("init", "-q")
    git("-c", "user.name=Test", "-c", "user.email=test@example.com", "commit",
        "--allow-empty", "-qm", "Consumer release fixture")
    git("tag", tag)
    (fixture / "CHANGELOG.md").write_text(changelog)
    (fixture / "bin").mkdir()
    shutil.copy(root / "tests/fake-gh", fixture / "bin/gh")
    (fixture / "bin/gh").chmod(0o755)
    state = fixture / "remote.json"
    state.write_text("{}")
    output = fixture / "output"
    output.touch()
    env = dict(os.environ, PATH=str(fixture / "bin") + os.pathsep + os.environ["PATH"],
               GITHUB_WORKSPACE=str(fixture), GITHUB_REF="refs/tags/" + tag,
               GITHUB_REPOSITORY="example/consumer", GH_TOKEN="fixture-not-a-secret",
               FAKE_GH_STATE=str(state), GITHUB_OUTPUT=str(output))
    for attempt in range(2):
        result, outputs = run_composite(root / "action.yml", {}, env, fixture, "workflow-token-fixture")
        if result.returncode:
            sys.exit(result.stderr)
        print(result.stdout, end="")
        release = json.loads(state.read_text())["release"]
        assert release["body"].strip() == section[2].strip(), "Incorrect release body"
        assert release["name"] == "Release " + tag, "Incorrect release title"
        assert release["assets"] == {}, "Unexpected release assets"
        assert outputs["release-url"] == release["html_url"], "Incorrect public release URL"
        assert outputs["release-created"] == ("true" if attempt == 0 else "false")
    assert "release-created=true" in output.read_text()
    assert "release-created=false" in output.read_text()
    print(f"PASS: consumer changelog {tag}, release title, body, no assets, and rerun skip.")
