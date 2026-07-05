import NextAuth from "next-auth";
import type { Provider } from "next-auth/providers";
import Google from "next-auth/providers/google";
import Credentials from "next-auth/providers/credentials";
import { PrismaAdapter } from "@auth/prisma-adapter";
import bcrypt from "bcryptjs";
import { z } from "zod";

import prisma from "@/lib/prisma";
import type { QuantRole } from "@/types/quant-role";

const credentialSchema = z.object({
  email: z.string().email(),
  password: z.string().min(8),
});

const providers: Provider[] = [
  Credentials({
    name: "credentials",
    credentials: {
      email: { label: "Email", type: "email" },
      password: { label: "Password", type: "password" },
    },
    authorize: async (credentials) => {
      const parsed = credentialSchema.safeParse(credentials);
      if (!parsed.success) {
        return null;
      }
      const { email, password } = parsed.data;
      const normalizedEmail = email.trim().toLowerCase();
      const user = await prisma.user.findUnique({ where: { email: normalizedEmail } });
      if (!user?.passwordHash) return null;
      const valid = await bcrypt.compare(password, user.passwordHash);
      if (!valid) return null;

      return {
        id: user.id,
        email: user.email,
        name: user.name,
        image: user.image,
        role: coerceRole(user.role),
        libraryUnlocked: user.libraryUnlocked,
      };
    },
  }),
];

if (process.env.AUTH_GOOGLE_ID && process.env.AUTH_GOOGLE_SECRET) {
  providers.unshift(
    Google({
      clientId: process.env.AUTH_GOOGLE_ID,
      clientSecret: process.env.AUTH_GOOGLE_SECRET,
    }),
  );
}

export const { handlers, auth, signIn, signOut } = NextAuth({
  trustHost: true,
  secret: process.env.AUTH_SECRET,
  adapter: PrismaAdapter(prisma),
  session: { strategy: "jwt" },
  providers,
  callbacks: {
    async jwt({ token, user }) {
      if (user) {
        token.id = user.id;
        token.role = coerceRole(`${user.role ?? "USER"}`);
        token.libraryUnlocked = user.libraryUnlocked;
      }

      const userId =
        typeof token.id === "string"
          ? token.id
          : typeof token.sub === "string"
            ? token.sub
            : null;

      if (userId) {
        const dbUser = await prisma.user.findUnique({
          where: { id: userId },
          select: { role: true, libraryUnlocked: true },
        });
        if (dbUser) {
          token.role = coerceRole(dbUser.role);
          token.libraryUnlocked = dbUser.libraryUnlocked;
        }
      }

      return token;
    },
    async session({ session, token }) {
      if (!session.user) return session;

      session.user.id =
        typeof token.id === "string"
          ? token.id
          : typeof token.sub === "string"
            ? token.sub
            : "";
      session.user.role = coerceRole(
        typeof token.role === "string" ? token.role : `${token.role ?? "USER"}`,
      );
      session.user.libraryUnlocked =
        typeof token.libraryUnlocked === "boolean" ? token.libraryUnlocked : false;

      return session;
    },
  },
});

function coerceRole(value: string): QuantRole {
  return value === "ADMIN" ? "ADMIN" : "USER";
}

