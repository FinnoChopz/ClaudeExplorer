# ClaudeExplorer

A small, open-ended exploration of elementary cellular automata: 256 one-line
programs, each mapping a cell and its two neighbours to the cell's next state.

- `ca.py` – dependency-free library and CLI (`show`, `survey`, `equiv`)
- `test_ca.py` – `python -m unittest`
- `index.html` – open in a browser; click the eight rule bits to write your own rule

```
python ca.py show 90 -w 41 -n 12     # Sierpinski triangle
python ca.py survey                  # rank the 88 distinct rules by compressibility
python ca.py equiv 110               # -> [110, 124, 137, 193]
```

## Things I noticed

- Mirroring and 0/1-complementing fold the 256 rules into **88** behaviourally
  distinct classes (`canonical_rules()`); the tests check mirror-equivalence
  by actually evolving both rules.
- `survey` scores each rule by how well zlib compresses its space-time diagram
  from a random start. Trivial rules (0, 8, 204, …) sit at the bottom, as hoped.
  Rule 110 and rule 54 – Wolfram's "class 4", the interesting ones – land in the
  middle (ranks 15 and 9 of 88), between order and noise.
- Caveat: the linear XOR rules (60, 90, 105, 150) score as *maximally* complex.
  That is an artefact – from a random start they just copy the input's
  randomness forward. Compressibility measures apparent disorder, not
  computational richness; a better metric would look at transients or
  gliders. That's the obvious next thing to try.
