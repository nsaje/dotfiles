import {Routes} from '@angular/router';
import {CreativesView} from './views/creatives/creatives.view';
import {RoutePathName} from '../../app.constants';
import {CreativeBatchView} from './views/creative-batch/creative-batch.view';

const REDIRECT_TO_URL = `/${RoutePathName.APP_BASE}`;

export const CREATIVES_ROUTES: Routes = [
    {path: '', pathMatch: 'full', component: CreativesView},
    {
        path: `${RoutePathName.CREATIVES_BATCH}/:batchId`,
        pathMatch: 'full',
        component: CreativeBatchView,
    },
    {
        path: '**',
        redirectTo: REDIRECT_TO_URL,
    },
];
