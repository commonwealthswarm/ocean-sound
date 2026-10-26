# Sources

Every real source this project uses or plans to use is listed here with its terms. A source is only used for research
work after the Night Shift operator registers a curated source entry for it. Nothing listed below has been analysed.

## Inventory and blockers

Real-data state: **pending_source_entry** (gate: curated source entry).

One public MBARI CC-BY 4.0 excerpt (55 s, selected by MBARI's official notebook as a humpback example; 16 kHz mono 24-bit; source PCM unchanged; NOT the original 256 kHz source) is imported for Night Shift. It is a sample, not a Night Shift discovery. Real measurement work is generated as bounded 5-second window tasks from that exact registered file, only while it is registered. The server measures it; a model cannot hear it.

Inventory:
- mbari-20151207-065815-55s.wav (55 s excerpt, served by Night Shift from its hash-checked public path, not in this repository)

Blockers:
- Real-data tasks exist only while the reviewed excerpt is registered as a curated source with its exact hash.

## Rules

- Do not commit source data files. Records point to sources; they do not copy them (a test enforces this).
- Records built from a description alone are `unverified` and carry no hash.
- A source whose redistribution terms are restricted or unresolved is never marked publishable.
