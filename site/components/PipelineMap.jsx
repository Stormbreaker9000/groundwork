import { Table } from 'nextra/components'
import pipeline from '../content/_generated/pipeline.json'

/**
 * One stage's pipeline order, from generated data.
 *
 * Nothing here restates a stage. Renumber a stage in the orchestrator,
 * re-run the exporter, and this table moves with it.
 *
 * Retired stages are rendered rather than filtered. The design orchestrator
 * stops at 12 with 11 and 12 retired, and a reader who counts to 10 and
 * finds nothing after it has to wonder whether the page is hiding something.
 * A visible gap answers the question the filtered version would raise.
 *
 * Uses nextra/components' Table for the same reason RuleTable does: MDX
 * component substitution never reaches a raw <table> inside an imported
 * .jsx component.
 */
export function PipelineMap({ stage }) {
  const section = pipeline[stage]

  if (!section) {
    return (
      <p>
        <strong>PipelineMap error:</strong> no pipeline data for stage{' '}
        <code>{stage}</code>. Known stages: {Object.keys(pipeline).join(', ')}.
      </p>
    )
  }

  return (
    <Table className="nextra-scrollbar x:not-first:mt-[1.25em] x:p-0">
      <thead>
        <Table.Tr>
          <Table.Th>Stage</Table.Th>
          <Table.Th>What happens</Table.Th>
          <Table.Th>Hand-off</Table.Th>
        </Table.Tr>
      </thead>
      <tbody>
        {section.stages.map(entry => (
          <Table.Tr key={entry.number}>
            <Table.Td>{entry.number}</Table.Td>
            <Table.Td>
              {entry.retired ? <em>retired</em> : entry.label}
            </Table.Td>
            <Table.Td>
              {entry.contracts.length === 0
                ? '—'
                : entry.contracts.map(contract => (
                    <code key={contract.name}>{contract.name}</code>
                  ))}
            </Table.Td>
          </Table.Tr>
        ))}
      </tbody>
    </Table>
  )
}
