# Campaign stop

## Table of contents

* [Purpose](#purpose)
* [Implementation](#implementation)
    * [Enabling campaign stop](#enabling-campaign-stop)
    * [Model](#model)
    * [Priority k1 queue](#priority-k1-queue)
    * [Components](#components)
        * [Main job](#main-job)
        * [Selection job](#selection-job)
        * [Real time data refresh](#real-time-data-refresh)
        * [Async update handler](#async-update-handler)
* [Campaign stop log](#campaign-stop-log)

## Purpose

The purpose of campaign stop is to ensure campaigns in Z1 are stopped on time and on budget. It achieves this goal by periodically checking the spend of campaigns in external systems, updates the statuses and pings K1 for campaigns that have to be stopped. Because data in stats databases is delayed at least for a few hours it uses real time endpoint provided by K1 to get the most accurate snaphost of data possible at any given moment. An important detail is also that it stops campaigns when their remaining budget drops below a fixed threshold - it is impossible to stop campaigns exactly on budget because of delays between systems.

## Implementation

### Enabling campaign stop

Campaign stop is enabled for campaigns that have `real_time_campaign_stop` flag (on `Campaign` model) set to `True`.

### Model

The `CampaignStopState` is the main model used to hold the state for each campaign in Z1 that has campaign stop enabled. The most important fields are:
  - `state` (`ACTIVE` or `STOPPED`) - used by `k1api` to override ad group state if campaign is out of budget, 
  - `almost_depleted` (boolean) - marks a campaign to be checked periodically with high frequency, and
  - `max_allowed_end_date` - used to stop campaigns where budgets expire before the whole amount is used.

### Priority K1 queue

Campaign stop uses priority pings on K1 which use a separate queue and are executed in parallel with other actions. This way a congestion in K1 is less likely to prevent campaigns being stopped on time.

### Components

#### Main job

Main job is the most frequent job, designed to run at least every 5 minutes. It refreshes real time data of campaigns marked by selection job and checks whether their remaining budget will be under threshold by the time of next check (using simple estimation). In that case it sets `state` to `STOPPED` and pings K1.

#### Selection job

Selection job runs every hour for all campaigns with campaign stop enabled and marks campaigns for which the sum of ad groups' daily budgets is higher than their remaining budget. In that case it marks the campaign to be checked periodically by main job by setting `almost_depleted` flag.

#### Real time data Refresh

Real time data is refreshed by main and selection jobs. It uses K1 api to fetch data from external systems and then stores it in internal `RealTimeDataHistory` and `RealTimeCampaignDataHistory` to be used by other components.

#### Async update notifier and handler

In case campaign or ad group settings change some jobs have to be run again as soon as possible to prevent campaigns running out of budget. This is achieved by using Django signals infrastrucure. Campaign stop subscribes to budget `post_save` signal and custom signals for settings updates in `update_notifier` module. This module then posts a message to `campaignstop-updates` queue. The queue is periodically (with high frequency) emptied by `update_handler` module which runs appropriate jobs for campaigns depending on the event received.

This is performed in async manner in order to avoid delays on user settings change requests because running these jobs can take a few seconds or more.

## Campaign stop log

A special `CampaignStopLog` is used to store information about data on which campaign stop operated on in order to help when debugging. It stores a JSON object and has a readable representation implemented in Django admin. A single entity in this model represents a (main/selection) job run or some other event related to campaign stop.
