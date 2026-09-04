import { Table } from 'nextra/components'
import rules from '../content/_generated/rules.json'

/**
 * Renders one linter's rules from generated data.
 *
 * Nothing here restates a rule. Change a severity in the linter, re-run the
 * exporter, and this table changes with it — which is the whole point.
 *
 * Uses nextra/components' Table (not raw <table>/<th>/<td>) so this table
 * gets the same styling, overflow containment, and markup as every
 * Markdown-authored table on the site. Nextra's MDX component substitution
 * only rewrites tags compiled from .mdx source — a raw <table> written
 * inside an imported .jsx component never receives it.
 */
export function RuleTable({ linter }) {
  const section = rules[linter]

  if (!section) {
    return (
      <p>
        <strong>RuleTable error:</strong> no rule data for linter{' '}
        <code>{linter}</code>. Known linters: {Object.keys(rules).join(', ')}.
      </p>
    )
  }

  // Traceability findings name an artifact and a path, never a frontmatter
  // field, so their registry declares fields: []. Render the column only
  // where it carries something, rather than a column of em dashes.
  const hasFields = section.rules.some(rule => rule.fields.length > 0)

  return (
    <Table className="nextra-scrollbar x:not-first:mt-[1.25em] x:p-0">
      <thead>
        <Table.Tr>
          <Table.Th>Rule</Table.Th>
          <Table.Th>Severity</Table.Th>
          <Table.Th>Applies to</Table.Th>
          {hasFields && <Table.Th>Fields</Table.Th>}
          <Table.Th>What it catches</Table.Th>
        </Table.Tr>
      </thead>
      <tbody>
        {section.rules.map(rule => (
          <Table.Tr key={rule.id}>
            <Table.Td><code>{rule.id}</code></Table.Td>
            <Table.Td>{rule.severities.join(' / ')}</Table.Td>
            <Table.Td>{rule.applies_to}</Table.Td>
            {hasFields && (
              <Table.Td><code>{rule.fields.join(' / ')}</code></Table.Td>
            )}
            <Table.Td>{rule.summary}</Table.Td>
          </Table.Tr>
        ))}
      </tbody>
    </Table>
  )
}
