import type { DefaultSession } from "next-auth";
import type { QuantRole } from "./quant-role";

declare module "next-auth" {
  interface Session {
    user?: DefaultSession["user"] & {
      id: string;
      role: QuantRole;
      libraryUnlocked: boolean;
    };
  }

  interface User {
    role: QuantRole;
    libraryUnlocked: boolean;
  }
}

declare module "next-auth/jwt" {
  interface JWT {
    id?: string;
    role?: QuantRole;
    libraryUnlocked?: boolean;
  }
}
