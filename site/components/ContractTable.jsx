import pipeline from '../content/_generated/pipeline.json'

/**
 * One stage's hand-off contracts, verbatim from the orchestrator that owns
 * them.
 *
 * The YAML is rendered as text, not re-serialized from a parsed object. The
 * blocks carry inline comments — the `# ← TRANSIENT` markers among them —
 * and a round-trip through any parser would drop exactly the annotations a
 * contributor most needs to see.
 *
 * Transients get their own line rather than a column: which fields die at
 * the formatter is the single fact about these shapes that a reader cannot
 * recover by looking at an emitted artifact, because by then they are gone.
 *
 * Heading ids are scoped by stage. Both orchestrators own a `generation_brief`
 * and a `critique_report`, and both tables render on one page, so an id keyed
 * on the contract name alone would emit the same id twice and send every
 * link to the requirements copy.
 */
export function ContractTable({ stage }) {
  const section = pipeline[stage]

  if (!section) {
    return (
      <p>
        <strong>ContractTable error:</strong> no pipeline data for stage{' '}
        <code>{stage}</code>. Known stages: {Object.keys(pipeline).join(', ')}.
      </p>
    )
  }

  const contracts = section.stages.flatMap(entry =>
    entry.contracts.map(contract => ({ ...contract, stage: entry.number }))
  )

  if (contracts.length === 0) {
    return (
      <p>
        <strong>ContractTable error:</strong> no contracts found for{' '}
        <code>{stage}</code> in <code>{section.source}</code>.
      </p>
    )
  }

  return (
    <>
      {contracts.map(contract => (
        <section key={contract.name}>
          <h3 id={`${stage}-${contract.name.replace(/_/g, '-')}`}>
            <code>{contract.name}</code>
          </h3>
          <p>
            Stage {contract.stage} of <code>{section.agent}</code>.
            {contract.transients.length > 0 && (
              <>
                {' '}Transient:{' '}
                {contract.transients.map((field, index) => (
                  <span key={field}>
                    {index > 0 && ', '}
                    <code>{field}</code>
                  </span>
                ))}
                {' '}— carried between agents, never written to disk.
              </>
            )}
          </p>
          <pre>
            <code>{contract.yaml}</code>
          </pre>
        </section>
      ))}
    </>
  )
}
