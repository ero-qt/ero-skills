---
type: regex
pattern: '## \[Unreleased\][\s\S]*punctuation[\s\S]*## \[0\.1\.0\]'
target: { source: file, path: CHANGELOG.md }
---
