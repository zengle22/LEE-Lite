# Output Semantic Checklist

Review the UI Spec package against the upstream FEAT.

- Does the package explain how the user completes the FEAT in the interface, instead of restating FEAT prose?
- Does each UI Spec include a main path, at least two key branches, and an ASCII structure that matches the declared page type instead of a generic full-page form shell?
- For non-form pages such as panel, card list, enhancement entry, or status layer, do the states and user/system actions match the interaction model instead of a submit-oriented form state machine?
- Is the UI Spec still at interface-contract level rather than visual-polish level or code-implementation level?
- Are field boundaries explicit enough to separate UI-visible fields from technical payload fields when both exist?
- Do required fields match the required input fields, and are validation rules and API touchpoints explicit enough for downstream UI/TECH work?
- If the result is only `conditional_pass`, are the remaining open questions explicit rather than hidden?
