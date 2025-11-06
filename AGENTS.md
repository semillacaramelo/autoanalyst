# AI Agent Development Guidelines

**Version:** 1.0.0  
**Last Updated:** November 5, 2025  
**Scope:** Universal best practices for AI-assisted software development

---

## Purpose

This document establishes **mandatory** requirements for AI agents (including GitHub Copilot, coding assistants, and autonomous development tools) working on software projects. These guidelines are **project-agnostic**, **language-agnostic**, and **platform-agnostic** – they apply universally to professional software development.

**Key Principle:** AI agents MUST follow industry-standard software development practices, not merely suggest or recommend them.

---

## Table of Contents

1. [Testing Requirements](#testing-requirements)
2. [Development Workflow](#development-workflow)
3. [Code Quality Standards](#code-quality-standards)
4. [Documentation Obligations](#documentation-obligations)
5. [Version Control Practices](#version-control-practices)
6. [Error Handling & Debugging](#error-handling--debugging)
7. [Performance Considerations](#performance-considerations)
8. [Security & Validation](#security--validation)
9. [AI Agent Responsibilities](#ai-agent-responsibilities)
10. [Enforcement & Compliance](#enforcement--compliance)

---

## 1. Testing Requirements

### 1.1 Mandatory Testing

**Requirement:** AI agents MUST write automated tests for ALL new code and modifications.

**Implementation:**
- **Before writing implementation code:** Write failing tests first (Test-Driven Development preferred)
- **After writing implementation code:** IMMEDIATELY write comprehensive tests
- **No exceptions:** If implementation is committed, tests MUST be committed in the same session

**Test Coverage Requirements:**
```
Minimum Coverage Thresholds:
- Critical paths: 100%
- Business logic: ≥90%
- Utility functions: ≥85%
- Integration points: ≥80%
- Overall codebase: ≥75%
```

**Test Types (ALL required):**

1. **Unit Tests**
   - Test individual functions/methods in isolation
   - Use mocks/stubs for external dependencies
   - Fast execution (<100ms per test)
   - Example: Testing a calculation function with various inputs

2. **Integration Tests**
   - Test component interactions
   - Verify API contracts
   - Test database interactions
   - Example: Testing service layer with repository

3. **Functional Tests**
   - Test complete user workflows
   - Verify business requirements
   - End-to-end scenarios
   - Example: Testing user registration flow

4. **Edge Case Tests**
   - Boundary values (min/max, empty, null)
   - Error conditions
   - Race conditions (concurrent access)
   - Resource exhaustion scenarios

**Testing Frameworks (language-specific):**
- Python: `pytest` (preferred), `unittest`
- JavaScript/TypeScript: `Jest`, `Mocha`, `Vitest`
- Java: `JUnit`, `TestNG`
- C#: `NUnit`, `xUnit`
- Go: `testing` package
- Ruby: `RSpec`, `Minitest`

### 1.2 Test Structure

**Arrange-Act-Assert Pattern (AAA):**
```python
def test_user_registration():
    # ARRANGE: Set up test data and dependencies
    user_data = {"email": "test@example.com", "password": "secure123"}
    mock_db = Mock()
    
    # ACT: Execute the functionality being tested
    result = register_user(user_data, mock_db)
    
    # ASSERT: Verify expected outcomes
    assert result.success is True
    assert mock_db.save.called_once()
```

**Test Naming Convention:**
```
Pattern: test_<what>_<condition>_<expected_result>

Examples:
- test_login_with_valid_credentials_returns_success
- test_divide_by_zero_raises_value_error
- test_cache_with_expired_entry_returns_none
```

### 1.3 Test Execution

**AI Agent MUST:**
1. Run ALL tests before committing code
2. Verify 100% pass rate (no skipped/ignored tests)
3. Report test results with coverage metrics
4. Fix failing tests before proceeding

**Command Examples:**
```bash
# Python
pytest --cov=src --cov-report=term-missing tests/

# JavaScript
npm test -- --coverage

# Java
mvn test jacoco:report

# Go
go test -cover ./...
```

---

## 2. Development Workflow

### 2.1 Software Development Lifecycle (SDLC)

**Mandatory Phases:**

1. **Requirements Analysis**
   - Understand user request completely
   - Ask clarifying questions when ambiguous
   - Document assumptions explicitly

2. **Design**
   - Plan architecture before coding
   - Consider design patterns
   - Identify dependencies and interfaces

3. **Implementation**
   - Write clean, readable code
   - Follow language idioms
   - Apply SOLID principles

4. **Testing**
   - Write comprehensive test suite (see Section 1)
   - Achieve required coverage
   - Validate edge cases

5. **Code Review**
   - Self-review before presenting
   - Check for common anti-patterns
   - Verify documentation completeness

6. **Deployment Preparation**
   - Update CHANGELOG
   - Version bump if applicable
   - Migration scripts if needed

### 2.2 Test-Driven Development (TDD)

**Preferred Workflow:**

```
┌──────────────────────────────────────┐
│ 1. Write Failing Test (RED)         │
│    - Define expected behavior        │
│    - Test fails (code doesn't exist) │
└────────────┬─────────────────────────┘
             │
             ▼
┌──────────────────────────────────────┐
│ 2. Write Minimal Code (GREEN)       │
│    - Implement simplest solution     │
│    - Test passes                     │
└────────────┬─────────────────────────┘
             │
             ▼
┌──────────────────────────────────────┐
│ 3. Refactor (REFACTOR)              │
│    - Improve code quality            │
│    - Tests still pass                │
└────────────┬─────────────────────────┘
             │
             └───► Repeat for next feature
```

**Benefits:**
- Ensures testability
- Prevents over-engineering
- Documents expected behavior
- Catches regressions early

### 2.3 Continuous Integration (CI)

**Requirements:**
- All tests MUST pass in CI pipeline
- No commits bypass CI checks
- Failed CI blocks merge/deployment

**Typical CI Pipeline:**
```yaml
stages:
  - lint         # Code style checks
  - test         # Unit & integration tests
  - build        # Compile/package
  - security     # Vulnerability scans
  - deploy       # Staging/production
```

---

## 3. Code Quality Standards

### 3.1 Readability

**Principles:**
- Code is read 10x more than written
- Self-documenting code preferred
- Clear naming over clever tricks

**Naming Conventions:**
```python
# Variables: descriptive nouns
user_count = 10        # Good
x = 10                 # Bad

# Functions: verbs describing action
def calculate_total_price():  # Good
def do_stuff():              # Bad

# Classes: nouns representing concepts
class UserRepository:  # Good
class Manager:        # Bad (too generic)

# Constants: UPPER_SNAKE_CASE
MAX_RETRIES = 3       # Good
maxRetries = 3        # Bad
```

### 3.2 Maintainability

**SOLID Principles:**

1. **Single Responsibility Principle (SRP)**
   - One class/function = one reason to change
   - Example: Separate data validation from business logic

2. **Open/Closed Principle (OCP)**
   - Open for extension, closed for modification
   - Use inheritance/composition over editing existing code

3. **Liskov Substitution Principle (LSP)**
   - Subtypes must be substitutable for base types
   - No surprising behavior in derived classes

4. **Interface Segregation Principle (ISP)**
   - Many specific interfaces > one general interface
   - Clients shouldn't depend on unused methods

5. **Dependency Inversion Principle (DIP)**
   - Depend on abstractions, not concretions
   - High-level modules don't depend on low-level modules

### 3.3 Complexity Management

**Metrics:**
```
Cyclomatic Complexity: ≤10 per function
Lines of Code per Function: ≤50
Parameters per Function: ≤5
Nesting Depth: ≤4
```

**Refactoring Triggers:**
- Duplicate code (DRY principle)
- Long functions (extract methods)
- Large classes (split responsibilities)
- Complex conditionals (strategy pattern)

### 3.4 Code Smells to Avoid

| Smell | Description | Solution |
|-------|-------------|----------|
| Magic Numbers | Hardcoded values | Use named constants |
| God Object | Class knows/does too much | Split into smaller classes |
| Long Parameter List | >5 parameters | Use parameter objects |
| Shotgun Surgery | Change requires edits everywhere | Improve cohesion |
| Feature Envy | Method uses another class more | Move method |

---

## 4. Documentation Obligations

### 4.1 Code-Level Documentation

**Docstrings (MANDATORY for):**
- All public classes
- All public methods/functions
- All modules/packages
- Complex algorithms

**Format (language-specific):**

**Python (Google Style):**
```python
def calculate_discount(price: float, discount_percent: float) -> float:
    """Calculate final price after discount.

    Args:
        price: Original price before discount (must be positive).
        discount_percent: Discount percentage (0-100).

    Returns:
        Final price after applying discount.

    Raises:
        ValueError: If price is negative or discount_percent not in 0-100.

    Example:
        >>> calculate_discount(100.0, 20.0)
        80.0
    """
```

**JavaScript (JSDoc):**
```javascript
/**
 * Calculate final price after discount.
 * @param {number} price - Original price before discount.
 * @param {number} discountPercent - Discount percentage (0-100).
 * @returns {number} Final price after applying discount.
 * @throws {Error} If price is negative or discountPercent not in 0-100.
 * @example
 * calculateDiscount(100, 20); // Returns 80
 */
function calculateDiscount(price, discountPercent) { }
```

### 4.2 Project Documentation

**Required Files:**

1. **README.md**
   - Project overview
   - Installation instructions
   - Quick start guide
   - Contributing guidelines

2. **CHANGELOG.md**
   - Version history
   - Breaking changes
   - New features
   - Bug fixes

3. **API.md / API_REFERENCE.md**
   - Public API documentation
   - Request/response formats
   - Authentication details
   - Rate limits

4. **CONTRIBUTING.md**
   - How to contribute
   - Code style guide
   - Testing requirements
   - PR process

### 4.3 Inline Comments

**When to Comment:**
- **WHY**, not WHAT (code should be self-explanatory)
- Complex algorithms
- Non-obvious optimizations
- Workarounds for known issues
- TODO/FIXME for technical debt

**Example:**
```python
# Good: Explains WHY
# Use binary search for O(log n) lookup since list is sorted
index = binary_search(sorted_list, target)

# Bad: Explains WHAT (obvious from code)
# Set x to 5
x = 5
```

---

## 5. Version Control Practices

### 5.1 Commit Standards

**Conventional Commits Format:**
```
<type>(<scope>): <subject>

<body>

<footer>
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation only
- `style`: Formatting changes
- `refactor`: Code restructure (no behavior change)
- `test`: Add/update tests
- `chore`: Build/tooling updates

**Example:**
```
feat(auth): add OAuth2 authentication support

Implement OAuth2 flow using Authorization Code Grant.
Supports Google, GitHub, and Microsoft providers.

Closes #123
Breaking Change: Removes legacy token-based auth
```

### 5.2 Branching Strategy

**Git Flow (recommended):**
```
main (production)
  ├── develop (integration)
  │    ├── feature/user-auth
  │    ├── feature/payment-gateway
  │    └── bugfix/login-timeout
  ├── hotfix/critical-security-patch
  └── release/v2.0.0
```

**Branch Naming:**
```
feature/<issue-number>-<short-description>
bugfix/<issue-number>-<short-description>
hotfix/<issue-number>-<short-description>
release/<version-number>
```

### 5.3 Pull Request Requirements

**Before Creating PR:**
1. ✅ All tests pass locally
2. ✅ Code follows style guide
3. ✅ Documentation updated
4. ✅ No merge conflicts
5. ✅ Changelog updated

**PR Description Template:**
```markdown
## Description
Brief summary of changes.

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
- [ ] Unit tests added/updated
- [ ] Integration tests added/updated
- [ ] Manual testing performed

## Checklist
- [ ] Code follows project style guide
- [ ] Self-review completed
- [ ] Documentation updated
- [ ] No breaking changes (or documented)
```

---

## 6. Error Handling & Debugging

### 6.1 Error Handling

**Principles:**
- **Fail fast:** Detect errors early
- **Fail safe:** Graceful degradation
- **Fail loud:** Log errors comprehensively

**Exception Hierarchy:**
```python
# Create custom exception hierarchy
class ApplicationError(Exception):
    """Base exception for application."""
    pass

class ValidationError(ApplicationError):
    """Data validation failed."""
    pass

class DatabaseError(ApplicationError):
    """Database operation failed."""
    pass
```

**Error Handling Pattern:**
```python
def process_payment(amount: float) -> PaymentResult:
    """Process payment with proper error handling."""
    try:
        # Validate input
        if amount <= 0:
            raise ValidationError(f"Invalid amount: {amount}")
        
        # Perform operation
        result = payment_gateway.charge(amount)
        
        # Log success
        logger.info(f"Payment processed: {amount}")
        return result
        
    except ValidationError as e:
        # Handle expected errors
        logger.warning(f"Validation failed: {e}")
        raise
        
    except PaymentGatewayError as e:
        # Handle external service errors
        logger.error(f"Payment gateway error: {e}")
        raise DatabaseError("Payment processing failed") from e
        
    except Exception as e:
        # Catch unexpected errors
        logger.exception(f"Unexpected error: {e}")
        raise ApplicationError("Internal error") from e
```

### 6.2 Logging

**Log Levels:**
```
DEBUG:    Detailed diagnostic info (development only)
INFO:     General informational messages
WARNING:  Something unexpected (application continues)
ERROR:    Error occurred (operation failed)
CRITICAL: System failure (application may crash)
```

**Structured Logging:**
```python
import logging
import json

logger = logging.getLogger(__name__)

# Structured log entry
logger.info(
    "User action",
    extra={
        "user_id": 12345,
        "action": "login",
        "ip_address": "192.168.1.1",
        "timestamp": "2025-11-05T10:30:00Z"
    }
)
```

### 6.3 Debugging

**Debug Information Requirements:**
- Stack traces (full context)
- Variable states at failure point
- Input parameters
- Environment details (OS, versions)
- Timestamps for timing issues

---

## 7. Performance Considerations

### 7.1 Optimization Guidelines

**Rules:**
1. **Measure first:** Profile before optimizing
2. **Premature optimization is evil:** Optimize critical paths only
3. **Big O matters:** Choose correct algorithms/data structures

**Algorithmic Complexity:**
```
O(1)       - Constant:      Dict lookup
O(log n)   - Logarithmic:   Binary search
O(n)       - Linear:        List iteration
O(n log n) - Linearithmic:  Merge sort
O(n²)      - Quadratic:     Nested loops (avoid!)
O(2ⁿ)      - Exponential:   Brute force recursion (never!)
```

### 7.2 Performance Testing

**Requirements:**
- Benchmark critical operations
- Load testing for APIs (requests/sec)
- Memory profiling for leaks
- Database query optimization (N+1 queries)

**Example (Python):**
```python
import timeit

def performance_test():
    """Compare implementation performance."""
    setup = "from mymodule import func_v1, func_v2"
    
    time_v1 = timeit.timeit("func_v1(1000)", setup=setup, number=10000)
    time_v2 = timeit.timeit("func_v2(1000)", setup=setup, number=10000)
    
    print(f"v1: {time_v1:.4f}s")
    print(f"v2: {time_v2:.4f}s")
    print(f"Speedup: {time_v1/time_v2:.2f}x")
```

---

## 8. Security & Validation

### 8.1 Input Validation

**ALWAYS validate:**
- User input (never trust client)
- API request data
- File uploads
- Database queries (parameterized only)

**Validation Example:**
```python
from pydantic import BaseModel, validator, Field

class UserRegistration(BaseModel):
    email: str = Field(..., regex=r'^[\w\.-]+@[\w\.-]+\.\w+$')
    password: str = Field(..., min_length=8)
    age: int = Field(..., ge=18, le=120)
    
    @validator('password')
    def password_strength(cls, v):
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain uppercase')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain digit')
        return v
```

### 8.2 Security Best Practices

**Mandatory:**
- ✅ Never hardcode secrets/API keys
- ✅ Use environment variables
- ✅ Hash passwords (bcrypt/argon2)
- ✅ Use HTTPS for APIs
- ✅ Validate SSL certificates
- ✅ Sanitize SQL queries (parameterized)
- ✅ Escape HTML output (XSS prevention)
- ✅ Rate limiting on public endpoints

**Forbidden:**
- ❌ `eval()` / `exec()` on user input
- ❌ SQL string concatenation
- ❌ Insecure deserialization
- ❌ Storing passwords in plain text
- ❌ Exposing stack traces to users

---

## 9. AI Agent Responsibilities

### 9.1 Code Generation

**AI Agent MUST:**
1. ✅ Write production-quality code (not prototypes)
2. ✅ Follow project's existing style/patterns
3. ✅ Include comprehensive error handling
4. ✅ Add logging for debugging
5. ✅ Write tests BEFORE or IMMEDIATELY AFTER implementation
6. ✅ Update documentation
7. ✅ Run tests and report results
8. ✅ Fix all issues before declaring "complete"

**AI Agent MUST NOT:**
1. ❌ Generate code without tests
2. ❌ Skip error handling "for brevity"
3. ❌ Leave TODOs without implementation timeline
4. ❌ Ignore test failures
5. ❌ Commit commented-out code
6. ❌ Use deprecated APIs without migration plan

### 9.2 Code Review

**Self-Review Checklist (AI must verify):**
```
Functionality:
  [ ] Code solves stated problem
  [ ] Edge cases handled
  [ ] No regressions introduced

Quality:
  [ ] Follows coding standards
  [ ] No code smells
  [ ] Appropriate abstractions

Testing:
  [ ] Tests written and passing
  [ ] Coverage >= project minimum
  [ ] Tests cover edge cases

Documentation:
  [ ] Docstrings complete
  [ ] README updated if needed
  [ ] CHANGELOG updated

Security:
  [ ] Input validated
  [ ] No secrets in code
  [ ] Dependencies updated
```

### 9.3 Communication

**When AI Agent MUST ask questions:**
- Requirements are ambiguous
- Multiple valid approaches exist
- Breaking changes necessary
- Security implications unclear
- Performance tradeoffs significant

**When AI Agent MUST report:**
- Tests pass/fail status
- Coverage metrics
- Deprecation warnings
- Security vulnerabilities
- Performance regressions

---

## 10. Enforcement & Compliance

### 10.1 Automated Checks

**Pre-commit Hooks:**
```bash
# .pre-commit-config.yaml
repos:
  - repo: local
    hooks:
      - id: tests
        name: Run Tests
        entry: pytest
        language: system
        pass_filenames: false
        always_run: true
        
      - id: lint
        name: Lint Code
        entry: ruff check
        language: system
        types: [python]
        
      - id: type-check
        name: Type Check
        entry: mypy
        language: system
        types: [python]
```

### 10.2 CI/CD Gates

**Required Checks (must pass):**
1. ✅ All tests pass (100% pass rate)
2. ✅ Code coverage >= threshold
3. ✅ No linting errors
4. ✅ No type errors
5. ✅ Security scan passes
6. ✅ Build succeeds

### 10.3 Quality Metrics

**Tracked Metrics:**
```
Code Coverage:        ≥75% (target: 90%)
Test Pass Rate:       100%
Build Success Rate:   ≥95%
Deployment Frequency: Daily (CI/CD)
Mean Time to Recovery: <1 hour
Change Failure Rate:  <15%
```

---

## Appendix A: Language-Specific Resources

### Python
- **Style Guide:** PEP 8 (https://peps.python.org/pep-0008/)
- **Testing:** pytest (https://docs.pytest.org/)
- **Type Hints:** PEP 484 (https://peps.python.org/pep-0484/)
- **Linter:** Ruff, flake8, pylint

### JavaScript/TypeScript
- **Style Guide:** Airbnb JavaScript Style Guide
- **Testing:** Jest, Vitest
- **Type System:** TypeScript
- **Linter:** ESLint

### Java
- **Style Guide:** Google Java Style Guide
- **Testing:** JUnit 5
- **Build Tool:** Maven, Gradle
- **Linter:** Checkstyle, PMD

### Go
- **Style Guide:** Effective Go (official)
- **Testing:** `testing` package
- **Formatting:** `gofmt` (mandatory)
- **Linter:** `golangci-lint`

---

## Appendix B: Common Anti-Patterns

| Anti-Pattern | Description | Solution |
|--------------|-------------|----------|
| **God Object** | Class does everything | Split into focused classes |
| **Spaghetti Code** | Tangled control flow | Extract methods, use patterns |
| **Copy-Paste Programming** | Duplicate code everywhere | Extract to functions/classes |
| **Magic Numbers** | Unexplained constants | Named constants with comments |
| **Shotgun Surgery** | Changes spread across many files | Improve cohesion, encapsulation |
| **Premature Optimization** | Optimize before measuring | Profile first, optimize hotspots |
| **Golden Hammer** | Same solution for everything | Learn multiple patterns/tools |
| **Not Invented Here** | Rewrite existing libraries | Use proven libraries |

---

## Appendix C: Testing Anti-Patterns

| Anti-Pattern | Description | Solution |
|--------------|-------------|----------|
| **Testing Implementation** | Tests internal details | Test public interface/behavior |
| **Fragile Tests** | Break on unrelated changes | Test behavior, not structure |
| **Slow Tests** | Long execution time | Mock I/O, use test doubles |
| **Flaky Tests** | Random pass/fail | Fix race conditions, timing |
| **Test Interdependence** | Tests depend on each other | Isolated tests with setup/teardown |
| **Assertion Roulette** | Multiple assertions, unclear failure | One logical assert per test |
| **Mystery Guest** | Hidden test dependencies | Explicit setup in test |

---

## Revision History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2025-11-05 | Initial release - comprehensive AI agent guidelines |

---

## License

This document is released under CC0 1.0 Universal (Public Domain). Use freely without attribution.

---

**END OF DOCUMENT**
