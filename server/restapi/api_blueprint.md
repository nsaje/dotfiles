FORMAT: 1A
HOST: https://one.zemanta.com

# Zemanta REST API

This document describes the Zemanta REST Campaign Management API.

The API enables [Zemanta](https://www.zemanta.com) clients to programatically create and manage campaigns, ad groups and content ads using RESTful objects.
Custom performance reports are also available as part of the API.

In order to use Zemanta REST API, please contact your sales representative.

## Who should read this document?

This document is inteded for programmers who are developing an integration with the Zemanta One system.
A prerequisite for working with Zemanta REST API is an understanding of HTTP and JSON.

# Group Overview

## Entities

The diagram and the table below describe the objects this API deals with and the relationships between them.

![Entity Relation Diagram](https://s3.amazonaws.com/z1-static/rest-docs/ZemantaRESTAPIDiagram.png)

[//]: # (diagram source: https://drive.google.com/a/zemanta.com/file/d/0B6lNA2cM_sh8V3E3dmpoV1UzakU/view?usp=sharing)

Entity        | Description                                           | Functionality
--------------|-------------------------------------------------------|------------------------------|
Account       | Zemanta One client account                            | /
Credit Item   | Signed credit available for spending                  | Read
Budget Item   | Part of a credit assigned to a campaign as its budget | Read, Create, Update
Campaign      | A collection of Ad Groups                             | Read, Create, Update
Campaign Goal | Campaign optimization goal                            | Read, Create, Update, Delete
Ad Group      | A collection of Content Ads                           | Read, Create, Update
Content Ad    | A single piece of promoted content                    | Read, Create, Update

## HTTP Requests

As per the REST convention, the type of action performed is determined by the HTTP method of the request.

HTTP Method | Action
------------|------------------------------------------|
GET         | Retrieve an entity or a list of entities
POST        | Create a new entity
PUT         | Update an entity

Requests that include a JSON formatted body must include the following header in the request:

`Content-type: application/json`


## HTTP Response Status Codes

Status Code | Meaning      | Description
------------|--------------|------------------------------------------------|
200         | OK           | The request was successful
201         | Created      | Entity successfuly created
400         | Bad Request  | Invalid or missing required parameters
401         | Unauthorized | Authentication failed, check your access token
403         | Forbidden    | Not enough permissions for desired action
500         | Server Error | Server error, please contact us

## JSON Payload Format

Entities are represented by JSON objects. Multiple entities are represented as a JSON array of objects.

### Request

For `POST` or `PUT` requests, the payload is a JSON object or a JSON array of objects, as applicable to the endpoint:

```
{
    "id": "123",
    "name": "My Campaign"
}
```

or in the case of a list of entities:

```
[
    {
        "id": "123",
        "name": "My Campaign"
    },
    {
        "id": "124",
        "name": "My Campaign 2"
    }
]
```


### Response

The server will return an entity or a list of entities in the response payload's `data` field:

```
{
    "data": {
        "id": "123",
        "name": "My Campaign"
    }
}
```

or in the case of a list of entities:

```
{
    "data": [
        {
            "id": "123",
            "name": "My Campaign"
        },
        {
            "id": "124",
            "name": "My Campaign 2"
        }
    ]
}
```

### Partial Updates

The API supports partial updates, which means that for all `PUT` actions, if you're updating a hypothetical entity

```
{
    "name": "MyEntity",
    "value": "123"
}
```

you can send only updated fields as the payload:

```
{
    "value": "789"
}
```

which will result in the following entity:

```
{
    "name": "MyEntity",
    "value": "789"
}
```


### Errors

In case of an error, the server will return a response with the appropriate status code and the payload describing the error:

```
{
    "errorCode": "ValidationError",
    "details": "Name is required"
}
```

## Authentication
 
Zemanta REST API uses two-legged OAuth2 authentication using client credentials.
The client credentials are used to acquire an access token, which must
then be passed to all REST API calls as the header
 
```
Authorization: Bearer <access_token>
```
 

### Create client credentials

To create client credentials, first make sure you are logged in to Zemanta One. Then go to https://one.zemanta.com/o/applications/
and click the **New Application** button. Enter a name for your application, as shown in the image, and click the "Save" button.

![New application registration form](https://s3.amazonaws.com/z1-static/rest-docs/oauth2-1-scaled.png)

After you click the "Save" button, you will see the details of your newly created application credentials. The provided
Client ID and Client Secret are used for API authentication.

![Application credentials details](https://s3.amazonaws.com/z1-static/rest-docs/oauth2-2-scaled.png)

### Acquire a new authentication token [POST /o/token/]

This request requires you to use your client credentials (client ID and client secret)
as Basic HTTP Authentication. Manually, the header can be constructed as

```
Authorization: Basic base64(<client_id>:<client_secret>)
```

+ Request (application/x-www-form-urlencoded)
    + Attributes
        + `grant_type`: `client_credentials` (string, required)

    + Headers

            Authorization: Basic WkNTeDJXanhIeHhWNnJLWkMzaGRiNmVqTzhHTHdjZFV0bHRtcHQ5Sjp1N3BsRWQwNG1IYzExQ2NrUzlkb2poWWl3YVd6TnFlQjF3OUtnTXh3ZTVya1c2U3M3bVRSSXg2UGQ4dDdZdmRZYzdiQzEwMjVINzRzOThFMmVxaEljQmx2QmxIc2M1dkFwOVRKTVAyZTh5Nmt5SktRVVdrcFVpckZSbDNPczJmQw==

    + Body

            grant_type=client_credentials

+ Response 200 (application/json)

        {
            "access_token": "UUjXNkJDyLVjDzswOjdVm0ySIBYfp7",
            "token_type": "Bearer",
            "expires_in": 36000,
            "scope": "read write"
        }

# Group Account Credit Management
<a name="credit"></a>

After your Insertion Order for media spend has been executed Zemanta's Customer Success team
will assign a credit line to your account. With credit added to your account you have the
ability to create budget items and associate them with the campaigns you're planning. 

Property  | Type            | Description
----------|-----------------|----------------------------------------------|
id        | string          | the credit item's id
startDate | date            | start date of the credit
endDate   | date            | end date of the credit
total     | [money](#money) | total credit amount
allocated | [money](#money) | amount already allocated to campaign budgets
available | [money](#money) | amount still available for allocation


### Get active credit items for account [GET /rest/v1/accounts/{accountId}/credits/]

+ Parameters
    + accountId: 186 (required)

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
                    "available": "600.0000"
                }
            ]
        }


# Group Campaign Management

## Campaigns [/rest/v1/campaigns/]

A Campaign is a collection of Ad Groups. It holds common settings for
all Ad Groups and also has budgets and goals associated.

Property  | Type                  | Description                                | Create   | Update
----------|-----------------------|--------------------------------------------|----------|-----------|
id        | string                | the campaign's id                          | N/A      | read only
accountId | string                | id of the account this campaign belongs to | required | read only
name      | string                | the name of the campaign                   | required | optional
tracking  | [tracking](#tracking) | tracking settings                          | optional | optional


<a name="tracking"></a>
#### Tracking Settings

Postclick tracking integration can be set up for Google Analytics and Adobe Analytics.

Tracking | Property          | Type                                  | Description
---------|-------------------|---------------------------------------|--------------------------------------|
ga       |                   |                                       |
&nbsp;   | enabled           | boolean                               | Google Analytics integration enabled
&nbsp;   | type              | [GA Tracking Type](#ga-tracking-type) | Google Analytics tracking type
&nbsp;   | webProperyId      | string                                | Google Analytics Web Property ID
adobe    |                   |                                       |
&nbsp;   | enabled           | boolean                               | Adobe Analytics integration enabled
&nbsp;   | trackingParameter | string                                | Adobe Analytics tracking parameter


### Get campaign details [GET /rest/v1/campaigns/{campaignId}]

+ Parameters
    + campaignId: 608 (required)

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
                        "trackingParameter": "cid"
                    }
                }
            }
        }


### Update campaign details [PUT /rest/v1/campaigns/{campaignId}]

+ Parameters
    + campaignId: 608 (required)

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
                    "trackingParameter": "cid"
                }
            }
        }

+ Response 200 (application/json)

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
                        "trackingParameter": "cid"
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
                            "trackingParameter": "cid"
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
                    "trackingParameter": "cid"
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
                        "trackingParameter": "cid"
                    }
                }
            }
        }



## Campaign Budgets [/rest/v1/campaigns/{campaignId}/budgets/]
<a name="budget"></a>

Each budget item is part of a [Credit Item](#credit) and allows a campaign
to spend a portion of the credit.

A campaign needs at least one active budget associated with it before its
Ad Groups can be started.

Property  | Type            | Description                                      | Create   | Update
----------|-----------------|--------------------------------------------------|----------|-----------|
id        | string          | the budget'id                                    | N/A      | read only
creditId  | string          | id of the credit this budget is part of          | required | read only
amount    | [money](#money) | total amount allocated by the budget             | required | optional
startDate | date            | budget start date, must be in the future         | required | optional
endDate   | date            | budget end date, must end before the credit ends | required | optional
state     | string          | budget state, ACTIVE/PENDING/INACTIVE/DEPLETED   | N/A      | read only
spend     | [money](#money) | the amount of the budget already spent           | N/A      | read only
available | [money](#money) | the amount of the budget still available         | N/A      | read only

### List campaign budgets [GET /rest/v1/campaigns/{campaignId}/budgets/]

+ Parameters
    + campaignId: 608 (required)

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

### Create a new campaign budget [POST /rest/v1/campaigns/{campaignId}/budgets/]

+ Parameters
    + campaignId: 608 (required)

+ Request (application/json)

        {
            "creditId": "861",
            "amount": "600",
            "startDate": "2016-01-01",
            "endDate": "2016-01-31"
        }

+ Response 201 (application/json)

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


### Get a campaign budget [GET /rest/v1/campaigns/{campaignId}/budgets/{budgetId}]

+ Parameters
    + campaignId: 608 (required)
    + budgetId: 1910 (required)

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


### Edit a campaign budget [PUT /rest/v1/campaigns/{campaignId}/budgets/{budgetId}]

+ Parameters
    + campaignId: 608 (required)
    + budgetId: 1910 (required)

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

## Campaign goals [/rest/v1/campaigns/{campaignId}/goals/]
<a name="goal"></a>

Campaign goals give Zemanta's intelligent campaign automation feature Autopilot
data to help optimize your campaign for optimal results.

A campaign needs at least one goal associated with it before any of its
Ad Groups can be started.

Property        | Type                  | Description                   | Create | Update |
----------------|-----------------------|-------------------------------|--------|--------|
id              | string                | the campaign goal's id        | N/A | read only
type            | [enum](#goal-type)    | type of the goal | required | read only
value           | string (decimal)      | value to optimize for         | required | optional
primary         | boolean | Is this goal primary? There can only be one primary goal per campaign. If a primary goal already exists and you create a new primary goal, the old goal will no longer be primary.                                     | required | optional
conversionGoal  | [conversion goal](#conversion-goal) | conversion goal | optional | optional

<a name="conversion-goal"></a>
#### Conversion Goals

<!-- TODO: explain conversion goals -->

Property         | Type                          | Description                 | Create   | Update
-----------------|-------------------------------|-----------------------------|----------|-----------|
type             | [enum](#conversion-goal-type) | conversion goal type        | required | read only
name             | string                        | name of the conversion goal | required | read only
conversionWindow | [enum](#conversion-window)    | conversion goal type        | required | read only
goalId           | string                        | goal id                     | required | optional
pixelUrl         | url                           | pixel url, if applicable    | optional | optional


### List campaign goals [GET /rest/v1/campaigns/{campaignId}/goals/]

+ Parameters
    + campaignId: 608 (required)

+ Response 200 (application/json)

        {
            "data": [
                {
                    "id": "1238",
                    "type": "TIME_ON_SITE",
                    "primary": true,
                    "conversionGoal": {
                        "type": "PIXEL",
                        "name": "My conversion goal",
                        "conversionWindow": "LEQ_7_DAYS",
                        "goalId": "mygoal",
                        "pixelUrl": "http://example.com/mypixel1"
                    }
                }
            ]
        }
        
### Add a campaign goal [POST /rest/v1/campaigns/{campaignId}/goals/]

+ Parameters
    + campaignId: 608 (required)

+ Request (application/json)

        {
            "type": "CPA",
            "value": "30.0",
            "primary": true,
            "conversionGoal": {
                "type": "GA",
                "name": "My conversion goal 2",
                "conversionWindow": "LEQ_7_DAYS",
                "goalId": "mygoal",
                "pixelUrl": "http://example.com/mypixel1"
            }
        }

+ Response 201 (application/json)

        {
            "data": {
                "id": "1239",
                "type": "CPA",
                "value": "30.0",
                "primary": true,
                "conversionGoal": {
                    "type": "GA",
                    "name": "My conversion goal 2",
                    "conversionWindow": "LEQ_7_DAYS",
                    "goalId": "mygoal",
                    "pixelUrl": "http://example.com/mypixel1"
                }
            }
        }

### Modify a campaign goal [PUT /rest/v1/campaigns/{campaignId}/goals/{goalId}]

+ Parameters
    + campaignId: 608 (required)
    + goalId: 1238 (required)

+ Request (application/json)

        {
            "primary": true
        }
        
+ Response 200 (application/json)

        {
            "data": {
                "id": "1238",
                "type": "CPA",
                "primary": false,
                "conversionGoal": {
                    "type": "PIXEL",
                    "name": "My conversion goal",
                    "conversionWindow": "LEQ_7_DAYS",
                    "goalId": "mygoal",
                    "pixelUrl": "http://example.com/mypixel1"
                }
            }
        }

### Remove campaign goal [DELETE /rest/v1/campaigns/{campaignId}/goals/{goalId}]

+ Parameters
    + campaignId: 608 (required)
    + goalId: 1238 (required)

+ Response 204

            
# Group Ad Group Management

## Ad Groups [/rest/v1/adgroups/]

An Ad Group is a collection of Content Ads that has specific targeting settings.

Before any Ad Groups in the campaign can be activated, a campaign must
have at least one active [Budget](#budget) and at least one [Goal](#goal) associated.

Property     | Type                      | Description                                                                                                                      | Create   | Update
-------------|---------------------------|----------------------------------------------------------------------------------------------------------------------------------|----------|-----------|
id           | string                    | the ad group's id                                                                                                                | N/A      | read only
campaignId   | string                    | id of the campaign this ad group belongs to                                                                                      | required | read only
name         | string                    | the name of the ad group                                                                                                         | required | optional
state        | `ACTIVE` / `INACTIVE`     | Ad group state. Set to `ACTIVE` to activate the Ad Group and to `INACTIVE` to deactivate it.                                     | optional | optional
startDate    | string                    | start date of the ad group                                                                                                       | optional | optional
endDate      | string                    | End date of the ad group. Omit to leave it running until state is manually set to `INACTIVE`.                                    | optional | optional
startDate    | string                    | start date of the ad group                                                                                                       | optional | optional
maxCpc       | [money](#money)           | maximum CPC for this ad group                                                                                                    | optional | optional
targeting    | [targeting](#targeting)   | targeting settings                                                                                                               | optional | optional
dayparting   | [dayparting](#dayparting) | dayparting settings                                                                                                              | optional | optional
trackingCode | string                    | tracking codes appended to all content ads URLs ([more](http://help.zemanta.com/article/show/12985-tracking-parameters--macros)) | optional | optional
autopilot    | [autopilot](#autopilot)   | Zemanta Autopilot settings                                                                                                       | optional | optional

<a name="targeting"></a>
#### Targeting Settings

Targeting | Property | Property  | Type                                          | Description
----------|----------|-----------|-----------------------------------------------|---------------------------------------------------------------------------------------------|
devices   |          |           | array[[device](#device)]                      | A list of device types to target. If none specified, content is served to all device types.
geo       |          |           |
&nbsp;    | included |           |                                               |
&nbsp;    |          | countries | array[[country](#country)]                    | countries to target
&nbsp;    |          | regions   | array[[region](#region)]                      | regions to target
&nbsp;    |          | dma       | array[[DMA](#dma)]                            | DMA IDs to target
interest  |          |           |
&nbsp;    | included |           | array[[interestCategory](#interest-category)] | interest categories to target
&nbsp;    | excluded |           | array[[interestCategory](#interest-category)] | interest categories to avoid


<a name="dayparting"></a>
#### Dayparting

Dayparting structure is defined as a dictionary of days which point to a list of hours that are enabled in that day, eg. "monday" -> [0, 1, 2, 5]. 
This means that on monday bidding is enabled from 00:00 to 02:59 and from 5:00 to 5:59. 
The other value is "timezone" that defines in which timezone the hours are evaluated, eg. "timezone" -> "America/New_York". 
This value must be formatted according to the tz database (see https://en.wikipedia.org/wiki/Tz_database). If timezone isn't specified then user's timezone is used to resolve the hours.

Property  | Type                                                     | Description
----------|----------------------------------------------------------|-------------------------------------------------------------------------------------------------------------------|
sunday    | array[integer]                                           | active hours
monday    | array[integer]                                           | active hours
tuesday   | array[integer]                                           | active hours
wednesday | array[integer]                                           | active hours
thursday  | array[integer]                                           | active hours
friday    | array[integer]                                           | active hours
saturday  | array[integer]                                           | active hours
timezone  | [TZ timezone](https://en.wikipedia.org/wiki/Tz_database) | Timezone in which the hours are evaluated. If not specified, the timezone of the user being shown the ad is used.

<a name="autopilot"></a>
#### Zemanta Autopilot Settings

Get more information about Zemanta Autopilot in our [knowledge base](http://help.zemanta.com/article/show/12921-autopilot).

Property    | Type                                | Description
------------|-------------------------------------|------------------------|
state       | [autopilot state](#autopilot-state) | autopilot state
dailyBudget | dailyBudget                         | autopilot daily budget


### Get ad group details [GET /rest/v1/adgroups/{adGroupId}]

+ Parameters
    + adGroupId: 2040 (required)
    
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
                    "devices": ["DESKTOP", "TABLET"],
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
                    "state": "ACTIVE_CPC",
                    "dailyBudget": 100.0001
                },
                "dayparting": {
                    "monday": [0, 1, 2, 3],
                    "friday": [20, 21, 22, 23],
                    "timezone": "America/New_York"
                }
            }
        }


### Update ad group details [PUT /rest/v1/adgroups/{adGroupId}]

+ Parameters
    + adGroupId: 2040 (required)

+ Request (application/json)

        {
            "name": "My ad group 2",
            "state": "INACTIVE",
            "startDate": "2016-10-05",
            "endDate": "2016-11-05",
            "maxCpc": "0.25",
            "dailyBudget": "20.0",
            "targeting": {
                "devices": ["DESKTOP", "TABLET"],
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
                "state": "ACTIVE_CPC",
                "dailyBudget": "100.0001"
            },
            "dayparting": {
                "monday": [4, 5, 6, 7],
                "friday": [2, 3, 7, 8, 9, 10],
                "timezone": "Europe/Ljubljana"
            }
        }

+ Response 200 (application/json)

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
                    "state": "ACTIVE_CPC",
                    "dailyBudget": "100.0001"
                },
                "dayparting": {
                    "monday": [4, 5, 6, 7],
                    "friday": [2, 3, 7, 8, 9, 10],
                    "timezone": "Europe/Ljubljana"
                }
            }
        }

### List ad groups [GET /rest/v1/adgroups/{?campaignId}]

+ Parameters
    + campaignId: 608 (number) - Optional campaign ID

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
                        "devices": ["DESKTOP", "TABLET"],
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
                        "state": "ACTIVE_CPC",
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
            "state": "INACTIVE",
            "startDate": "2016-10-05",
            "endDate": "2016-11-05",
            "maxCpc": "0.25",
            "dailyBudget": "20.0",
            "targeting": {
                "devices": ["DESKTOP", "TABLET"],
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
                "state": "ACTIVE_CPC",
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
                "state": "INACTIVE",
                "startDate": "2016-10-05",
                "endDate": "2016-11-05",
                "maxCpc": "0.25",
                "dailyBudget": "20.0",
                "targeting": {
                    "devices": ["DESKTOP", "TABLET"],
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
                    "state": "ACTIVE_CPC",
                    "dailyBudget": "100.0001"
                },
                "dayparting": {
                    "monday": [4, 5, 6, 7],
                    "friday": [2, 3, 7, 8, 9, 10],
                    "timezone": "America/Los_Angeles"
                }
            }
        }

## Ad Group Sources [/rest/v1/adgroups/{adGroupId}/sources/]

Each Ad Group has specific configurable settings for each media source.
You can control whether the ad group is promoted on a given source, the
CPC you are willing to pay on that source and the daily budget you wish
to spend on that source.

Property    | Type                | Description
------------|---------------------|------------------------------------------------|
source      | string              | source identifier
state       | `ACTIVE`/`INACTIVE` | is ad group being promoted on the given source
cpc         | [money](#money)     | CPC for the given source
dailyBudget | [money](#money)     | daily budget for the given source

### Get ad group source settings [GET /rest/v1/adgroups/{adGroupId}/sources/]

+ Parameters
    + adGroupId: 2040 (required)

+ Response 200 (application/json)

        {
            "data": [
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

### Update ad group source settings [PUT /rest/v1/adgroups/{adGroupId}/sources/]

+ Parameters
    + adGroupId: 2040 (required)

+ Request (application/json)

        [
            {
                "source": "gumgum",
                "dailyBudget": "15.0",
                "cpc": "0.25"
            },
            {
                "source": "triplelift",
                "state": "INACTIVE"
            }
        ]
        

+ Response 200 (application/json)

        {
            "data": [
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
                    "state": "INACTIVE",
                    "cpc": "0.20",
                    "dailyBudget": "10.0"
                }
            ]
        }

## All Real-time bidding sources as one [/rest/v1/adgroups/{adGroupId}/sources/rtb/]

The sources you can promote your content on come in two flavours: real-time
bidding (RTB) and non-real-time bidding (Non-RTB) sources. RTB sources are all
sources except `yahoo`, `outbrain`, `instagram` and `facebook`.

In order to simplify manual source management (when not using Zemanta Autopilot),
you can use this special RTB settings endpoint, which allows you to group
all RTB sources together and treat them as a single source. This allows you to set
the state and daily budget of all RTB sources at once. The daily budget set by
this endpoint will be shared among all RTB sources.

Property     | Type                | Description
-------------|---------------------|---------------------------------------------------------------|
groupEnabled | boolean             | enable or disable treating all RTB sources as a single source
state        | `ACTIVE`/`INACTIVE` | the state of all RTB sources
dailyBudget  | [money](#money)     | daily budget shared among all RTB sources
        
### Get ad group source settings for All RTB sources as one [GET /rest/v1/adgroups/{adGroupId}/sources/rtb/]

+ Parameters
    + adGroupId: 2040 (required)

+ Response 200 (application/json)

        {
            "data": {
                "groupEnabled": true,
                "state": "ACTIVE",
                "dailyBudget": "50.00"
            }
        }
        
### Update ad group source settings for All RTB sources as one [PUT /rest/v1/adgroups/{adGroupId}/sources/rtb/]

+ Parameters
    + adGroupId: 2040 (required)

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

# Group Content Ad management

## Upload Content Ads [/rest/v1/contentads/batch/]

Content Ads are uploaded in batches. First, you create an upload batch with
the Content Ads you want to upload. Then, you poll the status of the batch
and the validation status of the individual Content Ads. If any of the Content
Ads in the batch fail the validation process, none of the Content Ads in the
batch will be accepted into the system.

If and when all the Content Ads in the batch pass the validation process, they
are accepted into the system.

<a name="content-ad"></a>
#### Content Ad

Property     | Type                      | Description                                                                                                                   | Create   | Update
-------------|---------------------------|-------------------------------------------------------------------------------------------------------------------------------|----------|-----------|
id           | string                    | the content ad's id                                                                                                           | N/A      | read only
adGroupId    | string                    | the id of the ad group this Content Ad belongs to                                                                             | N/A      | read only
state        | `ACTIVE`/`INACTIVE`       | the state of the Content Ad                                                                                                   | N/A      | optional
label        | string                    | free-form text label                                                                                                          | optional | read only
url          | string                    | landing url                                                                                                                   | required | read only
title        | string                    | title of the Content Ad                                                                                                       | required | read only
imageUrl     | string                    | URL of the Content Ad's image                                                                                                 | required | read only
imageCrop    | [image crop](#image-crop) | what strategy to use when cropping (most commonly `center` or `faces`, [more info](http://docs.imgix.com/apis/url/size/crop)) | required | read only
displayUrl   | string                    | the URL displayed with the Ad                                                                                                 | required | read only
brandName    | string                    | the brand name of the Content Ad                                                                                              | required | read only
description  | string                    | the description of the Content Ad                                                                                             | required | read only
callToAction | string                    | call to action, most commonly `Read more`                                                                                     | required | read only
trackerUrls  | array[string]             | tracker URLs                                                                                                                  | optional | read only

#### Upload Batch

Property           | Type                             | Description
-------------------|----------------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
id                 | string                           | id of the upload batch
status             | [batch status](#batch-status)    | status of the upload batch
validationStatus   | array[validation status]         | An array of validation statuses for each Content Ad uploaded in this batch. The statuses are in the same order as the ads were uploaded.
approvedContentAds | array[[Content Ad](#content-ad)] | An array that contains the uploaded Content Ads if/when all the ads pass the validation process. The Content Ads are in the same order as they were uploaded, but with added Zemanta IDs.


### Create a new content ad upload batch [POST /rest/v1/contentads/batch/{?adGroupId}]

+ Parameters
    + adGroupId: 2040 (required)

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


### Check content ad upload batch status [GET /rest/v1/contentads/batch/{batchId}]

+ Parameters
    + batchId: 1302 (required)

+ Response 200 (application/json)

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

## Manage content ads [/rest/v1/contentads/]

### List content ads [GET /rest/v1/contentads/{?adGroupId}]

+ Parameters
    + adGroupId: 2040 (number, required) - Ad group ID

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
                    "trackerUrls": ["https://example.com/t1", "https://example.com/t2"]
                }
            ]
        }
        

### Get content ad details [GET /rest/v1/contentads/{contentAdId}]

+ Parameters
    + contentAdId: 16805 (required)

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
                "trackerUrls": ["https://example.com/t1", "https://example.com/t2"]
            }
        }
        

### Edit a content ad [PUT /rest/v1/contentads/{contentAdId}]

+ Parameters
    + contentAdId: 16805 (required)

+ Request (application/json)

        {
            "state": "INACTIVE"
        }
        

+ Response 200 (application/json)

        {
            "data": {
                "id": "16805",
                "adGroupId": "2040",
                "state": "INACTIVE",
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
        }



# Group Publishers management

## Blacklisting [/rest/v1/adgroups/{adGroupId}/publishers/]

### Get publisher status [GET /rest/v1/adgroups/{adGroupId}/publishers/]

+ Parameters
    + adGroupId: 2040 (required)
    
+ Response 200 (application/json)

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

### Set publisher status [PUT /rest/v1/adgroups/{adGroupId}/publishers/]

+ Parameters
    + adGroupId: 2040 (required)

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
            }
        ]
    
+ Response 200 (application/json)

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
                "result": null
            }
        }
        

### Get report job status [GET /rest/v1/reports/{jobId}]

+ Parameters
    + jobId: 27 (required)

+ Response 200 (application/json)

        {
            "data": {
                "id": "27",
                "status": "DONE",
                "result": "https://z1-rest-reports.s3.amazonaws.com/KgrK55qCMO85v9JhHwCIv8kso2quYwEGV2MLpiVUgDVRDJm3HiGk1lWrOGfxJ7k2.csv"
            }
        }

# Group Additional Types

<a name="money"></a>
## Money

A string representing a decimal number. Example: `"15.48"`


# Group Constants reference

## Ad group / Content ad State

- `ACTIVE`
- `INACTIVE`

<a name="autopilot-state"></a>
## Autopilot State

- `ACTIVE_CPC` - Optimize Bids
- `ACTIVE_CPC_BUDGET` - Optimize Bids and Daily Budgets
- `INACTIVE` - Disabled


## Publishers

<a name="publishers-status"></a>
### Status
- `ENABLED`
- `BLACKLISTED`

<a name="publishers-level"></a>
### Level
- `ADGROUP`
- `CAMPAIGN`
- `ACCOUNT`

<a name="goal-type"></a>
## Campaign Goal KPIs
- `TIME_ON_SITE` -  Time on Site - Seconds
- `MAX_BOUNCE_RATE` -  Max Bounce Rate
- `PAGES_PER_SESSION` -  Pageviews per Visit
- `CPA` -  Cost per Acquisition
- `CPC` -  Cost per Click
- `NEW_UNIQUE_VISITORS` -  New Unique Visitors
- `CPV` -  Cost per Visit
- `CP_NON_BOUNCED_VISIT` -  Cost per Non-Bounced Visit

<a name="conversion-goal-type"></a>
### Conversion goal type
- `PIXEL` - Conversion Pixel
- `GA` - Google Analytics
- `OMNITURE` - Adobe Analytics

<a name="conversion-window"></a>
### Conversion window
- `LEQ_1_DAY` - 1 day
- `LEQ_7_DAYS` - 7 days
- `LEQ_30_DAYS` - 30 days
- `LEQ_90_DAYS` - 90 days

<a name="batch-status"></a>
## Content ad upload batch status
- `DONE`
- `FAILED`
- `IN_PROGRESS`
- `CANCELLED`

<a name="device"></a>
## Device targeting

- `DESKTOP`
- `TABLET`
- `MOBILE`

<a name="interest-category"></a>
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

<a name="dma"></a>
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
 
<a name="country"></a>
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
- `AR` - Argentina 〃
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
 
<a name="region"></a>
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







