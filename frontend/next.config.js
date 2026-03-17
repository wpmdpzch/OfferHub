/** @type {import('next').NextConfig} */
const nextConfig = {
  output: "standalone",
  images: {
    // SSRF 防护：收窄图片域名白名单，禁止通配符 hostname
    remotePatterns: [
      { protocol: "https", hostname: "avatars.githubusercontent.com" },
      { protocol: "https", hostname: "github.com" },
    ],
  },
};

module.exports = nextConfig;
