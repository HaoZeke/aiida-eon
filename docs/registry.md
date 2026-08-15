# AiiDA plugin registry

The key `aiida-eon` is already reserved on
[aiidateam/aiida-registry](https://github.com/aiidateam/aiida-registry)
(`plugins.yaml`), prefix `eon`, `code_home` this repository. Status
while there is no PyPI upload: planning, E001.

Do **not** add a second key. Do **not** publish `aiida-eonclient`.

Two edits, in order:

1. Add `plugin_info` now so the scanner can read `aiida-core` and
   the trove classifiers (clears E001/W002, status becomes alpha):

```yaml
aiida-eon:
  entry_point_prefix: eon
  code_home: https://github.com/HaoZeke/aiida-eon
  plugin_info: https://raw.githubusercontent.com/HaoZeke/aiida-eon/main/pyproject.toml
```

2. After `twine upload`, add `pip_url: aiida-eon`. Do not set
   `pip_url` before the wheel exists; `pip install --pre aiida-eon`
   in the registry test becomes the other E001.

Omit `documentation_url` unless it is a real docs host (not a
second copy of `code_home`).

`development_status` is deprecated (W006); the trove classifier
`Development Status :: 3 - Alpha` plus `Framework :: AiiDA` is what
the scanner wants.

Entry-point names already start with `eon` / `eon.` (W009 / W010).
Ship a `bdist_wheel` (W019).

```shell
python -m build
twine upload dist/*
```

Then open a PR against `aiidateam/aiida-registry` that **edits** the
existing `aiida-eon:` block. Head must be a personal fork
(`HaoZeke/aiida-registry`), not `aiidateam/aiida-registry:<branch>`.
