# NOTE: also used by import_maxmind_locations command
DMA_BY_CODE = {
    "669": "669 Madison, WI",
    "762": "762 Missoula, MT",
    "760": "760 Twin Falls, ID",
    "766": "766 Helena, MT",
    "662": "662 Abilene-Sweetwater, TX",
    "764": "764 Rapid City, SD",
    "765": "765 El Paso, TX",
    "804": "804 Palm Springs, CA",
    "610": "610 Rockford, IL",
    "692": "692 Beaumont-Port Arthur, TX",
    "693": "693 Little Rock-Pine Bluff, AR",
    "691": "691 Huntsville-Decatur (Florence), AL",
    "698": "698 Montgomery (Selma), AL",
    "758": "758 Idaho Falls-Pocatello, ID",
    "542": "542 Dayton, OH",
    "543": "543 Springfield-Holyoke, MA",
    "540": "540 Traverse City-Cadillac, MI",
    "541": "541 Lexington, KY",
    "546": "546 Columbia, SC",
    "547": "547 Toledo, OH",
    "544": "544 Norfolk-Portsmouth-Newport News,VA",
    "545": "545 Greenville-New Bern-Washington, NC",
    "810": "810 Yakima-Pasco-Richland-Kennewick, WA",
    "811": "811 Reno, NV",
    "548": "548 West Palm Beach-Ft. Pierce, FL",
    "813": "813 Medford-Klamath Falls, OR",
    "570": "570 Florence-Myrtle Beach, SC",
    "678": "678 Wichita-Hutchinson, KS",
    "679": "679 Des Moines-Ames, IA",
    "718": "718 Jackson, MS",
    "717": "717 Quincy, IL-Hannibal, MO-Keokuk, IA",
    "675": "675 Peoria-Bloomington, IL",
    "676": "676 Duluth, MN-Superior, WI",
    "670": "670 Ft. Smith-Fayetteville-Springdale-Rogers, AR",
    "671": "671 Tulsa, OK",
    "711": "711 Meridian, MS",
    "767": "767 Casper-Riverton, WY",
    "661": "661 San Angelo, TX",
    "673": "673 Columbus-Tupelo-West Point, MS",
    "537": "537 Bangor, ME",
    "536": "536 Youngstown, OH",
    "535": "535 Columbus, OH",
    "534": "534 Orlando-Daytona Beach-Melbourne, FL",
    "533": "533 Hartford & New Haven, CT",
    "828": "828 Monterey-Salinas, CA",
    "530": "530 Tallahassee, FL-Thomasville, GA",
    "825": "825 San Diego, CA",
    "821": "821 Bend, OR",
    "820": "820 Portland, OR",
    "539": "539 Tampa-St Petersburg (Sarasota), FL",
    "538": "538 Rochester, NY",
    "592": "592 Gainesville, FL",
    "709": "709 Tyler-Longview(Lufkin & Nacogdoches), TX",
    "597": "597 Parkersburg, WV",
    "596": "596 Zanesville, OH",
    "705": "705 Wausau-Rhinelander, WI",
    "702": "702 La Crosse-Eau Claire, WI",
    "740": "740 North Platte, NE",
    "604": "604 Columbia-Jefferson City, MO",
    "790": "790 Albuquerque-Santa Fe, NM",
    "839": "839 Las Vegas, NV",
    "798": "798 Glendive, MT",
    "524": "524 Atlanta, GA",
    "525": "525 Albany, GA",
    "526": "526 Utica, NY",
    "527": "527 Indianapolis, IN",
    "520": "520 Augusta, GA",
    "521": "521 Providence, RI-New Bedford, MA",
    "522": "522 Columbus, GA",
    "523": "523 Burlington, VT-Plattsburgh, NY",
    "528": "528 Miami-Ft. Lauderdale, FL",
    "529": "529 Louisville, KY",
    "532": "532 Albany-Schenectady-Troy, NY",
    "584": "584 Charlottesville, VA",
    "582": "582 Lafayette, IN",
    "583": "583 Alpena, MI",
    "581": "581 Terre Haute, IN",
    "588": "588 South Bend-Elkhart, IN",
    "598": "598 Clarksburg-Weston, WV",
    "789": "789 Tucson (Sierra Vista), AZ",
    "519": "519 Charleston, SC",
    "640": "640 Memphis, TN",
    "643": "643 Lake Charles, LA",
    "642": "642 Lafayette, LA",
    "644": "644 Alexandria, LA",
    "647": "647 Greenwood-Greenville, MS",
    "649": "649 Evansville, IN",
    "648": "648 Champaign & Springfield-Decatur,IL",
    "513": "513 Flint-Saginaw-Bay City, MI",
    "512": "512 Baltimore, MD",
    "515": "515 Cincinnati, OH",
    "514": "514 Buffalo, NY",
    "517": "517 Charlotte, NC",
    "516": "516 Erie, PA",
    "623": "623 Dallas-Ft. Worth, TX",
    "622": "622 New Orleans, LA",
    "627": "627 Wichita Falls, TX & Lawton, OK",
    "626": "626 Victoria, TX",
    "625": "625 Waco-Temple-Bryan, TX",
    "624": "624 Sioux City, IA",
    "573": "573 Roanoke-Lynchburg, VA",
    "571": "571 Ft. Myers-Naples, FL",
    "628": "628 Monroe, LA-El Dorado, AR",
    "577": "577 Wilkes Barre-Scranton, PA",
    "576": "576 Salisbury, MD",
    "575": "575 Chattanooga, TN",
    "574": "574 Johnstown-Altoona, PA",
    "606": "606 Dothan, AL",
    "600": "600 Corpus Christi, TX",
    "559": "559 Bluefield-Beckley-Oak Hill, WV",
    "752": "752 Colorado Springs-Pueblo, CO",
    "745": "745 Fairbanks, AK",
    "855": "855 Santa Barbara-Santa Maria-San Luis Obispo, CA",
    "746": "746 Biloxi-Gulfport, MS",
    "819": "819 Seattle-Tacoma, WA",
    "508": "508 Pittsburgh, PA",
    "656": "656 Panama City, FL",
    "657": "657 Sherman, TX-Ada, OK",
    "652": "652 Omaha, NE",
    "734": "734 Jonesboro, AR",
    "737": "737 Mankato, MN",
    "736": "736 Bowling Green, KY",
    "506": "506 Boston, MA-Manchester, NH",
    "507": "507 Savannah, GA",
    "504": "504 Philadelphia, PA",
    "505": "505 Detroit, MI",
    "502": "502 Binghamton, NY",
    "503": "503 Macon, GA",
    "500": "500 Portland-Auburn, ME",
    "501": "501 New York, NY",
    "630": "630 Birmingham, AL",
    "569": "569 Harrisonburg, VA",
    "632": "632 Paducah, KY-Cape Girardeau, MO-Harrisburg-Mount Vernon, IL",
    "633": "633 Odessa-Midland, TX",
    "757": "757 Boise, ID",
    "650": "650 Oklahoma City, OK",
    "755": "755 Great Falls, MT",
    "637": "637 Cedar Rapids-Waterloo-Iowa City & Dubuque, IA",
    "638": "638 St. Joseph, MO",
    "561": "561 Jacksonville, FL",
    "759": "759 Cheyenne, WY-Scottsbluff, NE",
    "651": "651 Lubbock, TX",
    "564": "564 Charleston-Huntington, WV",
    "565": "565 Elmira, NY",
    "566": "566 Harrisburg-Lancaster-Lebanon-York, PA",
    "567": "567 Greenville-Spartanburg, SC-Asheville, NC-Anderson, SC",
    "868": "868 Chico-Redding, CA",
    "549": "549 Watertown, NY",
    "747": "747 Juneau, AK",
    "862": "862 Sacramento-Stockton-Modesto, CA",
    "866": "866 Fresno-Visalia, CA",
    "724": "724 Fargo-Valley City, ND",
    "725": "725 Sioux Falls(Mitchell), SD",
    "722": "722 Lincoln & Hastings-Kearney, NE",
    "658": "658 Green Bay-Appleton, WI",
    "659": "659 Nashville, TN",
    "631": "631 Ottumwa, IA-Kirksville, MO",
    "605": "605 Topeka, KS",
    "753": "753 Phoenix, AZ",
    "881": "881 Spokane, WA",
    "743": "743 Anchorage, AK",
    "744": "744 Honolulu, HI",
    "558": "558 Lima, OH",
    "603": "603 Joplin, MO-Pittsburg, KS",
    "602": "602 Chicago, IL",
    "555": "555 Syracuse, NY",
    "554": "554 Wheeling, WV-Steubenville, OH",
    "557": "557 Knoxville, TN",
    "556": "556 Richmond-Petersburg, VA",
    "551": "551 Lansing, MI",
    "751": "751 Denver, CO",
    "553": "553 Marquette, MI",
    "552": "552 Presque Isle, ME",
    "550": "550 Wilmington, NC",
    "634": "634 Amarillo, TX",
    "756": "756 Billings, MT",
    "749": "749 Laredo, TX",
    "641": "641 San Antonio, TX",
    "636": "636 Harlingen-Weslaco-Brownsville-McAllen, TX",
    "518": "518 Greensboro-High Point-Winston Salem, NC",
    "754": "754 Butte-Bozeman, MT",
    "560": "560 Raleigh-Durham (Fayetteville), NC",
    "716": "716 Baton Rouge, LA",
    "618": "618 Houston, TX",
    "619": "619 Springfield, MO",
    "771": "771 Yuma, AZ-El Centro, CA",
    "770": "770 Salt Lake City, UT",
    "773": "773 Grand Junction-Montrose, CO",
    "612": "612 Shreveport, LA",
    "613": "613 Minneapolis-St. Paul, MN",
    "563": "563 Grand Rapids-Kalamazoo-Battle Creek, MI",
    "611": "611 Rochester, MN-Mason City, IA-Austin, MN",
    "616": "616 Kansas City, MO",
    "617": "617 Milwaukee, WI",
    "511": "511 Washington, DC (Hagerstown, MD)",
    "510": "510 Cleveland-Akron (Canton), OH",
    "635": "635 Austin, TX",
    "710": "710 Hattiesburg-Laurel, MS",
    "801": "801 Eugene, OR",
    "509": "509 Ft. Wayne, IN",
    "686": "686 Mobile, AL-Pensacola (Ft. Walton Beach), FL",
    "609": "609 St. Louis, MO",
    "803": "803 Los Angeles, CA",
    "802": "802 Eureka, CA",
    "687": "687 Minot-Bismarck-Dickinson(Williston), ND",
    "800": "800 Bakersfield, CA",
    "807": "807 San Francisco-Oakland-San Jose, CA",
    "639": "639 Jackson, TN",
    "682": "682 Davenport,IA-Rock Island-Moline,IL",
    "531": "531 Tri-Cities-Tn-Va",
}

COUNTRY_BY_CODE = {
    "BD": "Bangladesh",
    "BE": "Belgium",
    "BF": "Burkina Faso",
    "BG": "Bulgaria",
    "BA": "Bosnia and Herzegovina",
    "BB": "Barbados",
    "WF": "Wallis and Futuna",
    "BN": "Brunei Darussalam",
    "BO": "Bolivia, Plurinational State of",
    "BH": "Bahrain",
    "BI": "Burundi",
    "BJ": "Benin",
    "BT": "Bhutan",
    "JM": "Jamaica",
    "BW": "Botswana",
    "WS": "Samoa",
    "BR": "Brazil",
    "BS": "Bahamas",
    "BY": "Belarus",
    "BZ": "Belize",
    "RU": "Russian Federation",
    "RW": "Rwanda",
    "RS": "Serbia",
    "LT": "Lithuania",
    "LU": "Luxembourg",
    "LR": "Liberia",
    "RO": "Romania",
    "LS": "Lesotho",
    "GW": "Guinea-Bissau",
    "GU": "Guam",
    "GT": "Guatemala",
    "GS": "South Georgia and the South Sandwich Islands",
    "GR": "Greece",
    "GQ": "Equatorial Guinea",
    "JP": "Japan",
    "GY": "Guyana",
    "GE": "Georgia",
    "GD": "Grenada",
    "GB": "United Kingdom",
    "GA": "Gabon",
    "SV": "El Salvador",
    "GN": "Guinea",
    "GM": "Gambia",
    "KW": "Kuwait",
    "GH": "Ghana",
    "OM": "Oman",
    "JO": "Jordan",
    "HR": "Croatia",
    "HT": "Haiti",
    "HU": "Hungary",
    "HN": "Honduras",
    "HM": "Heard Island and McDonald Islands",
    "AD": "Andorra",
    "PW": "Palau",
    "PT": "Portugal",
    "PY": "Paraguay",
    "PA": "Panama",
    "PF": "French Polynesia",
    "PG": "Papua New Guinea",
    "PE": "Peru",
    "PK": "Pakistan",
    "PH": "Philippines",
    "PN": "Pitcairn",
    "PL": "Poland",
    "PM": "Saint Pierre and Miquelon",
    "ZM": "Zambia",
    "EE": "Estonia",
    "EG": "Egypt",
    "ZA": "South Africa",
    "EC": "Ecuador",
    "AL": "Albania",
    "AO": "Angola",
    "KZ": "Kazakhstan",
    "ET": "Ethiopia",
    "ZW": "Zimbabwe",
    "ES": "Spain",
    "ER": "Eritrea",
    "ME": "Montenegro",
    "MD": "Moldova, Republic of",
    "MG": "Madagascar",
    "MA": "Morocco",
    "MC": "Monaco",
    "UZ": "Uzbekistan",
    "LV": "Latvia",
    "ML": "Mali",
    "MN": "Mongolia",
    "MH": "Marshall Islands",
    "MK": "Macedonia, the Former Yugoslav Republic of",
    "MU": "Mauritius",
    "MT": "Malta",
    "MW": "Malawi",
    "MV": "Maldives",
    "MP": "Northern Mariana Islands",
    "MR": "Mauritania",
    "UG": "Uganda",
    "MY": "Malaysia",
    "MX": "Mexico",
    "VU": "Vanuatu",
    "FR": "France",
    "FI": "Finland",
    "FJ": "Fiji",
    "FM": "Micronesia, Federated States of",
    "NI": "Nicaragua",
    "NL": "Netherlands",
    "NO": "Norway",
    "NA": "Namibia",
    "NC": "New Caledonia",
    "NE": "Niger",
    "NF": "Norfolk Island",
    "NG": "Nigeria",
    "NZ": "New Zealand",
    "NP": "Nepal",
    "NR": "Nauru",
    "NU": "Niue",
    "CK": "Cook Islands",
    "CH": "Switzerland",
    "CO": "Colombia",
    "CN": "China",
    "CM": "Cameroon",
    "CL": "Chile",
    "CC": "Cocos (Keeling) Islands",
    "CA": "Canada",
    "CG": "Congo",
    "CF": "Central African Republic",
    "CD": "Congo, the Democratic Republic of the",
    "CZ": "Czech Republic",
    "CY": "Cyprus",
    "CX": "Christmas Island",
    "CR": "Costa Rica",
    "CV": "Cape Verde",
    "SZ": "Swaziland",
    "KG": "Kyrgyzstan",
    "KE": "Kenya",
    "SR": "Suriname",
    "KI": "Kiribati",
    "KH": "Cambodia",
    "KN": "Saint Kitts and Nevis",
    "KM": "Comoros",
    "ST": "Sao Tome and Principe",
    "SK": "Slovakia",
    "KR": "Korea, Republic of",
    "SI": "Slovenia",
    "SH": "Saint Helena, Ascension and Tristan da Cunha",
    "SO": "Somalia",
    "SN": "Senegal",
    "SM": "San Marino",
    "SL": "Sierra Leone",
    "SC": "Seychelles",
    "SB": "Solomon Islands",
    "SA": "Saudi Arabia",
    "SG": "Singapore",
    "SE": "Sweden",
    "DO": "Dominican Republic",
    "DM": "Dominica",
    "DJ": "Djibouti",
    "DK": "Denmark",
    "DE": "Germany",
    "YE": "Yemen",
    "AT": "Austria",
    "DZ": "Algeria",
    "US": "United States",
    "UY": "Uruguay",
    "UM": "United States Minor Outlying Islands",
    "TZ": "Tanzania, United Republic of",
    "LC": "Saint Lucia",
    "LA": "Lao People's Democratic Republic",
    "TV": "Tuvalu",
    "TT": "Trinidad and Tobago",
    "TR": "Turkey",
    "LK": "Sri Lanka",
    "LI": "Liechtenstein",
    "TN": "Tunisia",
    "TO": "Tonga",
    "TL": "Timor-Leste",
    "TM": "Turkmenistan",
    "TJ": "Tajikistan",
    "TK": "Tokelau",
    "TH": "Thailand",
    "TG": "Togo",
    "TD": "Chad",
    "LY": "Libya",
    "VA": "Holy See (Vatican City State)",
    "VC": "Saint Vincent and the Grenadines",
    "AE": "United Arab Emirates",
    "VE": "Venezuela, Bolivarian Republic of",
    "AG": "Antigua and Barbuda",
    "AF": "Afghanistan",
    "IQ": "Iraq",
    "IS": "Iceland",
    "AM": "Armenia",
    "IT": "Italy",
    "VN": "Viet Nam",
    "AQ": "Antarctica",
    "AS": "American Samoa",
    "AR": "Argentina",
    "AU": "Australia",
    "IL": "Israel",
    "IN": "India",
    "LB": "Lebanon",
    "AZ": "Azerbaijan",
    "IE": "Ireland",
    "ID": "Indonesia",
    "UA": "Ukraine",
    "QA": "Qatar",
    "MZ": "Mozambique"
}

SUBDIVISION_BY_CODE = {
    "US-AL": "Alabama",
    "US-AK": "Alaska",
    "US-AZ": "Arizona",
    "US-AR": "Arkansas",
    "US-CA": "California",
    "US-CO": "Colorado",
    "US-CT": "Connecticut",
    "US-DE": "Delaware",
    "US-FL": "Florida",
    "US-GA": "Georgia",
    "US-HI": "Hawaii",
    "US-ID": "Idaho",
    "US-IL": "Illinois",
    "US-IN": "Indiana",
    "US-IA": "Iowa",
    "US-KS": "Kansas",
    "US-KY": "Kentucky",
    "US-LA": "Louisiana",
    "US-ME": "Maine",
    "US-MD": "Maryland",
    "US-MA": "Massachusetts",
    "US-MI": "Michigan",
    "US-MN": "Minnesota",
    "US-MS": "Mississippi",
    "US-MO": "Missouri",
    "US-MT": "Montana",
    "US-NE": "Nebraska",
    "US-NV": "Nevada",
    "US-NH": "New Hampshire",
    "US-NJ": "New Jersey",
    "US-NM": "New Mexico",
    "US-NY": "New York",
    "US-NC": "North Carolina",
    "US-ND": "North Dakota",
    "US-OH": "Ohio",
    "US-OK": "Oklahoma",
    "US-OR": "Oregon",
    "US-PA": "Pennsylvania",
    "US-RI": "Rhode Island",
    "US-SC": "South Carolina",
    "US-SD": "South Dakota",
    "US-TN": "Tennessee",
    "US-TX": "Texas",
    "US-UT": "Utah",
    "US-VT": "Vermont",
    "US-VA": "Virginia",
    "US-WA": "Washington",
    "US-WV": "West Virginia",
    "US-WI": "Wisconsin",
    "US-WY": "Wyoming",
    "US-DC": "District of Columbia",
    "US-AS": "American Samoa",
    "US-GU": "Guam",
    "US-MP": "Northern Mariana Islands",
    "US-PR": "Puerto Rico",
    "US-UM": "United States Minor Outlying Islands",
    "US-VI": "Virgin Islands"
}

SUBDIVISION_TO_COUNTRY = {
    "US-AS": "AS",
    "US-GU": "GU",
    "US-MP": "MP",
    "US-PR": "PR",
    "US-UM": "UM",
    "US-VI": "VI"
}
