import "next-auth";
import "next-auth/jwt";

declare module "next-auth" {
  interface Session {
    djangoAccessToken?: string;
    error?: string;
    user: {
      id: string;
      name?: string | null;
      email?: string | null;
      image?: string | null;
    };
  }
}

declare module "next-auth/jwt" {
  interface JWT {
    djangoAccessToken?: string;
    djangoRefreshToken?: string;
    djangoUserId?: string;
    accessTokenExpires?: number;
    error?: string;
  }
}
