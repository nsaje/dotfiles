FORMAT: 1A
HOST: https://oneapi.zemanta.com

# Zemanta API

This document describes the Zemanta One REST Campaign Management API.

The API enables [Zemanta](https://www.zemanta.com) clients to programatically create and manage campaigns, ad groups and content ads using RESTful objects.
Custom performance reports are also available as part of the API.

In order to use Zemanta REST API, please contact your sales representative.

## Who should read this document?

This document is inteded for programmers who are developing an integration with the Zemanta One system.
A prerequisite for working with Zemanta REST API is an understanding of HTTP and JSON.

# Group Technical Overview

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


## Rate Limiting

Each Zemanta One user can perform a maximum of 20 requests per second to the Zemanta One API.
In case that limit is crossed, the API will start responding with HTTP status 429 (Too Many Requests).

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
targeting | [targeting](#account-targeting) | account targeting settings       | optional | optional


<a name="account-targeting"></a>
#### Account Targeting Settings

Targeting        | Property | Property  | Type                                          | Description
-----------------|----------|-----------|-----------------------------------------------|---------------------------------------------------------------------------------------------|
publisherGroups  |          |           |                                               |
&nbsp;           | included |           | array[[publisherGroupId](#publishers-management-publisher-groups)]   | whitelisted publisher group IDs
&nbsp;           | excluded |           | array[[publisherGroupId](#publishers-management-publisher-groups)]   | blacklisted publisher group IDs


### Get account details [GET /rest/v1/accounts/{accountId}]

+ Parameters
    + accountId: 186 (required)

+ Response 200 (application/json)

    + Attributes (AccountResponse)


### Update account details [PUT /rest/v1/accounts/{accountId}]

+ Parameters
    + accountId: 186 (required)

+ Request (application/json)

    + Attributes (AccountWithoutIds)

+ Response 200 (application/json)

    + Attributes (AccountResponse)

### List accounts [GET /rest/v1/accounts/]

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
iabCategory | [IAB category](#iab-categories) | IAB category of the campaign   | optional | optional
language  | [Language](#languages) | Language of the ads in the campaign       | optional | read only
archived  | bool                  | Is the Campaign archived? Set to `true` to archive a Campaign and to `false` to restore it. | optional | optional
tracking  | [tracking](#tracking) | tracking settings                          | optional | optional
targeting    | [targeting](#campaign-targeting)   | campaign targeting settings                                                                                                               | optional | optional


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

<a name="campaign-targeting"></a>
#### Campaign Targeting Settings

Targeting        | Property | Property  | Type                                          | Description
-----------------|----------|-----------|-----------------------------------------------|---------------------------------------------------------------------------------------------|
devices          |          |           | array[[device](#device)]                      | A list of default device types that will be set on newly created ad groups.
placements       |          |           | array[[placement](#placement)]                | A list of default placements that will be set on newly created ad groups.
os               |          |           | array[[operatingSystem](#os-targeting)        | A list of default operating systems and operating system versions that will be se on newly created ad groups.
publisherGroups  |          |           |                                               |
&nbsp;           | included |           | array[[publisherGroupId](#publishers-management-publisher-groups)]   | whitelisted publisher group IDs
&nbsp;           | excluded |           | array[[publisherGroupId](#publishers-management-publisher-groups)]   | blacklisted publisher group IDs


### Get campaign details [GET /rest/v1/campaigns/{campaignId}]

+ Parameters
    + campaignId: 608 (required)

+ Response 200 (application/json)

    + Attributes (CampaignResponse)


### Update campaign details [PUT /rest/v1/campaigns/{campaignId}]

+ Parameters
    + campaignId: 608 (required)

+ Request (application/json)

    + Attributes (CampaignWithoutIds)

+ Response 200 (application/json)

    + Attributes (CampaignResponse)

### List campaigns [GET /rest/v1/campaigns/]

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

Property  | Type            | Description                                      | Create   | Update
----------|-----------------|--------------------------------------------------|----------|-----------|
id        | string          | the budget'id                                    | N/A      | read only
creditId  | string          | id of the credit this budget is part of          | required | read only
amount    | [money](#money) | total amount allocated by the budget             | required | optional
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
                "creditId": "861",
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
                "creditId": "861",
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
goalId           | string                        | goal id                     | N/A      | read only
pixelUrl         | url                           | pixel url, if applicable    | N/A      | read only


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

Property     | Type                      | Description                                                                                                                      | Create   | Update
-------------|---------------------------|----------------------------------------------------------------------------------------------------------------------------------|----------|-----------|
id           | string                    | the ad group's id                                                                                                                | N/A      | read only
campaignId   | string                    | id of the campaign this ad group belongs to                                                                                      | required | read only
name         | string                    | the name of the ad group                                                                                                         | required | optional
state        | `ACTIVE` / `INACTIVE`     | Ad group state. Set to `ACTIVE` to activate the Ad Group and to `INACTIVE` to deactivate it.                                     | optional | optional
archived     | bool                      | Is the Ad Group archived? Set to `true` to archive an Ad Group and to `false` to restore it.                                     | optional | optional
startDate    | string                    | start date of the ad group                                                                                                       | optional | optional
endDate      | string                    | End date of the ad group. Omit to leave it running until state is manually set to `INACTIVE`.                                    | optional | optional
startDate    | string                    | start date of the ad group                                                                                                       | optional | optional
maxCpc       | [money](#money)           | maximum CPC for this ad group                                                                                                    | optional | optional
maxCpm       | [money](#money)           | maximum CPM for this ad group (currently beta only, please contact us for access)                                                | optional | optional
targeting    | [targeting](#targeting)   | targeting settings                                                                                                               | optional | optional
dayparting   | [dayparting](#dayparting) | dayparting settings                                                                                                              | optional | optional
trackingCode | string                    | tracking codes appended to all content ads URLs ([more](http://help.zemanta.com/article/show/12985-tracking-parameters--macros)) | optional | optional
autopilot    | [autopilot](#autopilot)   | Zemanta Autopilot settings                                                                                                       | optional | optional
deliveryType | [delivery](#delivery)     | Delivery Type. Set to `STANDARD` to deliver ads throughout the day and to `ACCELERATED` to deliver ads as soon as possible.      | optional | optional

<a name="targeting"></a>
#### Targeting Settings

Targeting        | Property | Property   | Type                                                                 | Description
-----------------|----------|------------|----------------------------------------------------------------------|---------------------------------------------------------------------------------------------|
devices          |          |            | array[[device](#device)]                                             | A list of device types to target. If none specified, content is served to all device types.
placements       |          |            | array[[placement](#placement)]                                       | A list of placements to target. If none specified, content is served to all placements.
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

Property    | Type                                | Description
------------|-------------------------------------|------------------------|
state       | [autopilot state](#autopilot-state) | autopilot state
dailyBudget | dailyBudget                         | autopilot daily budget


### Get ad group details [GET /rest/v1/adgroups/{adGroupId}]

+ Parameters
    + adGroupId: 2040 (required)

+ Response 200 (application/json)
    + Attributes (AdGroupResponse)


### Update ad group details [PUT /rest/v1/adgroups/{adGroupId}]

+ Parameters
    + adGroupId: 2040 (required)

+ Request (application/json)

    + Attributes (AdGroupWithoutIds)

+ Response 200 (application/json)

    + Attributes (AdGroupResponse)

### List ad groups [GET /rest/v1/adgroups/{?campaignId}]

+ Parameters
    + campaignId: 608 (number) - Optional campaign ID

+ Response 200 (application/json)

    + Attributes (AdGroupListResponse)


### Create new ad group [POST /rest/v1/adgroups/]

+ Request (application/json)

    + Attributes
        - `campaignId`: `608` (string)
        - Include AdGroupWithoutIds

+ Response 201 (application/json)

    + Attributes (AdGroupResponse)

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
                "dailyBudget": "15.0"
            }
        }

## All Real-time bidding sources as one [/rest/v1/adgroups/{adGroupId}/sources/rtb/]
<a name="all-rtb-as-one"></a>

The sources you can promote your content on come in two flavours: real-time
bidding (RTB) and non-real-time bidding (Non-RTB) sources. RTB sources are all
sources except `yahoo`, `outbrain`, `instagram` and `facebook`.

In order to simplify manual source management (when not using Zemanta Autopilot),
you can use this special RTB settings endpoint, which allows you to group
all RTB sources together and treat them as a single source. This allows you to set
the state and daily budget of all RTB sources at once. The daily budget set by
this endpoint will be shared among all RTB sources.

This setting has to be enabled in order to be able to set [autopilot](#autopilot)
state to `ACTIVE_CPC_BUDGET`.

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

Note: At the moment only the `state`, `label` and `trackerUrls` fields can be modified through the API.
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
                "trackerUrls": ["https://example.com/t1", "https://example.com/t2"]
            }
        }



# Group Publishers management

## Publisher Groups [/rest/v1/accounts/{accountId}/publishergroups/] ##
<a name='publisher-groups'></a>

Publisher Groups are named collections of publishers that can be referenced in Ad Group's `publisherGroups`
targeting section as whitelists.
Publishers are represented as publisher domain (or name) and source pairs in the same manner as in publisher reports and blacklist management.

Property     | Type                | Description
-------------|---------------------|---------------------------------------------------------------|
id           | string              | id of the publisher group
name         | string              | name of the publisher group

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
            "name": "Mobile campaigns whitelist"
        }

+ Response 200 (application/json)

        {
            "data": {
                  "id": "153",
                  "accountId": "186",
                  "name": "Mobile campaigns whitelist"
            }
        }

### Delete a publisher group [DELETE /rest/v1/accounts/{accountId}/publishergroups/{publisherGroupId}] ###

Publisher groups can be deleted when they are not referenced by any Ad Group.

+ Parameters
    + accountId: 186 (required)
    + publisherGroupId: 155 (required)

+ Response 204

## Publisher Groups Entries [/rest/v1/publishergroups/{publisherGroupId}/entries/] ##

Property           | Type                | Description                                                           | Create         |
-------------------|---------------------|-----------------------------------------------------------------------|----------------|
id                 | string              | id of the entry                                                       | N/A            |
publisherGroupId   | string              | id of the publisher group                                             | required       |
publisher          | string              | publisher's domain (or name), strict matching                         | required       |
source             | string              | source identifier, if not set it refers to all sources                | optional       |
includeSubdomains  | boolean             | if true, the publisher's subdomains will also be included in the group | optional, defaults to true      |

### List publisher group entries [GET /rest/v1/publishergroups/{publisherGroupId}/entries/{?offset,limit}] ###

+ Parameters
    + publisherGroupId: 153 (required)
    + offset: 0 (optional, int) - 0-based starting index
    + limit: 100 (required, int) - Maximum number of entries to return, up to `1000`, defaults to `100`

+ Response 200 (application/json)

        {
            "count": 2,
            "next": "https://oneapi.zemanta.com/rest/v1/publishergroups/154/entries/?offset=2&limit=5",
            "data": [
                {
                    "id": "652",
                    "publisherGroupId": "153",
                    "publisher": "example.com/publisher1",
                    "source": "gumgum"
                },
                {
                    "id": "655",
                    "publisherGroupId": "153",
                    "publisher": "example.com/publisher2",
                    "source": "gumgum"
                }
            ]
        }

### Create new publisher group entries [POST /rest/v1/publishergroups/{publisherGroupId}/entries/] ###

This endpoint supports creating multiple entries at once that are all appended to the same publisher group.

+ Parameters
    + publisherGroupId: 153 (required)

+ Request (application/json)

        [
            {
                "publisherGroupId": "153",
                "publisher": "example.com/publisher3",
                "source": "triplelift"
            },
            {
                "publisherGroupId": "153",
                "publisher": "example.com/publisher4",
                "source": "yahoo"
            }
        ]

+ Response 201 (application/json)

        {
            "data": [
                {
                      "id": "650",
                      "publisherGroupId": "153",
                      "publisher": "example.com/publisher3",
                      "source": "triplelift"
                },
                {
                      "id": "622",
                      "publisherGroupId": "153",
                      "publisher": "example.com/publisher4",
                      "source": "yahoo"
                }
            ]
        }

### Get a publisher group entry [GET /rest/v1/publishergroups/{publisherGroupId}/entries/{entryId}] ###

+ Parameters
    + publisherGroupId: 153 (required)
    + entryId: 622 (required)

+ Response 200 (application/json)

        {
            "data": {
                  "id": "622",
                  "publisherGroupId": "153",
                  "publisher": "example.com/publisher4",
                  "source": "yahoo"
            }
        }

### Edit a publisher group entry [PUT /rest/v1/publishergroups/{publisherGroupId}/entries/{entryId}] ###

+ Parameters
    + publisherGroupId: 153 (required)
    + entryId: 622 (required)

+ Request (application/json)

        {
                  "publisher": "example.com/publisher4",
                  "source": "yahoo"
        }

+ Response 200 (application/json)

        {
            "data": {
                  "id": "622",
                  "publisherGroupId": "153",
                  "publisher": "example.com/publisher4",
                  "source": "yahoo"
            }
        }

### Delete a publisher group entry [DELETE /rest/v1/publishergroups/{publisherGroupId}/entries/{entryId}] ###

+ Parameters
    + publisherGroupId: 153 (required)
    + entryId: 622 (required)

+ Response 204


## Blacklisting [/rest/v1/adgroups/{adGroupId}/publishers/]

This endpoint allows you to manage publisher status on different levels.

Optionally, you can assign a bid modifier to a publisher to modify the
bidding price for that publisher. Publisher bid modifiers are currently
only supported on `ADGROUP` level.

*NOTE: Publisher bid modifiers are currently only supported on RTB sources*


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
            },
            {
                "name": "example.com/publisher3",
                "status": "ENABLED",
                "level": "ADGROUP",
                "source": "gumgum",
                "modifier": 0.8
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
                },
                {
                    "name": "example.com/publisher3",
                    "status": "ENABLED",
                    "level": "ADGROUP",
                    "source": "gumgum",
                    "modifier": 0.8
                }
            ]
        }



# Group Reporting
<a name='reporting'></a>

Getting a report is performed asynchronously. First, you create a report job, then you poll
its status and finally, when its status is DONE, you receive a link to a CSV file in the result field.

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

### Fields
#### Breakdown Fields
When breakdown fields are specified, the report will be broken down by that field.

Entity breakdown:
- Account, Account Id
- Campaign, Campaign Id
- Ad Group, Ad Group Id
- Content Ad, Content Ad Id
- Media Source, Media Source Id
- Publisher

Time breakdown:
- Day (e.g. 2017-03-30)
- Week (e.g. Week 2017-03-27 - 2017-04-02)
- Month (e.g. Month 3/2017)

#### Entity Specific Fields
- Account:
    - Total Fee
    - Recognized Flat Fee
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

#### Common Fields
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

#### Conversion Fields
To get conversion data in the report, simply specify the same column names as you see them in the Zemanta Dashboard.

For example, if your conversion goal name is "MyGoal", the valid column names would be

- MyGoal 1 day
- MyGoal 7 days
- MyGoal 30 days
- MyGoal 90 days


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


# Group Utilities

<a name="geolocations"></a>
## Geolocations [/rest/v1/geolocations/]

### List geolocations [GET /rest/v1/geolocations/{?keys,types,nameContains,limit}]

+ Parameters
    + keys: `US,US-HI` (optional, string) - Comma-separated list of [location keys](#header-geo-targeting)
    + types: COUNTRY,REGION (optional, string) - Comma-separated list of [location types](#location-type)
    + nameContains: United (optional, string) - Search query
    + limit: 10 (optional, int) - Maximum number of locations to return, up to `50`, defaults to `10`

+ Response 200 (application/json)

    + Attributes (GeolocationResponse)

<a name="bluekai-taxonomy"></a>
## BlueKai Taxonomy [/rest/v1/bluekai/taxonomy/]

### List BlueKai Categories [GET /rest/v1/bluekai/taxonomy/]

+ Response 200 (application/json)

    + Attributes (BlueKaiTaxonomyResponse)

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

<a name="delivery"></a>
## Delivery Type
- `STANDARD` - Deliver ads throughout the day.
- `ACCELERATED` - Deliver ads as soon as possible.

<a name="device"></a>
## Device targeting

- `DESKTOP`
- `TABLET`
- `MOBILE`

<a name="placement"></a>
## Placement targeting

- `SITE`
- `APP`

<a name="os"></a>
## Operating system targeting

- `WINDOWS` - Windows
- `MACOSX` - MacOSX and macOS
- `LINUX` - Linux
- `ANDROID` - Android
- `IOS` - iOS
- `WINPHONE` - Windows Phone

<a name="osv"></a>
## Operating system version targeting

- `WINDOWS_10` - Windows 10
- `WINDOWS_8_1` - Windows 8.1
- `WINDOWS_8` - Windows 8
- `WINDOWS_7` - Windows 7
- `WINDOWS_VISTA` - Windows Vista
- `WINDOWS_XP` - Windows XP
- `WINDOWS_2000` - Windows 2000
- `WINDOWS_98` - Windows 98
- `MACOSX_10_13` - macOS 10.13 High Sierra
- `MACOSX_10_12` - macOS 10.12 Sierra
- `MACOSX_10_11` - Mac OS X 10.11 El Capitan
- `MACOSX_10_10` - Mac OS X 10.10 Yosemite
- `MACOSX_10_9` - Mac OS X 10.9 Mavericks
- `MACOSX_10_8` - Mac OS X 10.8 Mountain Lion
- `MACOSX_10_7` - Mac OS X 10.7 Lion
- `MACOSX_10_6` - Mac OS X 10.6 Snow Leopard
- `MACOSX_10_5` - Mac OS X 10.5 Leopard
- `MACOSX_10_4` - Mac OS X 10.4 Tiger
- `ANDROID_8_0` - Android 8.0 Oreo
- `ANDROID_7_1` - Android 7.1 Nougat
- `ANDROID_7_0` - Android 7.0 Nougat
- `ANDROID_6_0` - Android 6.0 Marshmallow
- `ANDROID_5_1` - Android 5.1 Lollipop
- `ANDROID_5_0` - Android 5.0 Lollipop
- `ANDROID_4_4` - Android 4.4 KitKat
- `ANDROID_4_3` - Android 4.3 Jelly Bean
- `ANDROID_4_2` - Android 4.2 Jelly Bean
- `ANDROID_4_1` - Android 4.1 Jelly Bean
- `ANDROID_4_0` - Android 4.0 Ice Cream Sandwich
- `ANDROID_3_2` - Android 3.2 Honeycomb
- `ANDROID_3_1` - Android 3.1 Honeycomb
- `ANDROID_3_0` - Android 3.0 Honeycomb
- `ANDROID_2_3` - Android 2.3 Gingerbread
- `ANDROID_2_2` - Android 2.2 Froyo
- `ANDROID_2_1` - Android 2.1 Eclair
- `IOS_11_0` - iOS 11.0
- `IOS_10_3` - iOS 10.3
- `IOS_10_2` - iOS 10.2
- `IOS_10_1` - iOS 10.1
- `IOS_10_0` - iOS 10.0
- `IOS_9_3` - iOS 9.3
- `IOS_9_2` - iOS 9.2
- `IOS_9_1` - iOS 9.1
- `IOS_9_0` - iOS 9.0
- `IOS_8_4` - iOS 8.4
- `IOS_8_3` - iOS 8.3
- `IOS_8_2` - iOS 8.2
- `IOS_8_1` - iOS 8.1
- `IOS_8_0` - iOS 8.0
- `IOS_7_1` - iOS 7.1
- `IOS_7_0` - iOS 7.0
- `IOS_6_1` - iOS 6.1
- `IOS_6_0` - iOS 6.0
- `IOS_5_1` - iOS 5.1
- `IOS_5_0` - iOS 5.0
- `IOS_4_3` - iOS 4.3
- `IOS_4_2` - iOS 4.2
- `IOS_4_1` - iOS 4.1
- `IOS_4_0` - iOS 4.0
- `IOS_3_2` - iOS 3.2
- `WINPHONE_10` - Windows Phone 10
- `WINPHONE_8_1` - Windows Phone 8.1
- `WINPHONE_8_0` - Windows Phone 8.0
- `WINPHONE_7` - Windows Phone 7

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


## Geo targeting

<a name="location-type"></a>
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
### Region
Regions are identified by the country's [ISO 3166-1 alpha-2](https://en.wikipedia.org/wiki/ISO_3166-1_alpha-2)
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

## `targeting` (object)

- `devices`: `DESKTOP`, `MOBILE` (array[string])
- `placements`: `SITE`, `APP` (array[string])
- `os` (array[os])
- `geo` (geo)
- `interest` (interest)
- `publisherGroups` (publisherGroups)
- `audiences` (AudienceTargetingExpression)
- `customAudiences` (customAudiences)
- `retargetingAdGroups` (retargetingAdGroups)

## `autopilot` (object)

- `state`: `ACTIVE_CPC` (string)
- `dailyBudget`: `100.0001` (string)

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
- `maxCpc`: `0.25` (string)
- `maxCpm`: `1.20` (string)
- `dailyBudget`: `20.0` (string)
- `targeting` (targeting)
- `trackingCode`: `this=1&that=2` (string)
- `autopilot` (autopilot)
- `dayparting` (dayparting)
- `deliveryType`: `STANDARD` (string)

## AdGroupIds (object)

- `id`: `2040` (string)
- `campaignId`: `608` (string)

## AdGroup (object)

- Include AdGroupIds
- Include AdGroupWithoutIds

## AdGroupResponse

- `data` (AdGroup)

## AdGroupListResponse

- `data` (array[AdGroup])


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

## CampaignIds (object)

- `id`: `608` (string)
- `accountId`: `186` (string)

## Campaign (object)

- Include CampaignIds
- Include CampaignWithoutIds

## CampaignResponse

- `data` (Campaign)

## CampaignListResponse

- `data` (array[Campaign])


<!-- ACCOUNT -->
## `accountTargeting` (object)

- `publisherGroups` (publisherGroups)

## AccountWithoutIds (object)

- `name`: `My Account 1` (string)
- `targeting` (accountTargeting)

## AccountIds (object)

- `id`: `186` (string)
- `agencyId`: `1` (string)

## Account (object)

- Include AccountIds
- Include AccountWithoutIds

## AccountResponse

- `data` (Account)

## AccountListResponse

- `data` (array[Account])


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
- `desctiption`: `Parent category description` (string)
- `navigationOnly`: `false` (boolean)
- `price`: `1.0` (string)
- `reach`: 1000000000 (number)
- `childNodes`: (array[BlueKaiChildCategory])

## BlueKaiChildCategory (object)

- `categoryId`: `671902` (number)
- `name`: `Child category name` (string)
- `desctiption`: `Child category description` (string)
- `navigationOnly`: `false` (boolean)
- `price`: `1.20` (string)
- `reach`: 1000000000 (number)
- `childNodes`: (array)

## BlueKaiTaxonomyResponse

- `data` (BlueKaiCategory)

<!-- AUDIENCES -->
## AudienceTargetingCategory (object)

- `category`: `bluekai:21230` (string)


## AudienceTargetingExpression (object)

- `AND`: (array[AudienceTargetingCategory])
