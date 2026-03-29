# Authoring Checklist

- Keep the scaffold aligned to the current repository conventions in `resources/project-structure-reference.md`.
- Treat root files such as `.editorconfig`, `.gitignore`, `.projectignore`, `README.md`, and `docs/repository-layout.md` as managed outputs.
- Keep runtime shells separate from durable governed directories.
- Make write policy explicit so the runtime never silently overwrites unmanaged user files.
- Ensure the output package names every created, updated, and skipped path.
- Keep executor logic separate from supervisor review even when both are implemented in one runtime entrypoint.
