"""Unit tests for the prompt registry (YAML backend + composite fallback)."""

from __future__ import annotations

from pathlib import Path

import pytest

from app.services.prompt_registry import (
    CompositePromptRegistry,
    PromptNotFoundError,
    PromptTemplate,
    YamlPromptRegistry,
    reset_prompt_registry,
)


def _write_yaml(path: Path, body: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body, encoding="utf-8")


@pytest.fixture(autouse=True)
def _reset_registry_singleton():
    reset_prompt_registry()
    yield
    reset_prompt_registry()


def test_yaml_registry_returns_latest_version(tmp_path):
    _write_yaml(
        tmp_path / "hello" / "v1.yaml",
        "id: hello\nversion: '1'\ntemplate: 'Hi from v1'\n",
    )
    _write_yaml(
        tmp_path / "hello" / "v2.yaml",
        "id: hello\nversion: '2'\ntemplate: 'Hi from v2'\n",
    )

    registry = YamlPromptRegistry(prompts_dir=tmp_path, cache_ttl_seconds=0)
    tpl = registry.get("hello")

    assert isinstance(tpl, PromptTemplate)
    assert tpl.version == "2"
    assert tpl.template.strip() == "Hi from v2"
    assert tpl.label == "hello@v2"


def test_yaml_registry_env_pin_overrides_latest(tmp_path, monkeypatch):
    _write_yaml(
        tmp_path / "hello" / "v1.yaml",
        "id: hello\nversion: '1'\ntemplate: 'Hi from v1'\n",
    )
    _write_yaml(
        tmp_path / "hello" / "v2.yaml",
        "id: hello\nversion: '2'\ntemplate: 'Hi from v2'\n",
    )
    monkeypatch.setenv("PROMPT_HELLO_VERSION", "1")

    registry = YamlPromptRegistry(prompts_dir=tmp_path, cache_ttl_seconds=0)
    tpl = registry.get("hello")

    assert tpl.version == "1"
    assert tpl.template.strip() == "Hi from v1"


def test_yaml_registry_variant_folder(tmp_path):
    _write_yaml(
        tmp_path / "persona" / "customer" / "v1.yaml",
        "id: persona\nvariant: customer\nversion: '1'\ntemplate: 'shopper persona'\n",
    )
    _write_yaml(
        tmp_path / "persona" / "vendor" / "v1.yaml",
        "id: persona\nvariant: vendor\nversion: '1'\ntemplate: 'seller persona'\n",
    )

    registry = YamlPromptRegistry(prompts_dir=tmp_path, cache_ttl_seconds=0)
    customer = registry.get("persona", variant="customer")
    vendor = registry.get("persona", variant="vendor")

    assert customer.template.strip() == "shopper persona"
    assert vendor.template.strip() == "seller persona"
    assert customer.variant == "customer"
    assert customer.label == "persona@v1:customer"


def test_yaml_registry_structured_payload_intent_anchors(tmp_path):
    body = (
        "id: intent_anchors\n"
        "version: '1'\n"
        "structured:\n"
        "  greeting:\n"
        "    - hi\n"
        "    - hello\n"
        "  product_search:\n"
        "    - show me shoes\n"
    )
    _write_yaml(tmp_path / "intent_anchors" / "v1.yaml", body)

    registry = YamlPromptRegistry(prompts_dir=tmp_path, cache_ttl_seconds=0)
    tpl = registry.get("intent_anchors")

    assert tpl.structured["greeting"] == ["hi", "hello"]
    assert tpl.structured["product_search"] == ["show me shoes"]


def test_yaml_registry_missing_prompt_raises(tmp_path):
    registry = YamlPromptRegistry(prompts_dir=tmp_path, cache_ttl_seconds=0)
    with pytest.raises(PromptNotFoundError):
        registry.get("does_not_exist")


def test_yaml_registry_explicit_version_not_found(tmp_path):
    _write_yaml(
        tmp_path / "hello" / "v1.yaml",
        "id: hello\nversion: '1'\ntemplate: 'Hi from v1'\n",
    )
    registry = YamlPromptRegistry(prompts_dir=tmp_path, cache_ttl_seconds=0)
    with pytest.raises(PromptNotFoundError):
        registry.get("hello", version="99")


def test_composite_falls_back_to_yaml(tmp_path):
    _write_yaml(
        tmp_path / "hello" / "v1.yaml",
        "id: hello\nversion: '1'\ntemplate: 'from yaml'\n",
    )

    class AlwaysMiss:
        def get(self, *_args, **_kwargs):
            raise PromptNotFoundError("primary miss")

    yaml_backend = YamlPromptRegistry(prompts_dir=tmp_path, cache_ttl_seconds=0)
    composite = CompositePromptRegistry(primary=AlwaysMiss(), fallback=yaml_backend)

    tpl = composite.get("hello")
    assert tpl.template.strip() == "from yaml"
    assert tpl.source == "yaml"


def test_prompt_template_render_substitutes_vars():
    tpl = PromptTemplate(id="x", version="1", template="Hello {name}!", variables=("name",))
    assert tpl.render(name="Alice") == "Hello Alice!"


def test_prompt_template_render_raises_when_structured_only():
    tpl = PromptTemplate(id="x", version="1", template="", structured={"a": [1]})
    with pytest.raises(ValueError):
        tpl.render()


def test_repo_prompts_seed_files_load(monkeypatch):
    """Sanity check: the checked-in prompts/ folder is well-formed."""
    from app.services import prompt_registry as reg_mod

    repo_prompts = Path(__file__).resolve().parents[1] / "prompts"
    if not repo_prompts.is_dir():
        pytest.skip("repo prompts directory not present in this build")

    registry = YamlPromptRegistry(prompts_dir=repo_prompts, cache_ttl_seconds=0)

    system = registry.get("support_system")
    assert system.template  # non-empty
    assert system.label.startswith("support_system@v")

    for role in ("customer", "vendor", "admin"):
        persona = registry.get("role_persona", variant=role)
        assert persona.template
        help_text = registry.get("role_help_text", variant=role)
        assert help_text.template

    anchors = registry.get("intent_anchors")
    assert isinstance(anchors.structured, dict)
    assert "policy_support" in anchors.structured
    assert reg_mod.PromptNotFoundError  # exported
