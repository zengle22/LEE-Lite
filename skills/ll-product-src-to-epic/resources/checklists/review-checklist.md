# Review Checklist

- Does the skill keep a standard `SKILL.md` shell while naming the canonical LEE template?
- Does the input contract explicitly accept only `ll-product-raw-to-src` freeze-ready packages?
- Does the output contract produce an EPIC package that can feed `product.epic-to-feat`?
- Are structural and semantic validations separate, including ADR-025 and provenance checks?
- Are `epic_freeze_ref`, `src_root_id`, evidence, and downstream handoff called out explicitly?
- Are executor and supervisor prompts split and opinionated about layer boundaries?
