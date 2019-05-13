import {Injectable, Inject} from '@angular/core';
import {downgradeInjectable} from '@angular/upgrade/static';
import {MulticurrencyService} from '../../../../core/multicurrency/multicurrency.service';
import * as campaignGoalsHelpers from '../../helpers/campaign-goals.helpers';
import {APP_OPTIONS} from '../../../../app.options';

@Injectable()
export class CampaignGoalsService {
    constructor(
        private multicurrencyService: MulticurrencyService,
        @Inject('zemNavigationNewService') private zemNavigationNewService: any
    ) {}

    extendAvailableGoalsWithEditedGoal(
        editedCampaignGoal: any,
        availableGoals: any[]
    ): any[] {
        const extendedAvailableGoals = campaignGoalsHelpers.extendAvailableGoalsWithEditedGoal(
            editedCampaignGoal,
            availableGoals,
            APP_OPTIONS.campaignGoalKPIs
        );

        const currencySymbol = this.multicurrencyService.getAppropriateCurrencySymbol(
            this.zemNavigationNewService.getActiveAccount()
        );
        return campaignGoalsHelpers.mapAvailableGoalsToCurrencySymbol(
            extendedAvailableGoals,
            currencySymbol
        );
    }

    getAvailableGoals(
        enabledCampaignGoals: any[],
        campaignType: Number,
        onlyCpc: boolean
    ): any[] {
        const availableGoals = campaignGoalsHelpers.getAvailableGoals(
            APP_OPTIONS.campaignGoalKPIs,
            enabledCampaignGoals,
            campaignType,
            onlyCpc
        );

        const currencySymbol = this.multicurrencyService.getAppropriateCurrencySymbol(
            this.zemNavigationNewService.getActiveAccount()
        );
        return campaignGoalsHelpers.mapAvailableGoalsToCurrencySymbol(
            availableGoals,
            currencySymbol
        );
    }
}

declare var angular: angular.IAngularStatic;
angular
    .module('one.downgraded')
    .factory(
        'zemCampaignGoalsService',
        downgradeInjectable(CampaignGoalsService)
    );
