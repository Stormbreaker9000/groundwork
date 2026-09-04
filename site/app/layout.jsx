import { Footer, Layout, Navbar } from 'nextra-theme-docs'
import { Head } from 'nextra/components'
import { getPageMap } from 'nextra/page-map'
import 'nextra-theme-docs/style.css'

export const metadata = {
  title: { default: 'Groundwork', template: '%s — Groundwork' },
  description: 'SDLC discipline workflows for Claude Code'
}

export default async function RootLayout({ children }) {
  return (
    <html lang="en" dir="ltr" suppressHydrationWarning>
      <Head />
      <body>
        <Layout
          navbar={<Navbar logo={<b>Groundwork</b>} />}
          pageMap={await getPageMap()}
          docsRepositoryBase="https://github.com/Stormbreaker9000/groundwork/tree/main/site"
          footer={<Footer>MIT © Mark D&apos;Adamo</Footer>}
        >
          {children}
        </Layout>
      </body>
    </html>
  )
}
