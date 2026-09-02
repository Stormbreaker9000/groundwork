import nextra from 'nextra'

const withNextra = nextra({})

/**
 * @type {import('next').NextConfig}
 */
const nextConfig = {
  output: 'export',
  basePath: '/groundwork',
  trailingSlash: true,
  images: { unoptimized: true }
}

export default withNextra(nextConfig)
