# Product

## One-sentence concept

GitIRL is version control for the physical world: save a meaningful room state, see what changed, and restore it with a robot.

## User experience

A user observes a space, saves a named desired state, changes occur, GitIRL shows the difference, and the user asks the robot to restore and verify that state.

## Core value proposition

Turn a physical environment into something people can save, compare, and return to—not merely describe or monitor.

## P0 MVP

Reliably complete this loop for one object: observe, save, disturb, re-observe, diff, restore, and verify.

> **Feature gate:** “Before adding another feature: can GitIRL save, disturb, diff, restore, and verify one object reliably five times in a row?”

## P1 enhancements

- Restore multiple objects in a constrained, repeatable setup.
- Support multiple named physical states.
- Improve the human-facing status, diff, and restoration-progress experience.

## P2 stretch goals

- Natural-language state retrieval.
- Remote commands via SMS.
- Semantic search/retrieval.
- Agentic planning.
- Physical merge conflicts.
- Git-style history/status/diff UI.

## DO NOT BUILD UNTIL P0 WORKS

Do not add P1 or P2 features until the P0 feature-gate question is answered **yes** with five consecutive reliable one-object runs. Do not introduce integrations, abstractions, or architecture for unconfirmed hardware capabilities.

## Scope boundaries

- This repository currently defines intent and a testable prototype path; it does not contain the application.
- BracketBot APIs, execution capabilities, perception outputs, and constraints remain TBD pending official documentation.
- Remote services, sponsor technologies, LLMs, databases, and agent systems are out of scope unless they become necessary after P0 works and are confirmed available.
