import {Routes} from '@angular/router';
import {UsersView} from './views/users.view';
import {RoutePathName} from '../../app.constants';

const REDIRECT_TO_URL = `/${RoutePathName.APP_BASE}`;

export const USERS_ROUTES: Routes = [
    {
        path: '',
        pathMatch: 'full',
        component: UsersView,
    },
    {
        path: '**',
        redirectTo: REDIRECT_TO_URL,
    },
];
