# Project Principles and Rules To Follow

Think Longer and Harder. Short cuts will cut you.

1. AI note: Do not hallucinate. Do not make up facts.
2. No BoyScouting: Do not try to clean up unrelated tasks or side quests in the code. Only complete what you set out to do. If your task is to refactor then it must be scoped before you start writing code.
3. Separate concerns — keep UI, business logic, and data layers isolated.
4. Minimize code duplication — follow the DRY (Don’t Repeat Yourself) principle.
5. Fail fast — validate inputs early and handle errors clearly.
6. Architecture should follow SOLID Principles
7. CSS should never be inline
8. Logic deciding the UI should live inside of React component files only.
9. Logic determining feature functionality should live inside of a file that follows the theme.
10. Files should never exceed a size limit of 200 lines.
11. Code should be formatted for reading and understanding using the projects default lint rules.
12. Follow consistent naming conventions — meaningful, descriptive, and standardized.
13. Avoid magic numbers and strings — use constants or enums instead. Leverage a constant instead.
14. Every Commit must summarize the changes and list the files changed. Preferrably using emojis to signify the theme of each change.
15. Favor composition over inheritance — prefer modular, decoupled components.
16. Use interfaces and abstractions — decouple implementation from usage.
17. Think in systems — design for scalability, performance, and observability.
18. Avoid premature optimization — but write code that is easy to optimize later.
19. Document architecture decisions (ADRs) — keep track of trade-offs. These files live in ./Docs
20. Write tests as you write code — test-driven development when practical.
21. Strive for high test coverage — prioritize logic-heavy code.
22. Use unit, integration, and end-to-end tests appropriately.
23. Mock only when necessary — use real behavior when possible.
24. Ensure tests are deterministic — no flaky or time-dependent results.
25. Continuously integrate and run tests — CI/CD is non-negotiable. Use npm run test:watch and npm run dev to watch the build.
26. Sanitize all inputs — trust no external data by default.
27. Avoid hardcoding secrets or credentials — use environment variables or secret managers.
28. Follow the principle of least privilege — minimize access where possible.
29. Patch dependencies regularly — and monitor for CVEs.
30. Log responsibly — never log sensitive data.
31. Always keep documentation updated — code isn’t finished without it.

## Architecture

1. Service Architecture - Services for OS specific methods structure should have a CleaningService method that calls a FileSystemService method which then in turn calls the correct OS method.
   1. We are currently building out Windows methods and features, but in the future we will call other OS methods such as Linux and Max.
   2. CleaningServiceMethod --> FileSystemServiceMethod --> WindowsServiceMethod
   3. This structure allows us to reuse the first two layers with logic that will play out in our application no matter what OS we're on, but the FileSystemService will decide which OS method to use.

 2. IOC (Inversion of Control) When to start using it 
    1. Small project (in the context of dependency injection and architecture) typically means:
>1–3 developers
Only a handful of modules/services (e.g., <10)
Few or no transitive dependencies (services depending on other services)
Simple startup/bootstrapping (no complex wiring)
Testing can be done with simple manual mocks or stubs
Example: a CLI tool, a simple Electron app, a small API, a single-purpose script
Medium to large project means:

>4+ developers, or multiple teams
Dozens or hundreds of modules/services
Many transitive dependencies (services depend on other services, which depend on others, etc.)
Complex startup/bootstrapping (wiring dependencies by hand is tedious/error-prone)
Needs robust, automated testing with easy mocking/swapping of dependencies
Example: a business application, a modular Electron app, a large API, a microservices backend, anything with plugin/extension architecture
Rule of thumb:

>If you ever find yourself writing constructors with more than 2–3 dependencies, or you have to pass the same dependency through multiple layers, or you want to swap implementations for testing or platform, you’re in “medium/large” territory and should consider a DI container.
Summary Table:

Project Size	Typical Characteristics
Small	1–3 devs, <10 services, simple wiring, little/no transitive deps, simple tests
Medium/Large	4+ devs, 10+ services, complex wiring, many transitive deps, robust tests, extensible