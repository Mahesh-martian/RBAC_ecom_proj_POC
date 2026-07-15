# Prompt Registry

Versioned prompts loaded by `app/services/prompt_registry.py`.

## Layout

```
prompts/
├── support_system/          # System prompt for the RAG answer generation
│   ├── v1.yaml
│   └── vN.yaml              # (add new versions as separate files)
├── role_persona/
│   ├── customer/vN.yaml
│   ├── vendor/vN.yaml
│   └── admin/vN.yaml
├── role_help_text/
│   ├── customer/vN.yaml
│   ├── vendor/vN.yaml
│   └── admin/vN.yaml
└── intent_anchors/          # Semantic router example utterances (structured payload)
    └── vN.yaml
```

Every YAML file has:

| Field | Purpose |
|---|---|
| `id` | Logical prompt name (matches the folder name) |
| `variant` | Optional sub-key (e.g. `customer`, `vendor`, `admin`) |
| `version` | Version string, referenced by env-var overrides |
| `description` | Human-readable purpose |
| `variables` | List of `{name}` placeholders callers must supply |
| `template` | Plain-string prompt (with `{var}` placeholders) |
| `structured` | Alternative to `template` — arbitrary YAML payload (e.g. intent anchors) |

## Selecting the active version

The registry serves the **highest numeric `version`** by default. Pin a specific
version per prompt via env vars:

```
PROMPT_SUPPORT_SYSTEM_VERSION=1
PROMPT_ROLE_PERSONA_VERSION=1
PROMPT_ROLE_HELP_TEXT_VERSION=1
PROMPT_INTENT_ANCHORS_VERSION=1
```

## Adding a new version

1. Copy `v1.yaml` → `v2.yaml`.
2. Edit the `template` (or `structured` payload) and bump `version: "2"`.
3. Deploy. Traffic still uses v1 unless you pin `PROMPT_..._VERSION=2` or make v2
   the highest.
4. When comfortable, delete the older file (or leave for rollback).

## Langfuse (optional)

Set `LANGFUSE_PUBLIC_KEY` + `LANGFUSE_SECRET_KEY` (and `LANGFUSE_HOST` for
self-hosted) and set `PROMPT_REGISTRY_PROVIDER=composite` to prefer Langfuse
with automatic YAML fallback.
