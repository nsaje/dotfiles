FORMAT: 1A
HOST: https://one.zemanta.com/

# Zemanta REST API

## Authentication

Zemanta REST API uses two-legged OAuth2 authentication using client credentials.

To acquire client credentials, first make sure you are logged in to Zemanta One. Then go to https://one.zemanta.com/o/applications/
and click the **New Application** button. Enter a name for your application and *Client type* as *Confidential*
and *Authorization type* as *Client credentials*, as shown in the image:

![New registration form](https://s3.amazonaws.com/z1-static/rest-docs/Z1registerNewApplicationScaled.png)

### Acquire a new authentication token [POST /o/token/]

This request requires you to use your client credentials (client ID and client secret)
as Basic HTTP Authentication. Manually, the header can be constructed as

```
Authorization: Basic base64(<client_id>:<client_secret>)
```


The acquired access token must then be passed to all REST API calls as the header

```
Authorization: Bearer <access_token>
```

+ Request
    + Attributes
        + `grant_type`: `client_credentials` (string, required)
    + Headers

            Authorization: Basic ABCDEF
    
+ Response 201 (application/json)

        {
            "access_token": "UUjXNkJDyLVjDzswOjdVm0ySIBYfp7",
            "token_type": "Bearer",
            "expires_in": 36000,
            "scope": "read write"
        }

# Group Account Credit Management

### Get active credit items for account [GET /rest/v1/account/{id}/credits/]

+ Response 200 (application/json)

        {
            "data": [
                {
                    "id":"861",
                    "startDate": "2016-01-01",
                    "endDate": "2016-11-05",
                    "createdOn": "2014-06-04",
                    "total": "1000.0000",
                    "allocated": "400.0000",
                    "available": "600.0000",
                }
            ]
        }


# Group Campaign Management

## Campaign Budgets [/rest/v1/campaigns/{campaign_id}/budgets/]

### List campaign budgets [GET /rest/v1/campaigns/{campaign_id}/budgets/]

+ Response 200 (application/json)

        {
            "data": [
                {
                    "id": "1910",
                    "amount": "400",
                    "startDate": "2016-01-01",
                    "endDate": "2016-01-31",
                    "state": "ACTIVE",
                    "spend": "0.0000",
                    "available": "400.0000"
                }
            ]
        }

### Create a new campaign budget [POST /rest/v1/campaigns/{campaign_id}/budgets/]

+ Request (application/json)

        {
            "creditId": "861",
            "amount": "600",
            "startDate": "2016-01-01",
            "endDate": "2016-01-31"
        }

+ Response 200 (application/json)

        {
            "data": {
                "id": "1911",
                "amount": "600",
                "startDate": "2016-01-01",
                "endDate": "2016-01-31",
                "state": "ACTIVE",
                "spend": "0.0000",
                "available": "600.0000"
            }
        }


### Get a campaign budget [GET /rest/v1/campaigns/{campaign_id}/budgets/{budget_id}]

+ Response 200 (application/json)

        {
            "data": {
                "id": "1910",
                "amount": "400",
                "startDate": "2016-01-01",
                "endDate": "2016-01-31",
                "state": "ACTIVE",
                "spend": "0.0000",
                "available": "400.0000"
            }
        }


### Edit a campaign budget [PUT /rest/v1/campaigns/{campaign_id}/budgets/{budget_id}]

+ Request (application/json)

        {
            "amount": "800"
        }

+ Response 200 (application/json)

        {
            "data": {
                "id": "1911",
                "amount": "800",
                "startDate": "2016-01-01",
                "endDate": "2016-01-31",
                "state": "ACTIVE",
                "spend": "0.0000",
                "available": "800.0000"
            }
        }

## Campaigns [/rest/v1/campaigns/]

### Get campaign details [GET /rest/v1/campaigns/{id}]

+ Response 200 (application/json)

        {
            "data": {
                "id": "608",
                "accountId": "186",
                "name": "My Campaign 1",
                "tracking": {
                    "ga": {
                        "enabled": true,
                        "type": "API",
                        "webPropertyId": "UA-123456789-1"
                    },
                    "adobe": {
                        "enabled": true,
                        "trackingParam": "cid"
                    }
                }
            }
        }


### Update campaign details [PUT /rest/v1/campaigns/{id}]

+ Request (application/json)

        {
            "name": "My Campaign 2",
            "tracking": {
                "ga": {
                    "enabled": true,
                    "type": "API",
                    "webPropertyId": "UA-123456789-1"
                },
                "adobe": {
                    "enabled": true,
                    "trackingParam": "cid"
                }
            }
        }

+ Response 201 (application/json)

        {
            "data": {
                "id": "608",
                "accountId": "186",
                "name": "My Campaign 2",
                "tracking": {
                    "ga": {
                        "enabled": true,
                        "type": "API",
                        "webPropertyId": "UA-123456789-1"
                    },
                    "adobe": {
                        "enabled": true,
                        "trackingParam": "cid"
                    }
                }
            }
        }

### List campaigns [GET /rest/v1/campaigns/]

+ Response 200 (application/json)

        {
            "data": [
                {
                    "id": "608",
                    "accountId": "186",
                    "name": "My Campaign 1",
                    "tracking": {
                        "ga": {
                            "enabled": true,
                            "type": "API",
                            "webPropertyId": "UA-123456789-1"
                        },
                        "adobe": {
                            "enabled": true,
                            "trackingParam": "cid"
                        }
                    }
                }
            ]
        }


### Create new campaign [POST /rest/v1/campaigns/]


+ Request (application/json)

        {
            "accountId": "186",
            "name": "My Campaign 3",
            "tracking": {
                "ga": {
                    "enabled": true,
                    "type": "API",
                    "webPropertyId": "UA-123456789-1"
                },
                "adobe": {
                    "enabled": true,
                    "trackingParam": "cid"
                }
            }
        }

+ Response 201 (application/json)

        {
            "data": {
                "id": "609",
                "accountId": "186",
                "name": "My Campaign 3",
                "tracking": {
                    "ga": {
                        "enabled": true,
                        "type": "API",
                        "webPropertyId": "UA-123456789-1"
                    },
                    "adobe": {
                        "enabled": true,
                        "trackingParam": "cid"
                    }
                }
            }
        }

## Campaign goals [/rest/v1/campaigns/{campaign_id}/goals/]

### List campaign goals [GET /rest/v1/campaigns/{campaign_id}/goals/]

+ Response 200 (application/json)

        {
            "data": [
                {
                    "id": "1238",
                    "campaignId": "608",
                    "type": "TIME_ON_SITE",
                    "primary": true,
                    "conversionGoal": {
                        "type": "PIXEL",
                        "name": "My conversion goal",
                        "conversionWindow": 7,
                        "goalId": "mygoal",
                        "pixelUrl": "http://example.com/mypixel1"
                    }
                }
            ]
        }
        
### Add a campaign goal [POST /rest/v1/campaigns/{campaign_id}/goals/]

+ Request (application/json)

        {
            "campaignId": "608",
            "type": "CPA",
            "value": "30.0",
            "primary": true,
            "conversionGoal": {
                "type": "PIXEL",
                "name": "My conversion goal 2",
                "conversionWindow": 7,
                "goalId": "mygoal",
                "pixelUrl": "http://example.com/mypixel1"
            }
        }

+ Response 200 (application/json)

        {
            "data": {
                "id": "1239",
                "campaignId": "608",
                "type": "CPA",
                "value": "30.0",
                "primary": true,
                "conversionGoal": {
                    "type": "PIXEL",
                    "name": "My conversion goal 2",
                    "conversionWindow": 7,
                    "goalId": "mygoal",
                    "pixelUrl": "http://example.com/mypixel1"
                }
            }
        }

### Modify a campaign goal [PUT /rest/v1/campaigns/{campaign_id}/goals/{goal_id}]

+ Request (application/json)

        {
            "primary": false,
        }
        
+ Response 200 (application/json)

        {
            "data": {
                "id": "1238",
                "campaignId": "608",
                "type": "CPA",
                "primary": false,
                "conversionGoal": {
                    "type": "PIXEL",
                    "name": "My conversion goal",
                    "conversionWindow": 7,
                    "goalId": "mygoal",
                    "pixelUrl": "http://example.com/mypixel1"
                }
            }
        }

### Remove campaign goal [DELETE /rest/v1/campaigngoals/{goal_id}]

+ Response 204

            
# Group Ad Group Management

## Ad Groups [/rest/v1/adgroups/]

### Get ad group details [GET /rest/v1/adgroups/{id}]

    
+ Response 200 (application/json)

        {
            "data": {
                "id": "2040",
                "campaignId": "608",
                "name": "My ad group 1",
                "state": "ACTIVE",
                "startDate": "2016-10-05",
                "endDate": "2016-11-05",
                "maxCpc": "0.25",
                "dailyBudget": "20.0",
                "targeting": {
                    "devices": ["desktop", "tablet"],
                    "geo": {
                        "included": {
                            "countries": ["CA"],
                            "regions": ["US-NY"],
                            "dma": ["693"]
                        }
                    },
                    "interest": {
                        "included": ["WOMEN", "FASHION"],
                        "excluded": ["POLITICS"]
                    }
                },
                "trackingCode": "this=1&that=2",
                "autopilot": {
                    "state": "OPTIMIZE_BIDS",
                    "dailyBudget": 100.0001
                },
                "dayparting": {
                    "monday": [0, 1, 2, 3],
                    "tuesday": [20, 21, 22, 23],
                    "timezone": "America/New_York"
                }
            }
        }


### Update ad group details [PUT /rest/v1/adgroups/{id}]


+ Request (application/json)

        {
            "name": "My ad group 2",
            "state": "ACTIVE",
            "startDate": "2016-10-05",
            "endDate": "2016-11-05",
            "maxCpc": "0.25",
            "dailyBudget": "20.0",
            "targeting": {
                "devices": ["desktop", "tablet"],
                "geo": {
                    "included": {
                        "countries": ["CA"],
                        "regions": ["US-NY"],
                        "dma": ["693"]
                    }
                },
                "interest": {
                    "included": ["WOMEN", "FASHION"],
                    "excluded": ["POLITICS"]
                }
            },
            "trackingCode": "this=1&that=2",
            "autopilot": {
                "state": "OPTIMIZE_BIDS",
                "dailyBudget": "100.0001"
            },
            "dayparting": {
                "monday": [4, 5, 6, 7],
                "friday": [2, 3, 7, 8, 9, 10]
            }
        }

+ Response 201 (application/json)

        {
            "data": {
                "id": "2040",
                "campaignId": "608",
                "name": "My ad group 2",
                "state": "ACTIVE",
                "startDate": "2016-10-05",
                "endDate": "2016-11-05",
                "maxCpc": "0.25",
                "dailyBudget": "20.0",
                "targeting": {
                    "devices": ["desktop", "tablet"],
                    "geo": {
                        "included": {
                            "countries": ["CA"],
                            "regions": ["US-NY"],
                            "dma": ["693"]
                        }
                    },
                    "interest": {
                        "included": ["WOMEN", "FASHION"],
                        "excluded": ["POLITICS"]
                    }
                },
                "trackingCode": "this=1&that=2",
                "autopilot": {
                    "state": "OPTIMIZE_BIDS",
                    "dailyBudget": "100.0001"
                },
                "dayparting": {
                    "monday": [4, 5, 6, 7],
                    "friday": [2, 3, 7, 8, 9, 10]
                }
            }
        }

### List ad groups [GET /rest/v1/adgroups/]

+ Attributes
    + campaign_id: 608 (number) - Optional campaign ID

+ Response 200 (application/json)

        {
            "data": [
                {
                    "id": "2040",
                    "campaignId": "608",
                    "name": "My ad group 1",
                    "state": "ACTIVE",
                    "startDate": "2016-10-05",
                    "endDate": "2016-11-05",
                    "maxCpc": "0.25",
                    "dailyBudget": "20.0",
                    "targeting": {
                        "devices": ["desktop", "tablet"],
                        "geo": {
                            "included": {
                                "countries": ["CA"],
                                "regions": ["US-NY"],
                                "dma": ["693"]
                            }
                        },
                        "interest": {
                            "included": ["WOMEN", "FASHION"],
                            "excluded": ["POLITICS"]
                        }
                    },
                    "trackingCode": "this=1&that=2",
                    "autopilot": {
                        "state": "OPTIMIZE_BIDS",
                        "dailyBudget": "100.0001"
                    },
                    "dayparting": {
                        "monday": [4, 5, 6, 7],
                        "friday": [2, 3, 7, 8, 9, 10],
                        "timezone": "Europe/Ljubljana"
                    }
                }
            ]
        }


### Create new ad group [POST /rest/v1/adgroups/]

+ Request (application/json)

        {
            "campaignId": "608",
            "name": "My ad group 3",
            "state": "ACTIVE",
            "startDate": "2016-10-05",
            "endDate": "2016-11-05",
            "maxCpc": "0.25",
            "dailyBudget": "20.0",
            "targeting": {
                "devices": ["desktop", "tablet"],
                "geo": {
                    "included": {
                        "countries": ["CA"],
                        "regions": ["US-NY"],
                        "dma": ["693"]
                    }
                },
                "interest": {
                    "included": ["WOMEN", "FASHION"],
                    "excluded": ["POLITICS"]
                }

            },
            "trackingCode": "this=1&that=2",
            "autopilot": {
                "state": "OPTIMIZE_BIDS",
                "dailyBudget": "100.0001"
            },
            "dayparting": {
                "monday": [4, 5, 6, 7],
                "friday": [2, 3, 7, 8, 9, 10],
                "timezone": "America/Los_Angeles"
            }
        }

+ Response 201 (application/json)

        {
            "data": {
                "id": "2040",
                "campaignId": "608",
                "name": "My ad group 1",
                "state": "ACTIVE",
                "startDate": "2016-10-05",
                "endDate": "2016-11-05",
                "maxCpc": "0.25",
                "dailyBudget": "20.0",
                "targeting": {
                    "devices": ["desktop", "tablet"],
                    "geo": {
                        "included": {
                            "countries": ["CA"],
                            "regions": ["US-NY"],
                            "dma": ["693"]
                        }
                    },
                    "interest": {
                        "included": ["WOMEN", "FASHION"],
                        "excluded": ["POLITICS"]
                    }
                },
                "trackingCode": "this=1&that=2",
                "autopilot": {
                    "state": "OPTIMIZE_BIDS",
                    "dailyBudget": "100.0001"
                },
                "dayparting": {
                    "monday": [4, 5, 6, 7],
                    "friday": [2, 3, 7, 8, 9, 10],
                    "timezone": "America/Los_Angeles"
                }
            }
        }

## Ad Group Sources [/rest/v1/adgroupsources/]

### Get ad group source settings [GET /rest/v1/adgroups/{id}/sources]

+ Response 201 (application/json)

        {
            "data": [
                {
                    "source": "outbrain",
                    "state": "ACTIVE",
                    "cpc": "0.20",
                    "dailyBudget": "10.0"
                },
                {
                    "source": "yahoo",
                    "state": "ACTIVE",
                    "cpc": "0.20",
                    "dailyBudget": "10.0"
                },
                {
                    "source": "gumgum",
                    "state": "ACTIVE",
                    "cpc": "0.20",
                    "dailyBudget": "10.0"
                },
                {
                    "source": "triplelift",
                    "state": "ACTIVE",
                    "cpc": "0.20",
                    "dailyBudget": "10.0"
                }
            ]
        }

### Update ad group source settings [PUT /rest/v1/adgroups/{id}/sources/]

+ Request (application/json)

        [
            {
                "source": "gumgum",
                "dailyBudget": "15.0",
                "cpc": "0.25",
            },
            {
                "source": "triplelift",
                "state": "PAUSED"
            }
            {
                "source": "outbrain",
                "state": "PAUSED"
            }
        ]
        

+ Response 201 (application/json)

        {
            "data": [
                {
                    "source": "outbrain",
                    "state": "PAUSED",
                    "cpc": "0.20",
                    "dailyBudget": "10.0"
                },
                {
                    "source": "yahoo",
                    "state": "ACTIVE",
                    "cpc": "0.20",
                    "dailyBudget": "10.0"
                },
                {
                    "source": "gumgum",
                    "state": "ACTIVE",
                    "cpc": "0.25",
                    "dailyBudget": "15.0"
                },
                {
                    "source": "triplelift",
                    "state": "PAUSED",
                    "cpc": "0.20",
                    "dailyBudget": "10.0"
                }
            ]
        }
        
### Get ad group source settings for all RTB sources [GET /rest/v1/adgroups/{id}/sources/rtb]

+ Response 200 (application/json)

        {
            "data": {
                "groupEnabled": true,
                "state": "ACTIVE",
                "dailyBudget": "50.00"
            }
        }
        
### Update ad group source settings for all RTB sources [PUT /rest/v1/adgroups/{id}/sources/rtb]

+ Request (application/json)

        {
            "groupEnabled": true,
            "state": "ACTIVE",
            "dailyBudget": "40.00"
        }

+ Response 200 (application/json)

        {
            "data": {
                "groupEnabled": true,
                "state": "ACTIVE",
                "dailyBudget": "40.00"
            }
        }

# Group Content ad management

## Manage content ads [/rest/v1/contentads/]

### List content ads [GET /rest/v1/contentads/]

+ Attributes
    + adGroupid: 2040 (number) - Ad group ID

+ Response 200 (application/json)

        {
            "data": [
                {
                    "id": "16805",
                    "adGroupId": "2040",
                    "state": "ACTIVE",
                    "label": "My label",
                    "url": "http://example.com/myblog",
                    "title": "My title",
                    "imageUrl": "http://example.com/myimage",
                    "imageCrop": "faces",
                    "displayUrl": "http://example.com/mycompany",
                    "brandName": "My Company",
                    "description": "My description",
                    "callToAction": "Read more",
                    "primaryTrackerUrl": "https://example.com/t1",
                    "secondaryTrackerUrl": "https://example.com/t2"
                }
            ]
        }
        

### Get content ad details [GET /rest/v1/contentads/{id}]

+ Response 200 (application/json)

        {
            "data": {
                "id": "16805",
                "adGroupId": "2040",
                "state": "ACTIVE",
                "label": "My label",
                "url": "http://example.com/myblog",
                "title": "My title",
                "imageUrl": "http://example.com/myimage",
                "imageCrop": "faces",
                "displayUrl": "http://example.com/mycompany",
                "brandName": "My Company",
                "description": "My description",
                "callToAction": "Read more",
                "primaryTrackerUrl": "https://example.com/t1",
                "secondaryTrackerUrl": "https://example.com/t2"
            }
        }
        

### Edit a content ad [PUT /rest/v1/contentads/{id}]

+ Request (application/json)

        {
            "label": "My label 2",
            "state": "PAUSED"
        }
        

+ Response 201 (application/json)

        {
            "data": {
                "id": "16805",
                "adGroupId": "2040",
                "state": "PAUSED",
                "label": "My label 2",
                "url": "http://example.com/myblog",
                "title": "My title",
                "imageUrl": "http://example.com/myimage",
                "imageCrop": "faces",
                "displayUrl": "http://example.com/mycompany",
                "brandName": "My Company",
                "description": "My description",
                "callToAction": "Read more",
                "primaryTrackerUrl": "https://example.com/t1",
                "secondaryTrackerUrl": "https://example.com/t2"
            }
        }

## Upload content ads [/rest/v1/contentads/batch/]


### Create a new content ad upload batch [POST /rest/v1/contentads/batch/]

+ Request (application/json)

        [
            {
                "label": "My label",
                "url": "http://example.com/myblog",
                "title": "My title",
                "imageUrl": "http://example.com/myimage",
                "imageCrop": "faces",
                "displayUrl": "http://example.com/mycompany",
                "brandName": "My Company",
                "description": "My description",
                "callToAction": "Read more",
                "trackerUrls": ["https://example.com/t1", "https://example.com/t2"]
            }
        ]
        
+ Response 201 (application/json)

        {
            "data": {
                "id": "1302",
                "status": "IN_PROGRESS",
                "validationStatus": [{"__all__": "Content ad still processing."}],
                "approvedContentAds": []
            }
        }


### Check content ad upload batch status [GET /rest/v1/contentads/batch/{batch_id}]

+ Response 201 (application/json)

        {
            "data": {
                "id": "1302",
                "status": "DONE",
                "validationStatus": [],
                "approvedContentAds": [
                    {
                        "id": "16805",
                        "adGroupId": "2040",
                        "state": "ACTIVE",
                        "label": "My label",
                        "url": "http://example.com/myblog",
                        "title": "My title",
                        "imageUrl": "http://example.com/myimage",
                        "imageCrop": "faces",
                        "displayUrl": "http://example.com/mycompany",
                        "brandName": "My Company",
                        "description": "My description",
                        "callToAction": "Read more",
                        "trackerUrls": ["https://example.com/t1", "https://example.com/t2"]
                    }
                ]
            }
        }


# Group Publishers management

## Blacklisting and whitelisting [/rest/v1/adgroups/{ad_group_id}/publishers/]


### Get publisher status [GET /rest/v1/adgroups/{ad_group_id}/publishers/]
    
+ Response 201 (application/json)

        {
            "data": [
                {
                    "name": "example.com/publisher1",
                    "status": "ENABLED",
                    "level": "ADGROUP",
                    "source": "gumgum"
                }, 
                {
                    "name": "example.com/publisher2",
                    "status": "ENABLED",
                    "level": "ADGROUP",
                    "source": "gumgum"
                },
                {
                    "name": "example.com/publisher3",
                    "status": "BLACKLISTED",
                    "level": "ADGROUP",
                    "source": null
                }
            ]
        }

### Set publisher status [PUT /rest/v1/adgroups/{ad_group_id}/publishers/]

+ Request (application/json)

        [
            {
                "name": "example.com/publisher1",
                "status": "BLACKLISTED",
                "level": "ADGROUP",
                "source": "gumgum"
            }, 
            {
                "name": "example.com/publisher2",
                "status": "BLACKLISTED",
                "level": "ADGROUP",
                "source": "gumgum"
            }, 
            }
        ]
    
+ Response 201 (application/json)

        {
            "data": [
                {
                    "name": "example.com/publisher1",
                    "status": "BLACKLISTED",
                    "level": "ADGROUP",
                    "source": "gumgum"
                }, 
                {
                    "name": "example.com/publisher2",
                    "status": "BLACKLISTED",
                    "level": "ADGROUP",
                    "source": "gumgum"
                }
            ]
        }


# Group Reporting

Getting a report is performed asynchronously. First, you create a report job, then you poll
its status and finally, when its status is DONE, you receive a link to a CSV file in the result field.

For now, only the following lists of fields are supported:

- [Content Ad Id, Content Ad, Label, Total Spend, Impressions, Clicks, Avg. CPC]
- [Domain Id, Domain, Media Source, Total Spend, Impressions, Clicks, Avg. CPC]
- [Media Source Id, Media Source, Total Spend, Impressions, Clicks, Avg. CPC]

## Report jobs [/rest/v1/reports/]

### Create a new report job [POST /rest/v1/reports/]

+ Request (application/json)

        {
            "fields": [
                {"field": "Content Ad Id"},
                {"field": "Content Ad"},
                {"field": "Label"},
                {"field": "Total Spend"},
                {"field": "Impressions"},
                {"field": "Clicks"},
                {"field": "Avg. CPC"}
            ],
            "filters": [
                {"field": "Date", "operator": "between", "from": "2016-10-01", "to": "2016-10-31"},
                {"field": "Ad Group Id", "operator": "=", "value": "2036"}
            ]
        }
    
+ Response 201 (application/json)

        {
            "data": {
                "id": "27",
                "status": "IN_PROGRESS",
                "result": null,
            }
        }
        

### Get report job status [GET /rest/v1/reports/{job_id}]

+ Response 201 (application/json)

        {
            "data": {
                "id": "27",
                "status": "DONE",
                "result": "https://z1-rest-reports.s3.amazonaws.com/KgrK55qCMO85v9JhHwCIv8kso2quYwEGV2MLpiVUgDVRDJm3HiGk1lWrOGfxJ7k2.csv"
            }
        }

# Types

## Dayparting

Dayparting structure is defined as a dictionary of days which point to a list of hours that are enabled in that day, eg. "monday" -> [0, 1, 2, 5]. 
This means that on monday bidding is enabled from 00:00 to 02:59 and from 5:00 to 5:59. 
The other value is "timezone" that defines in which timezone the hours are evaluated, eg. "timezone" -> "America/New_York". 
This value must be formatted according to the tz database (see https://en.wikipedia.org/wiki/Tz_database). If timezone isn't specified then user's timezone is used to resolve the hours.


# Group Constants reference

## Ad group / Content ad State

- `ACTIVE`
- `INACTIVE`

## Autopilot State

- `ACTIVE_CPC` - Optimize Bids
- `ACTIVE_CPC_BUDGET` - Optimize Bids and Daily Budgets
- `INACTIVE` - Disabled


## Publishers

### Status
- `ENABLED`
- `BLACKLISTED`
- `WHITELISTED`

### Level
- `ADGROUP`
- `CAMPAIGN`
- `ACCOUNT`

## Campaign Goal KPIs
- `TIME_ON_SITE` -  Time on Site - Seconds
- `MAX_BOUNCE_RATE` -  Max Bounce Rate
- `PAGES_PER_SESSION` -  Pageviews per Visit
- `CPA` -  Cost per Acquisition
- `CPC` -  Cost per Click
- `NEW_UNIQUE_VISITORS` -  New Unique Visitors
- `CPV` -  Cost per Visit
- `CP_NON_BOUNCED_VISIT` -  Cost per Non-Bounced Visit

### Conversion goal type
- `PIXEL` - Conversion Pixel
- `GA` - Google Analytics
- `OMNITURE` - Adobe Analytics

## Content ad upload batch status
- `DONE`
- `FAILED`
- `IN_PROGRESS`
- `CANCELLED`

## Device targeting

- `DESKTOP`
- `TABLET`
- `MOBILE`

## Interest targeting

- `COMMUNICATION` - Communication Tools
- `MEN` - Men’s Lifestyle
- `DATING` - Dating & Relationships
- `WEATHER` - Weather & Environment
- `FASHION` - Beauty & Fashion
- `TRAVEL` - Travel and Leisure
- `FUN` - Fun & Entertaining Sites
- `HEALTH` - Health & Fitness
- `SCIENCE` - Science
- `TECHNOLOGY` - Technology
- `CARS` - Automotive
- `MEDIA` - News
- `HOME` - Home & Garden
- `FAMILY` - Family & Parenting
- `SHOPPING` - Shopping
- `COUPONS` - Couponing
- `ENTERTAINMENT` - Arts & Entertainment
- `HOBBIES` - Hobbies & Interests
- `RELIGION` - Religion & Spirituality
- `MUSIC` - Music
- `FOOD` - Food & Drink
- `SPANISH` - Spanish Sites
- `PETS` - Pets
- `WOMEN` - Women’s Lifestyle
- `SPORTS` - Sports
- `FRENCH` - French Sites
- `POLITICS` - Gov’t & Politics
- `LAW` - Law
- `GAMES` - Games & Gaming
- `FINANCE` - Business & Finance
- `EDUCATION` - Education
- `UTILITY` - Software & Services
- `QUIZZES` - Quizzes
- `OTHER` - Other
- `FOREIGN` - International Sites


## Geo targeting

### DMA
- `669` - 669 Madison, WI 
- `762` - 762 Missoula, MT 
- `760` - 760 Twin Falls, ID 
- `766` - 766 Helena, MT 
- `662` - 662 Abilene-Sweetwater, TX 
- `764` - 764 Rapid City, SD 
- `765` - 765 El Paso, TX 
- `804` - 804 Palm Springs, CA 
- `610` - 610 Rockford, IL 
- `692` - 692 Beaumont-Port Arthur, TX 
- `693` - 693 Little Rock-Pine Bluff, AR 
- `691` - 691 Huntsville-Decatur (Florence), AL 
- `698` - 698 Montgomery (Selma), AL 
- `758` - 758 Idaho Falls-Pocatello, ID 
- `542` - 542 Dayton, OH 
- `543` - 543 Springfield-Holyoke, MA 
- `540` - 540 Traverse City-Cadillac, MI 
- `541` - 541 Lexington, KY 
- `546` - 546 Columbia, SC 
- `547` - 547 Toledo, OH 
- `544` - 544 Norfolk-Portsmouth-Newport News,VA 
- `545` - 545 Greenville-New Bern-Washington, NC 
- `810` - 810 Yakima-Pasco-Richland-Kennewick, WA 
- `811` - 811 Reno, NV 
- `548` - 548 West Palm Beach-Ft. Pierce, FL 
- `813` - 813 Medford-Klamath Falls, OR 
- `570` - 570 Florence-Myrtle Beach, SC 
- `678` - 678 Wichita-Hutchinson, KS 
- `679` - 679 Des Moines-Ames, IA 
- `718` - 718 Jackson, MS 
- `717` - 717 Quincy, IL-Hannibal, MO-Keokuk, IA 
- `675` - 675 Peoria-Bloomington, IL 
- `676` - 676 Duluth, MN-Superior, WI 
- `670` - 670 Ft. Smith-Fayetteville-Springdale-Rogers, AR 
- `671` - 671 Tulsa, OK 
- `711` - 711 Meridian, MS 
- `767` - 767 Casper-Riverton, WY 
- `661` - 661 San Angelo, TX 
- `673` - 673 Columbus-Tupelo-West Point, MS 
- `537` - 537 Bangor, ME 
- `536` - 536 Youngstown, OH 
- `535` - 535 Columbus, OH 
- `534` - 534 Orlando-Daytona Beach-Melbourne, FL 
- `533` - 533 Hartford & New Haven, CT 
- `828` - 828 Monterey-Salinas, CA 
- `530` - 530 Tallahassee, FL-Thomasville, GA 
- `825` - 825 San Diego, CA 
- `821` - 821 Bend, OR 
- `820` - 820 Portland, OR 
- `539` - 539 Tampa-St Petersburg (Sarasota), FL 
- `538` - 538 Rochester, NY 
- `592` - 592 Gainesville, FL 
- `709` - 709 Tyler-Longview(Lufkin & Nacogdoches), TX 
- `597` - 597 Parkersburg, WV 
- `596` - 596 Zanesville, OH 
- `705` - 705 Wausau-Rhinelander, WI 
- `702` - 702 La Crosse-Eau Claire, WI 
- `740` - 740 North Platte, NE 
- `604` - 604 Columbia-Jefferson City, MO 
- `790` - 790 Albuquerque-Santa Fe, NM 
- `839` - 839 Las Vegas, NV 
- `798` - 798 Glendive, MT 
- `524` - 524 Atlanta, GA 
- `525` - 525 Albany, GA 
- `526` - 526 Utica, NY 
- `527` - 527 Indianapolis, IN 
- `520` - 520 Augusta, GA 
- `521` - 521 Providence, RI-New Bedford, MA 
- `522` - 522 Columbus, GA 
- `523` - 523 Burlington, VT-Plattsburgh, NY 
- `528` - 528 Miami-Ft. Lauderdale, FL 
- `529` - 529 Louisville, KY 
- `532` - 532 Albany-Schenectady-Troy, NY 
- `584` - 584 Charlottesville, VA 
- `582` - 582 Lafayette, IN 
- `583` - 583 Alpena, MI 
- `581` - 581 Terre Haute, IN 
- `588` - 588 South Bend-Elkhart, IN 
- `598` - 598 Clarksburg-Weston, WV 
- `789` - 789 Tucson (Sierra Vista), AZ 
- `519` - 519 Charleston, SC 
- `640` - 640 Memphis, TN 
- `643` - 643 Lake Charles, LA 
- `642` - 642 Lafayette, LA 
- `644` - 644 Alexandria, LA 
- `647` - 647 Greenwood-Greenville, MS 
- `649` - 649 Evansville, IN 
- `648` - 648 Champaign & Springfield-Decatur,IL 
- `513` - 513 Flint-Saginaw-Bay City, MI 
- `512` - 512 Baltimore, MD 
- `515` - 515 Cincinnati, OH 
- `514` - 514 Buffalo, NY 
- `517` - 517 Charlotte, NC 
- `516` - 516 Erie, PA 
- `623` - 623 Dallas-Ft. Worth, TX 
- `622` - 622 New Orleans, LA 
- `627` - 627 Wichita Falls, TX & Lawton, OK 
- `626` - 626 Victoria, TX 
- `625` - 625 Waco-Temple-Bryan, TX 
- `624` - 624 Sioux City, IA 
- `573` - 573 Roanoke-Lynchburg, VA 
- `571` - 571 Ft. Myers-Naples, FL 
- `628` - 628 Monroe, LA-El Dorado, AR 
- `577` - 577 Wilkes Barre-Scranton, PA 
- `576` - 576 Salisbury, MD 
- `575` - 575 Chattanooga, TN 
- `574` - 574 Johnstown-Altoona, PA 
- `606` - 606 Dothan, AL 
- `600` - 600 Corpus Christi, TX 
- `559` - 559 Bluefield-Beckley-Oak Hill, WV 
- `752` - 752 Colorado Springs-Pueblo, CO 
- `745` - 745 Fairbanks, AK 
- `855` - 855 Santa Barbara-Santa Maria-San Luis Obispo, CA 
- `746` - 746 Biloxi-Gulfport, MS 
- `819` - 819 Seattle-Tacoma, WA 
- `508` - 508 Pittsburgh, PA 
- `656` - 656 Panama City, FL 
- `657` - 657 Sherman, TX-Ada, OK 
- `652` - 652 Omaha, NE 
- `734` - 734 Jonesboro, AR 
- `737` - 737 Mankato, MN 
- `736` - 736 Bowling Green, KY 
- `506` - 506 Boston, MA-Manchester, NH 
- `507` - 507 Savannah, GA 
- `504` - 504 Philadelphia, PA 
- `505` - 505 Detroit, MI 
- `502` - 502 Binghamton, NY 
- `503` - 503 Macon, GA 
- `500` - 500 Portland-Auburn, ME 
- `501` - 501 New York, NY 
- `630` - 630 Birmingham, AL 
- `569` - 569 Harrisonburg, VA 
- `632` - 632 Paducah, KY-Cape Girardeau, MO-Harrisburg-Mount Vernon, IL 
- `633` - 633 Odessa-Midland, TX 
- `757` - 757 Boise, ID 
- `650` - 650 Oklahoma City, OK 
- `755` - 755 Great Falls, MT 
- `637` - 637 Cedar Rapids-Waterloo-Iowa City & Dubuque, IA 
- `638` - 638 St. Joseph, MO 
- `561` - 561 Jacksonville, FL 
- `759` - 759 Cheyenne, WY-Scottsbluff, NE 
- `651` - 651 Lubbock, TX 
- `564` - 564 Charleston-Huntington, WV 
- `565` - 565 Elmira, NY 
- `566` - 566 Harrisburg-Lancaster-Lebanon-York, PA 
- `567` - 567 Greenville-Spartanburg, SC-Asheville, NC-Anderson, SC 
- `868` - 868 Chico-Redding, CA 
- `549` - 549 Watertown, NY 
- `747` - 747 Juneau, AK 
- `862` - 862 Sacramento-Stockton-Modesto, CA 
- `866` - 866 Fresno-Visalia, CA 
- `724` - 724 Fargo-Valley City, ND 
- `725` - 725 Sioux Falls(Mitchell), SD 
- `722` - 722 Lincoln & Hastings-Kearney, NE 
- `658` - 658 Green Bay-Appleton, WI 
- `659` - 659 Nashville, TN 
- `631` - 631 Ottumwa, IA-Kirksville, MO 
- `605` - 605 Topeka, KS 
- `753` - 753 Phoenix, AZ 
- `881` - 881 Spokane, WA 
- `743` - 743 Anchorage, AK 
- `744` - 744 Honolulu, HI 
- `558` - 558 Lima, OH 
- `603` - 603 Joplin, MO-Pittsburg, KS 
- `602` - 602 Chicago, IL 
- `555` - 555 Syracuse, NY 
- `554` - 554 Wheeling, WV-Steubenville, OH 
- `557` - 557 Knoxville, TN 
- `556` - 556 Richmond-Petersburg, VA 
- `551` - 551 Lansing, MI 
- `751` - 751 Denver, CO 
- `553` - 553 Marquette, MI 
- `552` - 552 Presque Isle, ME 
- `550` - 550 Wilmington, NC 
- `634` - 634 Amarillo, TX 
- `756` - 756 Billings, MT 
- `749` - 749 Laredo, TX 
- `641` - 641 San Antonio, TX 
- `636` - 636 Harlingen-Weslaco-Brownsville-McAllen, TX 
- `518` - 518 Greensboro-High Point-Winston Salem, NC 
- `754` - 754 Butte-Bozeman, MT 
- `560` - 560 Raleigh-Durham (Fayetteville), NC 
- `716` - 716 Baton Rouge, LA 
- `618` - 618 Houston, TX 
- `619` - 619 Springfield, MO 
- `771` - 771 Yuma, AZ-El Centro, CA 
- `770` - 770 Salt Lake City, UT 
- `773` - 773 Grand Junction-Montrose, CO 
- `612` - 612 Shreveport, LA 
- `613` - 613 Minneapolis-St. Paul, MN 
- `563` - 563 Grand Rapids-Kalamazoo-Battle Creek, MI 
- `611` - 611 Rochester, MN-Mason City, IA-Austin, MN 
- `616` - 616 Kansas City, MO 
- `617` - 617 Milwaukee, WI 
- `511` - 511 Washington, DC (Hagerstown, MD) 
- `510` - 510 Cleveland-Akron (Canton), OH 
- `635` - 635 Austin, TX 
- `710` - 710 Hattiesburg-Laurel, MS 
- `801` - 801 Eugene, OR 
- `509` - 509 Ft. Wayne, IN 
- `686` - 686 Mobile, AL-Pensacola (Ft. Walton Beach), FL 
- `609` - 609 St. Louis, MO 
- `803` - 803 Los Angeles, CA 
- `802` - 802 Eureka, CA 
- `687` - 687 Minot-Bismarck-Dickinson(Williston), ND 
- `800` - 800 Bakersfield, CA 
- `807` - 807 San Francisco-Oakland-San Jose, CA 
- `639` - 639 Jackson, TN 
- `682` - 682 Davenport,IA-Rock Island-Moline,IL
- `531` - 531 Tri-Cities-Tn-Va
 
### Country
- `BD` - Bangladesh 
- `BE` - Belgium 
- `BF` - Burkina Faso 
- `BG` - Bulgaria 
- `BA` - Bosnia and Herzegovina 
- `BB` - Barbados 
- `WF` - Wallis and Futuna 
- `BN` - Brunei Darussalam 
- `BO` - Bolivia, Plurinational State of 
- `BH` - Bahrain 
- `BI` - Burundi 
- `BJ` - Benin 
- `BT` - Bhutan 
- `JM` - Jamaica 
- `BW` - Botswana 
- `WS` - Samoa 
- `BR` - Brazil 
- `BS` - Bahamas 
- `BY` - Belarus 
- `BZ` - Belize 
- `RU` - Russian Federation 
- `RW` - Rwanda 
- `RS` - Serbia 
- `LT` - Lithuania 
- `LU` - Luxembourg 
- `LR` - Liberia 
- `RO` - Romania 
- `LS` - Lesotho 
- `GW` - Guinea-Bissau 
- `GU` - Guam 
- `GT` - Guatemala 
- `GS` - South Georgia and the South Sandwich Islands 
- `GR` - Greece 
- `GQ` - Equatorial Guinea 
- `JP` - Japan 
- `GY` - Guyana 
- `GE` - Georgia 
- `GD` - Grenada 
- `GB` - United Kingdom 
- `GA` - Gabon 
- `SV` - El Salvador 
- `GN` - Guinea 
- `GM` - Gambia 
- `KW` - Kuwait 
- `GH` - Ghana 
- `OM` - Oman 
- `JO` - Jordan 
- `HR` - Croatia 
- `HT` - Haiti 
- `HU` - Hungary 
- `HN` - Honduras 
- `HM` - Heard Island and McDonald Islands 
- `AD` - Andorra 
- `PW` - Palau 
- `PT` - Portugal 
- `PY` - Paraguay 
- `PA` - Panama 
- `PF` - French Polynesia 
- `PG` - Papua New Guinea 
- `PE` - Peru 
- `PK` - Pakistan 
- `PH` - Philippines 
- `PN` - Pitcairn 
- `PL` - Poland 
- `PM` - Saint Pierre and Miquelon 
- `ZM` - Zambia 
- `EE` - Estonia 
- `EG` - Egypt 
- `ZA` - South Africa 
- `EC` - Ecuador 
- `AL` - Albania 
- `AO` - Angola 
- `KZ` - Kazakhstan 
- `ET` - Ethiopia 
- `ZW` - Zimbabwe 
- `ES` - Spain 
- `ER` - Eritrea 
- `ME` - Montenegro 
- `MD` - Moldova, Republic of 
- `MG` - Madagascar 
- `MA` - Morocco 
- `MC` - Monaco 
- `UZ` - Uzbekistan 
- `LV` - Latvia 
- `ML` - Mali 
- `MN` - Mongolia 
- `MH` - Marshall Islands 
- `MK` - Macedonia, the Former Yugoslav Republic of 
- `MU` - Mauritius 
- `MT` - Malta 
- `MW` - Malawi 
- `MV` - Maldives 
- `MP` - Northern Mariana Islands 
- `MR` - Mauritania 
- `UG` - Uganda 
- `MY` - Malaysia 
- `MX` - Mexico 
- `VU` - Vanuatu 
- `FR` - France 
- `FI` - Finland 
- `FJ` - Fiji 
- `FM` - Micronesia, Federated States of 
- `NI` - Nicaragua 
- `NL` - Netherlands 
- `NO` - Norway 
- `NA` - Namibia 
- `NC` - New Caledonia 
- `NE` - Niger 
- `NF` - Norfolk Island 
- `NG` - Nigeria 
- `NZ` - New Zealand 
- `NP` - Nepal 
- `NR` - Nauru 
- `NU` - Niue 
- `CK` - Cook Islands 
- `CH` - Switzerland 
- `CO` - Colombia 
- `CN` - China 
- `CM` - Cameroon 
- `CL` - Chile 
- `CC` - Cocos (Keeling) Islands 
- `CA` - Canada 
- `CG` - Congo 
- `CF` - Central African Republic 
- `CD` - Congo, the Democratic Republic of the 
- `CZ` - Czech Republic 
- `CY` - Cyprus 
- `CX` - Christmas Island 
- `CR` - Costa Rica 
- `CV` - Cape Verde 
- `SZ` - Swaziland 
- `KG` - Kyrgyzstan 
- `KE` - Kenya 
- `SR` - Suriname 
- `KI` - Kiribati 
- `KH` - Cambodia 
- `KN` - Saint Kitts and Nevis 
- `KM` - Comoros 
- `ST` - Sao Tome and Principe 
- `SK` - Slovakia 
- `KR` - Korea, Republic of 
- `SI` - Slovenia 
- `SH` - Saint Helena, Ascension and Tristan da Cunha 
- `SO` - Somalia 
- `SN` - Senegal 
- `SM` - San Marino 
- `SL` - Sierra Leone 
- `SC` - Seychelles 
- `SB` - Solomon Islands 
- `SA` - Saudi Arabia 
- `SG` - Singapore 
- `SE` - Sweden 
- `DO` - Dominican Republic 
- `DM` - Dominica 
- `DJ` - Djibouti 
- `DK` - Denmark 
- `DE` - Germany 
- `YE` - Yemen 
- `AT` - Austria 
- `DZ` - Algeria 
- `US` - United States 
- `UY` - Uruguay 
- `UM` - United States Minor Outlying Islands 
- `TZ` - Tanzania, United Republic of 
- `LC` - Saint Lucia 
- `LA` - Lao People's Democratic Republic 
- `TV` - Tuvalu 
- `TT` - Trinidad and Tobago 
- `TR` - Turkey 
- `LK` - Sri Lanka 
- `LI` - Liechtenstein 
- `TN` - Tunisia 
- `TO` - Tonga 
- `TL` - Timor-Leste 
- `TM` - Turkmenistan 
- `TJ` - Tajikistan 
- `TK` - Tokelau 
- `TH` - Thailand 
- `TG` - Togo 
- `TD` - Chad 
- `LY` - Libya 
- `VA` - Holy See (Vatican City State) 
- `VC` - Saint Vincent and the Grenadines 
- `AE` - United Arab Emirates 
- `VE` - Venezuela, Bolivarian Republic of 
- `AG` - Antigua and Barbuda 
- `AF` - Afghanistan 
- `IQ` - Iraq 
- `IS` - Iceland 
- `AM` - Armenia 
- `IT` - Italy 
- `VN` - Viet Nam 
- `AQ` - Antarctica 
- `AS` - American Samoa 
- `AR` - Argentina 
- `AU` - Australia 
- `IL` - Israel 
- `IN` - India 
- `LB` - Lebanon 
- `AZ` - Azerbaijan 
- `IE` - Ireland 
- `ID` - Indonesia 
- `UA` - Ukraine 
- `QA` - Qatar 
- `MZ` - Mozambique
 
### Region
- `US-AL` - Alabama
- `US-AK` - Alaska
- `US-AZ` - Arizona
- `US-AR` - Arkansas
- `US-CA` - California
- `US-CO` - Colorado
- `US-CT` - Connecticut
- `US-DE` - Delaware
- `US-FL` - Florida
- `US-GA` - Georgia
- `US-HI` - Hawaii
- `US-ID` - Idaho
- `US-IL` - Illinois
- `US-IN` - Indiana
- `US-IA` - Iowa
- `US-KS` - Kansas
- `US-KY` - Kentucky
- `US-LA` - Louisiana
- `US-ME` - Maine
- `US-MD` - Maryland
- `US-MA` - Massachusetts
- `US-MI` - Michigan
- `US-MN` - Minnesota
- `US-MS` - Mississippi
- `US-MO` - Missouri
- `US-MT` - Montana
- `US-NE` - Nebraska
- `US-NV` - Nevada
- `US-NH` - New Hampshire
- `US-NJ` - New Jersey
- `US-NM` - New Mexico
- `US-NY` - New York
- `US-NC` - North Carolina
- `US-ND` - North Dakota
- `US-OH` - Ohio
- `US-OK` - Oklahoma
- `US-OR` - Oregon
- `US-PA` - Pennsylvania
- `US-RI` - Rhode Island
- `US-SC` - South Carolina
- `US-SD` - South Dakota
- `US-TN` - Tennessee
- `US-TX` - Texas
- `US-UT` - Utah
- `US-VT` - Vermont
- `US-VA` - Virginia
- `US-WA` - Washington
- `US-WV` - West Virginia
- `US-WI` - Wisconsin
- `US-WY` - Wyoming
- `US-DC` - District of Columbia
- `US-AS` - American Samoa
- `US-GU` - Guam
- `US-MP` - Northern Mariana Islands
- `US-PR` - Puerto Rico
- `US-UM` - United States Minor Outlying Islands
- `US-VI` - Virgin Islands







