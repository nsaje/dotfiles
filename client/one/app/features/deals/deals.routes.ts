import {Routes} from '@angular/router';
import {DealsView} from './views/deals/deals.view';
import {RoutePathName} from '../../app.constants';

const REDIRECT_TO_URL = `/${RoutePathName.APP_BASE}`;

export const DEALS_ROUTES: Routes = [
    {
        path: '',
        pathMatch: 'full',
        component: DealsView,
    },
    {
        path: '**',
        redirectTo: REDIRECT_TO_URL,
    },
];
