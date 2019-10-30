# ruterstop

Et program som viser sanntidsinformasjon for stoppesteder i Oslo og Akershus.

- Lister opp de neste 10 avgangene
- Starter en HTTP server i `--server` modus
- Velg fast kjøreretning med `--direction`
- *0 min* er det samme som *nå*
- Bruk `--help` for full hjelp

Innspill, tanker og feilmeldinger mottas med glede!

![Adafruit Feather HUZZAH ESP8266 med OLED FeatherWing som kjører ruterstop.py][demopic-1]

## Brukerveiledning

Trenger Python >=3.6 for å kjøre.

Last ned kildekoden og installer avhengigheter:

```
$ git clone
$ pip install -r requirements.txt
```

Installer programmet (hvis du vil):

```
# python setup.py install
```

Kjør programmet med et valgt stoppested. *6013* er Stig, på Årvoll i Oslo:

```
$ ruterstop.py --stop-id 6013
31 Grorud T     1 min
25 Majorstuen   4 min
31 Fornebu      6 min
25 Loerenskog   8 min
31 Tonsenhage  11 min
31 Snaroeya    16 min
25 Majorstuen  19 min
31 Grorud T    21 min
25 Loerenskog  23 min
31 Fornebu     26 min
```

## Eksempel

Fungerende kode for en Adafruit Feather HUZZAH ESP8266 med OLED FeatherWing finnes i
[eksempel-mappen](./examples/arduino-esp8266-feather-oled).

## Referanser og linker
- [Søk etter stoppesteder](https://stoppested.entur.org/?stopPlaceId=NSR:StopPlace:6013) (Logg inn med guest:guest)
- [EnTur JourneyPlanner docs](https://developer.entur.org/pages-journeyplanner-journeyplanner)
- [EnTur JourneyPlanner IDE](https://api.entur.io/journey-planner/v2/ide/)

[demopic-1]: ./demo-1.png
