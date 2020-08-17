var commonHelpers = require('../../../shared/helpers/common.helpers');
var arrayHelpers = require('../../../shared/helpers/array.helpers');

angular
    .module('one.services')
    .service('zemPermissions', function(zemUserService) {
        this.hasPermission = hasPermission;
        this.isPermissionInternal = isPermissionInternal;
        this.canAccessPlatformCosts = canAccessPlatformCosts;
        this.canAccessAgencyCosts = canAccessAgencyCosts;
        this.hasAgencyScope = hasAgencyScope;
        this.canEditUsersOnEntity = canEditUsersOnEntity;
        this.canEditUsersOnAgency = canEditUsersOnAgency;
        this.canEditUsersOnAllAccounts = canEditUsersOnAllAccounts;
        this.getCurrentUserId = getCurrentUserId;

        function hasPermission(permission) {
            // Can take string or array (legacy option), returns true if user has all of the permissions
            // TODO: remove option to pass array
            var permissions;
            if (typeof permission === 'string') permissions = [permission];
            if (permission instanceof Array) permissions = permission;

            var user = zemUserService.current();
            if (!user || !permissions) {
                return false;
            }

            var userPermissions = user.permissions.map(function(x) {
                return x.permission;
            });

            var intersection = arrayHelpers.intersect(
                userPermissions,
                permissions
            );
            return intersection.length === permissions.length;
        }

        function hasEntityPermission(agencyId, accountId, permission) {
            var user = zemUserService.current();
            if (!user || !user.entityPermissions) {
                return false;
            }
            var parsedAgencyId = commonHelpers.isDefined(agencyId)
                ? parseInt(agencyId, 10)
                : null;
            var parsedAccountId = commonHelpers.isDefined(accountId)
                ? parseInt(accountId, 10)
                : null;

            return user.entityPermissions.some(function(ep) {
                return (
                    [agencyId, parsedAgencyId, null].includes(ep.agencyId) &&
                    [accountId, parsedAccountId, null].includes(ep.accountId) &&
                    ep.permission === permission
                );
            });
        }

        function isPermissionInternal(permission) {
            var user = zemUserService.current();
            if (!user || !hasPermission(permission)) {
                return false;
            }

            return !user.permissions.find(function(x) {
                return x.permission === permission;
            }).isPublic;
        }

        function canAccessPlatformCosts() {
            return hasPermission('zemauth.can_view_platform_cost_breakdown');
        }

        function canAccessAgencyCosts() {
            return hasPermission('zemauth.can_view_agency_cost_breakdown');
        }

        function hasAgencyScope(agencyId) {
            var user = zemUserService.current();
            if (hasPermission('zemauth.fea_use_entity_permission')) {
                return hasEntityPermission(agencyId, null, 'write');
            }
            // TODO (msuber): deleted after User Roles will be released.
            if (hasPermission('zemauth.can_see_all_accounts')) {
                return true;
            }
            return user.agencies.includes(Number(agencyId));
        }

        function canEditUsersOnEntity(agencyId, accountId) {
            return hasEntityPermission(agencyId, accountId, 'user');
        }

        function canEditUsersOnAgency(agencyId) {
            return hasEntityPermission(agencyId, null, 'user');
        }

        function canEditUsersOnAllAccounts() {
            return hasEntityPermission(null, null, 'user');
        }

        function getCurrentUserId() {
            return zemUserService.current().id;
        }
    });
