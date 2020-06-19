import {Routes} from '@angular/router';
import {RoutePathName} from '../../app.constants';

const REDIRECT_TO_URL = `/${RoutePathName.APP_BASE}`;

export const RULES_ROUTES: Routes = [
    // TODO (katrca) add when view is added
    // {
    //     path: '',
    //     pathMatch: 'full',
    //     component: RulesView,
    // },
    {
        path: '**',
        redirectTo: REDIRECT_TO_URL,
    },
];
