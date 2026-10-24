# SYSTEM ARCHITECTURE & CONSTRAINTS

This template deliberately records project-specific constraints rather than
assuming a particular operating system, shell, hardware profile, or runtime.

## Runtime and dependency constraints
- **Primary languages:** Define per project.
- **Supported environments:** Define per project.
- **Memory and performance ceiling:** Define measurable limits when known.
- **Network and persistence:** Document required local services, ports, and data stores.
- Prefer local, standard-library, and streaming approaches when they satisfy the requirement.

## Data flow

Document the project-specific flow here, for example:

```text
[Input] -> [Application boundary] -> [Domain logic] -> [Local state or output]
```
