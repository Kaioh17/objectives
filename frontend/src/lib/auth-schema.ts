import { z } from "zod";

export const userSchema = z.object({
  id: z.number(),
  email: z.string(),
  full_name: z.string().nullable(),
  timezone: z.string(),
});
export type User = z.infer<typeof userSchema>;

// What /auth/login, /auth/register and /auth/refresh return
export const authResultSchema = z.object({ access_token: z.string(), user: userSchema });
export type AuthResult = z.infer<typeof authResultSchema>;
