import NextAuth, { type User } from "next-auth";
import Google from "next-auth/providers/google";

interface DjangoUser extends User {
  djangoAccessToken?: string;
  djangoRefreshToken?: string;
  djangoUserId?: string;
}

const BACKEND_URL = process.env.BACKEND_URL || "http://localhost:8000";

export const { handlers, signIn, signOut, auth } = NextAuth({
  providers: [
    Google({
      clientId: process.env.GOOGLE_CLIENT_ID!,
      clientSecret: process.env.GOOGLE_CLIENT_SECRET!,
    }),
  ],

  session: { strategy: "jwt" },

  pages: {
    signIn: "/login",
  },

  callbacks: {
    async signIn({ user, account }) {
      if (account?.provider === "google") {
        try {
          const res = await fetch(`${BACKEND_URL}/api/v1/auth/social-sync/`, {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
              "X-Auth-Sync-Secret": process.env.AUTH_SYNC_SECRET!,
            },
            body: JSON.stringify({
              provider: "google",
              provider_account_id: account.providerAccountId,
              email: user.email,
              name: user.name,
              image: user.image,
            }),
          });

          if (!res.ok) return false;

          const data = await res.json();
          (user as DjangoUser).djangoAccessToken = data.access;
          (user as DjangoUser).djangoRefreshToken = data.refresh;
          (user as DjangoUser).djangoUserId = String(data.user.id);
        } catch {
          return false;
        }
      }
      return true;
    },

    async jwt({ token, user }) {
      // Initial sign-in: persist Django tokens
      if (user) {
        token.djangoAccessToken = (user as DjangoUser).djangoAccessToken;
        token.djangoRefreshToken = (user as DjangoUser).djangoRefreshToken;
        token.djangoUserId = (user as DjangoUser).djangoUserId;
        // Access token expires in ~55 minutes (buffer before 60min lifetime)
        token.accessTokenExpires = Date.now() + 55 * 60 * 1000;
        token.error = undefined;
      }

      // Return early if access token is still valid
      if (Date.now() < (token.accessTokenExpires as number)) {
        return token;
      }

      // Access token expired — try to refresh
      try {
        const res = await fetch(`${BACKEND_URL}/api/v1/auth/token/refresh/`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ refresh: token.djangoRefreshToken }),
        });

        if (!res.ok) throw new Error("Refresh failed");

        const data = await res.json();
        token.djangoAccessToken = data.access;
        // simplejwt rotates refresh tokens
        if (data.refresh) {
          token.djangoRefreshToken = data.refresh;
        }
        token.accessTokenExpires = Date.now() + 55 * 60 * 1000;
        token.error = undefined;
      } catch {
        token.error = "RefreshTokenError";
      }

      return token;
    },

    async session({ session, token }) {
      session.user.id = token.djangoUserId as string;
      session.djangoAccessToken = token.djangoAccessToken as string;
      if (token.error) {
        session.error = token.error as string;
      }
      return session;
    },
  },
});
