import {Routes} from '@angular/router';
import {RoutePathName, LevelParam} from '../../app.constants';
import {CreditsLibraryView} from './views/credits-library/credits-library.view';

const REDIRECT_TO_URL = `/${RoutePathName.APP_BASE}`;

export const CREDITS_LIBRARY_ROUTES: Routes = [
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
                component: CreditsLibraryView,
            },
        ],
    },
    {
        path: '**',
        redirectTo: REDIRECT_TO_URL,
    },
];
