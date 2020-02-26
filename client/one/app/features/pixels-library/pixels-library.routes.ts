import {Routes} from '@angular/router';
import {RoutePathName, LevelParam} from '../../app.constants';
import {PixelsLibraryView} from './views/pixels-library/pixels-library.view';

const REDIRECT_TO_URL = `/${RoutePathName.APP_BASE}`;

export const PIXELS_LIBRARY_ROUTES: Routes = [
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
                component: PixelsLibraryView,
            },
        ],
    },
    {
        path: '**',
        redirectTo: REDIRECT_TO_URL,
    },
];
