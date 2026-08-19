/**
 * Fold the built interface into one self-contained HTML file.
 *
 * Some hosts serve a single page and nothing else: a sandboxed viewer, an
 * email attachment, a USB stick handed to a reviewer. This inlines the
 * stylesheet and the script, and replaces the self-hosted typefaces with the
 * hosted stylesheet, because the font files cannot travel inside a single
 * document at a sensible size.
 *
 * Usage:
 *   npm run build && node scripts/build-singlefile.mjs [output path]
 *
 * The multi-file build in dist/ is unchanged and remains the one to deploy
 * to a real static host, where the typefaces are served from the origin and
 * the sample files can be downloaded.
 */

import { readdirSync, readFileSync, writeFileSync, statSync } from 'node:fs'

const output = process.argv[2] ?? 'dist/mizan-single-file.html'
const assets = readdirSync('dist/assets')
const cssFile = assets.find((f) => f.endsWith('.css'))
const jsFile = assets.find((f) => f.endsWith('.js'))

if (cssFile === undefined || jsFile === undefined) {
  throw new Error('No built assets found. Run npm run build first.')
}

let css = readFileSync(`dist/assets/${cssFile}`, 'utf8')
const js = readFileSync(`dist/assets/${jsFile}`, 'utf8')

// Drop the self-hosted face declarations. Their files are not in this
// document, and leaving them in makes the browser block on a request that
// cannot succeed. The families are requested from the hosted stylesheet
// below under the same names, so the token stacks still resolve.
css = css.replace(/@font-face\s*\{[^}]*\}/g, '')

const fontLink =
  '<link rel="preconnect" href="https://fonts.googleapis.com">' +
  '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>' +
  '<link rel="stylesheet" href="https://fonts.googleapis.com/css2' +
  '?family=Amiri:wght@400;700' +
  '&family=IBM+Plex+Sans:wght@300;400;500;600' +
  '&family=IBM+Plex+Sans+Arabic:wght@300;400;500;600' +
  '&family=IBM+Plex+Mono:wght@400;500' +
  '&family=Playfair+Display:wght@400;500;600;700' +
  '&display=swap">'

const html = `<title>MIZAN</title>
${fontLink}
<style>${css}</style>
<div id="root"></div>
<script type="module">${js}</script>
`

writeFileSync(output, html)
const size = statSync(output).size / 1024
console.log(`Wrote ${output} (${size.toFixed(0)} kB).`)
