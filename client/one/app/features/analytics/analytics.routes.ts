import {Routes} from '@angular/router';
import {LevelParam, BreakdownParam, RoutePathName} from '../../app.constants';
import {AnalyticsView} from './views/analytics/analytics.view';
import {CanActivateBreakdownGuard} from './route-guards/canActivateBreakdown.guard';
import {CanActivateEntityGuard} from './route-guards/canActivateEntity.guard';

const REDIRECT_TO_URL = `/${RoutePathName.APP_BASE}/${RoutePathName.ANALYTICS}/${LevelParam.ACCOUNTS}`;

export const ANALYTICS_ROUTES: Routes = [
    {
        path: '',
        pathMatch: 'full',
        redirectTo: REDIRECT_TO_URL,
    },
    {
        path: LevelParam.ACCOUNTS,
        data: {
            level: LevelParam.ACCOUNTS,
        },
        children: [
            {
                path: '',
                pathMatch: 'full',
                data: {
                    reuseComponent: true,
                },
                component: AnalyticsView,
            },
            {
                path: ':breakdown',
                canActivate: [CanActivateBreakdownGuard],
                data: {
                    reuseComponent: true,
                    breakdowns: [
                        BreakdownParam.SOURCES,
                        BreakdownParam.PUBLISHERS,
                        BreakdownParam.PLACEMENTS,
                        BreakdownParam.COUNTRY,
                        BreakdownParam.STATE,
                        BreakdownParam.DMA,
                        BreakdownParam.DEVICE,
                        BreakdownParam.ENVIRONMENT,
                        BreakdownParam.OPERATING_SYSTEM,
                        BreakdownParam.BROWSER,
                        BreakdownParam.CONNECTION_TYPE,
                    ],
                },
                component: AnalyticsView,
            },
        ],
    },
    {
        path: LevelParam.ACCOUNT,
        data: {
            level: LevelParam.ACCOUNT,
        },
        children: [
            {
                path: '',
                pathMatch: 'full',
                redirectTo: REDIRECT_TO_URL,
            },
            {
                path: ':id',
                canActivate: [CanActivateEntityGuard],
                children: [
                    {
                        path: '',
                        pathMatch: 'full',
                        data: {
                            reuseComponent: true,
                        },
                        component: AnalyticsView,
                    },
                    {
                        path: ':breakdown',
                        canActivate: [CanActivateBreakdownGuard],
                        data: {
                            reuseComponent: true,
                            breakdowns: [
                                BreakdownParam.SOURCES,
                                BreakdownParam.PUBLISHERS,
                                BreakdownParam.PLACEMENTS,
                                BreakdownParam.COUNTRY,
                                BreakdownParam.STATE,
                                BreakdownParam.DMA,
                                BreakdownParam.DEVICE,
                                BreakdownParam.ENVIRONMENT,
                                BreakdownParam.OPERATING_SYSTEM,
                                BreakdownParam.BROWSER,
                                BreakdownParam.CONNECTION_TYPE,
                            ],
                        },
                        component: AnalyticsView,
                    },
                ],
            },
        ],
    },
    {
        path: LevelParam.CAMPAIGN,
        data: {
            level: LevelParam.CAMPAIGN,
        },
        children: [
            {
                path: '',
                pathMatch: 'full',
                redirectTo: REDIRECT_TO_URL,
            },
            {
                path: ':id',
                canActivate: [CanActivateEntityGuard],
                children: [
                    {
                        path: '',
                        pathMatch: 'full',
                        data: {
                            reuseComponent: true,
                        },
                        component: AnalyticsView,
                    },
                    {
                        path: ':breakdown',
                        canActivate: [CanActivateBreakdownGuard],
                        data: {
                            reuseComponent: true,
                            breakdowns: [
                                BreakdownParam.SOURCES,
                                BreakdownParam.PUBLISHERS,
                                BreakdownParam.PLACEMENTS,
                                BreakdownParam.INSIGHTS,
                                BreakdownParam.COUNTRY,
                                BreakdownParam.STATE,
                                BreakdownParam.DMA,
                                BreakdownParam.DEVICE,
                                BreakdownParam.ENVIRONMENT,
                                BreakdownParam.OPERATING_SYSTEM,
                                BreakdownParam.BROWSER,
                                BreakdownParam.CONNECTION_TYPE,
                            ],
                        },
                        component: AnalyticsView,
                    },
                ],
            },
        ],
    },
    {
        path: LevelParam.AD_GROUP,
        data: {
            level: LevelParam.AD_GROUP,
        },
        children: [
            {
                path: '',
                pathMatch: 'full',
                redirectTo: REDIRECT_TO_URL,
            },
            {
                path: ':id',
                canActivate: [CanActivateEntityGuard],
                children: [
                    {
                        path: '',
                        pathMatch: 'full',
                        data: {
                            reuseComponent: true,
                        },
                        component: AnalyticsView,
                    },
                    {
                        path: ':breakdown',
                        canActivate: [CanActivateBreakdownGuard],
                        data: {
                            reuseComponent: true,
                            breakdowns: [
                                BreakdownParam.SOURCES,
                                BreakdownParam.PUBLISHERS,
                                BreakdownParam.PLACEMENTS,
                                BreakdownParam.COUNTRY,
                                BreakdownParam.STATE,
                                BreakdownParam.DMA,
                                BreakdownParam.DEVICE,
                                BreakdownParam.ENVIRONMENT,
                                BreakdownParam.OPERATING_SYSTEM,
                                BreakdownParam.BROWSER,
                                BreakdownParam.CONNECTION_TYPE,
                            ],
                        },
                        component: AnalyticsView,
                    },
                ],
            },
        ],
    },
    {
        path: '**',
        redirectTo: REDIRECT_TO_URL,
    },
];
