# ruterstop

Et program som viser sanntidsinformasjon for stoppesteder i Oslo og deler av Viken.

- Lister 20 av de neste avgangene
- Bruk filtre som `--direction`, `--grouped` og `--min-eta`
- Start en HTTP server med `--server`
- Søk etter stoppesteder med `--search-stop`
- Sett når du ønsker å se klokkeslett med `--long-eta`
- Bruk `--help` for full hjelp

Innspill, tanker og feilmeldinger mottas med glede!

![Adafruit Feather HUZZAH ESP8266 med OLED FeatherWing som kjører ruterstop.py][demopic-1]

## Installasjon

Trenger Python >=3.6 for å kjøre.

### Installer fra PyPi

```
$ pip install ruterstop
```

### Bygg fra kildekode

Last ned kildekoden og installer programmet med avhengigheter fra kildekodemappen

```
$ pip install poetry
$ poetry build
```

## Brukerveiledning

Søk etter stoppested

```
$ ruterstop --search-stop stig
6013    Stig (Oslo, Oslo)
59445   Stige (Ålesund, Møre og Romsdal)
13479   Stigen (Ringebu, Innlandet)
18602   Stigen (Sandefjord, Vestfold og Telemark)
18605   Stiger (Sandefjord, Vestfold og Telemark)
21507   Stigen (Porsgrunn, Vestfold og Telemark)
3857    Stigen (Aurskog-Høland, Viken)
45978   Stigen (Nærøysund, Trøndelag)
54253   Stigen (Lyngen, Troms og Finnmark)
7844    Stigen (Trysil, Innlandet)
```

Kjør programmet med et valgt stoppested

```
$ ruterstop --stop-id 6013 --direction outbound
31 Snaroeya       naa
31 Fornebu     10 min
31 Snaroeya    20 min
25 Majorstuen  28 min
31 Fornebu     30 min
```

Eller start som en HTTP server

```
$ ruterstop --server
```

Stoppested og filtre velges i adressen til spørringen

```
$ curl localhost:4000/6013?direction=outbound&long_eta=10
31 Fornebu        naa
31 Snaroeya     5 min
31 Fornebu      8 min
31 Fornebu     10 min
25 Majorstuen   20:21
31 Snaroeya     20:24
31 Snaroeya     20:36
25 Majorstuen   20:36
31 Fornebu      20:42
```

## Utvikling

### Kjør tester

```
$ poetry install
$ poetry run python -m unittest
```

### Kjør multi-versjon tester i Docker

```
$ make matrix
```

Se Makefile for detaljer

### Tag ny versjon

```
$ ./.deploy/bump_version.py
```

Verktøyet hjelper til å huske å bytte versjonsnummer før tagging og sjekke
at man er på riktig branch.

## Motivasjon

Jeg vil se avganger fra mitt nærmeste stoppested mens jeg sitter ved
kjøkkenbordet, uten å måtte bruke mobilen.

Dette prosjektet blir også utnyttet til å prøve ut alle ting om Python jeg
både kan og ikke kan.

Jeg skrev dette programmet som en backend til en ESP8266-variant med en
OLED skjerm.
Fungerende klient-kode for en Adafruit Feather HUZZAH ESP8266 med en OLED
FeatherWing finnes i [eksempel-mappen](./examples/arduino-esp8266-feather-oled).

## Referanser og linker
- [Søk etter stoppesteder][stoppesteder] (Logg inn med guest:guest)
- [EnTur JourneyPlanner docs](https://developer.entur.org/pages-journeyplanner-journeyplanner)
- [EnTur JourneyPlanner IDE](https://api.entur.io/journey-planner/v2/ide/)

[demopic-1]: ./demo-1.png
[stoppesteder]: https://stoppested.entur.org/?stopPlaceId=NSR:StopPlace:6013
