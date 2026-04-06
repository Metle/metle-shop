# Repository Guidelines

## Project Structure & Module Organization
This repository is a Django webshop project.

- `utsukushi/`: project config (`settings.py`, `urls.py`, `wsgi.py`, `asgi.py`).
- App modules: `store/`, `cart/`, `orders/`, `accounts/` (models, views, admin, urls).
- `templates/`: server-rendered HTML templates (`templates/store/*`, `templates/orders/*`, etc.).
- `static/`: CSS and image assets (`static/css/app.css`, `static/img/...`).
- `locale/`: translation files (`locale/<lang>/LC_MESSAGES/django.po|django.mo`).
- `media/`: uploaded media (for example brand logos).

## Build, Test, and Development Commands
- `python -m venv .venv && source .venv/bin/activate`: create/activate virtualenv.
- `pip install -r requirements.txt`: install dependencies.
- `python manage.py migrate`: apply database schema changes.
- `python manage.py runserver`: run locally at `http://127.0.0.1:8000/`.
- `python manage.py check`: run Django system checks.
- `python manage.py test`: run unit tests.
- `python manage.py makemessages -a` and `python manage.py compilemessages`: update i18n files.

## Coding Style & Naming Conventions
- Follow PEP 8 with 4-space indentation and clear, small functions.
- Keep app responsibilities separated (business logic in app modules, not templates).
- Use `snake_case` for Python variables/functions, `PascalCase` for model/class names.
- Template blocks and CSS classes should be descriptive and consistent with existing names (e.g., `product-action-row`, `wishlist-button`).

## Testing Guidelines
- Use Django’s test framework (`python manage.py test`).
- Place tests under each app (e.g., `store/tests.py` or `store/tests/test_stock.py`).
- Name tests by behavior (`test_add_to_cart_caps_quantity_by_stock`).
- Add tests for model logic, view behavior, and critical admin actions (stock updates, checkout flows).

## Commit & Pull Request Guidelines
Git history is not available in this workspace, so use this convention consistently:

- Commit format: `type(scope): short imperative summary`  
  Example: `feat(store): compute dynamic stock from purchase logs`
- Keep commits focused; include migrations with related model changes.
- PRs should include:
  - purpose and scope,
  - database/migration impact,
  - manual verification steps,
  - screenshots for template/admin UI changes.

## Security & Configuration Tips
- Keep secrets out of source control; use environment variables (project includes `python-decouple`).
- Validate all admin-triggered state changes and prefer POST-backed actions for mutations.

## Automated Agent Personas

### @architect
**Focus**: Project Structure & Module Organization.
**Task**: Ensure new logic follows the `/` vs `utsukushi/` separation. 
**Constraint**: Always verify that new Django models stay in their specific app folder and 

### @validator
**Focus**: Build, Test, and Development Commands.
**Instructions**:
- Before suggesting a backend change, run `cd backend && ../bin/python manage.py check`.
- Before finalizing frontend UI changes, run `cd frontend && npm run build` to catch linting or type errors.
- **Mandatory**: If a model changes, explicitly state the command: `../bin/python manage.py makemigrations`.

### @tester
**Focus**: Build Test to safeguard logic
**Instructions**: Create unit tests to ensure new code does not break business logic  

## Collaboration Protocols
1. **The "Check-Before-Commit" Loop**: 
   - Primary Agent: Writes the code.
   - @validator: Runs the specific `bin/` commands listed in "Build & Test".
   - @reviewer: Checks for PEP 8 compliance and consistent naming across the stack.
2. **Migration Guard**: Any agent modifying `models.py` must spawn a subagent to verify the migration file is generated in the correct `*/migrations/` directory.
