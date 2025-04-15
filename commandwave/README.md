# CommandWave Code Architecture Directory

This directory is part of a planned modular architecture for the CommandWave application. It follows a standard separation of concerns pattern with the following structure:

## Directory Structure

- **routes/**: Contains route handlers for Flask endpoints (API controllers)
- **services/**: Contains business logic and service layer components
- **utils/**: Contains utility functions and helper modules

## Current Status

This directory structure is currently preserved for future refactoring efforts. The application's logic currently resides primarily in `main.py` in the root directory, but a long-term goal is to migrate to this more modular structure.

## How to Use

When refactoring or adding new features, consider implementing them according to this structure:

1. Place API/route handlers in the `routes/` directory
2. Place business logic in the `services/` directory 
3. Place utilities and helpers in the `utils/` directory

## Related Tasks

For more information, see Task T8 in PROJECT_TASKS.md which documents the analysis of this directory structure.

*Last Updated: 2025-04-14*
