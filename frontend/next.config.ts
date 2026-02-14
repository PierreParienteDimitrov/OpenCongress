import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  images: {
    remotePatterns: [
      {
        protocol: "https",
        hostname: "lh3.googleusercontent.com",
      },
      {
        protocol: "https",
        hostname: "www.congress.gov",
        pathname: "/img/member/**",
      },
      {
        protocol: "https",
        hostname: "bioguide.congress.gov",
        pathname: "/bioguide/photo/**",
      },
    ],
  },

  async redirects() {
    return [
      // Old member list pages → new chamber pages (list tab)
      {
        source: "/senator",
        destination: "/senate?view=list",
        permanent: true,
      },
      {
        source: "/representative",
        destination: "/house?view=list",
        permanent: true,
      },
      // Old member detail pages → new detail routes
      {
        source: "/senator/:id",
        destination: "/senate/:id",
        permanent: true,
      },
      {
        source: "/representative/:id",
        destination: "/house/:id",
        permanent: true,
      },
      // Old seat map pages → new chamber pages (seats tab, default)
      {
        source: "/senate-seats",
        destination: "/senate",
        permanent: true,
      },
      {
        source: "/house-seats",
        destination: "/house",
        permanent: true,
      },
    ];
  },
};

export default nextConfig;
