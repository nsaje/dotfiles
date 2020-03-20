import {Routes} from '@angular/router';
import {RoutePathName} from '../../app.constants';
import {CreditsLibraryView} from './views/credits-library/credits-library.view';

const REDIRECT_TO_URL = `/${RoutePathName.APP_BASE}`;

export const CREDITS_LIBRARY_ROUTES: Routes = [
    {
        path: '',
        pathMatch: 'full',
        component: CreditsLibraryView,
    },
    {
        path: '**',
        redirectTo: REDIRECT_TO_URL,
    },
];
