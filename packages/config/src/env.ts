import { type ZodObject, type ZodRawShape, z } from "zod";

export const baseEnvSchema = z.object({
  NODE_ENV: z.enum(["development", "test", "production"]).default("development"),
});

export type BaseEnv = z.infer<typeof baseEnvSchema>;

/**
 * Parse and validate environment variables against a zod shape merged with the base schema.
 *
 * Security note: the thrown error stringifies only Zod's `fieldErrors` (field name + default
 * message). Zod's default messages for `.min`, `.max`, `.email`, `.enum`, etc. do NOT echo the
 * offending value. However, `z.literal(...)` and some `z.union(...)` cases include the received
 * value in their default message. If a consumer uses those for a secret-bearing field, override
 * the message with `.refine(..., { message: "<safe message>" })` to prevent leaks into logs.
 */
export function createEnv<T extends ZodRawShape>(
  shape: T,
  source: NodeJS.ProcessEnv = process.env,
): z.infer<ZodObject<T & typeof baseEnvSchema.shape>> {
  const schema = baseEnvSchema.extend(shape);
  const parsed = schema.safeParse(source);
  if (!parsed.success) {
    const fieldErrors = parsed.error.flatten().fieldErrors;
    throw new Error(`Invalid environment variables:\n${JSON.stringify(fieldErrors, null, 2)}`);
  }
  return parsed.data as z.infer<ZodObject<T & typeof baseEnvSchema.shape>>;
}
