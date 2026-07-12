# Contributing

Thanks for improving EN MOSTAFA AI AGENT.

1. Open an issue describing the change and its security impact.
2. Create a focused branch from the default branch.
3. Keep core runtime code in `src/`; incomplete research modules belong in `experimental/`.
4. Never add secrets, personal paths, browser profiles, screenshots or generated databases.
5. Run `python -m compileall -q src experimental` and `python -m unittest discover -s tests -v`.
6. Submit a pull request with the problem, approach, validation and any compatibility impact.

Changes that expand shell, filesystem or browser privileges must include threat-model notes and safe defaults.
