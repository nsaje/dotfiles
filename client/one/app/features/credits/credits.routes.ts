import {Routes} from '@angular/router';
import {RoutePathName} from '../../app.constants';
import {CreditsLegacyView} from './views/credits-legacy/credits-legacy.view';
import {CreditsView} from './views/credits/credits.view';

const REDIRECT_TO_URL = `/${RoutePathName.APP_BASE}`;

export const CREDITS_ROUTES: Routes = [
    {
        path: '',
        pathMatch: 'full',
        component: CreditsLegacyView,
    },
    {
        path: 'new',
        pathMatch: 'full',
        component: CreditsView,
    },
    {
        path: '**',
        redirectTo: REDIRECT_TO_URL,
    },
];
