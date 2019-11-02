# ruterstop

Et program som viser sanntidsinformasjon for stoppesteder i Oslo og Akershus.

- Lister opp de neste 10 avgangene
- Starter en HTTP server med `--server`
- Velg en bestemt kjøreretning med `--direction`
- Bruk `--help` for full hjelp

Innspill, tanker og feilmeldinger mottas med glede!

![Adafruit Feather HUZZAH ESP8266 med OLED FeatherWing som kjører ruterstop.py][demopic-1]

## Brukerveiledning

Trenger Python >=3.5 for å kjøre.

Last ned kildekoden og installer avhengigheter:

```
$ git clone
$ pip install -r requirements.txt
```

Installer programmet (hvis du vil):

```
# python setup.py install
```

Kjør programmet med et valgt stoppested. *6013* er Stig, på Årvoll i Oslo.
Søk opp flere stopp fra [EnTur sine sider for stoppesteder][stoppesteder].

```
$ python ruterstop.py --stop-id 6013 --direction outbound
31 Snaroeya       naa
31 Fornebu      5 min
25 Majorstuen   6 min
33 Filipstad    6 min
25 Majorstuen   8 min
```

## Motivasjon

Jeg fikk et ønske om å kunne se avganger fra mitt nærmeste stoppested mens
jeg sitter ved kjøkkenbordet, uten å måtte bruke mobilen.
Jeg skrev dette programmet som en backend til en ESP8266-variant med en
OLED skjerm.

Fungerende kode for en Adafruit Feather HUZZAH ESP8266 med en OLED FeatherWing
finnes i [eksempel-mappen](./examples/arduino-esp8266-feather-oled).

## Referanser og linker
- [Søk etter stoppesteder][stoppesteder] (Logg inn med guest:guest)
- [EnTur JourneyPlanner docs](https://developer.entur.org/pages-journeyplanner-journeyplanner)
- [EnTur JourneyPlanner IDE](https://api.entur.io/journey-planner/v2/ide/)

[demopic-1]: ./demo-1.png
[stoppesteder]: https://stoppested.entur.org/?stopPlaceId=NSR:StopPlace:6013
