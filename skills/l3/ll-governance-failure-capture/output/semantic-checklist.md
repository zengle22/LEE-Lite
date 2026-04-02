# Output Semantic Checklist

- The package kind matches `triage_level`.
- The package path matches the governed directory convention.
- The package captures the problem without attempting to fix it.
- `diagnosis_stub` is clearly a stub, not a final diagnosis report.
- `repair_context` constrains later repair instead of reopening the whole artifact.
- File refs point back to request, failed artifact, upstream, and evidence.
- The package is narrow enough to support later hotfix and future governance review.
