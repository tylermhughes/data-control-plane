// Unmount each test's screen afterwards (Testing Library only does this by itself when
// Vitest's globals are on).
import { cleanup } from "@testing-library/react";
import { afterEach } from "vitest";

afterEach(() => cleanup());
