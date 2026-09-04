import { Table } from 'nextra/components'
import fields from '../content/_generated/fields.json'

/**
 * Renders one stage's frontmatter fields from the artifact JSON Schema.
 *
 * The schema is the binding contract a validator enforces; this table is a
 * projection of it, never a restatement. Adding a field to the schema and
 * re-running the exporter adds a row here.
 */
export function FieldTable({ stage }) {
  const rows = fields[stage]

  if (!rows) {
    return (
      <p>
        <strong>FieldTable error:</strong> no field data for stage{' '}
        <code>{stage}</code>. Known stages: {Object.keys(fields).join(', ')}.
      </p>
    )
  }

  const required = entry => {
    if (entry.required_for.length === 0) return 'optional'
    if (entry.required_for.includes('*')) return 'always'
    return entry.required_for.join(', ')
  }

  const type = entry =>
    Array.isArray(entry.type) ? entry.type.join(' | ') : entry.type

  return (
    <Table className="nextra-scrollbar x:not-first:mt-[1.25em] x:p-0">
      <thead>
        <Table.Tr>
          <Table.Th>Field</Table.Th>
          <Table.Th>Type</Table.Th>
          <Table.Th>Required</Table.Th>
          <Table.Th>Values</Table.Th>
          <Table.Th>Meaning</Table.Th>
        </Table.Tr>
      </thead>
      <tbody>
        {rows.map(entry => (
          <Table.Tr key={entry.name}>
            <Table.Td><code>{entry.name}</code></Table.Td>
            <Table.Td>{type(entry)}</Table.Td>
            <Table.Td>{required(entry)}</Table.Td>
            <Table.Td>
              {entry.enum.length > 0
                ? entry.enum.map(v => <code key={v}>{v} </code>)
                : '—'}
            </Table.Td>
            <Table.Td>{entry.description}</Table.Td>
          </Table.Tr>
        ))}
      </tbody>
    </Table>
  )
}
