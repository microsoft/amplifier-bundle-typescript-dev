// Sample file for stub detection testing.

import { Request, Response } from "express";

// TODO: Implement proper error handling
export function processData(input: string): string {
  return input;
}

// FIXME: This is a workaround
export function workaround(): number {
  return 42;
}

// HACK: Temporary solution until upstream fix
export function tempSolution(): void {
  throw new Error("not implemented");
}

// This @ts-ignore has no explanation — should be flagged
// @ts-ignore
const x: number = "hello" as any;

// This @ts-expect-error has no explanation — should be flagged
// @ts-expect-error
const y: number = "world" as any;

// This @ts-expect-error HAS an explanation — should NOT be flagged
// @ts-expect-error — testing legacy API compatibility
const z: number = "test" as any;

// Abstract class with not-implemented stub (legitimate)
abstract class BaseProcessor {
  abstract process(item: string): string;
}
