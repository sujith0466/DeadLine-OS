# Contributing to DeadlineOS

Thank you for your interest in contributing to DeadlineOS! We welcome contributions from the community to help make this the premier open-source executive operating system.

## Code of Conduct
By participating in this project, you agree to maintain a respectful, professional, and inclusive environment. 

## Development Workflow

1. **Fork & Clone**
   Fork the repository to your own GitHub account and clone it locally.

2. **Branching Strategy**
   Create a branch for your feature or bugfix:
   `git checkout -b feature/your-feature-name` or `git checkout -b fix/your-bug-fix`

3. **Local Setup**
   - Refer to the `README.md` for full instructions on setting up the React frontend and Python backend.
   - Ensure you copy the `.env.example` files to `.env` and fill them with your development credentials.

4. **Testing & Linting**
   Before submitting a Pull Request, please ensure that:
   - Backend tests pass: `pytest tests/`
   - Frontend compiles without TS errors: `npx tsc --noEmit`
   - Frontend lints cleanly: `npm run lint`

5. **Commit Standards**
   We strongly encourage Conventional Commits (e.g., `feat: added google calendar sync` or `fix: patched dashboard rendering bug`).

6. **Pull Requests**
   - Push your branch to GitHub and open a Pull Request against the `main` branch.
   - Provide a clear, detailed description of your changes, the problem they solve, and instructions on how to test them.

## Reporting Bugs
If you find a bug, please check the existing issues to ensure it hasn't been reported. If it is new, open an issue with:
- Steps to reproduce
- Expected vs actual behavior
- Browser and OS details

Thank you for helping us build a better operating system!
