# Input Semantic Checklist

Review the `project_init_request` before any scaffold files are written.

- Does the request ask for the standard LEE Lite skill-first skeleton rather than a product-specific application layout?
- Is the target root really the repository that should receive the scaffold?
- Does the request preserve the rule that runtime state stays outside durable governed directories?
- Is the requested write policy safe for the current target root contents?
- Would applying this request create a second competing directory standard for the same repository?
