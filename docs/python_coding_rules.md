# Python coding standards for modern backends

> Python 3.11+ · Black · Ruff · mypy/Pyright · pytest · uv

**This document defines the engineering standards for Python 3.11+ backend development.** Every rule prioritizes maintainability, type safety, and testability through explicit dependency injection and clean architecture. The standards progress from syntax-level rules to system-level architecture patterns, each with rationale and concrete code examples. Adopt these incrementally — start with formatting and typing enforcement, then layer in architectural patterns as complexity warrants.

---

## Table of Contents

**[Part I — Code Style](#part-i--code-style)**
- [1. Syntax and formatting rules](#1-syntax-and-formatting-rules)
- [2. Typing rules](#2-typing-rules)

**[Part II — Architecture](#part-ii--architecture)**
- [3. Dependency injection rules](#3-dependency-injection-rules)
- [4. Architecture patterns](#4-architecture-patterns)

**[Part III — Quality & Operations](#part-iii--quality--operations)**
- [5. Testing strategy](#5-testing-strategy)
- [6. Async best practices](#6-async-best-practices)
- [7. Error handling](#7-error-handling)
- [8. Logging standards](#8-logging-standards)

**[Part IV — Project & Scaling](#part-iv--project--scaling)**
- [9. Project structure](#9-project-structure)
- [10. Scalability principles](#10-scalability-principles)

[Conclusion](#conclusion)

---

## Toolchain at a glance

| Tool | Purpose | Config |
|---|---|---|
| **Black** | Auto-formatter (88-char line length) | `pyproject.toml → [tool.black]` |
| **Ruff** | Linter — replaces flake8, isort, pydocstyle | `pyproject.toml → [tool.ruff]` |
| **mypy / Pyright** | Static type checker | `pyproject.toml → [tool.mypy]` |
| **pytest** | Test runner + fixtures | `pyproject.toml → [tool.pytest.ini_options]` |
| **uv** | Package & virtualenv manager | `pyproject.toml` |
| **Alembic** | Versioned DB schema migrations | `alembic.ini` |
| **structlog** | Structured / JSON logging | runtime config |

---

## Part I — Code Style

## 1. Syntax and formatting rules

### Naming conventions (PEP 8)

| Element | Convention | Example |
|---|---|---|
| Variables, functions | `snake_case` | `calculate_total`, `user_name` |
| Classes | `CapWords` | `HTTPClient`, `OrderService` |
| Constants | `UPPER_SNAKE_CASE` | `MAX_RETRIES`, `BASE_URL` |
| Modules/packages | `lowercase` (short, no underscores for packages) | `utils`, `mypackage` |
| Type variables | `CapWords` (short) | `T`, `ResponseT` |
| Exceptions | `CapWords` + `Error` suffix | `NotFoundError` |
| Private | `_single_leading_underscore` | `_internal_cache` |

Naming conventions signal intent: `UPPER_CASE` means don't reassign, `_prefix` means internal API, `CapWords` means instantiable class. First argument is always `self` for instance methods, `cls` for class methods. **Never use `l`, `O`, or `I`** as single-character names — they're visually ambiguous.

### Code layout

Use **4 spaces** per indentation level, never tabs. **Line length is 88 characters** (Black's default, a pragmatic 10% increase over PEP 8's 79). Use **2 blank lines** before top-level definitions and **1 blank line** between methods in a class. Break long lines before binary operators (Knuth style):

```python
# GOOD
total = (
    gross_wages
    + taxable_interest
    + (dividends - qualified_dividends)
    - ira_deduction
)

# BAD — break after operator
total = (gross_wages +
         taxable_interest)
```

### Import ordering and grouping

Group imports in three sections separated by blank lines: standard library, third-party, local. Use absolute imports. Never use wildcard imports. Ruff's `I` rule set (isort) enforces this automatically.

```python
# GOOD
import os
import sys
from collections.abc import Sequence

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from myapp.core.config import Settings
from myapp.users.repository import UserRepository

# BAD
from os import *
import sys, os
```

### String formatting — f-strings as default

**F-strings are the default** for Python 3.11+. They're faster than `.format()` and `%`-formatting because they compile to optimized bytecode at parse time. Use `.format()` only for reusable templates.

```python
# GOOD
f"User {user.name} has {len(user.items)} items"
f"{value:.2f}"     # format specifiers
f"{x=}"            # debug format (prints "x=42")

# BAD — legacy approaches in new code
"Hello %s" % name
"Hello {}".format(name)

# BAD — complex logic inside f-strings (extract to variable)
f"Result: {sum(x**2 for x in data if x > threshold) / len(data):.2f}"
```

### Comprehensions vs loops

Use comprehensions for simple transformations and filters that fit on one line. Switch to explicit loops when the logic involves side effects, multiple statements, complex nesting, or error handling. A comprehension should be immediately understandable — if you need to study it, use a loop.

```python
# GOOD — simple transformation
names = [user.name for user in users if user.active]
lookup = {u.id: u for u in users}

# GOOD — explicit loop for complex logic
results = []
for user in users:
    try:
        profile = fetch_profile(user.id)
        results.append(normalize(profile))
    except ProfileError:
        logger.warning("skipping user %s", user.id)
```

### Walrus operator (PEP 572)

Use `:=` to eliminate duplicate computation in while-loops, conditionals with computed values, and comprehension filters. **Don't use it when a simple assignment is clearer.**

```python
# GOOD — eliminates duplicate call
while (chunk := file.read(8192)):
    process(chunk)

if (n := len(data)) > 10:
    print(f"List too long ({n} elements)")

results = [clean for s in strings if (clean := s.strip())]

# BAD — no benefit, harms readability
(y := f(x))       # just use y = f(x)
result = (a := f()) + (b := g())  # too clever
```

### Structural pattern matching (PEP 636)

`match/case` excels at **structural destructuring** — parsing commands, handling protocol messages, processing ASTs. Don't use it as a glorified `if/elif` chain. **Critical rule:** bare names in patterns are capture variables, not value comparisons. Use dotted names (`Color.RED`, `Status.ACTIVE`) for value matching.

```python
# GOOD — structural destructuring with guards
match command.split():
    case ["quit"]:
        quit_game()
    case ["go", direction]:
        current_room = move(direction)
    case ["get", item, *rest]:
        pick_up(item)

match point:
    case Point(x=0, y=0):
        print("Origin")
    case Point(x, y) if x == y:
        print(f"On diagonal at {x}")

# BAD — bare name captures instead of comparing
RED = 0
match color:
    case RED:       # CAPTURES into RED, doesn't compare!
        ...
```

### Black formatter configuration

Black is the uncompromising formatter — it enforces **88-char lines, double quotes, 4-space indentation, and trailing-comma preservation**. Use `# fmt: off` / `# fmt: on` sparingly for intentional formatting.

```toml
[tool.black]
line-length = 88
target-version = ["py311"]
```

### Ruff linter configuration

Ruff replaces Flake8, isort, pyupgrade, and dozens of plugins at 10–100x speed. Start with a moderate rule set and expand incrementally. **The recommended expansion path is** `E,F` → `+I` → `+UP` → `+B` → `+SIM` → `+C4` → `+N` → `+D`.

```toml
[tool.ruff]
line-length = 88
target-version = "py311"

[tool.ruff.lint]
select = [
    "E", "W",    # pycodestyle
    "F",         # Pyflakes
    "I",         # isort
    "UP",        # pyupgrade (modernize syntax)
    "B",         # flake8-bugbear
    "SIM",       # flake8-simplify
    "C4",        # flake8-comprehensions
    "N",         # pep8-naming
    "RUF",       # Ruff-specific rules
    "PTH",       # prefer pathlib
    "PERF",      # performance anti-patterns
]
ignore = ["E501"]  # line length handled by formatter
fixable = ["ALL"]

[tool.ruff.lint.isort]
known-first-party = ["myapp"]

[tool.ruff.lint.per-file-ignores]
"__init__.py" = ["F401"]
"tests/**" = ["S101", "ARG", "ANN"]

[tool.ruff.format]
quote-style = "double"
docstring-code-format = true
```

Modern projects can use **`ruff format`** as a drop-in replacement for Black (>99.9% output parity). Run `ruff check --fix` then `ruff format` in your pre-commit hook:

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.15.1
    hooks:
      - id: ruff-check
        args: [--fix]
      - id: ruff-format
```

---

## 2. Typing rules

### The mandate: type everything

Every function signature, variable annotation, and class attribute must be typed. Type hints are not enforced at runtime — they exist for static analysis (mypy, Pyright) and serve as executable documentation. **Python 3.11+ uses built-in generics** (`list[str]`, `dict[str, int]`) — the `typing.List`, `typing.Dict` aliases are deprecated.

```python
# GOOD — Python 3.11+
def process(items: list[int]) -> dict[str, int]:
    return {str(i): i * 2 for i in items}

scores: list[int] = []
config: dict[str, str | int] = {}

# BAD — deprecated typing aliases
from typing import List, Dict
def process(items: List[int]) -> Dict[str, int]: ...
```

**Accept broad types as inputs, return concrete types.** Use `collections.abc` for parameter types (`Iterable`, `Sequence`, `Mapping`) and concrete types for return values.

```python
from collections.abc import Iterable, Mapping

# GOOD — broad input, concrete output
def summarize(items: Iterable[int]) -> list[int]:
    return sorted(items)

def merge(base: Mapping[str, int], override: Mapping[str, int]) -> dict[str, int]:
    return {**base, **override}
```

### Modern union syntax — `X | None` not `Optional[X]`

Use the `|` union operator (PEP 604) for all unions. **`Optional[X]` is misleading** — it means `X | None`, not that the parameter is optional.

```python
# GOOD
def fetch(url: str, timeout: float | None = None) -> bytes: ...
def process(value: int | str) -> str | None: ...

# BAD
from typing import Union, Optional
def fetch(url: str, timeout: Optional[float] = None) -> bytes: ...
```

### Protocol classes vs ABCs (PEP 544)

**Protocols define structural interfaces** — a class satisfies a Protocol if it has matching methods, no inheritance required. Use Protocols for dependency interfaces. Use ABCs only when you need runtime enforcement or default implementations.

```python
from typing import Protocol

# GOOD — Protocol for dependency interface
class UserRepository(Protocol):
    def find_by_id(self, user_id: int) -> User | None: ...
    def save(self, user: User) -> User: ...

# Any class with these methods satisfies the protocol — no inheritance needed
class PostgresUserRepository:
    def find_by_id(self, user_id: int) -> User | None:
        return self.session.get(User, user_id)
    def save(self, user: User) -> User:
        self.session.add(user)
        return user
```

### TypedDict, NamedTuple, dataclasses — when to use each

| Type | Underlying | Mutable | Best for |
|------|-----------|---------|----------|
| `@dataclass` | class | Yes (`frozen=True` for immutable) | Internal domain objects, DTOs |
| `TypedDict` | `dict` | Yes | JSON schemas, API responses, dict-shaped data |
| `NamedTuple` | `tuple` | No | Lightweight immutable records, function returns |

```python
# dataclass — default choice for internal data
@dataclass(slots=True)
class User:
    id: int
    name: str
    tags: list[str] = field(default_factory=list)

# TypedDict — for dict-shaped data (JSON, APIs)
class UserDict(TypedDict):
    id: int
    name: str
    email: NotRequired[str]  # optional key

# NamedTuple — immutable records
class Point(NamedTuple):
    x: float
    y: float
```

### TypeVar, ParamSpec, and Concatenate

`TypeVar` creates generic type variables. `ParamSpec` (PEP 612) captures entire function signatures for typing decorators. `Concatenate` prepends parameters.

```python
from typing import Callable, ParamSpec, TypeVar
from functools import wraps

P = ParamSpec("P")
R = TypeVar("R")

# Signature-preserving decorator
def logged(func: Callable[P, R]) -> Callable[P, R]:
    @wraps(func)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        print(f"Calling {func.__name__}")
        return func(*args, **kwargs)
    return wrapper

# BAD — loses type information
def bad_decorator(func: Callable[..., R]) -> Callable[..., R]: ...
```

### Type narrowing patterns

Use `isinstance`, `is None` checks, and `TypeGuard` for custom narrowing. Type checkers understand these patterns and narrow types automatically.

```python
def process(x: int | str) -> str:
    if isinstance(x, int):
        return str(x * 2)     # x is int here
    return x.upper()          # x is str here

def safe(val: str | None) -> str:
    if val is None:
        return "default"
    return val.upper()        # val is str here

# Custom narrowing with TypeGuard
from typing import TypeGuard
def is_str_list(val: list[object]) -> TypeGuard[list[str]]:
    return all(isinstance(x, str) for x in val)
```

### Avoiding `Any` — strategies for fully typed codebases

- **Use `object`** instead of `Any` when you need "accepts anything" but want type safety
- **Use `TypeVar`** for generic functions instead of `Any`
- **Use `Protocol`** for structural types instead of `Any`
- **Use `@overload`** for functions with varying return types
- **Use targeted `# type: ignore[error-code]`** as last resort — never bare `# type: ignore`

```python
# GOOD — object restricts operations
def to_string(o: object) -> str:
    return str(o)

# BAD — Any allows anything silently
def to_string(o: Any) -> str:
    return o.nonexistent()  # no error with Any!
```

### mypy and Pyright configuration

Enable **strict mode** in both tools. mypy's `--strict` flag enables all strictness checks including `disallow-untyped-defs`, `disallow-any-generics`, and `warn-return-any`.

```toml
[tool.mypy]
python_version = "3.11"
strict = true
warn_unreachable = true
enable_error_code = ["ignore-without-code", "truthy-bool"]

[[tool.mypy.overrides]]
module = ["untyped_lib.*"]
ignore_missing_imports = true

[tool.pyright]
pythonVersion = "3.11"
typeCheckingMode = "strict"
include = ["src"]
reportMissingTypeStubs = "warning"
```

---

## Part II — Architecture

## 3. Dependency injection rules

### Constructor injection is the default

Every class that has collaborators or infrastructure dependencies receives them through `__init__`. Dependencies are visible in the constructor signature — no hidden coupling, no global state.

```python
# GOOD — explicit dependencies
class OrderService:
    def __init__(self, repo: OrderRepository, notifier: EmailNotifier) -> None:
        self.repo = repo
        self.notifier = notifier

    async def place_order(self, order: Order) -> None:
        await self.repo.save(order)
        await self.notifier.send_confirmation(order)

# BAD — hardcoded dependency
class OrderService:
    def __init__(self) -> None:
        self.repo = PostgresOrderRepository()  # tight coupling, untestable
```

### Why DI matters

DI enables **testability** (swap real implementations with fakes), **maintainability** (dependencies visible in constructor), and **flexibility** (configure different implementations for dev/test/prod). The Cosmic Python approach uses `FakeRepository` and `FakeUnitOfWork` throughout for fast unit tests — no monkey-patching required.

### Protocol-based interfaces

Define dependencies as `Protocol` types. Implementations satisfy protocols structurally — no inheritance chain needed. This is the Pythonic version of interface-based programming.

```python
from typing import Protocol

class PaymentGateway(Protocol):
    async def charge(self, amount: float, token: str) -> str: ...

class StripeGateway:
    async def charge(self, amount: float, token: str) -> str:
        return await stripe.charges.create(amount=amount, source=token)

class FakeGateway:
    def __init__(self) -> None:
        self.charges: list[float] = []
    async def charge(self, amount: float, token: str) -> str:
        self.charges.append(amount)
        return "fake_charge_id"
```

### Composition root pattern

Wire all dependencies in **one place** at the application's entry point. This is the "bootstrap script" in Cosmic Python terminology. Tests override with fakes.

```python
# bootstrap.py — composition root
def create_app() -> FastAPI:
    settings = Settings()
    engine = create_async_engine(settings.database_url)
    session_factory = async_sessionmaker(engine)

    user_repo = PostgresUserRepository(session_factory)
    email_service = SMTPEmailService(settings.smtp_url)
    user_service = UserService(user_repo, email_service)
    # Register routes with wired services...
    return app

# test_bootstrap.py — override with fakes
def create_test_app() -> FastAPI:
    user_repo = FakeUserRepository()
    email_service = FakeEmailService()
    user_service = UserService(user_repo, email_service)
    return app
```

### Avoid the service locator anti-pattern

Service locators are global registries where components look up dependencies at runtime. They hide dependencies, create order-dependent initialization, and violate "explicit is better than implicit."

```python
# BAD — service locator
class OrderService:
    def process(self) -> None:
        repo = ServiceLocator.get("order_repo")  # hidden dependency!

# GOOD — constructor injection
class OrderService:
    def __init__(self, repo: OrderRepository) -> None:
        self.repo = repo  # visible, testable
```

### DI containers vs manual wiring

**Start with manual wiring** (bootstrap script). Graduate to a DI framework like `dependency-injector` only when the dependency graph becomes complex with chained dependencies. Manual wiring is simpler, more transparent, and sufficient for most projects.

### Factory patterns for complex creation

Use `functools.partial` or callable classes to pre-bind dependencies to handlers:

```python
import functools

def allocate(cmd: AllocateCommand, uow: AbstractUnitOfWork) -> str:
    with uow:
        batch = uow.batches.get(cmd.sku)
        batch.allocate(OrderLine(cmd.orderid, cmd.sku, cmd.qty))
        uow.commit()
    return batch.reference

# Bootstrap pre-binds the dependency
uow = SqlAlchemyUnitOfWork(session_factory)
allocate_handler = functools.partial(allocate, uow=uow)
```

---

## 4. Architecture patterns

### When each pattern applies

Not every application needs every pattern. **Adopt incrementally as complexity warrants.** The Cosmic Python authors explicitly warn: "We're not saying every single application needs to be built this way."

| Pattern | Use when | Skip when |
|---------|----------|-----------|
| Domain Model | Complex business rules, many invariants | Simple CRUD |
| Repository | Testable data access, plan to swap storage | Scripts, trivial apps |
| Unit of Work | Atomic writes across multiple repos | Single-table CRUD |
| Service Layer | Orchestration logic growing in controllers | < 3 use cases |
| CQRS | Read/write patterns differ significantly | Uniform access patterns |
| Events | Side effects, microservice integration | Simple monolith workflows |

### Domain Model — rich over anemic

The domain model encodes business rules in plain Python objects, free from infrastructure concerns. **Rich models contain behavior; anemic models are just data bags with logic scattered elsewhere.**

```python
# GOOD — rich domain model (Cosmic Python style)
@dataclass(frozen=True)
class OrderLine:  # Value Object
    orderid: str
    sku: str
    qty: int

class Batch:  # Entity
    def __init__(self, ref: str, sku: str, qty: int, eta: date | None) -> None:
        self.reference = ref
        self.sku = sku
        self.eta = eta
        self._purchased_quantity = qty
        self._allocations: set[OrderLine] = set()

    def allocate(self, line: OrderLine) -> None:
        if self.can_allocate(line):
            self._allocations.add(line)

    def can_allocate(self, line: OrderLine) -> bool:
        return self.sku == line.sku and self.available_quantity >= line.qty

    @property
    def available_quantity(self) -> int:
        return self._purchased_quantity - sum(l.qty for l in self._allocations)

# BAD — anemic model (logic outside the model)
class Batch:
    reference: str
    sku: str
    qty: int
    allocations: list  # just data, no behavior
```

### Repository pattern — abstracting data access

Repositories provide a collection-like interface for domain objects. The **abstract repository is the port; concrete implementations are adapters**.

```python
from abc import ABC, abstractmethod

class AbstractRepository(ABC):
    @abstractmethod
    def add(self, entity: Batch) -> None: ...
    @abstractmethod
    def get(self, reference: str) -> Batch: ...

class SqlAlchemyRepository(AbstractRepository):
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
    def add(self, entity: Batch) -> None:
        self.session.add(entity)
    def get(self, reference: str) -> Batch:
        return self.session.query(Batch).filter_by(reference=reference).one()

class FakeRepository(AbstractRepository):
    def __init__(self, batches: list[Batch] | None = None) -> None:
        self._batches = set(batches or [])
    def add(self, entity: Batch) -> None:
        self._batches.add(entity)
    def get(self, reference: str) -> Batch:
        return next(b for b in self._batches if b.reference == reference)
```

### Unit of Work — managing transactions

The UoW abstracts atomic operations, managing commit/rollback lifecycle and providing access to repositories. **Context managers make this idiomatic in Python** — the system is safe by default because `__exit__` rolls back uncommitted work.

```python
class AbstractUnitOfWork(ABC):
    batches: AbstractRepository

    def __enter__(self) -> "AbstractUnitOfWork":
        return self

    def __exit__(self, *args: object) -> None:
        self.rollback()

    @abstractmethod
    def commit(self) -> None: ...
    @abstractmethod
    def rollback(self) -> None: ...

# Usage in service layer
def allocate(orderid: str, sku: str, qty: int, uow: AbstractUnitOfWork) -> str:
    line = OrderLine(orderid, sku, qty)
    with uow:
        batches = uow.batches.list()
        batchref = model.allocate(line, batches)
        uow.commit()
    return batchref
```

### Service layer — orchestrating use cases

The service layer sits between entrypoints (API/CLI) and the domain model. It fetches from repos, calls domain logic, commits changes, and handles errors. **API handlers become thin adapters.**

```python
# services.py
def add_batch(ref: str, sku: str, qty: int, eta: date | None,
              uow: AbstractUnitOfWork) -> None:
    with uow:
        uow.batches.add(Batch(ref, sku, qty, eta))
        uow.commit()

# Flask/FastAPI becomes thin
@app.post("/allocate")
def allocate_endpoint(request: AllocateRequest) -> dict:
    try:
        ref = services.allocate(request.orderid, request.sku, request.qty, uow)
    except model.OutOfStock as e:
        return {"message": str(e)}, 400
    return {"batchref": ref}, 201
```

### Ports and adapters (Hexagonal Architecture)

All clean architecture variants reduce to the **Dependency Inversion Principle**: high-level modules (domain) don't depend on low-level ones (infrastructure). The ORM imports the model, not the other way around.

```
src/myapp/
├── domain/           # Core domain (no external dependencies)
│   └── model.py
├── service_layer/    # Use case orchestration
│   ├── services.py
│   └── unit_of_work.py
├── adapters/         # Infrastructure implementations
│   ├── orm.py
│   ├── repository.py
│   └── email.py
├── entrypoints/      # API/CLI
│   └── api.py
└── bootstrap.py      # Composition root
```

### CQRS and event-driven architecture

**CQRS** separates reads (simple SQL/views) from writes (full domain model + UoW). Use it when read and write access patterns differ significantly. **Domain events** capture side effects as first-class objects dispatched through a message bus, decoupling "what happened" from "what should happen next."

```python
# Domain event
@dataclass(frozen=True)
class OrderAllocated:
    orderid: str
    sku: str
    qty: int
    batchref: str

# Domain model raises events
class Batch:
    def allocate(self, line: OrderLine) -> None:
        self._allocations.add(line)
        self.events.append(OrderAllocated(
            orderid=line.orderid, sku=line.sku,
            qty=line.qty, batchref=self.reference,
        ))

# Handler responds to event
def publish_allocated(event: OrderAllocated, publish: Callable) -> None:
    publish("line_allocated", event)
```

---

## Part III — Quality & Operations

## 5. Testing strategy

### pytest as the standard

Use pytest with plain test functions. Leverage automatic discovery, assertion introspection, and the fixture system. **Never use `unittest.TestCase` in new code.**

```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
addopts = ["--strict-markers", "--strict-config", "-ra", "--tb=short"]
markers = ["slow: marks tests as slow", "integration: marks integration tests"]
```

### Test pyramid: 70/20/10

Aim for **70% unit tests** (milliseconds, no I/O), **20% integration** (real DB via containers, seconds), **10% E2E** (critical user workflows only). Unit tests should complete in under 2–3 minutes for the full suite.

### Fixtures and conftest.py patterns

Place shared fixtures in `conftest.py`. Use **factory fixtures** for flexible test data. Limit each fixture to one state-changing action with cleanup via `yield`. Use the narrowest scope possible — `function` scope is default and safest.

```python
# conftest.py
@pytest.fixture
def make_user():
    """Factory fixture for creating test users."""
    created: list[User] = []
    def _make(name: str = "default", role: str = "viewer") -> User:
        user = User(name=name, role=role)
        created.append(user)
        return user
    yield _make
    for u in created:
        u.delete()

@pytest.fixture(scope="session")
def db_engine():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    yield engine
    engine.dispose()

@pytest.fixture
def db_session(db_engine):
    connection = db_engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection)
    yield session
    session.close()
    transaction.rollback()
    connection.close()
```

### Mocking — prefer DI over patch()

**Prefer constructor injection with fakes over `patch()`.** When you must mock, use `patch()` targeting where the object is used (not where it's defined). Always use `autospec=True`.

```python
# GOOD — DI with fake
class FakeEmailSender:
    def __init__(self) -> None:
        self.sent: list[tuple[str, str]] = []
    def send(self, to: str, body: str) -> bool:
        self.sent.append((to, body))
        return True

def test_sends_welcome_email():
    fake = FakeEmailSender()
    service = NotificationService(email_sender=fake)
    service.welcome_user("user@test.com")
    assert len(fake.sent) == 1
    assert fake.sent[0][0] == "user@test.com"

# ACCEPTABLE — patch for external APIs
@patch("myapp.client.requests.get")
def test_fetch_data(mock_get):
    mock_get.return_value.json.return_value = {"status": "ok"}
    result = myapp.client.fetch_data("http://example.com")
    assert result == {"status": "ok"}
```

### Property-based testing with Hypothesis

Use Hypothesis for discovering edge cases through **round-trip properties** (`decode(encode(x)) == x`), **invariants** (`len(sorted(lst)) == len(lst)`), and no-crash testing. Hypothesis auto-shrinks failing examples to minimal reproductions.

```python
from hypothesis import given, strategies as st

@given(st.lists(st.integers()))
def test_sort_preserves_length(lst):
    assert len(sorted(lst)) == len(lst)

@given(st.text())
def test_json_roundtrip(s):
    assert json.loads(json.dumps(s)) == s
```

### Test naming and structure

Name tests descriptively: `test_<unit>_<scenario>_<expected>`. Structure every test with **Arrange-Act-Assert** separated by blank lines. One action per test.

```python
def test_transfer_funds_deducts_from_source():
    # Arrange
    source = Account(balance=1000)
    target = Account(balance=0)

    # Act
    transfer(source, target, amount=200)

    # Assert
    assert source.balance == 800
    assert target.balance == 200
```

### Coverage and async testing

Target **80% line coverage** as a minimum gate. Use branch coverage for critical paths. Don't chase 100% — it produces diminishing returns and incentivizes useless tests. For async testing, use `pytest-asyncio` with `asyncio_mode = "auto"` and `AsyncMock`.

```toml
[tool.coverage.run]
source = ["src"]
branch = true
omit = ["*/migrations/*", "*/tests/*"]

[tool.coverage.report]
fail_under = 80
show_missing = true
exclude_lines = ["pragma: no cover", "if TYPE_CHECKING:"]
```

```python
async def test_fetch_user_returns_data():
    service = UserService(client=AsyncMock(
        get=AsyncMock(return_value={"id": 1, "name": "Alice"})
    ))
    user = await service.fetch_user(1)
    assert user["name"] == "Alice"
```

---

## 6. Async best practices

### TaskGroups over gather (Python 3.11+)

**`asyncio.TaskGroup` provides stronger safety guarantees than `gather()`:** if any task raises, TaskGroup cancels all remaining tasks and collects exceptions into an `ExceptionGroup`. Use `asyncio.run()` as the single entry point.

```python
import asyncio

async def fetch_all() -> tuple[list[User], list[Post]]:
    async with asyncio.TaskGroup() as tg:
        users_task = tg.create_task(fetch_users())
        posts_task = tg.create_task(fetch_posts())
    return users_task.result(), posts_task.result()

if __name__ == "__main__":
    asyncio.run(fetch_all())

# Exception handling with except*
async def fetch_safe():
    try:
        async with asyncio.TaskGroup() as tg:
            tg.create_task(risky_op_1())
            tg.create_task(risky_op_2())
    except* ConnectionError as eg:
        for exc in eg.exceptions:
            logger.error("Connection failed: %s", exc)
```

### Structured concurrency

All concurrent tasks must have a **clear owner and bounded lifetime**. Use `TaskGroup` and `asyncio.timeout()`. Never fire-and-forget tasks without tracking references.

```python
# GOOD — bounded lifetime
async def process_batch(items: list[str]) -> None:
    async with asyncio.TaskGroup() as tg:
        for item in items:
            tg.create_task(process_item(item))
    # ALL tasks complete or cancel before this line

# GOOD — timeout
async def with_timeout() -> dict:
    try:
        async with asyncio.timeout(5.0):
            return await fetch(url)
    except TimeoutError:
        logger.warning("Timeout fetching %s", url)
        return {}
```

### The four async pitfalls

**Blocking the event loop** is the most common mistake. Any synchronous I/O (file reads, `requests.get()`, `time.sleep()`) blocks all coroutines.

```python
# BAD — blocks event loop
async def handler():
    data = requests.get("https://api.example.com")  # blocks everything!
    time.sleep(1)  # blocks everything!

# GOOD — use async alternatives or to_thread
async def handler():
    data = await asyncio.to_thread(requests.get, "https://api.example.com")
    await asyncio.sleep(1)
```

**Forgetting `await`** produces coroutine objects that are truthy, causing silent bugs. **Swallowing `CancelledError`** breaks TaskGroup/timeout internals — always re-raise after cleanup. **Using deprecated `get_event_loop()`** instead of `asyncio.run()` leads to lifecycle issues.

### Concurrency control with semaphores

Use `asyncio.Semaphore` to limit concurrent operations. Uncontrolled concurrency causes HTTP 429 errors and connection pool exhaustion.

```python
semaphore = asyncio.Semaphore(5)  # max 5 concurrent

async def fetch_with_limit(url: str, client: httpx.AsyncClient) -> Response:
    async with semaphore:
        return await client.get(url)

async def fetch_all(urls: list[str]) -> list[Response]:
    async with httpx.AsyncClient() as client:
        async with asyncio.TaskGroup() as tg:
            tasks = [tg.create_task(fetch_with_limit(url, client)) for url in urls]
    return [t.result() for t in tasks]
```

### When to use async vs sync

Use async for **I/O-bound tasks with high concurrency** (web servers, hundreds of concurrent connections). Use sync for CPU-bound work, simple scripts, or when all dependencies are synchronous. Async adds complexity — only adopt when the concurrency benefit justifies it. For CPU-bound work in async contexts, use `asyncio.to_thread()` for I/O blocking calls or `ProcessPoolExecutor` for true CPU parallelism.

---

## 7. Error handling

### Exception hierarchy design

Create a **single base exception** for your application. Derive all custom exceptions from it. This lets callers catch broadly (`except AppError`) or narrowly (`except NotFoundError`).

```python
class AppError(Exception):
    """Base exception for myapp."""
    def __init__(self, message: str, code: str = "UNKNOWN",
                 details: dict | None = None) -> None:
        self.message = message
        self.code = code
        self.details = details or {}
        super().__init__(message)

class NotFoundError(AppError):
    def __init__(self, resource: str, id: str | int) -> None:
        super().__init__(
            message=f"{resource} {id} not found",
            code="NOT_FOUND",
            details={"resource": resource, "id": id},
        )

class ValidationError(AppError):
    def __init__(self, field: str, reason: str) -> None:
        super().__init__(
            message=f"validation failed on '{field}': {reason}",
            code="VALIDATION_ERROR",
            details={"field": field, "reason": reason},
        )
```

### Catch, propagate, or translate

**Catch** if you can meaningfully recover (retry, fallback, default value). **Propagate** if the caller is better positioned. **Translate** at layer boundaries — convert infrastructure exceptions to domain exceptions.

```python
# GOOD — translate at boundary
def get_user(self, user_id: int) -> User:
    try:
        return self.session.query(User).filter_by(id=user_id).one()
    except NoResultFound:
        raise NotFoundError("user", user_id) from None

# BAD — catch and swallow
try:
    process_data(data)
except Exception:
    pass  # "The Most Diabolical Python Antipattern"
```

**Never catch bare `Exception` except at application boundaries** (ASGI handler, CLI main). Deep in business logic, it masks `TypeError`, `AttributeError`, and other real bugs.

### ExceptionGroups (Python 3.11+)

Use `ExceptionGroup` when **multiple independent errors** occur simultaneously — concurrent tasks, batch validation. Use `except*` to handle each type selectively. The `except*` clauses can all match (unlike `except` which stops at first match).

```python
def validate_config(config: dict) -> None:
    errors: list[Exception] = []
    if "host" not in config:
        errors.append(KeyError("'host' is required"))
    if "port" in config and not isinstance(config["port"], int):
        errors.append(TypeError("'port' must be an integer"))
    if errors:
        raise ExceptionGroup("config validation failed", errors)

try:
    validate_config({"port": "8080"})
except* TypeError as eg:
    print(f"Type errors: {[str(e) for e in eg.exceptions]}")
except* KeyError as eg:
    print(f"Missing keys: {[str(e) for e in eg.exceptions]}")
```

### Context managers and the Result pattern

Use context managers for deterministic cleanup. Use `contextlib.suppress()` for expected-and-ignorable exceptions. For expected business failures, consider returning **Result objects** instead of raising exceptions — they make success/failure explicit in the type signature.

```python
from contextlib import suppress

# Context manager for cleanup
with suppress(FileNotFoundError):
    os.remove("temp_cache.dat")

# Result pattern for expected failures
@dataclass(frozen=True, slots=True)
class Ok(Generic[T]):
    value: T

@dataclass(frozen=True, slots=True)
class Err(Generic[E]):
    error: E

type Result[T, E] = Ok[T] | Err[E]

def find_user(user_id: int) -> Result[User, str]:
    user = db.get(user_id)
    if user is None:
        return Err("user not found")
    return Ok(user)
```

### Validation at boundaries

**Validate all external input at the edges** (API handlers, CLI parsers, message consumers). Once validated, trust internals. "Parse, don't validate" — transform raw input into typed domain objects at the boundary.

```python
# GOOD — validate at boundary with Pydantic
class CreateUserRequest(BaseModel):
    email: str = Field(..., pattern=r"^[\w.-]+@[\w.-]+\.\w+$")
    age: int = Field(..., ge=0, le=150)

@app.post("/users")
async def create_user(request: CreateUserRequest):
    # From here, request.email is guaranteed valid
    return await user_service.create(request.email, request.age)
```

---

## 8. Logging standards

### Core rules

Always use **`logging.getLogger(__name__)`** in each module. Never use the root logger directly. Never call `basicConfig()` in library code. Use `dictConfig()` once at startup.

```python
import logging
logger = logging.getLogger(__name__)  # e.g., "myapp.services.payment"

def process_payment(amount: float) -> None:
    logger.info("processing payment of %s", amount)
    try:
        charge(amount)
    except ChargeError:
        logger.exception("charge failed for amount %s", amount)
        raise
```

### Never use f-strings in log calls

Use **lazy `%`-formatting** or structlog's keyword binding. F-strings evaluate immediately even when the log level is disabled, wasting CPU on `expensive_serialize()` calls that produce output nobody sees. Lazy formatting also enables log aggregation tools to group identical patterns.

```python
# GOOD — lazy formatting
logger.debug("processing item %s with value %d", item_id, value)

# GOOD — structlog keyword binding
log.info("order_processed", order_id=order.id, total=order.total)

# BAD — f-string always evaluates
logger.debug(f"processing item {item_id} with value {expensive_fn()}")
```

### Log levels

| Level | When to use | Example |
|-------|------------|---------|
| `DEBUG` | Detailed diagnostic info, disabled in production | Cache hits, SQL queries |
| `INFO` | Normal operations, confirms things work | Server started, request completed |
| `WARNING` | Unexpected but recoverable condition | Rate limit approaching, deprecated API call |
| `ERROR` | Operation failed, application continues | Payment processing failed |
| `CRITICAL` | System-level failure, may need to stop | Database pool exhausted |

Reserve ERROR/CRITICAL for true system failures. User input validation failures are WARNING or INFO, not ERROR.

### structlog for structured logging

Use `structlog` for machine-parseable JSON logs. Configure once at startup with `contextvars` integration for automatic correlation ID propagation.

```python
import structlog

def configure_logging(json_logs: bool = True, log_level: str = "INFO") -> None:
    shared_processors = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.format_exc_info,
    ]
    renderer = (structlog.processors.JSONRenderer() if json_logs
                else structlog.dev.ConsoleRenderer())

    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            *shared_processors,
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )
```

### Correlation IDs for request tracing

Generate or extract a request ID at the entry point (middleware). Store it in a `ContextVar`. Inject it into every log record automatically.

```python
from contextvars import ContextVar
import uuid

request_id_var: ContextVar[str] = ContextVar("request_id", default="-")

@app.middleware("http")
async def correlation_middleware(request: Request, call_next):
    req_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
    token = request_id_var.set(req_id)
    structlog.contextvars.bind_contextvars(request_id=req_id)
    try:
        response = await call_next(request)
        response.headers["X-Request-ID"] = req_id
        return response
    finally:
        request_id_var.reset(token)
        structlog.contextvars.clear_contextvars()
```

### Complete dictConfig example

```python
LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "json": {"()": "myapp.logging.JSONFormatter"},
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "json",
            "stream": "ext://sys.stdout",
        },
    },
    "loggers": {
        "myapp": {"level": "DEBUG", "handlers": ["console"], "propagate": False},
        "sqlalchemy.engine": {"level": "WARNING", "handlers": ["console"]},
        "uvicorn": {"level": "INFO", "handlers": ["console"], "propagate": False},
    },
    "root": {"level": "WARNING", "handlers": ["console"]},
}
```

---

## Part IV — Project & Scaling

## 9. Project structure

### src layout is the default

The `src/` layout prevents accidental imports from the project root (Python adds CWD to `sys.path` first). It forces installability, catching packaging bugs early. **PyPA and pyOpenSci recommend `src/` layout for new projects.**

### Organize by feature, not by layer

Feature-first organization keeps bounded contexts cohesive. Layer-first (`models/`, `services/`, `routes/`) scatters related code across directories. Use layers *within* each feature module.

```
myproject/
├── src/
│   └── myapp/
│       ├── __init__.py
│       ├── __main__.py              # python -m myapp
│       ├── main.py                  # FastAPI app factory
│       ├── bootstrap.py             # Composition root
│       ├── core/
│       │   ├── config.py            # pydantic-settings
│       │   ├── database.py          # Engine/session setup
│       │   └── security.py
│       ├── users/                   # Feature module
│       │   ├── models.py
│       │   ├── schemas.py
│       │   ├── repository.py
│       │   ├── service.py
│       │   └── router.py
│       ├── orders/                  # Another feature module
│       │   ├── models.py
│       │   ├── schemas.py
│       │   ├── repository.py
│       │   ├── service.py
│       │   └── router.py
│       └── api/v1/router.py         # Aggregates all v1 routes
├── tests/
│   ├── conftest.py
│   ├── users/
│   └── orders/
├── alembic/
├── pyproject.toml                   # Single config file
├── uv.lock                          # Deterministic lockfile
├── .python-version
└── Dockerfile
```

### pyproject.toml as single configuration file

`pyproject.toml` replaces `setup.py`, `setup.cfg`, `requirements.txt`, `.flake8`, `pytest.ini`, and `mypy.ini`. It's declarative, standard, and tool-agnostic (PEP 518/621).

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "myapp"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = [
    "fastapi>=0.115",
    "uvicorn[standard]>=0.30",
    "sqlalchemy>=2.0",
    "pydantic-settings>=2.0",
]

[project.optional-dependencies]
dev = ["pytest>=8.0", "ruff>=0.5", "mypy>=1.10"]

[project.scripts]
myapp = "myapp.cli:main"
```

### Dependency management with uv

**`uv` is the modern all-in-one Python package manager** — 10–100x faster than pip, with a universal lockfile, automatic venv management, and built-in Python version management.

```bash
uv init myapp                   # creates pyproject.toml
uv add fastapi sqlalchemy       # adds deps + updates lockfile
uv add --group dev pytest ruff  # dev dependencies
uv lock                         # deterministic lockfile
uv sync                         # install from lockfile
uv run pytest                   # run inside managed venv
uv run uvicorn myapp.main:app --reload
```

### Configuration management with pydantic-settings

Use `BaseSettings` for typed, validated configuration from environment variables. Fail fast at startup if required config is missing.

```python
from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_nested_delimiter="__",
        case_sensitive=False,
    )

    app_name: str = "MyApp"
    debug: bool = False
    database_url: str                    # required — fails fast if missing
    redis_url: str = "redis://localhost:6379"
    secret_key: SecretStr               # required, masked in logs
    log_level: str = "INFO"
```

---

## 10. Scalability principles

### SOLID applied to Python

**Single Responsibility:** each class/module has one reason to change. **Interface Segregation via Protocols:** define narrow, role-based interfaces — don't force implementors to depend on methods they don't use. **Dependency Inversion:** high-level modules depend on abstractions (Protocols), not concrete implementations.

```python
# ISP — small, focused protocols
class Readable(Protocol):
    def read(self, id: int) -> dict: ...

class Writable(Protocol):
    def write(self, data: dict) -> int: ...

# Consumer depends only on what it needs
def generate_report(source: Readable) -> str:
    data = source.read(42)
    return format_report(data)
```

### Immutability where possible

Use **frozen dataclasses** for value objects, **tuples** for immutable sequences, **frozensets** for immutable sets. Immutable objects are thread-safe, hashable, and prevent accidental mutation. `slots=True` (Python 3.10+) reduces memory and speeds up attribute access.

```python
@dataclass(frozen=True, slots=True)
class Money:
    amount: int        # cents
    currency: str = "USD"

    def add(self, other: "Money") -> "Money":
        assert self.currency == other.currency
        return Money(self.amount + other.amount, self.currency)

ALLOWED_ROLES: frozenset[str] = frozenset({"admin", "editor", "viewer"})
```

### Stateless services and configuration externalization

Services hold no request-specific state. All state lives in external stores (database, Redis, S3). This enables horizontal scaling — any instance can handle any request. Follow **12-factor app principles**: store config in environment variables, never hardcode credentials or deploy-specific values.

### Database migrations with Alembic

Use Alembic for versioned, reversible schema migrations. Always review autogenerated migrations. Use `alembic check` in CI to verify no pending migrations exist.

```bash
alembic init alembic
alembic revision --autogenerate -m "add users table"
alembic upgrade head
alembic downgrade -1
```

### Horizontal scaling for Python backends

Python's GIL limits parallelism within a single process. Scale out with **multiple Gunicorn/Uvicorn workers** (one per CPU core), container orchestration (Kubernetes HPA), and async I/O for concurrent connections. Use the workers formula **`(2 × CPU cores) + 1`** as a baseline. Externalize all state, use connection pooling, and offload CPU-heavy tasks to Celery workers.

```bash
gunicorn myapp.main:app \
    --worker-class uvicorn.workers.UvicornWorker \
    --workers $((2 * $(nproc) + 1)) \
    --bind 0.0.0.0:8000 \
    --max-requests 1000 \
    --max-requests-jitter 100
```

```python
engine = create_async_engine(
    settings.database_url,
    pool_size=5,          # per worker
    max_overflow=10,      # burst capacity
    pool_recycle=300,     # recycle stale connections
    pool_pre_ping=True,   # verify before use
)
```

### API versioning from day one

Prefer **URL path versioning** (`/api/v1/`) for visibility and simplicity. Include deprecation headers with sunset dates on old versions. Version your API from the start — retrofitting is far more painful than planning ahead.

```python
app.include_router(api_v1_router, prefix="/api/v1")
app.include_router(api_v2_router, prefix="/api/v2")
```

---

## Conclusion

These standards form a coherent system, not a random collection of rules. The formatting and typing rules create a foundation where code is consistent and statically verifiable. Dependency injection makes that well-typed code testable without monkey-patching. The architecture patterns — Repository, Unit of Work, Service Layer — give DI natural boundaries to operate within. The testing strategy validates everything cheaply through the injected seams. Async patterns, error handling, and logging provide the operational backbone. Project structure and scalability principles ensure the codebase grows without collapsing under its own weight.

**The single most important principle** running through every section: make dependencies explicit. Explicit type hints. Explicit constructor injection. Explicit error handling. Explicit configuration. When everything is visible in the code, the system is understandable, testable, and maintainable. Adopt these standards incrementally — enforce formatting and typing first, add architectural patterns only as your domain complexity demands them, and resist the temptation to over-engineer simple CRUD services with patterns designed for complex business logic.