import {Routes} from '@angular/router';
import {RoutePathName, LevelParam} from '../../app.constants';
import {ArchivedView} from './views/archived/archived.view';
import {CanActivateArchivedEntityGuard} from './route-guards/canActivateArchivedEntity.guard';

const REDIRECT_TO_URL = `/${RoutePathName.APP_BASE}`;

export const ARCHIVED_ROUTES: Routes = [
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
                canActivate: [CanActivateArchivedEntityGuard],
                component: ArchivedView,
            },
        ],
    },
    {
        path: LevelParam.CAMPAIGN,
        data: {
            level: LevelParam.CAMPAIGN,
        },
        children: [
            {
                path: '',
                pathMatch: 'full',
                redirectTo: REDIRECT_TO_URL,
            },
            {
                path: ':id',
                canActivate: [CanActivateArchivedEntityGuard],
                component: ArchivedView,
            },
        ],
    },
    {
        path: LevelParam.AD_GROUP,
        data: {
            level: LevelParam.AD_GROUP,
        },
        children: [
            {
                path: '',
                pathMatch: 'full',
                redirectTo: REDIRECT_TO_URL,
            },
            {
                path: ':id',
                canActivate: [CanActivateArchivedEntityGuard],
                component: ArchivedView,
            },
        ],
    },
    {
        path: '**',
        redirectTo: REDIRECT_TO_URL,
    },
];
