import {Inject, Injectable} from '@angular/core';
import {Observable} from 'rxjs';
import {UpdateBlacklistStatusesRequest} from '../types/update-blacklist-statuses-request';
import {PublishersEndpoint} from './publishers.endpoint';
import {
    PublisherBlacklistLevel,
    PublisherTargetingStatus,
} from '../../../app.constants';
import {PublisherInfo} from '../types/publisher-info';
import {downgradeInjectable} from '@angular/upgrade/static';
import {PublisherBlacklistActionLevel} from '../types/publisher-blacklist-action-level';
import {isDefined} from '../../../shared/helpers/common.helpers';
import {PublisherBlacklistAction} from '../types/publisher-blacklist-action';
import {PUBLISHERS_CONFIG} from './publishers.config';
import {RequestStateUpdater} from '../../../shared/types/request-state-updater';

@Injectable()
export class PublishersService {
    constructor(
        private endpoint: PublishersEndpoint,
        @Inject('zemPermissions') public zemPermissions: any
    ) {}

    updateBlacklistStatuses(
        rows: PublisherInfo[],
        status: PublisherTargetingStatus,
        level: PublisherBlacklistLevel,
        entityId: number,
        requestStateUpdater: RequestStateUpdater
    ): Observable<boolean> {
        const request: UpdateBlacklistStatusesRequest = {
            entries: rows.map(row => {
                return {
                    ...row,
                    ...(status === PublisherTargetingStatus.BLACKLISTED && {
                        includeSubdomains: true,
                    }),
                };
            }),
            status: status,
        };

        switch (level) {
            case PublisherBlacklistLevel.ADGROUP:
                request.adGroup = entityId;
                break;
            case PublisherBlacklistLevel.CAMPAIGN:
                request.campaign = entityId;
                break;
            case PublisherBlacklistLevel.ACCOUNT:
                request.account = entityId;
                break;
        }

        return this.endpoint.updateBlacklistStatuses(
            request,
            requestStateUpdater
        );
    }

    getBlacklistActions(): PublisherBlacklistAction[] {
        return PUBLISHERS_CONFIG.blacklistActions.filter(
            this.hasPermissions.bind(this)
        );
    }

    getBlacklistLevels(
        accountId: number,
        campaignId: number,
        adGroupId: number
    ): PublisherBlacklistActionLevel[] {
        return PUBLISHERS_CONFIG.blacklistLevels.filter(level =>
            this.isLevelAvailable(accountId, campaignId, adGroupId, level)
        );
    }

    private hasPermissions(item: {permissions?: string[]}): boolean {
        return (item.permissions || []).every(permission =>
            this.zemPermissions.hasPermission(permission)
        );
    }

    private isLevelAvailable(
        accountId: number,
        campaignId: number,
        adGroupId: number,
        level: PublisherBlacklistActionLevel
    ): boolean {
        if (!this.hasPermissions(level)) {
            return false;
        }
        if (
            level.level === PublisherBlacklistLevel.GLOBAL ||
            (level.level === PublisherBlacklistLevel.ACCOUNT &&
                isDefined(accountId)) ||
            (level.level === PublisherBlacklistLevel.CAMPAIGN &&
                isDefined(campaignId)) ||
            (level.level === PublisherBlacklistLevel.ADGROUP &&
                isDefined(adGroupId))
        ) {
            return true;
        }
        return false;
    }
}

declare var angular: angular.IAngularStatic;
angular
    .module('one.downgraded')
    .factory('zemPublishersService', downgradeInjectable(PublishersService));
