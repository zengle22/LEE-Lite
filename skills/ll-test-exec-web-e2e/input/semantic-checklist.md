# Input Semantic Checklist

- Confirm `command = skill.test-exec-web-e2e` and the request is not a generic CLI request copied into the wrong skill.
- Confirm `payload.test_set_ref` points to a formal `TESTSET`, not analysis notes, strategy drafts, or freeform governance prose.
- Confirm the resolved environment contract is Web E2E and includes stable browser/base URL settings before execution starts.
- Confirm optional `frontend_code_ref`, `ui_runtime_ref`, or `ui_source_spec` only enrich UI binding; they must not expand scope beyond the authoritative test set.
- Confirm the request still makes sense when UI binding remains partial; do not silently convert missing binding into fabricated locators.
