import {Routes} from '@angular/router';
import {RoutePathName, LevelParam} from '../../app.constants';
import {UsersLibraryView} from './views/users-library/users-library.view';

const REDIRECT_TO_URL = `/${RoutePathName.APP_BASE}`;

export const USERS_LIBRARY_ROUTES: Routes = [
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
                component: UsersLibraryView,
            },
        ],
    },
    {
        path: '**',
        redirectTo: REDIRECT_TO_URL,
    },
];
