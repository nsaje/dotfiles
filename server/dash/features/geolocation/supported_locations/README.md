# Zemanta One Geolocations

The Geolocations table is based on Maxmind's supported locations, since
that is what Bidder uses for locating IPs. They are available on Maxmind's
site as a product (need to be logged in) in the form of a CSV.

## Outbrain

Outbrain uses their own ids for locations which they do not disclose
ahead. We used their search API to enumerate all their available
locations.

The helper script is available
[here](https://gist.github.com/nsaje/601217afcdc53543a585e6255bf1c503).

Region ids used by Outbrain are in FIPS 10-4 standard (Maxmind GeoIP2 v1) while Zemanta's systems use ISO 3166-2 standard (Maxmind GeoIP2 v2). Because of that Outbrain's mapping were converted to ISO 3166-2 using this [script](https://gist.github.com/jurebajt/36272394743a8e07a38f7fc53c13daa2#file-remap_fips_to_iso_regions-py) and this [source for iso3166 codes](https://github.com/esosedi/3166).

Note: French regions were changed on 2016/01/01. `outbrain-mapping.csv` was then updated manually using this [reference](https://en.wikipedia.org/wiki/ISO_3166-2:FR). Because some regions were merged, some mappings don't exist anymore (`FR---`).

## Yahoo

We can query Yahoo's supported locations via their [data dictionary
API](https://developer.yahoo.com/gemini/guide/data-dictionary.html). They
use WOEID for locations, so we must build a mapping. Cities can be matched
using [this
mapping](https://github.com/blackmad/geoplanet-concordance/tree/master/current).
Countries, regions & zips can be matched by name using Maxmind's location
names and some Python :)

## Re-importing locations

If any of the CSVs is updated/changed, the locations need to be re-imported using
something like (adjust for correct paths)

```
./manage.py import_geolocations dash/features/geolocation/supported_locations/GeoIP2-City-Locations-en.csv dash/features/geolocation/supported_locations/yahoo-mapping.csv dash/features/geolocation/supported_locations/outbrain-mapping.csv dash/features/geolocation/supported_locations/facebook-mapping.csv
```
