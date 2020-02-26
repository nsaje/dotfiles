import {Routes} from '@angular/router';
import {RoutePathName, LevelParam} from '../../app.constants';
import {ReportsLibraryView} from './views/reports-library/reports-library.view';

const REDIRECT_TO_URL = `/${RoutePathName.APP_BASE}`;

export const REPORTS_LIBRARY_ROUTES: Routes = [
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
        component: ReportsLibraryView,
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
                component: ReportsLibraryView,
            },
        ],
    },
    {
        path: '**',
        redirectTo: REDIRECT_TO_URL,
    },
];
