/*globals angular,oneApp,constants,options,moment*/
"use strict";

oneApp.constant('demoDefaults', {
    newCampaignSettings: function (id) {
        return {
            id: id,
            name: 'New demo campaign',
            accountManager: "1",
            IABCategory: "IAB1",
            promotionGoal: 1,
            salesRepresentative: "1",
            serviceFee: "20"
        };
    },
    newAdGroupSettings: function (id) {
        return {
            trackingCode: '',
            dailyBudget: '500.00',
            cpc: "0.40",
            state: 2,
            targetRegions: ['US'],
            targetDevices: [
                {name: 'Desktop', value: 'desktop', checked: true},
                {name: 'Mobile', value: 'mobile', checked: true}
            ],
            id: id,
            name: 'New demo ad group',
            endDate: null,
            startDate: null,
            contentAdsTabWithCMS: true
        };
    },
    emptyChart: {
        "goals": {},
        "chartData": [
            { "seriesData": {}, "id": "totals", "name": "Totals" }
        ]
    },
    emptyTable: function () {
        return {
            is_sync_recent: true,
            rows: [],
            pagination: {},
            totals: { "impressions": 0, "cost": 0, "clicks": 0, "ctr": 0, "cpc": 0 }
        };
    },
    campaignsTableRow: function (name, id) {
        return {
            archived: false,
            name: name,
            avg_tos: 0,
            bounce_rate: 0,
            available_budget: 0,
            clicks: 0,
            click_discrepancy: 100,
            cost: 0,
            goals: {},
            cpc: 0,
            ctr: 0,
            impressions: 0,
            last_sync: (new Date()).toISOString(),
            pageviews: 0,
            percent_new_users: 0,
            pv_per_visit: 0,
            state: constants.adGroupSettingsState.ACTIVE,
            unspent_budget: 0,
            visits: 0,
            campaign: id
        };
    },
    accountManagers: [
        {
            'id': "1",
            'name': 'John Smith'
        },
        {
            'id': '2',
            'name': 'Steve Gatsby'
        },
        {
            'id': '3',
            'name': 'Greg Stallone'
        },
        {
            'id': '4',
            'name': 'Olga Moore'
        }
    ],
    budget: function () {
        return {
            "available": 0,
            "total": 0,
            "spend": 0,
            "history": []
        };
    },
    emptySourcesTable: function () {
        return {
            incomplete_postclick_metrics: false,
            is_sync_in_progress: false,
            is_sync_recent: true,
            last_change: (new Date()).toISOString(),
            last_sync: (new Date()).toISOString(),
            notifications: {},
            rows: [],
            totals: {
                avg_tos: 1, current_daily_budget: "", pageviews: 0,
                yesterday_cost: null, visits: 4
            }
        };
    },
    newAdGroupSources: function (all) {
        var skip = { '3': 1, '2': 1, '4': 1, '32': 1, '34': 1},
            sources = [];
        angular.forEach(all, function (source) {
            if (! skip[source.id] && !source.deprecated) {
                sources.push(source);
            }
        });
        return sources;
    },
    newAdGroupSourcesTable: function () {
        return {
            incomplete_postclick_metrics: false,
            is_sync_in_progress: false,
            is_sync_recent: true,
            last_change: (new Date()).toISOString(),
            last_sync: (new Date()).toISOString(),
            notifications: {},
            rows: [
                this.sourcesRow({name: 'Outbrain', id: '3'}),
                this.sourcesRow({name: 'Gravity', id: '2'}),
                this.sourcesRow({name: 'Yahoo', id: '4'}),
                this.sourcesRow({name: 'Yieldmo', id: '32'}),
                this.sourcesRow({name: 'TripleLif', id: '34'})
            ],
            totals: {
                avg_tos: 1, current_daily_budget: "", pageviews: 0,
                yesterday_cost: null, visits: 4
            }
        };
    },
    sourcesRow: function (values) {
        var obj = {
            archived: false,
            avg_tos: null,
            bid_cpc: '0.0',
            bounce_rate: null,
            can_edit_budget_and_cpc: true,
            click_discrepancy: null,
            mainteance: false,
            clicks: 0,
            editable_fields: {
                "status_setting": {  
                    "message": null,
                    "enabled": true
                },
                "bid_cpc": {  
                    "message": null,
                    "enabled": true
                },
                "daily_budget": {  
                    "message": null,
                    "enabled": true
                }
            },
            cost: 0,
            cpc: 0,
            status: 'Active',
            status_setting: 1,
            last_synecd: (new Date()).toISOString(),
            impressions: 0,
            ctr: 0,
            daily_budget: '0',
            _demo_new: true
        };
        return angular.extend(obj, values);
    },
    contentAds: function () {
        return {
            "notifications": {},
            "pagination": {
                "numPages": 1, "count": 5, "endIndex": 5,
                "startIndex": 1, "currentPage": 1, "size": 5
            },
            "lastChange": true,
            "rows": [
                {
                    "status_setting": 1,
                    "cpc": 0, "clicks": 0, "cost": 0, "impressions": 0, "ctr": 0,
                    "image_urls": {
                        "square": "http://static1.squarespace.com/static/537a2036e4b05ff1a08a6e1b/t/552d02c9e4b0c23003302aae/1429013198329/?format=1500w",
                        "landscape": "http://static1.squarespace.com/static/537a2036e4b05ff1a08a6e1b/t/552d02c9e4b0c23003302aae/1429013198329/?format=1500w"
                    },
                    "submission_status": [ 
                        {"status": 2, "text": "Approved / Enabled", "name": "AdsNative"},
                        {"status": 2, "text": "Approved / Enabled", "name": "Yieldmo"}
                    ],
                    "display_url": "",
                    "url": "http://www.zemanta.com/news/weve-partnered-with-adsnative-for-programmatic-native-supply",
                    "title": "We’ve Partnered with AdsNative for Programmatic Native Supply",
                    "editable_fields": {"status_setting": { message: null, enabled: true }}
                },
                {
                    "status_setting": 1,
                    "cpc": 0, "clicks": 0, "cost": 0, "impressions": 0, "ctr": 0,
                    "image_urls": {
                        "square": "http://static1.squarespace.com/static/537a2036e4b05ff1a08a6e1b/t/552d02c9e4b0c23003302aae/1429013198329/?format=1500w",
                        "landscape": "http://static1.squarespace.com/static/537a2036e4b05ff1a08a6e1b/t/552d02c9e4b0c23003302aae/1429013198329/?format=1500w"
                    },
                    "submission_status": [
                        {"status": 2, "text": "Approved / Enabled", "name": "AdsNative"},
                        {"status": 2, "text": "Approved / Enabled", "name": "Yieldmo"}
                    ],
                    "display_url": "",
                    "url": "http://www.zemanta.com/news/weve-partnered-with-adsnative-for-programmatic-native-supply",
                    "title": "Zemanta + AdsNative = More Native Supply Accessible Programmatically",
                    "editable_fields": {"status_setting": { message: null, enabled: true }}
                },
                {
                    "status_setting": 1,
                    "cpc": 0, "clicks": 0, "cost": 0, "impressions": 0, "ctr": 0,
                    "image_urls": {
                        "square": "http://static1.squarespace.com/static/537a2036e4b05ff1a08a6e1b/54369edee4b001842e669258/552d0296e4b0bfddbb2581b4/1429859532791/",
                        "landscape": "http://static1.squarespace.com/static/537a2036e4b05ff1a08a6e1b/54369edee4b001842e669258/552d0296e4b0bfddbb2581b4/1429859532791/"
                    },
                    "submission_status": [
                        {"status": 2, "text": "Approved / Enabled", "name": "AdsNative"},
                        {"status": 2, "text": "Approved / Enabled", "name": "Yieldmo"}
                    ],
                    "display_url": "",
                    "url": "http://www.zemanta.com/news/weve-partnered-with-adsnative-for-programmatic-native-supply",
                    "title": "We’ve Partnered with AdsNative for Programmatic Native Supply",
                    "editable_fields": {"status_setting": { message: null, enabled: true }}
                },
                {
                    "status_setting": 1,
                    "cpc": 0, "clicks": 0, "cost": 0, "impressions": 0, "ctr": 0,
                    "image_urls": {
                        "square": "http://static1.squarespace.com/static/537a2036e4b05ff1a08a6e1b/54369edee4b001842e669258/552d0296e4b0bfddbb2581b4/1429859532791/",
                        "landscape": "http://static1.squarespace.com/static/537a2036e4b05ff1a08a6e1b/54369edee4b001842e669258/552d0296e4b0bfddbb2581b4/1429859532791/"
                    },
                    "submission_status": [
                        {"status": 2, "text": "Approved / Enabled", "name": "AdsNative"},
                        {"status": 2, "text": "Approved / Enabled", "name": "Yieldmo"}
                    ],
                    "display_url": "",
                    "url": "http://www.zemanta.com/news/weve-partnered-with-adsnative-for-programmatic-native-supply",
                    "title": "Zemanta + AdsNative = More Native Supply Accessible Programmatically",
                    "editable_fields": {"status_setting": { message: null, enabled: true }}
                },
                {
                    "status_setting": 1,
                    "cpc": 0, "clicks": 0, "cost": 0, "impressions": 0, "ctr": 0,
                    "image_urls": {
                        "square": "http://static1.squarespace.com/static/537a2036e4b05ff1a08a6e1b/54369edee4b001842e669258/5507fb44e4b0fb424faf40d3/1426624899137/",
                        "landscape": "http://static1.squarespace.com/static/537a2036e4b05ff1a08a6e1b/54369edee4b001842e669258/5507fb44e4b0fb424faf40d3/1426624899137/"
                    },
                    "submission_status": [
                        {"status": 2, "text": "Approved / Enabled", "name": "AdsNative"},
                        {"status": 2, "text": "Approved / Enabled", "name": "Yieldmo"}
                    ],
                    "display_url": "",
                    "url": "http://www.zemanta.com/news/native-advertising-coming-of-age-programmatic-standards-emerge",
                    "title": "Native Advertising Coming of Age: Programmatic Standards Emerge",
                    "editable_fields": {"status_setting": { message: null, enabled: true }}
                },
                {
                    "status_setting": 1,
                    "cpc": 0, "clicks": 0, "cost": 0, "impressions": 0, "ctr": 0,
                    "image_urls": {
                        "square": "http://static1.squarespace.com/static/537a2036e4b05ff1a08a6e1b/54369edee4b001842e669258/5507fb44e4b0fb424faf40d3/1426624899137/",
                        "landscape": "http://static1.squarespace.com/static/537a2036e4b05ff1a08a6e1b/54369edee4b001842e669258/5507fb44e4b0fb424faf40d3/1426624899137/"
                    },
                    "submission_status": [
                        {"status": 2, "text": "Approved / Enabled", "name": "AdsNative"},
                        {"status": 2, "text": "Approved / Enabled", "name": "Yieldmo"}
                    ],
                    "display_url": "",
                    "url": "http://www.zemanta.com/news/native-advertising-coming-of-age-programmatic-standards-emerge",
                    "title": "OpenRTB 2.3 Will Help Native Advertising To Scale",
                    "editable_fields": {"status_setting": { message: null, enabled: true }}
                },
                {
                    "status_setting": 1,
                    "cpc": 0, "clicks": 0, "cost": 0, "impressions": 0, "ctr": 0,
                    "image_urls": {
                        "square": "http://static1.squarespace.com/static/537a2036e4b05ff1a08a6e1b/t/5500629de4b05b6c406ac30a/1426088613779/",
                        "landscape": "http://static1.squarespace.com/static/537a2036e4b05ff1a08a6e1b/t/5500629de4b05b6c406ac30a/1426088613779/"
                    },
                    "submission_status": [
                        {"status": 2, "text": "Approved / Enabled", "name": "AdsNative"},
                        {"status": 2, "text": "Approved / Enabled", "name": "Yieldmo"}
                    ],
                    "display_url": "",
                    "url": "http://www.zemanta.com/news/native-advertising-coming-of-age-programmatic-standards-emerge",
                    "title": "Native Advertising Coming of Age: Programmatic Standards Emerge",
                    "editable_fields": {"status_setting": { message: null, enabled: true }}
                },
                {
                    "status_setting": 1,
                    "cpc": 0, "clicks": 0, "cost": 0, "impressions": 0, "ctr": 0,
                    "image_urls": {
                        "square": "http://static1.squarespace.com/static/537a2036e4b05ff1a08a6e1b/t/5500629de4b05b6c406ac30a/1426088613779/",
                        "landscape": "http://static1.squarespace.com/static/537a2036e4b05ff1a08a6e1b/t/5500629de4b05b6c406ac30a/1426088613779/"
                    },
                    "submission_status": [
                        {"status": 2, "text": "Approved / Enabled", "name": "AdsNative"},
                        {"status": 2, "text": "Approved / Enabled", "name": "Yieldmo"}
                    ],
                    "display_url": "",
                    "url": "http://www.zemanta.com/news/native-advertising-coming-of-age-programmatic-standards-emerge",
                    "title": "OpenRTB 2.3 Will Help Native Advertising To Scale",
                    "editable_fields": {"status_setting": { message: null, enabled: true }}
                }
            ],
            "order": "url",
            "totals": { "impressions": 0, "cost": 0, "clicks": 0, "ctr": 0, "cpc": 0 }
        };
    },
    contentAdsUpdates: {
        "notifications": {}, "in_progress": false, "rows": {}, "last_change": null
    },
    tableColumns: {
        adGroupAdsPlus: [{"name":"zem-simple-menu","field":"ad_selected","type":"checkbox","shown":false,"hasPermission":false,"checked":true,"totalRow":true,"unselectable":true,"order":false,"disabled":false,"selectionOptions":[{"name":"All","type":"link"},{"name":"This page","type":"link"},{"title":"Upload batch","name":"","type":"link-list-item-first"}],"$$hashKey":"object:673"},{"name":"Thumbnail","nameCssClass":"table-name-hidden","field":"image_urls","checked":true,"type":"image","shown":true,"totalRow":false,"titleField":"title","order":false,"$$hashKey":"object:643"},{"name":"","nameCssClass":"active-circle-icon-gray","field":"status_setting","type":"state","enabledValue":1,"pausedValue":2,"internal":false,"shown":true,"checked":true,"totalRow":false,"unselectable":true,"help":"A setting for enabling and pausing content ads.","disabled":false,"$$hashKey":"object:674"},{"name":"Status","field":"submission_status","checked":true,"type":"submissionStatus","shown":true,"help":"Current submission status.","totalRow":false,"$$hashKey":"object:644"},{"name":"","unselectable":true,"checked":true,"type":"notification","shown":true,"totalRow":false,"extraTdCss":"notification-no-text","$$hashKey":"object:675"},{"name":"Title","field":"titleLink","checked":true,"type":"linkText","shown":true,"totalRow":false,"help":"The creative title/headline of a content ad.","extraTdCss":"trimmed title","titleField":"title","order":true,"orderField":"title","initialOrder":"asc","$$hashKey":"object:645"},{"name":"URL","field":"urlLink","checked":true,"type":"linkText","shown":true,"help":"The web address of the content ad.","extraTdCss":"trimmed url","totalRow":false,"titleField":"url","order":true,"orderField":"url","initialOrder":"asc","$$hashKey":"object:676"},{"name":"Uploaded","field":"upload_time","checked":false,"type":"datetime","shown":true,"help":"The time when the content ad was uploaded.","totalRow":false,"order":true,"initialOrder":"desc","$$hashKey":"object:646"},{"name":"Batch Name","field":"batch_name","checked":false,"extraTdCss":"no-wrap","type":"text","shown":true,"help":"The name of the upload batch.","totalRow":false,"titleField":"batch_name","order":true,"orderField":"batch_name","initialOrder":"asc","$$hashKey":"object:647"},{"name":"Spend","field":"cost","checked":true,"type":"currency","shown":true,"help":"The amount spent per content ad.","totalRow":true,"order":true,"initialOrder":"desc","$$hashKey":"object:661"},{"name":"Avg. CPC","field":"cpc","checked":true,"type":"currency","shown":true,"fractionSize":3,"help":"The average CPC for each content ad.","totalRow":true,"order":true,"initialOrder":"desc","$$hashKey":"object:662"},{"name":"Clicks","field":"clicks","checked":true,"type":"number","shown":true,"help":"The number of times a content ad has been clicked.","totalRow":true,"order":true,"initialOrder":"desc","$$hashKey":"object:663"},{"name":"Impressions","field":"impressions","checked":true,"type":"number","shown":true,"help":"The number of times a content ad has been displayed.","totalRow":true,"order":true,"initialOrder":"desc","$$hashKey":"object:664"},{"name":"CTR","field":"ctr","checked":true,"type":"percent","shown":true,"help":"The number of clicks divided by the number of impressions.","totalRow":true,"order":true,"initialOrder":"desc","$$hashKey":"object:665"},{"name":"Display URL","field":"display_url","checked":false,"extraTdCss":"no-wrap","type":"text","shown":true,"help":"Advertiser's display URL.","totalRow":false,"titleField":"display_url","order":true,"orderField":"display_url","initialOrder":"asc","$$hashKey":"object:648"},{"name":"Brand Name","field":"brand_name","checked":false,"extraTdCss":"no-wrap","type":"text","shown":true,"help":"Advertiser's brand name","totalRow":false,"titleField":"brand_name","order":true,"orderField":"brand_name","initialOrder":"asc","$$hashKey":"object:649"},{"name":"Description","field":"description","checked":false,"extraTdCss":"no-wrap","type":"text","shown":true,"help":"Description of the ad group.","totalRow":false,"titleField":"description","order":true,"orderField":"description","initialOrder":"asc","$$hashKey":"object:650"},{"name":"Call to action","field":"call_to_action","checked":false,"extraTdCss":"no-wrap","type":"text","shown":true,"help":"Call to action text.","totalRow":false,"titleField":"call_to_action","order":true,"orderField":"call_to_action","initialOrder":"asc","$$hashKey":"object:651"}]
    }
});
