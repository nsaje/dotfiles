import {Routes} from '@angular/router';
import {DashboardView} from './views/dashboard/dashboard.view';
import {ErrorForbiddenView} from './views/error-forbidden/error-forbidden.view';
import {RoutePathName} from './app.constants';
import {DEALS_ROUTES} from './features/deals/deals.routes';
import {INVENTORY_PLANNING_ROUTES} from './features/inventory-planning/inventory-planning.routes';
import {CREDITS_ROUTES} from './features/credits/credits.routes';
import {PIXELS_LIBRARY_ROUTES} from './features/pixels-library/pixels-library.routes';
import {PUBLISHER_GROUPS_ROUTES} from './features/publisher-groups/publisher-groups.routes';
import {SCHEDULED_REPORTS_ROUTES} from './features/scheduled-reports/scheduled-reports.routes';
import {ANALYTICS_ROUTES} from './features/analytics/analytics.routes';
import {ARCHIVED_ROUTES} from './features/archived/archived.routes';
import {NEW_ENTITY_ANALYTICS_MOCK_ROUTES} from './features/new-entity-analytics-mock/new-entity-analytics-mock.routes';
import {CanActivateDashboardGuard} from './route-guards/canActivateDashboard.guard';
import {CanActivateRedirectGuard} from './route-guards/canActivateRedirect.guard';
import {USERS_ROUTES} from './features/users/users.routes';
import {RULES_ROUTES} from './features/rules/rules.routes';
import {CanActivateUserGuard} from './route-guards/canActivateUser.guard';
import {CREATIVES_ROUTES} from './features/creatives/creatives.routes';
import {CanActivatePermissionGuard} from './route-guards/canActivatePermission.guard';

export const APP_ROUTES: Routes = [
    {path: '', redirectTo: RoutePathName.APP_BASE, pathMatch: 'full'},
    {
        path: RoutePathName.APP_BASE,
        component: DashboardView,
        canActivate: [
            CanActivateUserGuard,
            CanActivateDashboardGuard,
            CanActivateRedirectGuard,
        ],
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
                path: RoutePathName.SCHEDULED_REPORTS,
                children: SCHEDULED_REPORTS_ROUTES,
            },
            {
                path: RoutePathName.CREDITS,
                children: CREDITS_ROUTES,
            },
            {
                path: RoutePathName.PUBLISHER_GROUPS,
                children: PUBLISHER_GROUPS_ROUTES,
            },
            {
                path: RoutePathName.PIXELS_LIBRARY,
                children: PIXELS_LIBRARY_ROUTES,
            },
            {
                path: RoutePathName.DEALS,
                children: DEALS_ROUTES,
            },
            {
                path: RoutePathName.USERS,
                children: USERS_ROUTES,
            },
            {
                path: RoutePathName.RULES,
                children: RULES_ROUTES,
            },
            {
                path: RoutePathName.INVENTORY_PLANNING,
                children: INVENTORY_PLANNING_ROUTES,
            },
            {
                path: RoutePathName.CREATIVES,
                children: CREATIVES_ROUTES,
                canActivate: [CanActivatePermissionGuard],
                data: {permissions: ['zemauth.can_see_creative_library']},
            },
            {path: '**', redirectTo: `/${RoutePathName.APP_BASE}`},
        ],
    },
    {
        path: RoutePathName.ERROR_FORBIDDEN,
        component: ErrorForbiddenView,
        canActivate: [CanActivateUserGuard],
    },
    {path: '**', redirectTo: RoutePathName.APP_BASE},
];
