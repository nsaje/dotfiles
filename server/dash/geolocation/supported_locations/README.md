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

## Yahoo

We can query Yahoo's supported locations via their [data dictionary
API](https://developer.yahoo.com/gemini/guide/data-dictionary.html). They
use WOEID for locations, so we must build a mapping. Cities can be matched
using [this
mapping](https://github.com/blackmad/geoplanet-concordance/tree/master/current).
Countries, regions & zips can be matched by name using Maxmind's location
names and some Python :)
