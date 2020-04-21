import {CampaignCloningFormStoreState} from './campaign-cloning-form.store.state';
import {OnDestroy, Injectable} from '@angular/core';
import {Subject} from 'rxjs';
import {RequestStateUpdater} from '../../../../../../../shared/types/request-state-updater';
import {Store} from 'rxjs-observable-store';
import {CampaignService} from '../../../../../../../core/entities/services/campaign/campaign.service';
import * as storeHelpers from '../../../../../../../shared/helpers/store.helpers';
import {takeUntil} from 'rxjs/operators';
import {AdGroupState, AdState} from '../../../../../../../app.constants';
import {CampaignCloningRule} from '../campaign-cloning.constants';
import {CloneRulesConfig} from '../types/clone-rules-config';
import {CLONE_RULES_OPTIONS} from '../campaign-cloning-config';
import {Campaign} from '../../../../../../../core/entities/types/campaign/campaign';
import {HttpErrorResponse} from '@angular/common/http';

@Injectable()
export class CampaignCloningFormStore
    extends Store<CampaignCloningFormStoreState>
    implements OnDestroy {
    private ngUnsubscribe$: Subject<undefined> = new Subject();
    private requestStateUpdater: RequestStateUpdater;

    constructor(private campaignService: CampaignService) {
        super(new CampaignCloningFormStoreState());
        this.requestStateUpdater = storeHelpers.getStoreRequestStateUpdater(
            this
        );
    }

    ngOnDestroy(): void {
        this.ngUnsubscribe$.next();
        this.ngUnsubscribe$.complete();
    }

    init(campaignName: string): void {
        const selectedCloneRule = CLONE_RULES_OPTIONS.find(
            (rule: CloneRulesConfig) => rule.value === CampaignCloningRule.ADS
        );
        this.setState({
            ...this.state,
            campaignCloneSettings: {
                ...this.state.campaignCloneSettings,
                destinationCampaignName: `${campaignName} (copy)`,
                cloneAdGroups: selectedCloneRule.cloneAdGroups,
                cloneAds: selectedCloneRule.cloneAds,
            },
            cloneRule: selectedCloneRule.value,
        });
    }

    setDestinationCampaignName(destinationCampaignName: string) {
        this.patchState(
            destinationCampaignName,
            'campaignCloneSettings',
            'destinationCampaignName'
        );
    }

    setCloneRule(cloneRuleValue: CampaignCloningRule) {
        const selectedCloneRule = CLONE_RULES_OPTIONS.find(
            (rule: CloneRulesConfig) => rule.value === cloneRuleValue
        );
        this.setState({
            ...this.state,
            campaignCloneSettings: {
                ...this.state.campaignCloneSettings,
                cloneAdGroups: selectedCloneRule.cloneAdGroups,
                cloneAds: selectedCloneRule.cloneAds,
            },
            cloneRule: selectedCloneRule.value,
        });
    }

    setAdGroupStateOverride(stateOverrideValue: AdGroupState | null) {
        this.patchState(
            stateOverrideValue,
            'campaignCloneSettings',
            'adGroupStateOverride'
        );
    }

    setAdStateOverride(stateOverrideValue: AdState | null) {
        this.patchState(
            stateOverrideValue,
            'campaignCloneSettings',
            'adStateOverride'
        );
    }

    clone(campaignId: string): Promise<Campaign> {
        return new Promise<Campaign>((resolve, reject) => {
            this.campaignService
                .clone(
                    campaignId,
                    this.state.campaignCloneSettings,
                    this.requestStateUpdater
                )
                .pipe(takeUntil(this.ngUnsubscribe$))
                .subscribe(
                    (campaign: Campaign) => {
                        resolve(campaign);
                    },
                    (error: HttpErrorResponse) => {
                        reject(error);
                    }
                );
        });
    }
}
