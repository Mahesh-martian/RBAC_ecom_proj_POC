"""Standalone smoke test for the prompt registry (bypasses conftest)."""

import os
import shutil
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.prompt_registry import (
    CompositePromptRegistry,
    PromptNotFoundError,
    YamlPromptRegistry,
)


def _write(path: str, body: str) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(body)


def main() -> int:
    tmp = tempfile.mkdtemp()
    try:
        _write(os.path.join(tmp, "hello", "v1.yaml"), 'id: hello\nversion: "1"\ntemplate: "v1"\n')
        _write(os.path.join(tmp, "hello", "v2.yaml"), 'id: hello\nversion: "2"\ntemplate: "v2"\n')
        r = YamlPromptRegistry(prompts_dir=tmp, cache_ttl_seconds=0)
        tpl = r.get("hello")
        assert tpl.version == "2", tpl
        assert tpl.label == "hello@v2"
        print("OK latest_version_wins:", tpl.label)

        os.environ["PROMPT_HELLO_VERSION"] = "1"
        r2 = YamlPromptRegistry(prompts_dir=tmp, cache_ttl_seconds=0)
        assert r2.get("hello").version == "1"
        print("OK env_pin_v1")
        del os.environ["PROMPT_HELLO_VERSION"]

        _write(os.path.join(tmp, "persona", "customer", "v1.yaml"), 'id: persona\nvariant: customer\nversion: "1"\ntemplate: "shopper"\n')
        _write(os.path.join(tmp, "persona", "vendor", "v1.yaml"), 'id: persona\nvariant: vendor\nversion: "1"\ntemplate: "seller"\n')
        r3 = YamlPromptRegistry(prompts_dir=tmp, cache_ttl_seconds=0)
        assert r3.get("persona", variant="customer").template.strip() == "shopper"
        assert r3.get("persona", variant="vendor").template.strip() == "seller"
        print("OK variants")

        _write(
            os.path.join(tmp, "anchors", "v1.yaml"),
            'id: anchors\nversion: "1"\nstructured:\n  greeting: [hi, hello]\n  product_search: ["show me shoes"]\n',
        )
        r4 = YamlPromptRegistry(prompts_dir=tmp, cache_ttl_seconds=0)
        anchors = r4.get("anchors")
        assert anchors.structured["greeting"] == ["hi", "hello"]
        print("OK structured_anchors")

        try:
            r4.get("nonexistent")
            print("FAIL: should have raised")
            return 1
        except PromptNotFoundError:
            print("OK not_found_raises")

        r5 = YamlPromptRegistry(prompts_dir="prompts", cache_ttl_seconds=0)
        system = r5.get("support_system")
        assert system.template and system.label.startswith("support_system@v")
        print("OK repo_seed support_system:", system.label)
        for role in ("customer", "vendor", "admin"):
            p = r5.get("role_persona", variant=role)
            h = r5.get("role_help_text", variant=role)
            assert p.template and h.template
            print(f"   {role}: {p.label}, {h.label}")
        repo_anchors = r5.get("intent_anchors")
        assert isinstance(repo_anchors.structured, dict) and "policy_support" in repo_anchors.structured
        print("OK repo_seed intent_anchors:", repo_anchors.label, sorted(repo_anchors.structured.keys()))

        print("\nALL PROMPT REGISTRY TESTS PASSED")
        return 0
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
