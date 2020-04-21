import './campaign-cloning-form.component.less';

import {
    Component,
    ChangeDetectionStrategy,
    Input,
    Output,
    EventEmitter,
    AfterViewInit,
    OnInit,
} from '@angular/core';
import {downgradeComponent} from '@angular/upgrade/static';
import {AdGroupStateOverrideConfig} from './types/ad-group-state-override-config';
import {AdStateOverrideConfig} from './types/ad-state-override-config';
import {CloneRulesConfig} from './types/clone-rules-config';
import {CampaignCloningFormApi} from './types/campaign-cloning-form-api';
import {
    CLONE_RULES_OPTIONS,
    AD_GROUP_STATE_OVERRIDES_OPTIONS,
    AD_STATE_OVERRIDES_OPTIONS,
} from './campaign-cloning-config';
import {CampaignCloningFormStore} from './services/campaign-cloning-form.store';
import {Campaign} from '../../../../../../core/entities/types/campaign/campaign';

@Component({
    selector: 'zem-campaign-cloning-form',
    templateUrl: './campaign-cloning-form.component.html',
    changeDetection: ChangeDetectionStrategy.OnPush,
    providers: [CampaignCloningFormStore],
})
export class CampaignCloningFormComponent implements OnInit, AfterViewInit {
    @Input()
    campaignName: string;
    @Input()
    campaignId: string;
    @Output()
    componentReady = new EventEmitter<CampaignCloningFormApi>();

    CLONE_RULES_OPTIONS: CloneRulesConfig[] = CLONE_RULES_OPTIONS;
    AD_GROUP_STATE_OVERRIDES_OPTIONS: AdGroupStateOverrideConfig[] = AD_GROUP_STATE_OVERRIDES_OPTIONS;
    AD_STATE_OVERRIDES_OPTIONS: AdStateOverrideConfig[] = AD_STATE_OVERRIDES_OPTIONS;

    constructor(public store: CampaignCloningFormStore) {}

    ngOnInit(): void {
        this.store.init(this.campaignName);
    }

    ngAfterViewInit(): void {
        this.componentReady.emit({
            executeClone: this.executeClone.bind(this),
        });
    }

    executeClone(): Promise<Campaign> {
        return this.store.clone(this.campaignId);
    }
}

declare var angular: angular.IAngularStatic;
angular.module('one.downgraded').directive(
    'zemCampaignCloningForm',
    downgradeComponent({
        component: CampaignCloningFormComponent,
        propagateDigest: false,
    })
);
