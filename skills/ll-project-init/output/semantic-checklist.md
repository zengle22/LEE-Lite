# Output Semantic Checklist

Review the `project_init_package` against the request and the structure reference.

- Does the scaffold match the current workspace's durable top-level layout and shell directories?
- Do the generated root files preserve the repository rule that runtime state stays outside the durable tree?
- Were existing unmanaged files skipped instead of silently overwritten?
- Does the package explain every created, updated, and skipped path clearly enough for review?
- Would another agent initialize the same repository the same way from this package and reference set?
