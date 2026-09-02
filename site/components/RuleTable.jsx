import rules from '../content/_generated/rules.json'

/**
 * Renders one linter's rules from generated data.
 *
 * Nothing here restates a rule. Change a severity in the linter, re-run the
 * exporter, and this table changes with it — which is the whole point.
 */
export function RuleTable({ linter }) {
  const section = rules[linter]

  return (
    <table>
      <thead>
        <tr>
          <th>Rule</th>
          <th>Severity</th>
          <th>Applies to</th>
          <th>Fields</th>
          <th>What it catches</th>
        </tr>
      </thead>
      <tbody>
        {section.rules.map(rule => (
          <tr key={rule.id}>
            <td><code>{rule.id}</code></td>
            <td>{rule.severities.join(' / ')}</td>
            <td>{rule.applies_to}</td>
            <td><code>{rule.fields.join(' / ')}</code></td>
            <td>{rule.summary}</td>
          </tr>
        ))}
      </tbody>
    </table>
  )
}
