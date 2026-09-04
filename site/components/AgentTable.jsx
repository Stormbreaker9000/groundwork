import { Table } from 'nextra/components'
import agents from '../content/_generated/agents.json'

/**
 * The agent roster, from each agent file's frontmatter and H1.
 *
 * A roster, not an explanation: stage order, hand-off contracts and the
 * reasoning behind the pipeline's shape belong to the architecture guide,
 * and this page links there rather than reproducing any of it.
 */
export function AgentTable() {
  return (
    <Table className="nextra-scrollbar x:not-first:mt-[1.25em] x:p-0">
      <thead>
        <Table.Tr>
          <Table.Th>Agent</Table.Th>
          <Table.Th>Role</Table.Th>
          <Table.Th>What it does</Table.Th>
        </Table.Tr>
      </thead>
      <tbody>
        {agents.map(agent => (
          <Table.Tr key={agent.name}>
            <Table.Td><code>{agent.name}</code></Table.Td>
            <Table.Td>{agent.title}</Table.Td>
            <Table.Td>{agent.description}</Table.Td>
          </Table.Tr>
        ))}
      </tbody>
    </Table>
  )
}
