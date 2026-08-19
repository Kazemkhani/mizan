/**
 * A mark for a publishing entity.
 *
 * These are typographic marks drawn by MIZAN, not official emblems: the
 * initials of the entity inside a bordered field, in the product's own
 * type. Reproducing a government emblem would misrepresent endorsement,
 * and the offline design rule forbids fetching one at run time.
 *
 * An entity's real emblem can be dropped into web/public/entity-logos/ as
 * <dataset_id>.svg or .png and it is used in place of the mark, with no
 * code change.
 */

import React from 'react'

interface EntityMarkProps {
  datasetId: string
  publisher: string
}

/** Initials of an entity name, at most three letters. */
function initials(name: string): string {
  const skip = new Set(['of', 'and', 'the', 'for', 'department', '&'])
  const words = name
    .replace(/[(),]/g, ' ')
    .split(/\s+/)
    .filter((w) => w.length > 0 && !skip.has(w.toLowerCase()))
  const letters = words.map((w) => w[0].toUpperCase()).join('')
  return letters.slice(0, 3)
}

/** File names of any emblems present, read once from the folder manifest. */
let logoManifest: Record<string, string> | null = null

function useLogo(datasetId: string): string | null {
  const [file, setFile] = React.useState<string | null>(
    logoManifest === null ? null : (logoManifest[datasetId] ?? null),
  )

  React.useEffect(() => {
    if (logoManifest !== null) return
    let active = true
    void fetch(`${import.meta.env.BASE_URL}entity-logos/manifest.json`)
      .then((response) => (response.ok ? response.json() : { logos: {} }))
      .then((body: { logos?: Record<string, string> }) => {
        logoManifest = body.logos ?? {}
        if (active) setFile(logoManifest[datasetId] ?? null)
      })
      .catch(() => {
        logoManifest = {}
      })
    return () => {
      active = false
    }
  }, [datasetId])

  return file
}

export function EntityMark({ datasetId, publisher }: EntityMarkProps): React.ReactElement {
  const file = useLogo(datasetId)

  if (file !== null) {
    return (
      <img
        className="entity-mark entity-mark--image"
        src={`${import.meta.env.BASE_URL}entity-logos/${file}`}
        alt=""
        aria-hidden="true"
      />
    )
  }

  return (
    <span className="entity-mark" aria-hidden="true">
      <span className="entity-mark__letters">{initials(publisher)}</span>
    </span>
  )
}
