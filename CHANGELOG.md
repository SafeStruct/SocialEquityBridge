# Changelog

## 1.0.0 — 2026-09-11

Publication-ready release matching the IJDRR paper
[Integrating structural and social vulnerability for equitable bridge maintenance prioritisation](https://doi.org/10.1016/j.ijdrr.2026.106115).

- Add citation (`CITATION.cff`), Zenodo data DOI (`10.5281/zenodo.22756091`), and conda environment file
- Move analysis defaults into `config/params.yaml` and expose a shared command-line interface
- Replace print statements with logging; wrap pipeline scripts in `main()`
- Apply Google-style docstrings and type hints; add ruff and pre-commit config
- Sanitize the HPC Slurm template
