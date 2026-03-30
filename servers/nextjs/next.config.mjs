
const nextConfig = {
  reactStrictMode: false,
  distDir: ".next-build",
  experimental: {
      proxyTimeout: 120000,
  },

  // Rewrites for development - proxy font requests to FastAPI backend
  async rewrites() {
    return [
      {
        source: '/ppt/:path*',
        destination: '/:path*',
      },
      {
        source: '/app_data/fonts/:path*',
        destination: 'http://localhost:8000/app_data/fonts/:path*',
      },
      {
        source: '/static/:path*',
        destination: 'http://localhost:8000/static/:path*',
      },
      {
        source: '/api/v1/ppt/:path*',
        destination: 'http://localhost:8000/api/v1/ppt/:path*',
      },
    ];
  },
  async redirects() {
    return [
      {
        source: "/upload",
        destination: "/ppt/deck-studio",
        permanent: false,
      },
      {
        source: "/dashboard",
        destination: "/ppt/deck-dashboard",
        permanent: false,
      },
      {
        source: "/ppt/upload",
        destination: "/ppt/deck-studio",
        permanent: false,
      },
      {
        source: "/ppt/dashboard",
        destination: "/ppt/deck-dashboard",
        permanent: false,
      },
      {
        source: "/templates",
        destination: "/ppt/templates",
        permanent: false,
      },
      {
        source: "/theme",
        destination: "/ppt/theme",
        permanent: false,
      },
      {
        source: "/template-preview/:path*",
        destination: "/ppt/template-preview/:path*",
        permanent: false,
      },
      {
        source: "/custom-template",
        destination: "/ppt/custom-template",
        permanent: false,
      },
      {
        source: "/settings",
        destination: "/ppt/settings",
        permanent: false,
      },
      {
        source: "/generate",
        destination: "/ppt/deck-studio",
        permanent: false,
      },
      {
        source: "/ppt/generate",
        destination: "/ppt/deck-studio",
        permanent: false,
      },
    ];
  },

  images: {
    remotePatterns: [
      {
        protocol: "https",
        hostname: "pub-7c765f3726084c52bcd5d180d51f1255.r2.dev",
      },
      {
        protocol: "https",
        hostname: "pptgen-public.ap-south-1.amazonaws.com",
      },
      {
        protocol: "https",
        hostname: "pptgen-public.s3.ap-south-1.amazonaws.com",
      },
      {
        protocol: "https",
        hostname: "img.icons8.com",
      },
      {
        protocol: "https",
        hostname: "present-for-me.s3.amazonaws.com",
      },
      {
        protocol: "https",
        hostname: "yefhrkuqbjcblofdcpnr.supabase.co",
      },
      {
        protocol: "https",
        hostname: "images.unsplash.com",
      },
      {
        protocol: "https",
        hostname: "picsum.photos",
      },
      {
        protocol: "https",
        hostname: "unsplash.com",
      },
    ],
  },
  
};

export default nextConfig;
