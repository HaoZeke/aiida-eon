<!-- vale proselint.Uncomparables = NO -->
# AiiDA plugin registry

`aiida-eon` is reserved on
[aiidateam/aiida-registry](https://github.com/aiidateam/aiida-registry)
with prefix `eon`. Do not add a second key and do not publish
`aiida-eonclient`.

The listing needs `plugin_info` (raw `pyproject.toml`) so the scanner
can read the `aiida-core` pin. After a wheel is on PyPI, add
`pip_url: aiida-eon`. That pair is what
[aiidateam/aiida-registry#379](https://github.com/aiidateam/aiida-registry/pull/379)
sends.

<!-- vale off -->
```yaml
aiida-eon:
  entry_point_prefix: eon
  code_home: https://github.com/HaoZeke/aiida-eon
  plugin_info: https://raw.githubusercontent.com/HaoZeke/aiida-eon/main/pyproject.toml
  pip_url: aiida-eon
```
<!-- vale on -->

Open the PR from `HaoZeke/aiida-registry`, not from
`aiidateam/aiida-registry:<branch>`.
