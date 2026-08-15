# AiiDA plugin registry

The key `aiida-eon` is already reserved on
[aiidateam/aiida-registry](https://github.com/aiidateam/aiida-registry)
(`plugins.yaml`), prefix `eon`, `code_home` this repository. Status
while there is no PyPI upload: planning, E001.

Do **not** add a second key. Do **not** publish `aiida-eonclient`.

After a wheel is on PyPI, replace the reserved block with:

```yaml
aiida-eon:
  entry_point_prefix: eon
  code_home: https://github.com/HaoZeke/aiida-eon
  pip_url: aiida-eon
  plugin_info: https://raw.githubusercontent.com/HaoZeke/aiida-eon/main/pyproject.toml
  documentation_url: https://github.com/HaoZeke/aiida-eon
```

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
