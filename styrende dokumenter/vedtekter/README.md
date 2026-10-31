# Vedtekter

Nåværende vedtekter skal alltid være tilgjengelig i PDF-format gjennom [https://vedtekter.uiogaming.no](https://vedtekter.uiogaming.no)

## Struktur

- `gjeldende/` – gjeldende vedtekter som PDF, på norsk og engelsk
- `kilde/` – LaTeX-kilde for gjeldende vedtekter (`no/` og `en/`)
- `utgåtte/` – tidligere vedtekter som PDF (`no/` og `en/`)

Filnavn følger formatet `Vedtekter UiO Gaming (<fra> - <til>).pdf`. Norske filer bruker datoformatet `DD.MM.ÅÅÅÅ`, og engelske filer bruker `ÅÅÅÅ-MM-DD`. Utgåtte vedtekter er nummerert, og engelske oversettelser har samme nummer som den norske versjonen de oversetter.

Når vedtektene skal endres:

1. Oppdater LaTeX-kilden i `kilde/`, og sett datoen på forsiden til datoen endringen ble vedtatt
2. Push til `main`. En GitHub Action flytter den gjeldende PDF-en til `utgåtte/`, bygger en ny PDF til `gjeldende/` og åpner en pull request
3. Sjekk PDF-ene i pull requesten og merge den

Endres kilden uten at datoen endres, bygges den gjeldende PDF-en på nytt uten å arkiveres. Den engelske oversettelsen kan oppdateres senere enn den norske, men datoen må tilsvare en norsk versjon.

PDF-ene får metadata etter samme mønster: tittel lik filnavnet (uten nummer), forfatter `UiO Gaming`, og opprettelses- og endringsdato satt til midnatt norsk tid på startdatoen. Skriptet kan også kjøres lokalt med `python .github/scripts/vedtekter.py build --dry-run`.

Den engelske oversettelsen er ikke juridisk bindende da den ikke er godkjent av generalforsmalingen. Det fungerer bare som hjelp for våre engelsktalende medlemmer.
