FORMAT: 1A
HOST: https://oneapi.zemanta.com

# Zemanta API

This document describes the Zemanta One REST Campaign Management API.

The API enables [Zemanta](https://www.zemanta.com) clients to programmatically create and manage campaigns, ad groups and content ads using RESTful objects.
Custom performance reports are also available as part of the API.

In order to use Zemanta REST API, please contact your sales representative.

If you want to be notified of new features and maintenance windows, please join the [Zemanta API Announcements Mailing List](https://groups.google.com/forum/#!forum/zemanta-api-announcements/join).

Try our API by using our [Swagger UI](https://one.zemanta.com/swagger/) to make calls and get a response. Note that this is a live production API and calls will affect your account(s)
## Who should read this document?

This document is intended for programmers who are developing an integration with the Zemanta One system.
A prerequisite for working with Zemanta REST API is an understanding of HTTP and JSON.

# Group Technical Overview

## Entities

The diagram and the table below describe the objects this API deals with and the relationships between them.

![Entity Relation Diagram](https://s3.amazonaws.com/one-static.zemanta.com/rest-docs/ZemantaRESTAPIDiagram.png)

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
201         | Created      | Entity successfully created
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

## Pagination

Zemanta One API paginates list views using marker offset pagination by default.

By specifying the `offset` URL query parameter it is possible to use a simple limit offset pagination which might lead to slow responses with large lists.

### Marker Offset Pagination

The format for marker offset pagination URL is:

```
/rest/v1/{resourceListPath}/{?marker,limit}
```

Navigation through pages is done by two URL parameters:

* `marker`: the primary key of the last element in the previous page (the first page has `marker=0`)
* `limit`: maximum number of entries to return, up to `1000`, defaults to `100`

The response has the following content:

```
{
    "count": 1000,
    "next": "https://oneapi.zemanta.com/rest/v1/{resourceListPath}/?marker=200&limit=100",
    "data": []
}
```

### Limit Offset Pagination

The format for limit offset pagination URL is:

```
/rest/v1/{resourceListPath}/?offset{,limit}
```

Navigation through pages is done by two URL parameters:

* `offset`: the offset of starting element of the page in the list
* `limit`: maximum number of entries to return, up to `1000`, defaults to `100`

The response has the following content:

```
{
    "count": 1000,
    "next": "https://oneapi.zemanta.com/rest/v1/{resourceListPath}/?offset=200&limit=100",
    "previous": "https://oneapi.zemanta.com/rest/v1/{resourceListPath}/?offset=100&limit=100",
    "data": []
}
```

## Rate Limiting

Each Zemanta One user can perform a maximum of 20 requests per second to the Zemanta One API.
In case that limit is crossed, the API will start responding with HTTP status 429 (Too Many Requests).
We suggest the implementation of client side request rate limiting and graceful handling of HTTP status 429 responses. 


## Authentication

Zemanta REST API uses two-legged OAuth2 authentication using client credentials.
The client credentials are used to acquire an access token, which must
then be passed to all REST API calls as the header

```
Authorization: Bearer <access_token>
```

Access tokens are valid for 10 hours, after which a new access token must be obtained using the client credentials.
Please cache and reuse access tokens for the duration of their validity.


### Create client credentials

To create client credentials, first make sure you are logged in to Zemanta One. Then go to https://one.zemanta.com/o/applications/
and click the **New Application** button. Enter a name for your application, as shown in the image, and click the "Save" button.

![New application registration form](https://s3.amazonaws.com/one-static.zemanta.com/rest-docs/oauth2-1-scaled.jpg)

After you click the "Save" button, you will see the details of your newly created application credentials. The provided
Client ID and Client Secret are used for API authentication.

![Application credentials details](https://s3.amazonaws.com/one-static.zemanta.com/rest-docs/oauth2-2-scaled.jpg)

### Acquire a new authentication token [POST /o/token/]

This request requires you to use your client credentials (client ID and client secret)
as Basic HTTP Authentication. Manually, the header can be constructed as

```
Authorization: Basic base64(<client_id>:<client_secret>)
```

+ Request (application/x-www-form-urlencoded)
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


# Group Account Management

## Accounts [/rest/v1/accounts/]

Property  | Type                  | Description                                | Create   | Update
----------|-----------------------|--------------------------------------------|----------|-----------|
id        | string                | the account's id                           | N/A      | read only
agencyId  | string                | the agency's id                            | required | read only
name      | string                | the name of the account                    | required | optional
archived  | bool                  | Is the account archived? Set to `true` to archive an account and to `false` to restore it. | optional  | optional
targeting | [targeting](#account-targeting) | account targeting settings       | optional | optional
currency  | [Currency](#currency) | the account's currency (default is USD)    | optional | N\A
frequencyCapping | number | The maximum number of times ads from the account can be shown to a unique user in one day. | optional | optional
defaultIconUrl | string           | URL of a brand logo which will be placed in all creatives and served with ads where this is required by the publisher. Setting the brand logo for a specific creative can be done on the ad creative level. The minimum required size is 128x128 pixels and the required format is square (1:1). | required | optional
deliveryStatus | [deliveryStatus](#delivery-status) | Delivery status of the account. Set `includeDeliveryStatus` flag to `true` to get this information.| N/A      | read only

                        

<a name="account-targeting"></a>
#### Account Targeting Settings

Targeting        | Property | Property  | Type                                          | Description
-----------------|----------|-----------|-----------------------------------------------|---------------------------------------------------------------------------------------------|
publisherGroups  |          |           |                                               |
&nbsp;           | included |           | array[[publisherGroupId](#publishers-management-publisher-groups)]   | whitelisted publisher group IDs
&nbsp;           | excluded |           | array[[publisherGroupId](#publishers-management-publisher-groups)]   | blacklisted publisher group IDs


### Get account details [GET /rest/v1/accounts/{accountId}{?includeDeliveryStatus}]

+ Parameters
    + accountId: 186 (required)
    + includeDeliveryStatus: true (bool, optional)
        + Default: false

+ Response 200 (application/json)

    + Attributes (AccountResponse)


### Update account details [PUT /rest/v1/accounts/{accountId}]

+ Parameters
    + accountId: 186 (required)

+ Request (application/json)

    + Attributes (AccountWithoutIds)

+ Response 200 (application/json)

    + Attributes (AccountResponse)

### List accounts [GET /rest/v1/accounts/{?includeArchived,includeDeliveryStatus}]

+ Parameters
    + includeArchived (bool, optional) - Set to true to retrieve archived accounts.
        + Default: false
    + includeDeliveryStatus: true (boolean, optional)
        + Default: false

+ Response 200 (application/json)

    + Attributes (AccountListResponse)


### Create a new account [POST /rest/v1/accounts/]


+ Request (application/json)

    + Attributes (AccountWithoutIds)
        - `agencyId`: `1` (string)

+ Response 201 (application/json)

    + Attributes (AccountResponse)


## Account Credit [/rest/v1/accounts/{accountId}/credits/]
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
currency  | [Currency](#currency) | the credit's currency


### Get credit item for account [GET /rest/v1/accounts/{accountId}/credits/{creditId}]

+ Parameters
    + accountId: 186 (required)
    + creditId: 861 (required)

+ Response 200 (application/json)

        {
            "data": {
                "id":"861",
                "startDate": "2016-01-01",
                "endDate": "2016-11-05",
                "createdOn": "2014-06-04",
                "total": "1000.0000",
                "allocated": "400.0000",
                "available": "600.0000",
                "currency": "EUR"
            }
        }


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
                    "available": "600.0000",
                    "currency": "EUR"
                }
            ]
        }


## Pixels [/rest/v1/accounts/{accountId}/pixels/]

Zemanta's pixels allow you to report conversions, build audiences and get insights about how people use your website.
Pixels need to be properly placed in order to measure goals effectively. We recommend placing your pixel on the confirmation page
which is shown to a person after the desired action is performed. 

Property        | Type            | Description                                                                           | Create    | Update  
----------------|-----------------|---------------------------------------------------------------------------------------|-----------|-----------
id              | string          | ID of the pixel                                                                       | N/A       | read only        
accountId       | string          | ID of the account                                                                     | read only | read only       
name            | string          | name of the pixel                                                                     | required  | read only        
archived        | bool            | Is the pixel archived? Set to `true` to archive a pixel and to `false` to restore it. | optional  | optional        
audienceEnabled (deprecated) | bool            | Is the pixel used for building custom audiences? Set to `true` to enable it. Can not be disabled once enabled. Only one pixel can be used for building custom audiences.  | read only  | read only       
url             | string          | URL of the pixel                                                                      | read only | read only
notes           | string          | a note describing where the pixel is placed on your website and what it tracks        | optional  | optional         
lastTriggered   | date            | date of when the pixel was last triggered                                             | read only | read only        
impressions     | number          | number of times the pixel was triggered yesterday                                     | read only | read only      


### Get pixel details [GET /rest/v1/accounts/{accountId}/pixels/{pixelId}]

+ Parameters
    + accountId: 186 (required)
    + pixelId: 123 (required)

+ Response 200 (application/json)

        {
            "data": {
                "id":"123",
                "accountId": "186",
                "name": "audience_pixel",
                "archived": false,
                "audienceEnabled": true,
                "url": "https://p1.zemanta.com/p/186/123/",
                "notes": "pixel used for testing",
                "lastTriggered": "2019-01-01T12:00:00.000000",
                "impressions": 100
            }
        }


### Update pixel [PUT /rest/v1/accounts/{accountId}/pixels/{pixelId}]

+ Parameters
    + accountId: 186 (required)
    + pixelId: 123 (required)

+ Request (application/json)

        {
            "archived": false,
            "audienceEnabled": true,
            "notes": "pixel used for audience testing"
        }

+ Response 200 (application/json)

        {
            "data": {
                "id":"123",
                "accountId": "186",
                "name": "audience_pixel",
                "archived": false,
                "audienceEnabled": true,
                "url": "https://p1.zemanta.com/p/186/123/",
                "notes": "pixel used for audience testing",
                "lastTriggered": "2019-01-01T12:00:00.000000",
                "impressions": 100
            }
        }

### List pixels [GET /rest/v1/accounts/{accountId}/pixels/]

+ Parameters
    + accountId: 186 (required)

+ Response 200 (application/json)

        {
            "data": [
                {
                    "id":"123",
                    "accountId": "186",
                    "name": "test_pixel",
                    "archived": false,
                    "audienceEnabled": true,
                    "url": "https://p1.zemanta.com/p/186/123/",
                    "notes": "pixel used for testing",
                    "lastTriggered": "2019-01-01T12:00:00.000000",
                    "impressions": 100
                }
            ]
        }

### Create new pixel [POST /rest/v1/accounts/{accountId}/pixels/]

+ Parameters
    + accountId: 186 (required)

+ Request (application/json)

        {
            "name": "test_pixel",
            "archived": false,
            "audienceEnabled": true,
            "notes": "pixel used for testing"
        }

+ Response 201 (application/json)

        {
            "data": {
                "id":"124",
                "accountId": "186",
                "name": "test_pixel",
                "archived": false,
                "audienceEnabled": true,
                "url": "https://p1.zemanta.com/p/186/124/",
                "notes": "pixel used for testing",
                "lastTriggered": null,
                "impressions": 0
            }
        }


## Audiences [/rest/v1/accounts/{accountId}/audiences/]

Custom audiences allow you to target your ads to a specific set of people with whom you have already established a relationship. Audiences can be defined by a combination of rules used to identify users who took specific actions on your website.

Property        | Type            | Description                                                                           | Create    | Update  
----------------|-----------------|---------------------------------------------------------------------------------------|-----------|-----------
id              | string          | ID of the audience                                                                    | N/A       | read only        
pixelId         | string          | ID of the pixel that is the source of this traffic                                    | required  | read only       
name            | string          | name of the audience                                                                  | required  | optional        
archived        | bool            | Is the audience archived? Set to `true` to archive an audience and to `false` to restore it. | optional  | optional        
ttl             | number          | The number of days people will remain in your audience after they've visited your website. People will be removed from your audience after the set time period unless they visit your website again. | required | read only        
rules           | [audience rule](#audience-rule) | Include traffic that meets the specified conditions.                  | required | read only        
createdDt       | date            | audience creation date                                                                | read only | read only      

<a name="audience-rule"></a>
#### Audience Rules

Choose how you want to add people to your audience. Include all of your website visitors or create rules that only add people visiting specific parts of your website. Audience can have multiple rules set. `CONTAINS` and `STARTS_WITH` rules can match multiple values separated by a comma. `STARTS_WITH` values need to be valid URLs.

Property         | Type                          | Description                 | Create    | Create (`VISIT`) | Update
-----------------|-------------------------------|-----------------------------|-----------|------------------|------------
type             | [enum](#audience-rule-type)   | rule type                   | required  | required         | read only
value            | string                        | rule value                  | required  | N/A              | read only


### Get audience details [GET /rest/v1/accounts/{accountId}/audiences/{audienceId}]

+ Parameters
    + accountId: 186 (required)
    + audienceId: 234 (required)

+ Response 200 (application/json)

        {
            "data": {
                "id":"234",
                "pixelId": "123",
                "name": "test_audience",
                "archived": false,
                "ttl": 7,
                "rules": [
                    {
                        "type": "CONTAINS",
                        "value": "these,are,all"
                    },
                    {
                        "type": "CONTAINS",
                        "value": "test,tags"
                    }
                ],
                "createdDt": "2019-01-01T12:00:00.000000"
            }
        }


### Update audience [PUT /rest/v1/accounts/{accountId}/audiences/{audienceId}]

+ Parameters
    + accountId: 186 (required)
    + audienceId: 234 (required)

+ Request (application/json)

        {
            "name": "new_audience",
            "archived": false
        }

+ Response 200 (application/json)

        {
            "data": {
                "id":"234",
                "pixelId": "123",
                "name": "new_audience",
                "archived": false,
                "ttl": 7,
                "rules": [
                    {
                        "type": "CONTAINS",
                        "value": "these,are,all"
                    },
                    {
                        "type": "CONTAINS",
                        "value": "test,tags"
                    }
                ],
                "createdDt": "2019-01-01T12:00:00.000000"
            }
        }

### List audiences [GET /rest/v1/accounts/{accountId}/audiences/{?includeArchived}]

+ Parameters
    + accountId: 186 (required)
    + includeArchived (bool, optional) - Set to true to retrieve archived audiences.
        + Default: false

+ Response 200 (application/json)

        {
            "data": [
                {
                    "id":"234",
                    "pixelId": "123",
                    "name": "test_audience",
                    "archived": false,
                    "ttl": 7,
                    "rules": [
                        {
                            "type": "STARTS_WITH",
                            "value": "http://test.com,https://urls.com"
                        }
                    ],
                    "createdDt": "2019-01-01T12:00:00.000000"
                }
            ]
        }

### Create new audience [POST /rest/v1/accounts/{accountId}/audiences/]

+ Parameters
    + accountId: 186 (required)

+ Request (application/json)

        {
            "pixelId": 123,
            "name": "test_audience",
            "archived": false,
            "ttl": 7,
            "rules": [
                {
                    "type": "VISIT"
                }
            ]

        }

+ Response 201 (application/json)

        {
            "data": {
                "id":"234",
                "pixelId": "123",
                "name": "new_audience",
                "archived": false,
                "ttl": 7,
                "rules": [
                    {
                        "type": "VISIT",
                        "value": ""
                    }
                ],
                "createdDt": "2019-01-01T12:00:00.000000"
            }
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
type      | [Campaign Type](#campaign-types) | The type of the campaign (the default is `CONTENT`) | optional | read only
iabCategory | [IAB category](#iab-categories) | IAB category of the campaign   | optional | optional
language  | [Language](#languages) | Language of the ads in the campaign       | optional | read only
archived  | bool                  | Is the Campaign archived? Set to `true` to archive a Campaign and to `false` to restore it. | optional | optional
autopilot | bool                  | Autopilot Budget optimization. [Read more](http://www.zemanta.com/blog/new-way-achieve-stronger-campaign-performance/). | optional | optional
tracking  | [tracking](#tracking) | tracking settings                          | optional | optional
targeting | [targeting](#campaign-targeting)   | campaign targeting settings   | optional | optional
frequencyCapping | number | The maximum number of times ads from the campaign can be shown to a unique user in one day. | optional | optional
deliveryStatus | [deliveryStatus](#delivery-status) | Delivery status of the campaign.  Set `includeDeliveryStatus` flag to `true` to get this information. | N/A      | read only


<a name="tracking"></a>
#### Tracking Settings

Postclick tracking integration can be set up for Google Analytics and Adobe Analytics.

Tracking | Property          | Type                                  | Description
---------|-------------------|---------------------------------------|--------------------------------------|
ga       |                   |                                       |
&nbsp;   | enabled           | boolean                               | Google Analytics integration enabled
&nbsp;   | type              | [GA Tracking Type](#ga-tracking-type) | Google Analytics tracking type
&nbsp;   | webPropertyId     | string                                | Google Analytics Web Property ID
adobe    |                   |                                       |
&nbsp;   | enabled           | boolean                               | Adobe Analytics integration enabled
&nbsp;   | trackingParameter | string                                | Adobe Analytics tracking parameter

<a name="campaign-targeting"></a>
#### Campaign Targeting Settings

Targeting        | Property | Property  | Type                                          | Description
-----------------|----------|-----------|-----------------------------------------------|---------------------------------------------------------------------------------------------|
devices (deprecated)         |          |           | array[[device](#device)]                      | A list of default device types that will be set on newly created ad groups.
environments (deprecated)     |          |           | array[[environment](#environment)]            | A list of default environments that will be set on newly created ad groups.
os (deprecated)               |          |           | array[[operatingSystem](#os-targeting)        | A list of default operating systems and operating system versions that will be se on newly created ad groups.
publisherGroups  |          |           |                                               |
&nbsp;           | included |           | array[[publisherGroupId](#publishers-management-publisher-groups)]   | whitelisted publisher group IDs
&nbsp;           | excluded |           | array[[publisherGroupId](#publishers-management-publisher-groups)]   | blacklisted publisher group IDs


### Get campaign details [GET /rest/v1/campaigns/{campaignId}{?includeDeliveryStatus}]

+ Parameters
    + campaignId: 608 (required)
    + includeDeliveryStatus: true (bool, optional)
        + Default: false

+ Response 200 (application/json)

    + Attributes (CampaignResponse)


### Update campaign details [PUT /rest/v1/campaigns/{campaignId}]

+ Parameters
    + campaignId: 608 (required)

+ Request (application/json)

    + Attributes (CampaignWithoutIds)

+ Response 200 (application/json)

    + Attributes (CampaignResponse)

### List ad groups [GET /rest/v1/adgroups/{?campaignId,accountId,includeArchived,includeDeliveryStatus}]

+ Parameters
    + accountId: 168 (number, optional) - Optional account ID.
    + campaignId: 608 (number, optional) - Optional campaign ID.
    + includeArchived (bool, optional) - Set to true to retrieve archived ad groups.
        + Default: false
    + includeDeliveryStatus: true (bool, optional)
        + Default: false

### List campaigns [GET /rest/v1/campaigns/{?includeArchived,onlyIds}]

+ Parameters
    + includeArchived (bool, optional) - Set to true to retrieve archived campaigns.
        + Default: false
    + onlyIds (bool, optional) - Set to true to retrieve only campaign IDs.
        + Default: false

+ Response 200 (application/json)

    + Attributes (CampaignListResponse)


### Create new campaign [POST /rest/v1/campaigns/]


+ Request (application/json)

    + Attributes (CampaignWithoutIds)
        - `accountId`: `186` (string)

+ Response 201 (application/json)

    + Attributes (CampaignResponse)


### Get campaign performance [GET /rest/v1/campaigns/{campaignId}/stats/{?from,to}]

This endpoint allows you to quickly view the performance of the campaign in a time span.

For more detailed reports, please use the [Reporting endpoints](#reporting).

+ Parameters
    + campaignId: 608 (required)
    + from: `2016-11-18` (required)
    + to: `2016-11-18` (required)

+ Response 200 (application/json)

        {
            "data": {
                "totalCost": "2240.56",
                "impressions": 4146083,
                "clicks": 14621,
                "cpc": "0.130"
            }
        }


## Campaign Budgets [/rest/v1/campaigns/{campaignId}/budgets/]
<a name="budget"></a>

Each budget item is part of a [Credit Item](#credit) and allows a campaign
to spend a portion of the credit.

A campaign needs at least one active budget associated with it before its
Ad Groups can be started.

More info available [here](http://help.zemanta.com/article/show/36733-budget-management).

Property  | Type            | Description                                      | Create   | Update
----------|-----------------|--------------------------------------------------|----------|-----------|
id        | string          | the budget's id                                    | N/A      | read only
creditId  | string          | id of the credit this budget is part of          | required | read only
amount    | [money](#money) | total amount allocated by the budget             | required | optional
margin    | string (decimal)| margin percentage fraction (e.g. 0.1)            | optional | optional
comment   | string          | free-form text field                             | optional | optional
startDate | date            | budget start date, must be in the future         | required | optional
endDate   | date            | budget end date, must end before the credit ends | required | optional
state     | string          | budget state, ACTIVE / PENDING / INACTIVE / DEPLETED | N/A  | read only
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
                    "creditId": "861",
                    "amount": "400",
                    "margin": "0.1",
                    "comment": "my budget",
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
            "margin": "0.1",
            "comment": "my budget",
            "startDate": "2016-01-01",
            "endDate": "2016-01-31"
        }

+ Response 201 (application/json)

        {
            "data": {
                "id": "1911",
                "amount": "600",
                "margin": "0.1",
                "comment": "my budget",
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
                "creditId": "861",
                "amount": "400",
                "margin": "0.1",
                "comment": "my budget",
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
                "creditId": "861",
                "amount": "800",
                "margin": "0.1",
                "comment": "my budget",
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

Property         | Type                          | Description                 | Create   | Create pixel goal | Update
-----------------|-------------------------------|-----------------------------|----------|-------------------|-----------|
type             | [enum](#conversion-goal-type) | conversion goal type        | required | required          | read only |
name             | string                        | name of the conversion goal | required | N/A               | read only |
conversionWindow | [enum](#conversion-window)    | conversion goal type        | required | required          | read only |
goalId           | string                        | goal id                     | N/A      | required          | read only |
pixelUrl         | url                           | pixel url, if applicable    | N/A      | N/A               | read only | 


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

When creating a pixel goal the `goalId` field should contain the ID of the pixel you want to use.  
The pixel ID can be found on your Account Pixels page (`https://one.zemanta.com/v2/pixels/account/<accountId>`) by clicking the Copy Tag button.  
Inside the tag you will find a URL of form `https://p1.zemanta.com/p/<accountId>/<pixelId>/`.  
Use the `pixelId` number when creating a new pixel (see example 2).

+ Parameters
    + campaignId: 608 (required)

+ Request (application/json)

        {
            "type": "CPA",
            "value": "30.0",
            "primary": false,
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

+ Request (application/json)

        {
            "type": "CPA",
            "value": "30.0",
            "primary": true,
            "conversionGoal": {
                "type": "PIXEL",
                "conversionWindow": "LEQ_7_DAYS",
                "goalId": "101"
            }
        }

+ Response 201 (application/json)

        {
            "data": {
                "id": "1234",
                "type": "CPA",
                "value": "30.0",
                "primary": true,
                "conversionGoal": {
                    "type": "PIXEL",
                    "name": "My pixel",
                    "conversionWindow": "LEQ_7_DAYS",
                    "goalId": "101",
                    "pixelUrl": "https://p1.zemanta.com/p/1/4321/"
                }
            }
        }

### Get campagin goal details [GET /rest/v1/campaigns/{campaignId}/goals/{goalId}]

+ Parameters
    + campaignId: 608 (required)
    + goalId: 1239 (required)

+ Response 200 (application/json)

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
    + goalId: 1239 (required)

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

Property     | Type                      | Description                                                                                                                        | Create   | Update
-------------|---------------------------|------------------------------------------------------------------------------------------------------------------------------------|----------|-----------|
id           | string                    | the ad group's id                                                                                                                  | N/A      | read only
campaignId   | string                    | id of the campaign this ad group belongs to                                                                                        | required | read only
name         | string                    | the name of the ad group                                                                                                           | required | optional
state        | `ACTIVE` / `INACTIVE`     | Ad group state. Set to `ACTIVE` to activate the Ad Group and to `INACTIVE` to deactivate it.                                       | optional | optional
archived     | bool                      | Is the Ad Group archived? Set to `true` to archive an Ad Group and to `false` to restore it.                                       | optional | optional
startDate    | string                    | start date of the ad group                                                                                                         | optional | optional
endDate      | string                    | End date of the ad group. Omit to leave it running until state is manually set to `INACTIVE`.                                      | optional | optional
biddingType  | `CPC` / `CPM`             | Bidding type. Set to `CPC` to focus on the clicks that your ad receives or `CPM` to focus on impressions. Use the `bid` field to set the bid value. | optional | optional
bid | [money](#money)           | Bid value for this ad group. When ad group bid property is updated, source bid values are calculated using the existing source bid modifiers. | required | required
maxCpc (deprecated) | [money](#money)    | Maximum CPC for this ad group if autopilot is enabled and ad group's bid CPC value if autopilot is inactive. This property exists due to backwards compatibility, please use "bid" instead. | optional | optional
maxCpm (deprecated) | [money](#money)    | Maximum CPM for this ad group if autopilot is enabled and ad group's bid CPM value if autopilot is inactive. This property exists due to backwards compatibility, please use "bid" instead. | optional | optional
targeting    | [targeting](#targeting)   | targeting settings                                                                                                                 | optional | optional
dayparting   | [dayparting](#dayparting) | dayparting settings                                                                                                                | optional | optional
trackingCode | string                    | tracking codes appended to all content ads URLs ([more](http://help.zemanta.com/article/show/12985-tracking-parameters--macros))   | optional | optional
autopilot    | [autopilot](#autopilot)   | Zemanta Autopilot settings                                                                                                         | optional | optional
deliveryType | [delivery](#delivery)     | Delivery Type. Set to `STANDARD` to deliver ads throughout the day and to `ACCELERATED` to deliver ads as soon as possible.        | optional | optional
frequencyCapping | number | The maximum number of times ads from the ad group can be shown to a unique user in one day.                                                       | optional | optional
clickCappingDailyAdGroupMaxClicks | number | Limit number of clicks you want to reach daily within the ad group. Once Zemanta hits the maximum number of clicks you set it will stop spending for the rest of the day. | optional | optional
deliveryStatus | [deliveryStatus](#delivery-status) | Delivery status of the ad group.  Set `includeDeliveryStatus` flag to `true` to get this information.                   | N/A      | read only


<a name="targeting"></a>
#### Targeting Settings

Targeting        | Property | Property   | Type                                                                 | Description
-----------------|----------|------------|----------------------------------------------------------------------|---------------------------------------------------------------------------------------------|
devices          |          |            | array[[device](#device)]                                             | A list of device types to target. If none specified, content is served to all device types.
environments     |          |            | array[[environment](#environment)]                                   | A list of environments to target. If none specified, content is served to all environments.
os               |          |            | array[[operatingSystem](#os-targeting)]                              | A list of operating systems and their versions to target. If none specified, content is served to any operating system or version.
geo              |          |            |
&nbsp;           | included |            |                                                                      |
&nbsp;           |          | countries  | array[[country](#country)]                                           | countries to target
&nbsp;           |          | regions    | array[[region](#region)]                                             | regions to target
&nbsp;           |          | dma        | array[[DMA](#dma)]                                                   | DMA IDs to target
&nbsp;           |          | cities     | array[[City](#city)]                                                 | cities to target
&nbsp;           |          | postalCodes| array[[PostalCode](#postalcode)]                                     | postal codes to target
&nbsp;           | excluded |            |                                                                      |
&nbsp;           |          | countries  | array[[country](#country)]                                           | countries to target
&nbsp;           |          | regions    | array[[region](#region)]                                             | regions to target
&nbsp;           |          | dma        | array[[DMA](#dma)]                                                   | DMA IDs to target
&nbsp;           |          | cities     | array[[City](#city)]                                                 | cities to target
&nbsp;           |          | postalCodes| array[[PostalCode](#postalcode)]                                     | postal codes to target
interest         |          |            |
&nbsp;           | included |            | array[[interestCategory](#interest-category)]                        | interest categories to target
&nbsp;           | excluded |            | array[[interestCategory](#interest-category)]                        | interest categories to avoid
publisherGroups  |          |            |                                                                      |
&nbsp;           | included |            | array[[publisherGroupId](#publishers-management-publisher-groups)]   | whitelisted publisher group IDs
&nbsp;           | excluded |            | array[[publisherGroupId](#publishers-management-publisher-groups)]   | blacklisted publisher group IDs
audience         |          |            | [audienceTargetingExpression](#audience-targeting-expression)        | audience targeting expression
customAudiences  |          |            |                                                                      |
&nbsp;           | included |            | array[customAudienceId]                                              | IDs of custom audiences to target
&nbsp;           | excluded |            | array[customAudienceId]                                              | IDs of custom audiences to avoid
retargetingAdGroups |       |            |                                                                      |
&nbsp;           | included |            | array[adGroupId]                                                     | IDs of ad groups to retarget
&nbsp;           | excluded |            | array[adGroupId]                                                     | IDs of ad groups to avoid
browsers         |          |            |                                                                      |
&nbsp;           | included |            | array[[browserFamily](#browser-targeting-settings)]                  | A list of browsers to target. If none specified, content is served to all browsers.
&nbsp;           | excluded |            | array[[browserFamily](#browser-targeting-settings)]                  | A list of browsers to target. If none specified, content is served to all browsers.
connectionType   |          |            | array[[connectionType](#connection-type)]                            | A list of connection types to target. If none specified, content is served to all connection types.

<a name="os-targeting"></a>
#### Operating System Targeting Settings
Property | Property | Type        | Description
---------|----------|-------------|---------------------------------------------------------------------------------------------------|
name     |          | [os](#os)   | Operating system.
version  |          |             | Operating system version. If none specified all versions are targeted.
&nbsp;   | min      | [osv](#osv) | Minimum version. If none specified, any version that is lower than maximum version is targeted.
&nbsp;   | max      | [osv](#osv) | Maximum version. If none specified, any version that is greater than minimum version is targeted.

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

<a name="audience-targeting-expression"></a>
#### Audience Targeting

An Audience Targeting expression is an object containing a single property. The name of the property represents the operator, while its value is an array representing the subexpression(s).
A subexpression can be either a nested Audience Targeting expression or a [Category](#audience-targeting-category) object.

Valid operators are `AND`,  `OR` and `NOT`. `NOT` has to have exactly one nested subexpression in the child array.

Example Audience Targeting expression:

```json
{
    "AND": [
        {
            "OR": [
                {
                    "category": "bluekai:839868"
                },
                {
                    "category": "bluekai:763921"
                }
            ]
        },
        {
            "NOT": [
                {
                    "category": "bluekai:839918"
                }
            ]
        }
    ]
}
```

<a name="audience-targeting-category"></a>
##### Audience Targeting Category

Audience targeting subexpressions can either be a nested audience targeting expressions or a leaf category node.

Property | Type    | Description
---------|---------|-------------------------
category | string  | Composed of two parts - the data provider and category id separated by `:`. (E.g. `bluekai:671901`)

Currently the only supported provider is `bluekai`. See [BlueKai Taxonomy API](#utilities-bluekai-taxonomy) for a list of all available
BlueKai categories.

<a name="autopilot"></a>
#### Zemanta Autopilot Settings

Get more information about Zemanta Autopilot in our [knowledge base](http://help.zemanta.com/article/show/12921-autopilot).

In order to set Autopilot state to `ACTIVE_CPC_BUDGET` [all real-time bidding sources](#all-rtb-as-one)
 `groupEnabled` setting has to be set to `true`.

Property          | Type                                | Description
------------------|-------------------------------------|---------------------
state             | [autopilot state](#autopilot-state) | autopilot state
dailyBudget       | dailyBudget                         | autopilot daily budget
maxBid            | [money][#money]                     | the maximum allowed bid for autopilot

<a name="browser-targeting-settings"></a>
#### Browser Targeting Settings
Property | Type                                | Description
---------|-------------------------------------|---------------------------------------------------------------------------------------------------|
family   | [browser](#browser)                 | Browser family



### Get ad group details [GET /rest/v1/adgroups/{adGroupId}{?includeDeliveryStatus}]

+ Parameters
    + adGroupId: 2040 (required)
    + includeDeliveryStatus: true (bool, optional)
        + Default: false

+ Response 200 (application/json)
    + Attributes (AdGroupResponse)


### Update ad group details [PUT /rest/v1/adgroups/{adGroupId}]

+ Parameters
    + adGroupId: 2040 (required)

+ Request (application/json)

    + Attributes (AdGroupWithoutIds)

+ Response 200 (application/json)

    + Attributes (AdGroupResponse)

### List ad groups [GET /rest/v1/adgroups/{?campaignId,accountId,includeArchived,includeDeliveryStatus}]

+ Parameters
    + accountId: 168 (number, optional) - Optional account ID.
    + campaignId: 608 (number, optional) - Optional campaign ID.
    + includeArchived (bool, optional) - Set to true to retrieve archived ad groups.
        + Default: false
    + includeDeliveryStatus: true (bool, optional)
        + Default: false

+ Response 200 (application/json)

    + Attributes (AdGroupListResponse)


### Create new ad group [POST /rest/v1/adgroups/]

+ Request (application/json)

    + Attributes
        - `campaignId`: `608` (string)
        - Include AdGroupWithoutIds

+ Response 201 (application/json)

    + Attributes (AdGroupResponse)

<a name="ad-group-sources"></a>
## Ad Group Sources [/rest/v1/adgroups/{adGroupId}/sources/]

Each Ad Group has specific configurable settings for each media source.
You can control whether the ad group is promoted on a given source, the
CPC you are willing to pay on that source and the daily budget you wish
to spend on that source.

Property    | Type                | Description
------------|---------------------|-------------------------------------------------------------|
source      | string              | source identifier
state       | `ACTIVE`/`INACTIVE` | is ad group being promoted on the given source
cpc (deprecated) | [money](#money)     | CPC for the given source. This property is deprecated, please use ad group bid property and source bid modifiers instead.
cpm (deprecated) | [money](#money)     | CPM for the given source (when ad group biddingType is CPM). This property is deprecated, please use ad group bid property and source bid modifiers instead.
dailyBudget | [money](#money)     | Daily budget for the given source. Can not be updated when [all real-time sources as one](#all-rtb-as-one) setting is enabled.

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
                    "cpm": null,
                    "dailyBudget": "10.0"
                },
                {
                    "source": "gumgum",
                    "state": "ACTIVE",
                    "cpc": "0.20",
                    "cpm": null,
                    "dailyBudget": "10.0"
                },
                {
                    "source": "triplelift",
                    "state": "ACTIVE",
                    "cpc": "0.20",
                    "cpm": null,
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
                    "cpm": null,
                    "dailyBudget": "10.0"
                },
                {
                    "source": "gumgum",
                    "state": "ACTIVE",
                    "cpc": "0.25",
                    "cpm": null,
                    "dailyBudget": "15.0"
                },
                {
                    "source": "triplelift",
                    "state": "INACTIVE",
                    "cpc": "0.20",
                    "cpm": null,
                    "dailyBudget": "10.0"
                }
            ]
        }

### Add a new ad group source [POST /rest/v1/adgroups/{adGroupId}/sources/]

+ Parameters
    + adGroupId: 2040 (required)


+ Request (application/json)

        {
            "source": "adiant",
            "state": "ACTIVE",
            "dailyBudget": "15.0",
            "cpc": "0.25"
        }

+ Response 200 (application/json)

        {
            "data": {
                "source": "adiant",
                "state": "ACTIVE",
                "cpc": "0.25",
                "cpm": null,
                "dailyBudget": "15.0"
            }
        }

## All Real-time bidding sources as one [/rest/v1/adgroups/{adGroupId}/sources/rtb/]
<a name="all-rtb-as-one"></a>

The sources you can promote your content on come in two flavours: real-time
bidding (RTB) and non-real-time bidding (Non-RTB) sources. RTB sources are all
sources except `yahoo` (US clients only) and `outbrain` (deprecated, please use `outbrainrtb`).

In order to simplify manual source management (when not using Zemanta Autopilot),
you can use this special RTB settings endpoint, which allows you to group
all RTB sources together and treat them as a single source. This allows you to set
the state and daily budget of all RTB sources at once. The daily budget set by
this endpoint will be shared among all RTB sources. Daily budget for non-RTB sources
must still be set through the [Ad Group Sources](#ad-group-sources) endpoint.

This setting has to be enabled in order to be able to set [autopilot](#autopilot)
state to `ACTIVE_CPC_BUDGET`.

Property     | Type                | Description
-------------|---------------------|---------------------------------------------------------------|
groupEnabled | boolean             | enable or disable treating all RTB sources as a single source
state        | `ACTIVE`/`INACTIVE` | the state of all RTB sources
cpc          | [money](#money)     | CPC for all RTB sources
cpm          | [money](#money)     | CPM for all RTB sources (when ad group biddingType is CPM)
dailyBudget  | [money](#money)     | Daily budget shared among all RTB sources. Can not be updated when [all real-time sources as one](#all-rtb-as-one) setting is disabled.

### Get ad group source settings for All RTB sources as one [GET /rest/v1/adgroups/{adGroupId}/sources/rtb/]

+ Parameters
    + adGroupId: 2040 (required)

+ Response 200 (application/json)

        {
            "data": {
                "groupEnabled": true,
                "state": "ACTIVE",
                "cpc": "0.25",
                "cpm": null,
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

## Bid Modifiers [/rest/v1/adgroups/{adGroupId}/bidmodifiers/]
<a name="bid-modifiers"></a>

Bid modifiers enable modifying the bidding price for an ad group according to the desired parameters. The modified CPC or CPM bid value is calculated in the following way: `modifiedBidValue = bidValue * modifier`. A bid request can match multiple bid modifiers with different types (for example `DEVICE`, `OPERATING_SYSTEM` and `COUNTRY`). In that case the modified bid value is calculated by multiplying all matching bid modifier values: `modifiedBidValue = bidValue * modifier1 * modifier2 * modifier3`. The allowed `modifier` values are limited to the interval between `0.01` and `11.0`.

| Property   | Type   | Description                                                                                                                                                            | Create   | Update    |
|-----------|-------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------|----------|-----------|
| id         | string | the id of bid modifier                                                                                                                                                 | N/A      | read only |
| type       | string | the [type](#bid-modifier-types) of bid modifier                                                                                                                        | required | optional  |
| sourceSlug | string | this value is always an empty string, except for the `PUBLISHER` and `PLACEMENT` type bid modifiers where it contains the source slug of the source it targets (for a given publisher) | optional | optional  |
| target     | string | a string representing the target of bid modifier                                                                                                                       | required | optional  |
| modifier   | number | a floating point factor for bidding price calculation                                                                                                                  | required | required  |

<a name="bid-modifier-types"></a>
#### Bid Modifier Types

The following bid modifier types are supported:

| Type             | Description                                                               | Allowed Values                        |
|-----------------|----------------------------------------------------------------------------|---------------------------------------|
| AD               | Modifies the bidding price for a specific content ad.                     | the ID of the content ad as a string  |
| PUBLISHER        | Modifies the bidding price for a specific source at a specific publisher. | the domain name of the publisher      |
| PLACEMENT        | Modifies the bidding price for a specific placement at a specific publisher and source combination.       | a string of the form `<publisher domain name>__<source id>__<placement id>` |
| SOURCE           | Modifies the bidding price for a specific source.                         | the source slug      |
| DEVICE           | Modifies the bidding price for a specific device type.                    | see [Device targeting](#device)       |
| OPERATING_SYSTEM | Modifies the bidding price for a specific operating system.               | see [Operating system targeting](#os) |
| ENVIRONMENT      | Modifies the bidding price for a specific add environment.                | see [Environment targeting](#environment) |
| COUNTRY          | Modifies the bidding price for a specific country.                        | see [Country](#country)               |
| STATE            | Modifies the bidding price for a specific state or region.                | see [State / Region](#region)         |
| DMA              | Modifies the bidding price for a specific DMA.                            | see [DMA](#dma)                       |
| DAY_HOUR         | Modifies the bidding price for a specific day and hour combination.       | see [DAY HOUR](#day_hour)             |

### Get bid modifiers for an ad group [GET /rest/v1/adgroups/{adGroupId}/bidmodifiers/{?type}]

+ Parameters
    + adGroupId: 2040 (required)
    + type (string, optional)
        + filter results by [bid modifier type](#bid-modifier-types)

+ Response 200 (application/json)

        {
            "data": [
                {
                    "id": "1234",
                    "type": "PUBLISHER",
                    "sourceSlug": "triplelift",
                    "target": "www.slader.com",
                    "modifier": 1.01
                },
                {
                    "id": "1235",
                    "type": "DEVICE",
                    "sourceSlug": "",
                    "target": "MOBILE",
                    "modifier": 0.99
                },
                {
                    "id": "1236",
                    "type": "AD",
                    "sourceSlug": "",
                    "target": "16805",
                    "modifier": 1.20
                },
                {
                    "id": "1237",
                    "type": "PLACEMENT",
                    "sourceSlug": "outbrainrtb",
                    "target": "www.orange.fr__85__00000000-0049-c63d-0000-000000000069",
                    "modifier": 1.02
                }
            ]
        }

### Add bid modifier for an ad group [POST /rest/v1/adgroups/{adGroupId}/bidmodifiers/]

+ Parameters
    + adGroupId: 2040 (required)

+ Request (application/json)

        {
            "type": "COUNTRY",
            "sourceSlug": "",
            "target": "US",
            "modifier": 1.5
        }

+ Response 201 (application/json)

        {
            "data": {
                "id": "1245",
                "type": "COUNTRY",
                "sourceSlug": "",
                "target": "US",
                "modifier": 1.5
            }
        }

### Bulk add or edit bid modifiers for an ad group [PUT /rest/v1/adgroups/{adGroupId}/bidmodifiers/]

Use for adding or editing multiple bid modifiers at the same time.

+ Parameters
    + adGroupId: 2040 (required)

+ Request (application/json)

        [
            {
                "type": "COUNTRY",
                "sourceSlug": "",
                "target": "US",
                "modifier": 1.5
            },
            {
                "type": "DEVICE",
                "sourceSlug": "",
                "target": "TABLET",
                "modifier": 1.6
            }
        ]

+ Response 200 (application/json)

        {
            "data": [
                {
                    "type": "COUNTRY",
                    "sourceSlug": "",
                    "target": "US",
                    "modifier": 1.5
                },
                {
                    "type": "DEVICE",
                    "sourceSlug": "",
                    "target": "TABLET",
                    "modifier": 1.6
                }
            ]
        }

### Delete bid modifiers for an ad group [DELETE /rest/v1/adgroups/{adGroupId}/bidmodifiers/]

A list of Bid Modifier IDs has to be included in request body to delete certain Bid Modifiers belonging to an Ad Group.

+ Parameters
    + adGroupId: 2040 (required)
    
+ Request (application/json)

        [
            {"id": 1240},
            {"id": 1241}
        ]

+ Response 204 (application/json)

        {}

### Get a bid modifier for an ad group [GET /rest/v1/adgroups/{adGroupId}/bidmodifiers/{bidModifierId}]

+ Parameters
    + adGroupId: 2040 (required)
    + bidModifierId: 1235 (required)

+ Response 200 (application/json)

        {
            "data": {
                "id": "1235",
                "type": "DEVICE",
                "sourceSlug": "",
                "target": "MOBILE",
                "modifier": 0.99
            }
        }

### Update a bid modifier for an ad group [PUT /rest/v1/adgroups/{adGroupId}/bidmodifiers/{bidModifierId}]

Only the `modifier` value can be changed for an existing Bid Modifier. It is not allowed to change the `type`, `sourceSlug` and `target` of an existing Bid Modifier, instead one can delete the existing Bid Modifier and create a new one with the desired values for these three attributes. However if `type`, `sourceSlug` and `target` values did not change, they can be provided along with the modified `modifier` value and will not cause a validation error.

+ Parameters
    + adGroupId: 2040 (required)
    + bidModifierId: 1235 (required)

+ Request (application/json)

        {
            "modifier": 0.98
        }

+ Response 200 (application/json)

        {
            "data": {
                "id": "1235",
                "type": "DEVICE",
                "sourceSlug": "",
                "target": "MOBILE",
                "modifier": 0.98
            }
        }

### Delete a bid modifier for an ad group [DELETE /rest/v1/adgroups/{adGroupId}/bidmodifiers/{bidModifierId}]

+ Parameters
    + adGroupId: 2040 (required)
    + bidModifierId: 1235 (required)

+ Response 204 (application/json)

        {}

## Realtime Statistics [/rest/v1/adgroups/{adGroupId}/realtimestats/]
<a name="realtime-stats"></a>

The realtime statistics endpoint shows the spend and clicks on a particular adgroup for the current day.
It is important to note that while the data here is updated in realtime, the data in the rest of the dashboard (including reporting)
is refreshed with about 4 hours of delay.

| Property   | Type            | Description                                                                    
|----------- |---------------- |-------------------------------------------------
| spend      | [money](#money) | the amount of the budget already spent                  
| clicks     | number          | 

### Get realtime statistics for an ad group [GET /rest/v1/adgroups/{adGroupId}/realtimestats/]

+ Parameters
    + adGroupId: 2040 (required)

+ Response 200 (application/json)

        {
            "data": {
                "spend": "1234.0000",
                "clicks": 4321
            }
        }

# Group Content Ad Management

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
iconUrl      | string                    | URL of a brand logo which will be served where this is required by the publisher. The minimum required size is 128x128 pixels and the required format is square (1:1). | required | read only
displayUrl   | string                    | the URL displayed with the Ad                                                                                                 | required | read only
brandName    | string                    | the brand name of the Content Ad                                                                                              | required | read only
description  | string                    | the description of the Content Ad                                                                                             | required | read only
callToAction | string                    | call to action, most commonly `Read more`                                                                                     | required | read only
trackerUrls (deprecated) | array[string] | tracker URLs                                                                                                                  | optional | read only
trackers     | array[[trackers](#trackers)]  | 3rd party image pixel or javascript trackers. Maximum of 3 trackers is allowed.                                           | optional | optional
videoAssetId | string                    | ID of the uploaded [video asset](#video-asset). Required on [video campaigns](#campaign-types).                               | optional | read only

#### Upload Batch

Property           | Type                             | Description
-------------------|----------------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
id                 | string                           | id of the upload batch
status             | [batch status](#batch-status)    | status of the upload batch
validationStatus   | array[validation status]         | An array of validation statuses for each Content Ad uploaded in this batch. The statuses are in the same order as the ads were uploaded.
approvedContentAds | array[[Content Ad](#content-ad)] | An array that contains the uploaded Content Ads if/when all the ads pass the validation process. The Content Ads are in the same order as they were uploaded, but with added Zemanta IDs.


<a name="trackers"></a>
#### Content Ad Trackers
Property         | Type                                     | Description                                                            | Create/Update |
-----------------|------------------------------------------|------------------------------------------------------------------------|---------------|
eventType        | [trackerEventType](#tracker-event-type)  | Tracker event type. VIEWABILITY type is available only with IMG method | required
method           | [trackerMethod](#tracker-method)         | Tracker method                                                         | required
url              | string                                   | URL of the tracker                                                     | required 
fallbackUrl      | string                                   | URL of a fallback image pixel tracker (only for JS method)             | optional
trackerOptional  | bool                                     | Allow Zemanta to purchase traffic where 3rd party tracking is not supported | optional


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
                "trackers": [
                        {
                            "eventType": "VIEWABILITY",
                            "method": "IMG",
                            "url": "https://example.com/t1",
                            "trackerOptional": true
                        },
                        {
                            "eventType": "IMPRESSION",
                            "method": "JS",
                            "url": "https://example.com/t2",
                            "fallbackUrl": "https://example.com/fallback",
                            "trackerOptional": true
                        }
                ]
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
                        "trackers": [
                            {
                                "eventType": "VIEWABILITY",
                                "method": "IMG",
                                "url": "https://example.com/t1",
                                "trackerOptional": true
                            },
                            {
                                "eventType": "IMPRESSION",
                                "method": "JS",
                                "url": "https://example.com/t2",
                                "fallbackUrl": "https://example.com/fallback",
                                "trackerOptional": true
                            }
                        ]
                    }
                ]
            }
        }

## Manage content ads [/rest/v1/contentads/]

### List content ads [GET /rest/v1/contentads/{?adGroupId,includeApprovalStatus}]

+ Parameters
    + adGroupId: 2040 (number, required) - Ad group ID
    + includeApprovalStatus: true (bool, optional)
        + default: false

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
                    "trackers": [
                        {
                            "eventType": "VIEWABILITY",
                            "method": "IMG",
                            "url": "https://example.com/t1",
                            "trackerOptional": true
                        },
                        {
                            "eventType": "IMPRESSION",
                            "method": "JS",
                            "url": "https://example.com/t2",
                            "fallbackUrl": "https://example.com/fallback",
                            "trackerOptional": true
                        }
                    ],
                    "approvalStatus": [{"slug": "source_slug", "status": "REJECTED", "reason": ""}]
                }
            ]
        }


### Get content ad details [GET /rest/v1/contentads/{contentAdId}{?includeApprovalStatus}]

+ Parameters
    + contentAdId: 16805 (required)
    + includeApprovalStatus: true (bool, optional)
        + default: false

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
                "trackers": [
                    {
                        "eventType": "VIEWABILITY",
                        "method": "IMG",
                        "url": "https://example.com/t1",
                        "trackerOptional": true
                    },
                    {
                        "eventType": "IMPRESSION",
                        "method": "JS",
                        "url": "https://example.com/t2",
                        "fallbackUrl": "https://example.com/fallback",
                        "trackerOptional": true
                    }
                ],
                "approvalStatus": [{"slug": "source_slug", "status": "REJECTED", "reason": ""}]
            }
        }


### Edit a content ad [PUT /rest/v1/contentads/{contentAdId}]

Note: At the moment only the `state`, `label` and `trackers` fields can be modified through the API.
As an alternative to editing other fields, please pause and/or archive the existing ads you want to change
and create new ones via the API.

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
                "trackers": [
                    {
                        "eventType": "VIEWABILITY",
                        "method": "IMG",
                        "url": "https://example.com/t1",
                        "trackerOptional": true
                    },
                    {
                        "eventType": "IMPRESSION",
                        "method": "JS",
                        "url": "https://example.com/t2",
                        "fallbackUrl": "https://example.com/fallback",
                        "trackerOptional": true
                    }
                ]
            }
        }


# Group Video Asset Management

## Upload Video Assets [/rest/v1/accounts/{accountId}/videoassets/]

Video assets are uploaded on the account level and separately from the ads that will later use them.
First you create a new video asset with a chosen method of upload. You can upload a video file or a VAST directly
or you can provide a URL from which the VAST will be downloaded.

When uploading a video file directly, you need to upload it to the provided upload URL and then poll
for the status as the video is processed asynchronously. Should any errors occur, the upload URL can be reused.
When the status changes to `READY_FOR_USE`, the `id` of the video asset can be used as a `videoAssetId`
when creating ads for a video campaign.

When uploading a VAST, the processing will trigger only when the first ad using this
`videoAssetId` is uploaded.

When uploading a VAST using `VAST_URL`, the VAST will be downloaded, processed and and ready for use immediately.

<a name='video-asset'></a>
#### Video Asset

Property     | Type                                  | Description                       | DIRECT_UPLOAD CREATE | VAST_UPLOAD CREATE | VAST_URL CREATE
-------------|---------------------------------------|-----------------------------------|----------------------|--------------------|------------------|
name         | string                                | full name of the video file       | required             | N/A                | N/A
status       | [upload status](#video-upload-status) | status of the uploaded video file | read only            | read only          | read only 
vastUrl      | string                                | URL of the VAST XML               | N/A                  | N/A                | required      
upload       | [upload](#video-upload)               | upload settings                   | required             | required           | required

<a name="video-upload"></a>
#### Video upload settings

Property | Type                                | Description                                                                                  | DIRECT_UPLOAD CREATE | VAST_UPLOAD CREATE | VAST_URL CREATE
---------|-------------------------------------|----------------------------------------------------------------------------------------------|----------------------|--------------------|------------------|
type     | [upload type](#video-upload-type)   | Video upload type. The required fields and steps may differ depending on the selected type.  | required             | required           | required
url      | string                              | URL where the video (`DIRECT_UPLOAD`) or VAST (`VAST_UPLOAD`) should be uploaded.            | read only            | read only          | N/A 

### Step 1: Create a new video asset [POST /rest/v1/accounts/{accountId}/videoassets/]

When uploading a video (`DIRECT_UPLOAD`) or a VAST (`VAST_UPLOAD`), the response will return a URL to which the video file (see example 1) or VAST (see example 2) has to be uploaded in the next step.

When using the `VAST_URL` option, the VAST will be downloaded, processed and ready for use immediately (see example 3).

+ Parameters
    + accountId: 186 (required)

+ Request (application/json)

        {
            "name": "test_video.mp4",
            "upload": {
                "type": "DIRECT_UPLOAD"
            }
        }

+ Response 200 (application/json)

        {
            "data": {
                "id": "video_asset_id",
                "account": "186",
                "type": "DIRECT_UPLOAD",
                "status": "NOT_UPLOADED",
                "statusMessage": "Video is not uploaded yet",
                "errorCode": null,
                "errorMessage": null,
                "name": "test_video.mp4",
                "upload": {
                    "type": "DIRECT_UPLOAD",
                    "url": "http://upload.com"
                },
                "previewUrl": null,
                "vastUrl": null
            }
        }

+ Request (application/json)

        {
            "upload": {
                "type": "VAST_UPLOAD"
            }
        }

+ Response 200 (application/json)

        {
            "data": {
                "id": "video_asset_id",
                "account": "186",
                "type": "VAST_UPLOAD",
                "status": "NOT_UPLOADED",
                "statusMessage": "Video is not uploaded yet",
                "errorCode": null,
                "errorMessage": null,
                "name": "",
                "upload": {
                    "type": "VAST_UPLOAD",
                    "url": "http://upload.com"
                },
                "previewUrl": null,
                "vastUrl": null
            }
        }

+ Request (application/json)

        {
            "upload": {
                "type": "VAST_URL"
            },
            "vastUrl": "http://upload.com/vast.xml"
        }

+ Response 200 (application/json)

        {
            "data": {
                "id": "video_asset_id",
                "account": "186",
                "type": "VAST_URL",
                "status": "READY_FOR_USE",
                "statusMessage": "Video is ready for use in creating ads",
                "errorCode": null,
                "errorMessage": null,
                "name": "",
                "previewUrl": "http://preview.com/",
                "vastUrl": "http://upload.com/vast.xml"
            }
        }

### Step 2: Upload the video file or VAST using the provided upload URL [GET /rest/v1/accounts/{accountId}/videoassets/{videoAssetId}]

```
curl -X PUT -H "Content-Type: application/octet-stream" -T "test_video.mp4" "http://upload.com"
```
```
curl -X PUT -H "Content-Type: text/xml" -d @vast.xml "http://upload.com"

```

+ Parameters
    + accountId: 186 (required)
    + videoAssetId: video_asset_id (required)

### Step 3: Check the video asset upload status [GET /rest/v1/accounts/{accountId}/videoassets/{videoAssetId}]

When uploading a video using `DIRECT_UPLOAD`, the video will be processed automatically and the above URL can be used to poll for the status of the video (see example 1).

When using the `VAST_UPLOAD` option, the VAST will not be processed (see example 2) until the first ad using it is uploaded (see example 3).

+ Parameters
    + accountId: 186 (required)
    + videoAssetId: video_asset_id (required)

+ Response 200 (application/json)

        {
            "data": {
                "id": "video_asset_id",
                "account": "186",
                "type": "DIRECT_UPLOAD",
                "status": "READY_FOR_USE",
                "statusMessage": "Video is ready for use in creating ads",
                "errorCode": null,
                "errorMessage": null,
                "name": "test_video.mp4",
                "previewUrl": "http://preview.com/",
                "vastUrl": null
            }
        }

+ Parameters
    + accountId: 186 (required)
    + videoAssetId: video_asset_id (required)

+ Response 200 (application/json)

        {
            "data": {
                "id": "video_asset_id",
                "account": "186",
                "type": "VAST_UPLOAD",
                "status": "NOT_UPLOADED",
                "statusMessage": "Video is not uploaded yet",
                "errorCode": null,
                "errorMessage": null,
                "name": "",
                "previewUrl": null,
                "vastUrl": null
            }
        }

+ Parameters
    + accountId: 186 (required)
    + videoAssetId: video_asset_id (required)

+ Response 200 (application/json)

        {
            "data": {
                "id": "video_asset_id",
                "account": "186",
                "type": "VAST_UPLOAD",
                "status": "READY_FOR_USE",
                "statusMessage": "Video is ready for use in creating ads",
                "errorCode": null,
                "errorMessage": null,
                "name": "",
                "previewUrl": "http://preview.com/",
                "vastUrl": "http://upload.com/vast/1234"
            }
        }


# Group Publishers Management

## Publisher Groups [/rest/v1/accounts/{accountId}/publishergroups/] ##
<a name='publisher-groups'></a>

Publisher Groups are named collections of publishers that can be referenced in Ad Group's `publisherGroups`
targeting section as whitelists or blacklists.
Publishers are represented as publisher domain (or name) and source pairs in the same manner as in publisher reports and blacklist management.

Property     | Type                | Description
-------------|---------------------|---------------------------------------------------------------|
id           | string              | ID of the publisher group
name         | string              | name of the publisher group
accountId    | string              | ID of the account this publisher group belongs to

### List publisher groups [GET /rest/v1/accounts/{accountId}/publishergroups/] ###

+ Parameters
    + accountId: 186 (required)

+ Response 200 (application/json)

        {
            "data": [
                {
                    "id": "111",
                    "accountId": "186",
                    "name": "Default whitelist"
                }
            ]
        }

### Create a new publisher group [POST /rest/v1/accounts/{accountId}/publishergroups/] ###

+ Parameters
    + accountId: 186 (required)

+ Request (application/json)

        {
            "name": "Secondary whitelist"
        }

+ Response 201 (application/json)

        {
            "data": {
                  "id": "153",
                  "accountId": "186",
                  "name": "Secondary whitelist"
            }
        }

### Get publisher group details [GET /rest/v1/accounts/{accountId}/publishergroups/{publisherGroupId}] ###

+ Parameters
    + accountId: 186 (required)
    + publisherGroupId: 153 (required)

+ Response 200 (application/json)

        {
            "data": {
                  "id": "153",
                  "accountId": "186",
                  "name": "Secondary whitelist"
            }
        }

### Edit a publisher group [PUT /rest/v1/accounts/{accountId}/publishergroups/{publisherGroupId}] ###

+ Parameters
    + accountId: 186 (required)
    + publisherGroupId: 153 (required)

+ Request (application/json)

        {
            "name": "Mobile campaigns blacklist"
        }

+ Response 200 (application/json)

        {
            "data": {
                  "id": "153",
                  "accountId": "186",
                  "name": "Mobile campaigns blacklist"
            }
        }

### Delete a publisher group [DELETE /rest/v1/accounts/{accountId}/publishergroups/{publisherGroupId}] ###

Publisher groups can be deleted when they are not referenced by any Ad Group.

+ Parameters
    + accountId: 186 (required)
    + publisherGroupId: 155 (required)

+ Response 204

## Publisher Groups Entries [/rest/v1/publishergroups/{publisherGroupId}/entries/] ##

Property           | Type                | Description                                                            | Create         |
-------------------|---------------------|------------------------------------------------------------------------|----------------|
id                 | string              | id of the entry                                                        | N/A            |
publisherGroupId   | string              | id of the publisher group                                              | required       |
publisher          | string              | publisher's domain (or name), strict matching                          | required       |
placement          | string              | The placement identifier string. If not set, it refers to all placements. | optional       |
source             | string              | Source identifier. If not set, it refers to all sources.                  | optional       |
includeSubdomains  | boolean             | if true, the publisher's subdomains will also be included in the group | optional, defaults to true      |

### List publisher group entries [GET /rest/v1/publishergroups/{publisherGroupId}/entries/{?offset,limit}] ###

+ Parameters
    + publisherGroupId: 157 (required)
    + offset: 0 (optional, int) - 0-based starting index
    + limit: 100 (required, int) - Maximum number of entries to return, up to `1000`, defaults to `100`

+ Response 200 (application/json)

        {
            "count": 2,
            "next": "https://oneapi.zemanta.com/rest/v1/publishergroups/154/entries/?offset=2&limit=5",
            "data": [
                {
                    "id": "652",
                    "publisherGroupId": "157",
                    "publisher": "example.com/publisher1",
                    "source": "gumgum"
                },
                {
                    "id": "655",
                    "publisherGroupId": "157",
                    "publisher": "example.com/publisher2",
                    "source": "gumgum"
                }
            ]
        }

### Create new publisher group entries [POST /rest/v1/publishergroups/{publisherGroupId}/entries/] ###

This endpoint supports creating multiple entries at once that are all appended to the same publisher group.

+ Parameters
    + publisherGroupId: 157 (required)

+ Request (application/json)

        [
            {
                "publisherGroupId": "157",
                "publisher": "example.com/publisher3",
                "source": "triplelift"
            },
            {
                "publisherGroupId": "157",
                "publisher": "example.com/publisher4",
                "source": "yahoo"
            }
        ]

+ Response 201 (application/json)

        {
            "data": [
                {
                      "id": "650",
                      "publisherGroupId": "157",
                      "publisher": "example.com/publisher3",
                      "source": "triplelift"
                },
                {
                      "id": "625",
                      "publisherGroupId": "157",
                      "publisher": "example.com/publisher4",
                      "source": "yahoo"
                }
            ]
        }

### Get a publisher group entry [GET /rest/v1/publishergroups/{publisherGroupId}/entries/{entryId}] ###

+ Parameters
    + publisherGroupId: 157 (required)
    + entryId: 625 (required)

+ Response 200 (application/json)

        {
            "data": {
                  "id": "625",
                  "publisherGroupId": "157",
                  "publisher": "example.com/publisher4",
                  "source": "yahoo"
            }
        }

### Edit a publisher group entry [PUT /rest/v1/publishergroups/{publisherGroupId}/entries/{entryId}] ###

+ Parameters
    + publisherGroupId: 157 (required)
    + entryId: 625 (required)

+ Request (application/json)

        {
                  "publisher": "example.com/publisher4",
                  "source": "yahoo"
        }

+ Response 200 (application/json)

        {
            "data": {
                  "id": "625",
                  "publisherGroupId": "157",
                  "publisher": "example.com/publisher4",
                  "source": "yahoo"
            }
        }

### Delete a publisher group entry [DELETE /rest/v1/publishergroups/{publisherGroupId}/entries/{entryId}] ###

+ Parameters
    + publisherGroupId: 157 (required)
    + entryId: 625 (required)

+ Response 204


## Blacklisting [/rest/v1/adgroups/{adGroupId}/publishers/]

This endpoint allows you to manage publisher status on different levels.

Optionally, you can assign a bid modifier to a publisher and source combination to modify the bidding price. Publisher bid modifiers are currently only supported on `ADGROUP` level. In case `modifier` is specified, the `source` has to be specified as well or a validation error will be returned. *Note: this way of setting bid modifiers on publishers has been deprecated - please use [bid modifiers API](#bid-modifiers) instead.*

Property           | Type                | Description                                                               | Update         |
-------------------|---------------------|---------------------------------------------------------------------------|----------------|
name               | string              | publisher's domain (or name), strict matching                             | required       |
placement          | string              | The placement identifier string. If not set, it refers to all placements. | optional       |
source             | string              | Source identifier. If not set, it refers to all sources.                  | optional       |
status             | [publisher status](#publishers-status) | status of the publisher                                | required       |
level              | [publisher level](#publishers-level)   | level on which the publisher is managed                | required       |

### Get publisher status [GET /rest/v1/adgroups/{adGroupId}/publishers/]

+ Parameters
    + adGroupId: 2040 (required)

+ Response 200 (application/json)

        {
            "data": [
                {
                    "name": "example.com/publisher1",
                    "placement": "placement_1234",
                    "source": "gumgum",
                    "status": "ENABLED",
                    "level": "ADGROUP"
                },
                {
                    "name": "example.com/publisher2",
                    "placement": null,
                    "source": "gumgum",
                    "status": "ENABLED",
                    "level": "ADGROUP"
                },
                {
                    "name": "example.com/publisher3",
                    "placement": null,
                    "source": null,
                    "status": "BLACKLISTED",
                    "level": "ADGROUP"
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
                "source": "gumgum",
                "status": "BLACKLISTED",
                "level": "ADGROUP"
            },
            {
                "name": "example.com/publisher2",
                "placement": "placement_1234",
                "source": "gumgum",
                "status": "BLACKLISTED",
                "level": "ADGROUP"
            },
            {
                "name": "example.com/publisher3",
                "placement": null,
                "source": "gumgum",
                "status": "ENABLED",
                "level": "ADGROUP"
            }
        ]

+ Response 200 (application/json)

        {
            "data": [
                {
                    "name": "example.com/publisher1",
                    "placement": null,
                    "source": "gumgum",
                    "status": "BLACKLISTED",
                    "level": "ADGROUP"
                },
                {
                    "name": "example.com/publisher2",
                    "placement": "placement_1234",
                    "source": "gumgum",
                    "status": "BLACKLISTED",
                    "level": "ADGROUP"
                },
                {
                    "name": "example.com/publisher3",
                    "placement": null,
                    "source": "gumgum",
                    "status": "ENABLED",
                    "level": "ADGROUP"
                }
            ]
        }



# Group Reporting
<a name='reporting'></a>

Getting a report is performed asynchronously. First, you create a report job, then you poll
its status and finally, when its status is DONE, you receive a link to a CSV file in the result field.

We advise the implementation of an exponential backoff retrying mechanism in order to gap occasional service issues.


### Filters
#### Time Filter
```
{
  "field": "Date",
  "operator": "between",
  "from": "2016-10-01",
  "to": "2016-10-31"
}
```
#### Equal Filter
Supported fields: Account Id, Campaign Id, Ad Group Id, Media Source Id
```
{
  "field": "Ad Group Id",
  "operator": "=",
  "value": "2040"
}
```
#### In Filter
Supported fields: Account Id, Campaign Id, Ad Group Id, Content Ad Id, Media Source Id
```
{
  "field": "Ad Group Id",
  "operator": "IN",
  "values": ["2040", "2041"]
}
```

### Options
Property                   | Type                | Default      |  Description                                                    
---------------------------|---------------------|--------------|---------------------------------------------------------------
showArchived               | bool                | false        | Set to true to include the data from the archived entities.                    
showBlacklistedPublishers  | bool                | false        | Set to true to include the data from the blacklisted publishers and placements.
includeTotals              | bool                | false        | Set to true to include the totals in the last row.            
includeItemsWithNoSpend    | bool                | false        | Set to true to include the data of the entities (and/or delivery) with no spend.
allAccountsInLocalCurrency | bool                | false        | Show all the money data in the currency of the parent account.
showStatusDate             | bool                | false        | Add the current date to the status column name.
recipients                 | array[string]       | []           | When the report is ready, the link to it will be sent to all the emails in the list.
order                      | string              | -Media Spend | The field by which the report rows will be ordered. A `-` can be optionally added in front, denoting the descending order.
csvSeparator               | string              | `,`          | The character that separates the csv columns. 
csvDecimalSeparator        | string              | `.`          | The character that separates the integer and the fractional parts in decimal values.

### Fields
#### Breakdown Fields
When breakdown fields are specified, the report will be broken down by that field.

Entity breakdown:
- Account, Account Id
- Campaign, Campaign Id
- Ad Group, Ad Group Id
- Content Ad, Content Ad Id

Delivery breakdown:
- Media Source, Media Source Id
- Publisher
- Placement
- Environment
- Device
- Operating System
- Country
- State / Region
- DMA

Time breakdown:
- Day (e.g. 2017-03-30)
- Week (e.g. Week 2017-03-27 - 2017-04-02)
- Month (e.g. Month 3/2017)

#### Entity Specific Fields
- Content Ad:
    - URL
    - Display URL
    - Brand Name
    - Description
    - Image Hash
    - Image URL
    - Call to action
    - Label
    - Uploaded
    - Batch Name
- Media Source:
    - Media Source Slug
- Placement:
    - Placement Type

#### Common Fields
Any fields that can be viewed in the dashboard can be requested in a report.

- Impressions
- Clicks
- CTR
- Avg. CPC
- Avg. CPM
- Yesterday Spend
- Media Spend
- Data Cost
- License Fee
- Total Spend
- Margin
- Total Spend + Margin
- Visits
- Unique Users
- New Users
- Returning Users
- % New Users
- Pageviews
- Pageviews per Visit
- Bounced Visits
- Non-Bounced Visits
- Bounce Rate
- Total Seconds
- Time on Site
- Avg. Cost per Visit
- Avg. Cost per New Visitor
- Avg. Cost per Pageview
- Avg. Cost per Non-Bounced Visit
- Avg. Cost per Minute
- Avg. Cost per Unique User
- Account Status
- Campaign Status
- Ad Group Status
- Content Ad Status
- Media Source Status
- Publisher Status
- Video Start
- Video First Quartile
- Video Midpoint
- Video Third Quartile
- Video Complete
- Video Progress 3s
- Avg. CPV
- Avg. CPCV
- Measurable Impressions
- Viewable Impressions
- Not-Measurable Impressions
- Not-Viewable Impressions
- % Measurable Impressions
- % Viewable Impressions
- Impression Distribution (Viewable)
- Impression Distribution (Not-Measurable)
- Impression Distribution (Not-Viewable)
- Avg. VCPM

#### Conversion Fields
To get conversion data in the report, generate the column name by combining KPI, conversion pixel, conversion window name and attribution type values in this order, separated by a space.

To get the data for KPI other than conversion, the rest of the field needs to be in brackets (example below). It is also important to note that the only possible conversion window value for view attribution is 1 day.

For example, if your conversion pixel's name is "MyPixel", the valid column names would be:

- to get conversion for 7 days click attribution: `MyPixel 7 days - Click attr.`
- to get CPA for 1 day view attribution: `CPA (MyPixel 1 day - View attr.)`

Possible values:
- KPI: 
    - omitted value - conversion
    - `CPA` - CPA
    - `ROAS` - ROAS
- Conversion goal name
- Conversion window:
    - `1 day` - 1 day
    - `7 days` - 7 days
    - `30 days` - 30 days
- Attribution type:
    - `- Click attr.` - click attribution
    - `- View attr.` - view attribution

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
            "options": {
                "showArchived": true
            },
            "filters": [
                {"field": "Date", "operator": "between", "from": "2016-10-01", "to": "2016-10-31"},
                {"field": "Ad Group Id", "operator": "=", "value": "2040"}
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


## Books closed [/rest/v1/booksclosed/]

### Get latest date with complete data [GET /rest/v1/booksclosed/]
Get the latest date for which we have complete traffic data available (e.g. spend, clicks, impressions). Postclick data (e.g. Google Analytics, Omniture) might be complete at a later time.

+ Response 200 (application/json)

        {
            "data": {
                "trafficData": {
                    "latestCompleteDate" : "2020-11-16"
                }
            }
        }

# Group Utilities

<a name="geolocations"></a>
## Geolocations [/rest/v1/geolocations/]

### List geolocations [GET /rest/v1/geolocations/{?keys,types,nameContains,limit,offset}]

+ Parameters
    + keys: `US,US-HI` (optional, string) - Comma-separated list of [location keys](#header-geo-targeting)
    + types: COUNTRY,REGION (optional, string) - Comma-separated list of [location types](#location-type)
    + nameContains: United (optional, string) - Search query
    + limit: 10 (optional, int) - Maximum number of locations to return, up to `50`, defaults to `10`
    + offset: 0 (optional, int) - 0-based starting index

+ Response 200 (application/json)

    + Attributes (GeolocationResponse)

<a name="bluekai-taxonomy"></a>
## BlueKai Taxonomy [/rest/v1/bluekai/taxonomy/]

### List BlueKai Categories [GET /rest/v1/bluekai/taxonomy/]

+ Response 200 (application/json)

    + Attributes (BlueKaiTaxonomyResponse)
    
<a name="geolocations"></a>
## Sources [/rest/v1/sources/]

### List sources [GET /rest/v1/sources/{?limit,offset}]

+ Parameters
    + limit: 100 (optional, int) - Maximum number of sources to return
    + offset: 0 (optional, int) - 0-based starting index

+ Response 200 (application/json)

    + Attributes (SourceResponse)

# Group Additional Types

<a name="money"></a>
## Money

A string representing a decimal number. Example: `"15.48"`


# Group Constants reference

<a name="currency"></a>
## Account / Currency
{% for key, value in constants.currency.items %}
- `{{ key }}` - {{ value }}
{% endfor %}


<a name=audience-rule-type></a>
## Audience rule type

Include traffic that meets the following conditions:

##### People who visited specific web pages

- `STARTS_WITH` - URL starts with specified value
- `CONTAINS` - URL contains specified value

##### Anyone who visited your website

- `VISIT`

## Ad group / Content ad State

- `ACTIVE`
- `INACTIVE`

<a name="autopilot-state"></a>
## Autopilot State

- `ACTIVE_CPC` - Optimize Bids (deprecated)
- `ACTIVE_CPC_BUDGET` - Optimize Bids and Daily Spend Caps (deprecated)
- `ACTIVE` - Minimal Bid Bidding Strategy
- `INACTIVE` - Target Bid Bidding Strategy

<a name="campaign-types"></a>
## Campaign type

- `CONTENT` - Native Ad Campaign
- `CONVERSION` - Native Conversion Marketing
- `MOBILE` - Native Mobile App Advertising
- `VIDEO` - Native Video Advertising

<a name="delivery-status"></a>
## Delivery Status

{% for key, value in constants.delivery.items %}
- `{{ key }}` - {{ value }}
{% endfor %}

<a name="languages"></a>
## Language

- `ARABIC` - Arabic
- `GERMAN` - German
- `GREEK` - Greek
- `ENGLISH` - English
- `SPANISH` - Spanish
- `FRENCH` - French
- `INDONESIAN` - Indonesian
- `ITALIAN` - Italian
- `JAPANESE` - Japanese
- `MALAY` - Malay
- `DUTCH` - Dutch
- `PORTUGUESE` - Portuguese
- `ROMANIAN` - Romanian
- `RUSSIAN` - Russian
- `SWEDISH` - Swedish
- `TURKISH` - Turkish
- `VIETNAMESE` - Vietnamese
- `SIMPLIFIED_CHINESE` - Simplified Chinese
- `TRADITIONAL_CHINESE` - Traditional Chinese
- `OTHER` - Other

<a name="iab-categories"></a>
## IAB Category

- `IAB1_1` - Books & Literature
- `IAB1_2` - Celebrity Fan/Gossip
- `IAB1_3` - Fine Art
- `IAB1_4` - Humor
- `IAB1_5` - Movies
- `IAB1_6` - Music
- `IAB1_7` - Television
- `IAB2_1` - Auto Parts
- `IAB2_2` - Auto Repair
- `IAB2_3` - Buying/Selling Cars
- `IAB2_4` - Car Culture
- `IAB2_5` - Certified Pre-Owned
- `IAB2_6` - Convertible
- `IAB2_7` - Coupe
- `IAB2_8` - Crossover
- `IAB2_9` - Diesel
- `IAB2_10` - Electric Vehicle
- `IAB2_11` - Hatchback
- `IAB2_12` - Hybrid
- `IAB2_13` - Luxury
- `IAB2_14` - MiniVan
- `IAB2_15` - Mororcycles
- `IAB2_16` - Off-Road Vehicles
- `IAB2_17` - Performance Vehicles
- `IAB2_18` - Pickup
- `IAB2_19` - Road-Side Assistance
- `IAB2_20` - Sedan
- `IAB2_21` - Trucks & Accessories
- `IAB2_22` - Vintage Cars
- `IAB2_23` - Wagon
- `IAB3_1` - Advertising
- `IAB3_2` - Agriculture
- `IAB3_3` - Biotech/Biomedical
- `IAB3_4` - Business Software
- `IAB3_5` - Construction
- `IAB3_6` - Forestry
- `IAB3_7` - Government
- `IAB3_8` - Green Solutions
- `IAB3_9` - Human Resources
- `IAB3_10` - Logistics
- `IAB3_11` - Marketing
- `IAB3_12` - Metals
- `IAB4_1` - Career Planning
- `IAB4_2` - College
- `IAB4_3` - Financial Aid
- `IAB4_4` - Job Fairs
- `IAB4_5` - Job Search
- `IAB4_6` - Resume Writing/Advice
- `IAB4_7` - Nursing
- `IAB4_8` - Scholarships
- `IAB4_9` - Telecommuting
- `IAB4_10` - U.S. Military
- `IAB4_11` - Career Advice
- `IAB5_1` - 7-12 Education
- `IAB5_2` - Adult Education
- `IAB5_3` - Art History
- `IAB5_4` - Colledge Administration
- `IAB5_5` - College Life
- `IAB5_6` - Distance Learning
- `IAB5_7` - English as a 2nd Language
- `IAB5_8` - Language Learning
- `IAB5_9` - Graduate School
- `IAB5_10` - Homeschooling
- `IAB5_11` - Homework/Study Tips
- `IAB5_12` - K-6 Educators
- `IAB5_13` - Private School
- `IAB5_14` - Special Education
- `IAB5_15` - Studying Business
- `IAB6_1` - Adoption
- `IAB6_2` - Babies & Toddlers
- `IAB6_3` - Daycare/Pre School
- `IAB6_4` - Family Internet
- `IAB6_5` - Parenting - K-6 Kids
- `IAB6_6` - Parenting teens
- `IAB6_7` - Pregnancy
- `IAB6_8` - Special Needs Kids
- `IAB6_9` - Eldercare
- `IAB7_1` - Exercise
- `IAB7_2` - A.D.D.
- `IAB7_3` - AIDS/HIV
- `IAB7_4` - Allergies
- `IAB7_5` - Alternative Medicine
- `IAB7_6` - Arthritis
- `IAB7_7` - Asthma
- `IAB7_8` - Autism/PDD
- `IAB7_9` - Bipolar Disorder
- `IAB7_10` - Brain Tumor
- `IAB7_11` - Cancer
- `IAB7_12` - Cholesterol
- `IAB7_13` - Chronic Fatigue Syndrome
- `IAB7_14` - Chronic Pain
- `IAB7_15` - Cold & Flu
- `IAB7_16` - Deafness
- `IAB7_17` - Dental Care
- `IAB7_18` - Depression
- `IAB7_19` - Dermatology
- `IAB7_20` - Diabetes
- `IAB7_21` - Epilepsy
- `IAB7_22` - GERD/Acid Reflux
- `IAB7_23` - Headaches/Migraines
- `IAB7_24` - Heart Disease
- `IAB7_25` - Herbs for Health
- `IAB7_26` - Holistic Healing
- `IAB7_27` - IBS/Crohn's Disease
- `IAB7_28` - Incest/Abuse Support
- `IAB7_29` - Incontinence
- `IAB7_30` - Infertility
- `IAB7_31` - Men's Health
- `IAB7_32` - Nutrition
- `IAB7_33` - Orthopedics
- `IAB7_34` - Panic/Anxiety Disorders
- `IAB7_35` - Pediatrics
- `IAB7_36` - Physical Therapy
- `IAB7_37` - Psychology/Psychiatry
- `IAB7_38` - Senior Health
- `IAB7_39` - Sexuality
- `IAB7_40` - Sleep Disorders
- `IAB7_41` - Smoking Cessation
- `IAB7_42` - Substance Abuse
- `IAB7_43` - Thyroid Disease
- `IAB7_44` - Weight Loss
- `IAB7_45` - Women's Health
- `IAB8_1` - American Cuisine
- `IAB8_2` - Barbecues & Grilling
- `IAB8_3` - Cajun/Creole
- `IAB8_4` - Chinese Cuisine
- `IAB8_5` - Cocktails/Beer
- `IAB8_6` - Coffee/Tea
- `IAB8_7` - Cuisine-Specific
- `IAB8_8` - Desserts & Baking
- `IAB8_9` - Dining Out
- `IAB8_10` - Food Allergies
- `IAB8_11` - French Cuisine
- `IAB8_12` - Health/Lowfat Cooking
- `IAB8_13` - Italian Cuisine
- `IAB8_14` - Japanese Cuisine
- `IAB8_15` - Mexican Cuisine
- `IAB8_16` - Vegan
- `IAB8_17` - Vegetarian
- `IAB8_18` - Wine
- `IAB9_1` - Art/Technology
- `IAB9_2` - Arts & Crafts
- `IAB9_3` - Beadwork
- `IAB9_4` - Birdwatching
- `IAB9_5` - Board Games/Puzzles
- `IAB9_6` - Candle & Soap Making
- `IAB9_7` - Card Games
- `IAB9_8` - Chess
- `IAB9_9` - Cigars
- `IAB9_10` - Collecting
- `IAB9_11` - Comic Books
- `IAB9_12` - Drawing/Sketching
- `IAB9_13` - Freelance Writing
- `IAB9_14` - Genealogy
- `IAB9_15` - Getting Published
- `IAB9_16` - Guitar
- `IAB9_17` - Home Recording
- `IAB9_18` - Investors & Patents
- `IAB9_19` - Jewelry Making
- `IAB9_20` - Magic & Illusion
- `IAB9_21` - Needlework
- `IAB9_22` - Painting
- `IAB9_23` - Photography
- `IAB9_24` - Radio
- `IAB9_25` - Roleplaying Games
- `IAB9_26` - Sci-Fi & Fantasy
- `IAB9_27` - Scrapbooking
- `IAB9_28` - Screenwriting
- `IAB9_29` - Stamps & Coins
- `IAB9_30` - Video & Computer Games
- `IAB9_31` - Woodworking
- `IAB10_1` - Appliances
- `IAB10_2` - Entertaining
- `IAB10_3` - Environmental Safety
- `IAB10_4` - Gardening
- `IAB10_5` - Home Repair
- `IAB10_6` - Home Theater
- `IAB10_7` - Interior Decorating
- `IAB10_8` - Landscaping
- `IAB10_9` - Remodeling & Construction
- `IAB11_1` - Immigration
- `IAB11_2` - Legal Issues
- `IAB11_3` - U.S. Government Resources
- `IAB11_4` - Politics
- `IAB11_5` - Commentary
- `IAB12_1` - International News
- `IAB12_2` - National News
- `IAB12_3` - Local News
- `IAB13_1` - Beginning Investing
- `IAB13_2` - Credit/Debt & Loans
- `IAB13_3` - Financial News
- `IAB13_4` - Financial Planning
- `IAB13_5` - Hedge Fund
- `IAB13_6` - Insurance
- `IAB13_7` - Investing
- `IAB13_8` - Mutual Funds
- `IAB13_9` - Options
- `IAB13_10` - Retirement Planning
- `IAB13_11` - Stocks
- `IAB13_12` - Tax Planning
- `IAB14_1` - Dating
- `IAB14_2` - Divorce Support
- `IAB14_3` - Gay Life
- `IAB14_4` - Marriage
- `IAB14_5` - Senior Living
- `IAB14_6` - Teens
- `IAB14_7` - Weddings
- `IAB14_8` - Ethnic Specific
- `IAB15_1` - Astrology
- `IAB15_2` - Biology
- `IAB15_3` - Chemistry
- `IAB15_4` - Geology
- `IAB15_5` - Paranormal Phenomena
- `IAB15_6` - Physics
- `IAB15_7` - Space/Astronomy
- `IAB15_8` - Geography
- `IAB15_9` - Botany
- `IAB15_10` - Weather
- `IAB16_1` - Aquariums
- `IAB16_2` - Birds
- `IAB16_3` - Cats
- `IAB16_4` - Dogs
- `IAB16_5` - Large Animals
- `IAB16_6` - Reptiles
- `IAB16_7` - Veterinary Medicine
- `IAB17_1` - Auto Racing
- `IAB17_2` - Baseball
- `IAB17_3` - Bicycling
- `IAB17_4` - Bodybuilding
- `IAB17_5` - Boxing
- `IAB17_6` - Canoeing/Kayaking
- `IAB17_7` - Cheerleading
- `IAB17_8` - Climbing
- `IAB17_9` - Cricket
- `IAB17_10` - Figure Skating
- `IAB17_11` - Fly Fishing
- `IAB17_12` - Football
- `IAB17_13` - Freshwater Fishing
- `IAB17_14` - Game & Fish
- `IAB17_15` - Golf
- `IAB17_16` - Horse Racing
- `IAB17_17` - Horses
- `IAB17_18` - Hunting/Shooting
- `IAB17_19` - Inline Skating
- `IAB17_20` - Martial Arts
- `IAB17_21` - Mountain Biking
- `IAB17_22` - NASCAR Racing
- `IAB17_23` - Olympics
- `IAB17_24` - Paintball
- `IAB17_25` - Power & Motorcycles
- `IAB17_26` - Pro Basketball
- `IAB17_27` - Pro Ice Hockey
- `IAB17_28` - Rodeo
- `IAB17_29` - Rugby
- `IAB17_30` - Running/Jogging
- `IAB17_31` - Sailing
- `IAB17_32` - Saltwater Fishing
- `IAB17_33` - Scuba Diving
- `IAB17_34` - Skateboarding
- `IAB17_35` - Skiing
- `IAB17_36` - Snowboarding
- `IAB17_37` - Surfing/Bodyboarding
- `IAB17_38` - Swimming
- `IAB17_39` - Table Tennis/Ping-Pong
- `IAB17_40` - Tennis
- `IAB17_41` - Volleyball
- `IAB17_42` - Walking
- `IAB17_43` - Waterski/Wakeboard
- `IAB17_44` - World Soccer
- `IAB18_1` - Beauty
- `IAB18_2` - Body Art
- `IAB18_3` - Fashion
- `IAB18_4` - Jewelry
- `IAB18_5` - Clothing
- `IAB18_6` - Accessories
- `IAB19_1` - 3-D Graphics
- `IAB19_2` - Animation
- `IAB19_3` - Antivirus Software
- `IAB19_4` - C/C++
- `IAB19_5` - Cameras & Camcorders
- `IAB19_6` - Cell Phones
- `IAB19_7` - Computer Certification
- `IAB19_8` - Computer Networking
- `IAB19_9` - Computer Peripherals
- `IAB19_10` - Computer Reviews
- `IAB19_11` - Data Centers
- `IAB19_12` - Databases
- `IAB19_13` - Desktop Publishing
- `IAB19_14` - Desktop Video
- `IAB19_15` - Email
- `IAB19_16` - Graphics Software
- `IAB19_17` - Home Video/DVD
- `IAB19_18` - Internet Technology
- `IAB19_19` - Java
- `IAB19_20` - JavaScript
- `IAB19_21` - Mac Support
- `IAB19_22` - MP3/MIDI
- `IAB19_23` - Net Conferencing
- `IAB19_24` - Net for Beginners
- `IAB19_25` - Network Security
- `IAB19_26` - Palmtops/PDAs
- `IAB19_27` - PC Support
- `IAB19_28` - Portable
- `IAB19_29` - Entertainment
- `IAB19_30` - Shareware/Freeware
- `IAB19_31` - Unix
- `IAB19_32` - Visual Basic
- `IAB19_33` - Web Clip Art
- `IAB19_34` - Web Design/HTML
- `IAB19_35` - Web Search
- `IAB19_36` - Windows
- `IAB20_1` - Adventure Travel
- `IAB20_2` - Africa
- `IAB20_3` - Air Travel
- `IAB20_4` - Australia & New Zealand
- `IAB20_5` - Bed & Breakfasts
- `IAB20_6` - Budget Travel
- `IAB20_7` - Business Travel
- `IAB20_8` - By US Locale
- `IAB20_9` - Camping
- `IAB20_10` - Canada
- `IAB20_11` - Caribbean
- `IAB20_12` - Cruises
- `IAB20_13` - Eastern Europe
- `IAB20_14` - Europe
- `IAB20_15` - France
- `IAB20_16` - Greece
- `IAB20_17` - Honeymoons/Getaways
- `IAB20_18` - Hotels
- `IAB20_19` - Italy
- `IAB20_20` - Japan
- `IAB20_21` - Mexico & Central America
- `IAB20_22` - National Parks
- `IAB20_23` - South America
- `IAB20_24` - Spas
- `IAB20_25` - Theme Parks
- `IAB20_26` - Traveling with Kids
- `IAB20_27` - United Kingdom
- `IAB21_1` - Apartments
- `IAB21_2` - Architects
- `IAB21_3` - Buying/Selling Homes
- `IAB22_1` - Contests & Freebies
- `IAB22_2` - Couponing
- `IAB22_3` - Comparison
- `IAB22_4` - Engines
- `IAB23_1` - Alternative Religions
- `IAB23_2` - Atheism/Agnosticism
- `IAB23_3` - Buddhism
- `IAB23_4` - Catholicism
- `IAB23_5` - Christianity
- `IAB23_6` - Hinduism
- `IAB23_7` - Islam
- `IAB23_8` - Judaism
- `IAB23_9` - Latter-Day Saints
- `IAB23_10` - Pagan/Wiccan
- `IAB24` - Uncategorized
- `IAB25_1` - Unmoderated UGC
- `IAB25_2` - Extreme Graphic/Explicit Violence
- `IAB25_3` - Pornography
- `IAB25_4` - Profane Content
- `IAB25_5` - Hate Content
- `IAB25_6` - Under Construction
- `IAB25_7` - Incentivized
- `IAB26_1` - Illegal Content
- `IAB26_2` - Warez
- `IAB26_3` - Spyware/Malware
- `IAB26_4` - CopyrightInfringement

<a name="ga-tracking-type"></a>
## GA Tracking Type

- `EMAIL`
- `API`

## Publishers

<a name="publishers-status"></a>
### Status

- `ENABLED`
- `BLACKLISTED`

<a name="publishers-level"></a>
### Level

- `ACCOUNT`
- `CAMPAIGN`
- `ADGROUP`

<a name="goal-type"></a>
## Campaign Goal KPIs

- `TIME_ON_SITE` - Time on Site - Seconds
- `MAX_BOUNCE_RATE` - Max Bounce Rate
- `PAGES_PER_SESSION` - Pageviews per Visit
- `CPA` - Cost per Acquisition
- `CPC` - Cost per Click
- `NEW_UNIQUE_VISITORS` - New Users
- `CPV` - Cost per Visit
- `CP_NON_BOUNCED_VISIT` - Cost per Non-Bounced Visit
- `CP_NEW_VISITOR` - Cost per New Visitor
- `CP_PAGE_VIEW` - Cost per Page View
- `CPCV` - Cost per Completed Video View

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

<a name="image-crop"></a>
## Image crop

- `CENTER`
- `FACES`
- `ENTROPY`
- `LEFT`
- `RIGHT`
- `TOP`
- `BOTTOM`

<a name="tracker-event-type"></a>
## Tracker event type
{% for key, value in constants.trackerEventType.items %}
- `{{ key }}` - {{ value }}
{% endfor %}

<a name="tracker-method"></a>
## Tracker method
{% for key, value in constants.trackerMethod.items %}
- `{{ key }}` - {{ value }}
{% endfor %}

<a name="batch-status"></a>
## Content ad upload batch status

- `DONE`
- `FAILED`
- `IN_PROGRESS`
- `CANCELLED`

<a name="video-upload-status"></a>
## Video upload status

- `NOT_UPLOADED`
- `PROCESSING`
- `READY_FOR_USE`
- `PROCESSING_ERROR`

<a name="video-upload-type"></a>
## Video upload type

- `DIRECT_UPLOAD`
- `VAST_UPLOAD`
- `VAST_URL`

<a name="delivery"></a>
## Delivery Type

- `STANDARD` - Deliver ads throughout the day.
- `ACCELERATED` - Deliver ads as soon as possible.

<a name="device"></a>
## Device targeting

- `DESKTOP`
- `TABLET`
- `MOBILE`

<a name="environment"></a>
## Environment targeting

- `SITE`
- `APP`

<a name="os"></a>
## Operating system targeting
{% for key, value in constants.os.items %}
- `{{ key }}` - {{ value }}
{% endfor %}

<a name="osv"></a>
## Operating system version targeting
{% for key, value in constants.osv.items %}
- `{{ key }}` - {{ value }}
{% endfor %}

<a name="browser"></a>
## Browser targeting

- `CHROME` - Chrome
- `SAFARI` - Safari
- `FIREFOX` - Firefox
- `IE` - Internet Explorer
- `OPERA` - Opera
- `EDGE` - Microsoft Edge
- `SAMSUNG` - Samsung
- `UC_BROWSER` - UC Browser
- `OTHER` - Other (any browser other than the others named here)

<a name="connection-type"></a>
## Connection type targeting

- `WIFI` - Wi-Fi
- `CELLULAR` - Cellular

<a name="interest-category"></a>
## Interest targeting

- `COMMUNICATION` - Communication Tools
- `MEN` - Men’s Lifestyle
- `DATING` - Dating & Relationships
- `WEATHER` - Weather & Environment
- `FASHION` - Beauty & Fashion
- `TRAVEL` - Travel and Leisure
- `FUN_QUIZZES` - Viral, lists & Quizzes
- `HEALTH` - Health & Fitness
- `SCIENCE` - Science
- `TECHNOLOGY` - Technology
- `CARS` - Automotive
- `MEDIA` - News
- `HOME` - Home & Garden
- `FAMILY` - Family & Parenting
- `SHOPPING_COUPONS` - Shopping
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
- `POLITICS_LAW` - Law, Gov’t & Politics
- `GAMES` - Games & Gaming
- `FINANCE` - Business & Finance
- `EDUCATION` - Education
- `UTILITY` - Software & Services
- `OTHER` - Other
- `FOREIGN` - International Sites
- `PREMIUM` - Premium

## Geo targeting

<a name="location-type"></a>
Can be also found and listed under [geolocations](#geolocations)
### Location type

- `COUNTRY`
- `REGION`
- `CITY`
- `DMA`
- `ZIP`

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
Countries are identified by their [ISO 3166-1 alpha-2](https://en.wikipedia.org/wiki/ISO_3166-1_alpha-2) code.

Examples:
- `US` - United States
- `CA` - Canada

<a name="region"></a>
### State / Region
States or Regions are identified by the country's [ISO 3166-1 alpha-2](https://en.wikipedia.org/wiki/ISO_3166-1_alpha-2)
code and the region's [ISO 3166-2](https://en.wikipedia.org/wiki/ISO_3166-2) code concatenated with a `-` sign.

Examples:
- `US-NY` - New York, United States
- `CA-QC` - Quebec, Canada

<a name="city"></a>
### City
Cities are identified using [Geoname IDs](https://geonames.org).

Examples:
- `5128581` - New York, New York, United States
- `6167865` - Toronto, Ontario, Canada

<a name="postalcode"></a>
### Postal Code
Postal codes are identified by the [Country](#country) code and the postal code concatenated with a `:` (colon) sign.

Examples:
- `US:10001` - New York, United States
- `CA:M4E` - East Toronto (The Beaches), Ontario, Canada

<a name="day_hour"></a>
## DAY HOUR
Day hour constants represent a particular hour of a day of the week and are used for example with bid modifiers to modify bids on traffic at that those hours.

Examples:
- `MONDAY_0` - mondays from 00:00 to 01:00 EST timezone
- `SUNDAY_23` - sundays from 23:00 to 00:00 EST timezone

# Data Structures

## `geoCategories` (object)

- `countries`: `CA` (array[string])
- `regions`: `US-NY` (array[string])
- `dma`: `693` (array[string])
- `cities`: `123456` (array[string])
- `postalCodes`: `US:10001` (array[string])

## `geo` (object)

- `included` (geoCategories)
- `excluded` (geoCategories)

## `interest` (object)

- `included`: `WOMEN`, `FASHION` (array[string])
- `excluded`: `POLITICS` (array[string])

## `publisherGroups` (object)

- `included`: `153` (array[string])
- `excluded`: `154` (array[string])

## `customAudiences` (object)

- `included`: `123` (array[string])
- `excluded`: `124` (array[string])

## `retargetingAdGroups` (object)

- `included`: `2050` (array[string])
- `excluded`: `2051` (array[string])

## `os` (object)

- `name`: `ANDROID` (string)
- `version` (osv)

## `osv` (object)

- `min`: `ANDROID_6_0` (string)
- `max`: `ANDROID_7_1` (string)


## `browserFamilies` (object)

- `family`: `CHROME` (string)

## `browsers` (object)

- `included` (array[browserFamilies])
- `excluded`: (array[string])

## `targeting` (object)

- `devices`: `DESKTOP`, `MOBILE` (array[string])
- `environments`: `SITE`, `APP` (array[string])
- `os` (array[os])
- `geo` (geo)
- `interest` (interest)
- `publisherGroups` (publisherGroups)
- `audience` (AudienceTargetingExpression)
- `customAudiences` (customAudiences)
- `retargetingAdGroups` (retargetingAdGroups)
- `browsers` (browsers)
- `connectionTypes`: `WIFI`, `CELLULAR` (array[string])

## `autopilot` (object)

- `state`: `ACTIVE_CPC` (string)
- `dailyBudget`: `100.00` (string)
- `maxBid`: `0.25` (string, optional, nullable)

## `dayparting` (object)

- `monday`: `0`, `1`, `2`, `3` (array[number])
- `friday`: `20`, `21`, `22`, `23` (array[number])
- `timezone`: `America/New_York` (string)

## AdGroupWithoutIds (object)

- `name`: `My ad group 1` (string)
- `state`: `INACTIVE` (string)
- `archived`: `false` (boolean)
- `startDate`: `2016-10-05` (string)
- `endDate`: `2116-11-05` (string, optional, nullable)
- `biddingType`: `CPC` (string)
- `bid`: `0.25` (string)
- `maxCpc`: `0.25` (string)
- `maxCpm`: (string)
- `dailyBudget`: `100.00` (string)
- `targeting` (targeting)
- `trackingCode`: `this=1&that=2` (string)
- `autopilot` (autopilot)
- `dayparting` (dayparting)
- `deliveryType`: `STANDARD` (string)
- `frequencyCapping`: 10 (number, optional, nullable)

## AdGroupIds (object)

- `id`: `2040` (string)
- `campaignId`: `608` (string)

## AdGroup (object)

- Include AdGroupIds
- Include AdGroupWithoutIds

## AdGroupResponseData (object)

- Include AdGroup
- `deliveryStatus`: `ACTIVE` (string)

## AdGroupResponse

- `data` (AdGroupResponseData)

## AdGroupListResponse

- `data` (array[AdGroupResponseData])


<!-- CAMPAIGN -->

## `ga` (object)

- `enabled`: `true` (boolean)
- `type`: `API` (string)
- `webPropertyId`: `UA-123456789-1` (string)

## `adobe` (object)

- `enabled`: `true` (boolean)
- `trackingParameter`: `cid` (string)

## `tracking` (object)

- `ga` (ga)
- `adobe` (adobe)

## `campaignTargeting` (object)

- `publisherGroups` (publisherGroups)

## CampaignWithoutIds (object)

- `name`: `My Campaign 1` (string)
- `archived`: `false` (boolean)
- `iabCategory`: `IAB1_1` (string)
- `tracking` (tracking)
- `targeting` (campaignTargeting)
- `frequencyCapping`: 10 (number, optional, nullable)

## CampaignIds (object)

- `id`: `608` (string)
- `accountId`: `186` (string)

## Campaign (object)

- Include CampaignIds
- Include CampaignWithoutIds


## CampaignResponseData (object)

- Include Campaign
- `deliveryStatus`: `ACTIVE` (string)

## CampaignResponse

- `data` (CampaignResponseData)

## CampaignListResponse

- `data` (array[CampaignResponseData])


<!-- ACCOUNT -->
## `accountTargeting` (object)

- `publisherGroups` (publisherGroups)

## AccountWithoutIds (object)

- `name`: `My Account 1` (string)
- `targeting` (accountTargeting)
- `frequencyCapping`: 10 (number, optional, nullable)

## AccountIds (object)

- `id`: `186` (string)
- `agencyId`: `1` (string)

## Account (object)

- Include AccountIds
- Include AccountWithoutIds

## AccountResponseData (object)

- Include Account
- `deliveryStatus`: `ACTIVE` (string)

## AccountResponse

- `data` (AccountResponseData)

## AccountListResponse

- `data` (array[AccountResponseData])


<!-- GEOLOCATION -->
## GeolocationCountry (object)

- `key`: `US` (string)
- `type`: `COUNTRY` (string)
- `name`: `United States` (string)

## GeolocationRegion (object)

- `key`: `US-HI` (string)
- `type`: `REGION` (string)
- `name`: `Hawaii, United States` (string)

## GeolocationResponse

- `data` (array[GeolocationCountry, GeolocationRegion])

<!-- BLUEKAI -->
## BlueKaiCategory (object)

- `categoryId`: `671901` (number)
- `name`: `Parent category name` (string)
- `description`: `Parent category description` (string)
- `navigationOnly`: `false` (boolean)
- `price`: `1.0` (string)
- `reach`: 1000000000 (number)
- `childNodes`: (array[BlueKaiChildCategory])

## BlueKaiChildCategory (object)

- `categoryId`: `671902` (number)
- `name`: `Child category name` (string)
- `description`: `Child category description` (string)
- `navigationOnly`: `false` (boolean)
- `price`: `1.20` (string)
- `reach`: 1000000000 (number)
- `childNodes`: (array)

## BlueKaiTaxonomyResponse

- `data` (BlueKaiCategory)

<!-- SOURCE    -->
## SourceResponse

- `slug`: `outbrainrtb` (string)
- `name`: `Outbrain RTB` (string)

<!-- AUDIENCES -->
## AudienceTargetingCategory (object)

- `category`: `bluekai:21230` (string)


## AudienceTargetingExpression (object)

- `AND`: (array[AudienceTargetingCategory])
