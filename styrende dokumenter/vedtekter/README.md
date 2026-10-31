# Vedtekter

Nåværende vedtekter skal alltid være tilgjengelig i PDF-format gjennom [https://vedtekter.uiogaming.no](https://vedtekter.uiogaming.no)

## Struktur

- `gjeldende/` – gjeldende vedtekter som PDF, på norsk og engelsk
- `kilde/` – LaTeX-kilde for gjeldende vedtekter (`no/` og `en/`)
- `utgåtte/` – tidligere vedtekter som PDF (`no/` og `en/`)

Filnavn følger formatet `Vedtekter UiO Gaming (<fra> - <til>).pdf`. Norske filer bruker datoformatet `DD.MM.ÅÅÅÅ`, og engelske filer bruker `ÅÅÅÅ-MM-DD`. Utgåtte vedtekter er nummerert, og engelske oversettelser har samme nummer som den norske versjonen de oversetter.

Når vedtektene endres:

1. Flytt PDF-ene i `gjeldende/` til `utgåtte/no/` og `utgåtte/en/`, med neste nummer og sluttdato i filnavnet
2. Oppdater LaTeX-kilden i `kilde/` og bygg nye PDF-er til `gjeldende/`

Den engelske oversettelsen er ikke juridisk bindende da den ikke er godkjent av generalforsmalingen. Det fungerer bare som hjelp for våre engelsktalende medlemmer.
