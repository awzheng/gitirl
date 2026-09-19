# Prototype Checklist

Update each stage as evidence is gathered. Keep notes concrete: setup, observed behavior, failures, and the next blocker.

## 0. BracketBot hello world

- [ ] **Status**
- **Goal:** Confirm the supported development path and make BracketBot perform its official basic example.
- **Pass condition:** The documented hello-world interaction succeeds.
- **Notes / blockers:**

## 1. Observe environment / git add

- [ ] **Status**
- **Goal:** Obtain an observation suitable for describing the current environment.
- **Pass condition:** A repeatable observation of the test setup is captured.
- **Notes / blockers:**

## 2. Save state / git commit

- [ ] **Status**
- **Goal:** Save the observed test setup as a desired state.
- **Pass condition:** The team can retrieve the same saved state for comparison.
- **Notes / blockers:**

## 3. Single-object manipulation

- [ ] **Status**
- **Goal:** Move one suitable test object with the robot.
- **Pass condition:** The object reaches the intended location safely and repeatably.
- **Notes / blockers:**

## 4. Re-observe changed environment / git status

- [ ] **Status**
- **Goal:** Observe the environment after one object changes.
- **Pass condition:** The new observation clearly represents the changed setup.
- **Notes / blockers:**

## 5. Compute physical state diff / git diff

- [ ] **Status**
- **Goal:** Compare desired and current state for one changed object.
- **Pass condition:** The reported difference is correct for the controlled change.
- **Notes / blockers:**

## 6. ONE-OBJECT END-TO-END RESTORE

- [ ] **Status**
- **Goal:** Restore one disturbed object to its saved state.
- **Pass condition:** Observe → save → disturb → diff → restore → verify succeeds end to end.
- **Notes / blockers:**

## 7. Multi-object restore

- [ ] **Status**
- **Goal:** Extend restoration to several suitable objects.
- **Pass condition:** The controlled multi-object setup is restored correctly.
- **Notes / blockers:**

## 8. Verify + retry

- [ ] **Status**
- **Goal:** Verify outcomes and handle an unsuccessful restoration attempt.
- **Pass condition:** Verification distinguishes success from failure and supports a safe retry path.
- **Notes / blockers:**

## 9. Multiple named states

- [ ] **Status**
- **Goal:** Save and select more than one desired physical state.
- **Pass condition:** A chosen named state is retrieved reliably.
- **Notes / blockers:**

## 10. Natural-language state selection

- [ ] **Status**
- **Goal:** Select a saved state from a natural-language request.
- **Pass condition:** The intended saved state is selected in controlled examples.
- **Notes / blockers:**

## 11. SMS/remote interface

- [ ] **Status**
- **Goal:** Accept a remote restoration request.
- **Pass condition:** An authorized test request reaches the prototype and has a visible outcome.
- **Notes / blockers:**

## 12. Semantic retrieval

- [ ] **Status**
- **Goal:** Retrieve a relevant saved state from semantic descriptions.
- **Pass condition:** Controlled queries select the expected state.
- **Notes / blockers:**

## 13. Agentic planning

- [ ] **Status**
- **Goal:** Explore higher-level planning only if it improves the proven core loop.
- **Pass condition:** It measurably helps a controlled restoration scenario.
- **Notes / blockers:**

## 14. Git-style polish/features

- [ ] **Status**
- **Goal:** Add presentation polish and Git-inspired features after reliability is established.
- **Pass condition:** Features improve the demo without harming P0 reliability.
- **Notes / blockers:**
