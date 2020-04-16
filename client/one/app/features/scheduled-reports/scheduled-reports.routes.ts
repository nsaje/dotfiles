import {Routes} from '@angular/router';
import {RoutePathName, LevelParam} from '../../app.constants';
import {ScheduledReportsView} from './views/scheduled-reports/scheduled-reports.view';

const REDIRECT_TO_URL = `/${RoutePathName.APP_BASE}`;

export const SCHEDULED_REPORTS_ROUTES: Routes = [
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
        component: ScheduledReportsView,
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
                component: ScheduledReportsView,
            },
        ],
    },
    {
        path: '**',
        redirectTo: REDIRECT_TO_URL,
    },
];
