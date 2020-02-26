import {Routes} from '@angular/router';
import {RoutePathName, LevelParam} from '../../app.constants';
import {NewEntityAnalyticsMockView} from './views/new-entity-analytics-mock/new-entity-analytics-mock.view';

const REDIRECT_TO_URL = `/${RoutePathName.APP_BASE}`;

export const NEW_ENTITY_ANALYTICS_MOCK_ROUTES: Routes = [
    {
        path: '',
        pathMatch: 'full',
        redirectTo: REDIRECT_TO_URL,
    },
    {
        path: LevelParam.ACCOUNT,
        data: {
            level: LevelParam.ACCOUNT,
        },
        component: NewEntityAnalyticsMockView,
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
                component: NewEntityAnalyticsMockView,
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
                component: NewEntityAnalyticsMockView,
            },
        ],
    },
    {
        path: '**',
        redirectTo: REDIRECT_TO_URL,
    },
];
