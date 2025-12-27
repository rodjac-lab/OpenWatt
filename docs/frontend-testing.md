# Frontend Testing Guide - OpenWatt UI

**Date**: 2025-11-16
**Stack**: Vitest + React Testing Library + Happy-DOM
**Coverage**: 70% minimum (enforced)

---

## 📋 Table des Matières

1. [Quick Start](#quick-start)
2. [Configuration](#configuration)
3. [Writing Tests](#writing-tests)
4. [Running Tests](#running-tests)
5. [Coverage](#coverage)
6. [CI Integration](#ci-integration)
7. [Best Practices](#best-practices)

---

## 🚀 Quick Start

### Installation

Dependencies are already installed in `ui/package.json`:

```json
{
  "devDependencies": {
    "vitest": "^2.0.0",
    "@testing-library/react": "^16.0.0",
    "@testing-library/user-event": "^14.5.2",
    "@testing-library/jest-dom": "^6.6.3",
    "happy-dom": "^15.11.7",
    "@vitest/coverage-v8": "^2.0.0"
  }
}
```

### Run Tests

```bash
cd ui

# Run all tests once
npm test

# Watch mode (re-run on changes)
npm run test:watch

# UI mode (browser interface)
npm run test:ui

# Coverage report
npm run test:coverage
```

---

## ⚙️ Configuration

### Vitest Config ([ui/vitest.config.ts](../ui/vitest.config.ts))

```typescript
import { defineConfig } from "vitest/config";
import react from "@vitejs/plugin-react";
import path from "path";

export default defineConfig({
  plugins: [react()],
  test: {
    environment: "happy-dom", // Fast DOM implementation
    globals: true, // No need to import describe/it/expect
    setupFiles: ["./vitest.setup.ts"],
    coverage: {
      provider: "v8",
      reporter: ["text", "json", "html", "lcov"],
      exclude: [
        "node_modules/",
        "vitest.setup.ts",
        "vitest.config.ts",
        "**/*.config.*",
        "**/*/types.ts",
        "**/__tests__/**",
        "**/*.test.*",
        ".next/",
      ],
      thresholds: {
        lines: 70,
        functions: 70,
        branches: 70,
        statements: 70,
      },
    },
  },
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./"),
    },
  },
});
```

**Key Features**:

- ✅ **happy-dom**: Faster than jsdom, sufficient for most React tests
- ✅ **globals: true**: Automatic `describe`, `it`, `expect` imports
- ✅ **Coverage thresholds**: 70% minimum enforced (build fails if < 70%)
- ✅ **Path alias**: `@/` resolves to `ui/` directory

### Setup File ([ui/vitest.setup.ts](../ui/vitest.setup.ts))

```typescript
import { afterEach } from "vitest";
import { cleanup } from "@testing-library/react";
import "@testing-library/jest-dom/vitest";

// Cleanup after each test
afterEach(() => {
  cleanup();
});
```

---

## ✍️ Writing Tests

### Test Structure

Place tests in `__tests__/` directories next to components:

```
ui/components/
├── FreshnessBadge.tsx
├── TariffList.tsx
└── __tests__/
    ├── FreshnessBadge.test.tsx
    └── TariffList.test.tsx
```

### Example 1: Simple Component Test

**Component**: [FreshnessBadge.tsx](../ui/components/FreshnessBadge.tsx)

**Test**: [FreshnessBadge.test.tsx](../ui/components/__tests__/FreshnessBadge.test.tsx)

```typescript
import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { FreshnessBadge } from "../FreshnessBadge";

describe("FreshnessBadge", () => {
  it("renders 'Frais' for fresh status", () => {
    render(<FreshnessBadge status="fresh" />);
    expect(screen.getByText("Frais")).toBeInTheDocument();
    expect(screen.getByText("Frais")).toHaveClass("bg-green-100");
  });

  it("renders 'Obsolète' for stale status", () => {
    render(<FreshnessBadge status="stale" />);
    expect(screen.getByText("Obsolète")).toBeInTheDocument();
    expect(screen.getByText("Obsolète")).toHaveClass("bg-yellow-100");
  });

  it("renders 'En panne' for broken status", () => {
    render(<FreshnessBadge status="broken" />);
    expect(screen.getByText("En panne")).toBeInTheDocument();
    expect(screen.getByText("En panne")).toHaveClass("bg-red-100");
  });
});
```

**Key Testing Patterns**:

- ✅ `render()`: Mount React component in test DOM
- ✅ `screen.getByText()`: Find element by text content
- ✅ `toBeInTheDocument()`: Assert element exists
- ✅ `toHaveClass()`: Assert CSS class presence

### Example 2: Component with Fetch + User Interaction

**Component**: [TariffList.tsx](../ui/components/TariffList.tsx)

**Test**: [TariffList.test.tsx](../ui/components/__tests__/TariffList.test.tsx)

```typescript
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { TariffList } from "../TariffList";

// Mock fetch globally
const mockFetch = vi.fn();
global.fetch = mockFetch;

const mockTariffs = [
  {
    id: 1,
    supplier: "EDF",
    option: "BASE",
    puissance_kva: 6,
    abo_month_ttc: 12.5,
    price_kwh_ttc: 0.2,
    data_status: "fresh",
  },
];

describe("TariffList", () => {
  beforeEach(() => {
    mockFetch.mockClear();
  });

  it("fetches and displays tariffs", async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ items: mockTariffs }),
    });

    render(<TariffList />);

    await waitFor(() => {
      expect(screen.getByText("EDF")).toBeInTheDocument();
    });
  });

  it("filters tariffs by option", async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ items: mockTariffs }),
    });

    const user = userEvent.setup();
    render(<TariffList />);

    await waitFor(() => {
      expect(screen.getByText("EDF")).toBeInTheDocument();
    });

    // Simulate user selecting filter
    const optionSelect = screen.getByLabelText(/option/i);
    await user.selectOptions(optionSelect, "BASE");

    await waitFor(() => {
      expect(screen.getByText("EDF")).toBeInTheDocument();
    });
  });

  it("calculates annual cost correctly", async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        items: [
          {
            id: 1,
            supplier: "EDF",
            option: "BASE",
            puissance_kva: 6,
            abo_month_ttc: 10.0,
            price_kwh_ttc: 0.2,
            data_status: "fresh",
          },
        ],
      }),
    });

    render(<TariffList />);

    await waitFor(() => {
      // Annual cost = (10 * 12) + (5000 * 0.2) = 120 + 1000 = 1120 €
      expect(screen.getByText(/1120\s*€/)).toBeInTheDocument();
    });
  });
});
```

**Key Patterns for Complex Components**:

- ✅ **Mock fetch**: Use `vi.fn()` to mock global fetch
- ✅ **beforeEach**: Clear mocks before each test
- ✅ **mockResolvedValueOnce**: Mock successful API response
- ✅ **waitFor**: Wait for async state updates
- ✅ **userEvent**: Simulate real user interactions (clicks, typing, selects)

---

## 🧪 Running Tests

### CLI Commands

```bash
# Run all tests
npm test

# Watch mode (auto re-run on file changes)
npm run test:watch

# UI mode (interactive browser UI)
npm run test:ui

# Run specific test file
npm test -- FreshnessBadge.test.tsx

# Run tests matching pattern
npm test -- --grep "filters tariffs"

# Coverage report
npm run test:coverage
```

### Watch Mode Shortcuts

When running `npm run test:watch`:

- **`a`**: Run all tests
- **`f`**: Run only failed tests
- **`t`**: Run tests by pattern (regex filter)
- **`p`**: Run tests in specific file
- **`q`**: Quit watch mode

---

## 📊 Coverage

### Generate Coverage Report

```bash
npm run test:coverage
```

**Output**:

- Terminal: Summary table with percentages
- `ui/coverage/index.html`: Interactive HTML report
- `ui/coverage/lcov.info`: LCOV format (for CI tools)

### Coverage Thresholds

Coverage MUST meet these thresholds (enforced in CI):

| Metric     | Threshold |
| ---------- | --------- |
| Lines      | 70%       |
| Functions  | 70%       |
| Branches   | 70%       |
| Statements | 70%       |

**Build fails if < 70%** (prevents code quality regression)

### View HTML Coverage Report

```bash
npm run test:coverage
cd coverage
# Open index.html in browser
```

**Coverage report shows**:

- ✅ Covered lines (green)
- ❌ Uncovered lines (red)
- ⚠️ Partially covered branches (yellow)

### Files Excluded from Coverage

```typescript
// vitest.config.ts
exclude: [
  "node_modules/",
  "vitest.setup.ts",
  "vitest.config.ts",
  "**/*.config.*",
  "**/*/types.ts",
  "**/__tests__/**",
  "**/*.test.*",
  ".next/",
];
```

---

## 🤖 CI Integration

### GitHub Actions Workflow

Tests run automatically on **every push** and **PR** to `main`/`develop`.

**CI Job**: [.github/workflows/ci.yml:134-163](../.github/workflows/ci.yml#L134-L163)

```yaml
test-frontend:
  name: Test Frontend (Vitest)
  runs-on: ubuntu-latest
  defaults:
    run:
      working-directory: ./ui
  steps:
    - uses: actions/checkout@v4

    - name: Set up Node.js
      uses: actions/setup-node@v4
      with:
        node-version: "20"
        cache: "npm"
        cache-dependency-path: ui/package-lock.json

    - name: Install dependencies
      run: npm ci

    - name: Run tests with coverage
      run: npm run test:coverage

    - name: Upload coverage to Codecov
      uses: codecov/codecov-action@v4
      with:
        file: ./ui/coverage/coverage-final.json
        flags: frontend
        name: frontend-coverage
        fail_ci_if_error: false
```

### CI Behavior

✅ **Pass**: All tests pass + coverage ≥ 70%
❌ **Fail**: Any test fails OR coverage < 70%

### Local Pre-Commit Hook (Optional)

Run tests before every commit:

```bash
# .git/hooks/pre-commit
#!/bin/sh
cd ui && npm test
```

Make executable:

```bash
chmod +x .git/hooks/pre-commit
```

---

## 🎯 Best Practices

### 1. Test Behavior, Not Implementation

❌ **Bad** (testing implementation):

```typescript
it("sets state to loading", () => {
  const { result } = renderHook(() => useState(false));
  // Don't test internal state
});
```

✅ **Good** (testing behavior):

```typescript
it("shows loading spinner while fetching", () => {
  render(<TariffList />);
  expect(screen.getByText(/chargement/i)).toBeInTheDocument();
});
```

### 2. Use Testing Library Queries

**Query Priority** (most → least preferred):

1. **getByRole**: `getByRole("button", { name: /submit/i })`
2. **getByLabelText**: `getByLabelText(/email/i)`
3. **getByText**: `getByText(/welcome/i)`
4. **getByTestId**: `getByTestId("submit-btn")` (last resort)

❌ **Avoid**: `querySelector()`, `getElementById()`

### 3. Wait for Async Updates

❌ **Bad** (race condition):

```typescript
render(<TariffList />);
expect(screen.getByText("EDF")).toBeInTheDocument(); // Fails!
```

✅ **Good**:

```typescript
render(<TariffList />);
await waitFor(() => {
  expect(screen.getByText("EDF")).toBeInTheDocument();
});
```

### 4. Clean Up Side Effects

```typescript
import { afterEach, vi } from "vitest";

afterEach(() => {
  vi.restoreAllMocks(); // Restore mocked functions
  cleanup(); // Unmount components
});
```

### 5. Use userEvent for Interactions

❌ **Bad** (fireEvent):

```typescript
fireEvent.click(button); // Too low-level
```

✅ **Good** (userEvent):

```typescript
const user = userEvent.setup();
await user.click(button); // Simulates real user behavior
```

### 6. Mock External Dependencies

```typescript
// Mock fetch
const mockFetch = vi.fn();
global.fetch = mockFetch;

// Mock router
vi.mock("next/navigation", () => ({
  useRouter: () => ({
    push: vi.fn(),
    pathname: "/",
  }),
}));
```

### 7. Descriptive Test Names

❌ **Bad**:

```typescript
it("works", () => { ... });
```

✅ **Good**:

```typescript
it("calculates annual cost correctly for BASE option", () => { ... });
```

### 8. Arrange-Act-Assert Pattern

```typescript
it("filters tariffs by puissance", async () => {
  // Arrange
  mockFetch.mockResolvedValueOnce({ ... });
  const user = userEvent.setup();
  render(<TariffList />);

  // Act
  const select = screen.getByLabelText(/puissance/i);
  await user.selectOptions(select, "6");

  // Assert
  expect(screen.getByText("EDF")).toBeInTheDocument();
});
```

---

## 📚 Resources

### Official Docs

- [Vitest](https://vitest.dev/)
- [React Testing Library](https://testing-library.com/react)
- [Testing Library Queries](https://testing-library.com/docs/queries/about)
- [User Event](https://testing-library.com/docs/user-event/intro)

### OpenWatt Tests

- [FreshnessBadge.test.tsx](../ui/components/__tests__/FreshnessBadge.test.tsx) - Simple component
- [TariffList.test.tsx](../ui/components/__tests__/TariffList.test.tsx) - Complex component with fetch + user interaction

### Cheat Sheets

- [Common Testing Library Queries](https://testing-library.com/docs/queries/about#priority)
- [User Event API](https://testing-library.com/docs/user-event/utility)
- [Vitest API](https://vitest.dev/api/)

---

## 🎓 Next Steps

### Current Coverage (2025-11-16)

**Components tested**:

- ✅ FreshnessBadge (6 test cases)
- ✅ TariffList (10 test cases)

**To test next**:

1. **AdminConsole** (high priority)
   - Supplier management
   - Manual PDF upload
   - Data status updates
2. **Layout components**
   - Navigation
   - Footer
3. **Utility hooks**
   - Custom hooks for data fetching
   - Form handling

### Adding New Tests

1. Create test file: `ui/components/__tests__/YourComponent.test.tsx`
2. Write tests using patterns from existing tests
3. Run tests: `npm test`
4. Check coverage: `npm run test:coverage`
5. Commit (CI will validate)

---

## ✅ Sprint 2 - Frontend Testing Checklist

- [x] Install Vitest + React Testing Library
- [x] Configure Vitest with 70% coverage threshold
- [x] Create FreshnessBadge tests (6 test cases)
- [x] Create TariffList tests (10 test cases)
- [x] Add test scripts to package.json
- [x] Integrate tests in CI workflow
- [x] Document frontend testing guide

**Score**: 7/7 ✅ (100%)

---

**Fin du guide de tests frontend**
