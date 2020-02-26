import {Routes} from '@angular/router';
import {DealsLibraryView} from './views/deals-library/deals-library.view';
import {RoutePathName, LevelParam} from '../../app.constants';

const REDIRECT_TO_URL = `/${RoutePathName.APP_BASE}`;

export const DEALS_LIBRARY_ROUTES: Routes = [
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
        children: [
            {
                path: '',
                pathMatch: 'full',
                redirectTo: REDIRECT_TO_URL,
            },
            {
                path: ':id',
                component: DealsLibraryView,
            },
        ],
    },
    {
        path: '**',
        redirectTo: REDIRECT_TO_URL,
    },
];
