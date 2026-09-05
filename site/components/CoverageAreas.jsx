import { Table } from 'nextra/components'
import stages from '../content/_generated/stages.json'

/**
 * Renders one interview's coverage areas from generated data.
 *
 * The names and one-line details come from the skill file that implements
 * the interview, so this list cannot show five areas when the skill asks
 * about six. The prose around it on the page is hand-written on purpose —
 * generating the explanation would turn a guide into a schema dump.
 */
export function CoverageAreas({ stage }) {
  const section = stages[stage]

  if (!section) {
    return (
      <p>
        <strong>CoverageAreas error:</strong> no data for stage{' '}
        <code>{stage}</code>. Known stages: {Object.keys(stages).join(', ')}.
      </p>
    )
  }

  return (
    <Table className="nextra-scrollbar x:not-first:mt-[1.25em] x:p-0">
      <thead>
        <Table.Tr>
          <Table.Th>Area</Table.Th>
          <Table.Th>What it covers</Table.Th>
        </Table.Tr>
      </thead>
      <tbody>
        {section.areas.map(area => (
          <Table.Tr key={area.name}>
            <Table.Td><strong>{area.name}</strong></Table.Td>
            <Table.Td>{area.detail}</Table.Td>
          </Table.Tr>
        ))}
      </tbody>
    </Table>
  )
}
