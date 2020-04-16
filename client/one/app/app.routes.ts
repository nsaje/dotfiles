import {Routes} from '@angular/router';
import {DashboardView} from './views/dashboard/dashboard.view';
import {ErrorForbiddenView} from './views/error-forbidden/error-forbidden.view';
import {RoutePathName} from './app.constants';
import {DEALS_LIBRARY_ROUTES} from './features/deals-library/deals-library.routes';
import {INVENTORY_PLANNING_ROUTES} from './features/inventory-planning/inventory-planning.routes';
import {CREDITS_ROUTES} from './features/credits/credits.routes';
import {PIXELS_LIBRARY_ROUTES} from './features/pixels-library/pixels-library.routes';
import {PUBLISHER_GROUPS_LIBRARY_ROUTES} from './features/publisher-groups-library/publisher-groups-library.routes';
import {REPORTS_LIBRARY_ROUTES} from './features/reports-library/reports-library.routes';
import {USERS_LIBRARY_ROUTES} from './features/users-library/users-library.routes';
import {ANALYTICS_ROUTES} from './features/analytics/analytics.routes';
import {ARCHIVED_ROUTES} from './features/archived/archived.routes';
import {NEW_ENTITY_ANALYTICS_MOCK_ROUTES} from './features/new-entity-analytics-mock/new-entity-analytics-mock.routes';
import {CanActivateDashboardGuard} from './route-guards/canActivateDashboard.guard';
import {CanActivateRedirectGuard} from './route-guards/canActivateRedirect.guard';

export const APP_ROUTES: Routes = [
    {path: '', redirectTo: RoutePathName.APP_BASE, pathMatch: 'full'},
    {
        path: RoutePathName.APP_BASE,
        component: DashboardView,
        canActivate: [CanActivateDashboardGuard, CanActivateRedirectGuard],
        children: [
            {
                path: RoutePathName.ANALYTICS,
                children: ANALYTICS_ROUTES,
            },
            {
                path: RoutePathName.ARCHIVED,
                children: ARCHIVED_ROUTES,
            },
            {
                path: RoutePathName.NEW_ENTITY_ANALYTICS_MOCK,
                children: NEW_ENTITY_ANALYTICS_MOCK_ROUTES,
            },
            {
                path: RoutePathName.REPORTS_LIBRARY,
                children: REPORTS_LIBRARY_ROUTES,
            },
            {
                path: RoutePathName.CREDITS,
                children: CREDITS_ROUTES,
            },
            {
                path: RoutePathName.PUBLISHER_GROUPS_LIBRARY,
                children: PUBLISHER_GROUPS_LIBRARY_ROUTES,
            },
            {
                path: RoutePathName.USERS_LIBRARY,
                children: USERS_LIBRARY_ROUTES,
            },
            {
                path: RoutePathName.PIXELS_LIBRARY,
                children: PIXELS_LIBRARY_ROUTES,
            },
            {
                path: RoutePathName.DEALS_LIBRARY,
                children: DEALS_LIBRARY_ROUTES,
            },
            {
                path: RoutePathName.INVENTORY_PLANNING,
                children: INVENTORY_PLANNING_ROUTES,
            },
            {path: '**', redirectTo: `/${RoutePathName.APP_BASE}`},
        ],
    },
    {path: RoutePathName.ERROR_FORBIDDEN, component: ErrorForbiddenView},
    {path: '**', redirectTo: RoutePathName.APP_BASE},
];
