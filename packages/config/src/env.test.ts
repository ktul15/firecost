import { describe, expect, it } from "vitest";
import { z } from "zod";
import { baseEnvSchema, createEnv } from "./env.js";

describe("baseEnvSchema", () => {
  it("defaults NODE_ENV to 'development' when absent", () => {
    const parsed = baseEnvSchema.parse({});
    expect(parsed.NODE_ENV).toBe("development");
  });

  it("rejects NODE_ENV values outside the enum", () => {
    const result = baseEnvSchema.safeParse({ NODE_ENV: "staging" });
    expect(result.success).toBe(false);
  });
});

describe("createEnv", () => {
  it("merges custom shape with base schema and returns typed result", () => {
    const env = createEnv({ API_KEY: z.string() }, { API_KEY: "abc" });
    expect(env.NODE_ENV).toBe("development");
    expect(env.API_KEY).toBe("abc");
  });

  it("throws with field name but does NOT leak the offending value when validation fails", () => {
    const secret = "super-secret-leaked-value-xyz";
    let caught: Error | undefined;
    try {
      createEnv({ API_KEY: z.string().min(64) }, { API_KEY: secret });
    } catch (error) {
      caught = error as Error;
    }
    expect(caught).toBeDefined();
    expect(caught?.message).toContain("API_KEY");
    expect(caught?.message).not.toContain(secret);
  });
});
