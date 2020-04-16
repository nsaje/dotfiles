import {Routes} from '@angular/router';
import {RoutePathName, LevelParam} from '../../app.constants';
import {UserPermissionsView} from './views/user-permissions/user-permissions.view';

const REDIRECT_TO_URL = `/${RoutePathName.APP_BASE}`;

export const USER_PERMISSIONS_ROUTES: Routes = [
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
                component: UserPermissionsView,
            },
        ],
    },
    {
        path: '**',
        redirectTo: REDIRECT_TO_URL,
    },
];
