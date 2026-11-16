import "@testing-library/jest-dom/vitest";

Object.defineProperty(window.URL, "createObjectURL", { value: () => "blob:test" });
Object.defineProperty(window.URL, "revokeObjectURL", { value: () => undefined });

