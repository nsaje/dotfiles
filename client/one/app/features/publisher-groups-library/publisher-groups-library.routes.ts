import {Routes} from '@angular/router';
import {RoutePathName, LevelParam} from '../../app.constants';
import {PublisherGroupsLibraryView} from './views/publisher-groups-library/publisher-groups-library.view';

const REDIRECT_TO_URL = `/${RoutePathName.APP_BASE}`;

export const PUBLISHER_GROUPS_LIBRARY_ROUTES: Routes = [
    {
        path: '',
        pathMatch: 'full',
        component: PublisherGroupsLibraryView,
    },
    {
        path: '**',
        redirectTo: REDIRECT_TO_URL,
    },
];
