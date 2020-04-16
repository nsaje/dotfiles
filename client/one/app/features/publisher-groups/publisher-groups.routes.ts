import {Routes} from '@angular/router';
import {RoutePathName} from '../../app.constants';
import {PublisherGroupsView} from './views/publisher-groups/publisher-groups.view';

const REDIRECT_TO_URL = `/${RoutePathName.APP_BASE}`;

export const PUBLISHER_GROUPS_ROUTES: Routes = [
    {
        path: '',
        pathMatch: 'full',
        component: PublisherGroupsView,
    },
    {
        path: '**',
        redirectTo: REDIRECT_TO_URL,
    },
];
