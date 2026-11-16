mkdir -p notes
for i in $(seq 1 20); do
  printf 'Meeting notes %s\n\nDecided to keep the current schema.\n' "$i" > "notes/note-$i.md"
done
for i in 3 8 15; do
  printf 'TODO: send the summary to the team\n' >> "notes/note-$i.md"
done
