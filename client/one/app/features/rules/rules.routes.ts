import {Routes} from '@angular/router';
import {RulesView} from './views/rules/rules.view';
import {RoutePathName} from '../../app.constants';
import {RulesHistoriesView} from './views/rules-histories/rules-histories.view';

const REDIRECT_TO_URL = `/${RoutePathName.APP_BASE}`;

export const RULES_ROUTES: Routes = [
    {
        path: '',
        pathMatch: 'full',
        component: RulesView,
    },
    {
        path: RoutePathName.RULES_HISTORY,
        pathMatch: 'full',
        component: RulesHistoriesView,
    },
    {
        path: '**',
        redirectTo: REDIRECT_TO_URL,
    },
];
