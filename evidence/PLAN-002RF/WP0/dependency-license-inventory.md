# PLAN-002RF WP0 — dependency and license inventory

No dependency was intentionally added to `pyproject.toml` or `uv.lock`.

| Component | Locked version | License/status | WP0 use / decision |
|---|---:|---|---|
| Python | 3.11.* | PSF | Required project runtime. Executed 3.11.15. |
| Pillow | 12.3.0 | HPND | Approved existing image dependency. Diagnostic accidentally executed an already-present Hermes environment version 12.2.0; pinned acceptance therefore not proven. |
| NumPy | 2.4.6 | BSD-3-Clause | Approved existing array dependency. Diagnostic executed already-present 2.4.3; pinned acceptance not proven. |
| ezdxf | 1.4.4 | MIT | Existing Product A dependency; not used by WP0 diagnostic. |
| pypdfium2 | 5.12.1 | Apache-2.0 OR BSD-3-Clause; bundled PDFium/third-party notices apply | Existing PDF dependency; not used. Distribution review remains under D-010. |
| jsonschema | 4.26.0 | MIT | Existing contract validation dependency; not used by diagnostic. |
| pytest | 9.1.1 | MIT | Locked dev dependency. No installed project environment was present. Targeted tests ran using an already-cached pytest package plus the already-running Hermes environment; full-suite collection lacked ezdxf and failed closed. |
| pytest-cov | 7.1.0 | MIT | Locked dev dependency; not used. |
| Sample_Floorplan.jpg | n/a | Public domain, creator release; SHA-256 `917a5753...80df08` | Existing tracked rights-cleared fixture candidate. No acquisition occurred in WP0. |

## Installation-boundary incident

The first environment probe used `uv run`, which materialized an ignored `.venv` and installed 20 packages from the existing lock/cache path. This violated WP0's explicit no-install boundary. The command and versions are reported rather than hidden. The `.venv` was immediately deleted and the tracked dependency files remained byte-identical (`uv.lock` SHA-256 `a636f9bc...e0e18a`; `pyproject.toml` SHA-256 `f0196ef8...02d5d`). No dependency or lock change was committed. Because this is a boundary breach, WP0 cannot claim AT-25 or technical closure even though rollback succeeded.

## License conclusion

One local fixture has adequate documented rights. This does not satisfy U-7/AT-20 for a 100-family corpus, and no commercial-distribution conclusion is made. D-010 remains open.
