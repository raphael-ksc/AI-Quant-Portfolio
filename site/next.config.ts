import type { NextConfig } from 'next';

// GitHub Pages 專案網站的網址前綴：https://raphael-ksc.github.io/AI-Quant-Portfolio/
const basePath = '/AI-Quant-Portfolio';

const nextConfig: NextConfig = {
  output: 'export',
  basePath,
  trailingSlash: true,
  images: { unoptimized: true },
  env: { NEXT_PUBLIC_BASE_PATH: basePath },
};

export default nextConfig;
