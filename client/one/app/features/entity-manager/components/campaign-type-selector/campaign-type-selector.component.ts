import './campaign-type-selector.component.less';

import {
    Component,
    ChangeDetectionStrategy,
    Output,
    EventEmitter,
    Input,
    Inject,
} from '@angular/core';
import {downgradeComponent} from '@angular/upgrade/static';
import {CAMPAIGN_TYPE} from '../../../../app.constants';
import {GoogleAnalyticsService} from '../../../../core/google-analytics/google-analytics.service';
import {MixpanelService} from '../../../../core/mixpanel/mixpanel.service';

@Component({
    selector: 'zem-campaign-type-selector',
    templateUrl: './campaign-type-selector.component.html',
    changeDetection: ChangeDetectionStrategy.OnPush,
})
export class CampaignTypeSelectorComponent {
    @Input()
    shouldShowDisplayType?: boolean;
    @Input()
    shouldLogCampaignTypeSelection?: boolean;
    @Output()
    onSelect = new EventEmitter<number>();

    isDisplayDemoRequestVisible = false;
    CAMPAIGN_TYPE = CAMPAIGN_TYPE;

    constructor(
        private googleAnalyticsService: GoogleAnalyticsService,
        private mixpanelService: MixpanelService,
        @Inject('zemPermissions') private zemPermissions: any
    ) {}

    selectCampaignType(campaignType: number) {
        if (this.shouldLogCampaignTypeSelection) {
            this.googleAnalyticsService.logCampaignTypeSelection(campaignType);
            this.mixpanelService.logCampaignTypeSelection(campaignType);
        }
        if (
            campaignType === CAMPAIGN_TYPE.DISPLAY &&
            !this.zemPermissions.hasPermission(
                'zemauth.fea_can_change_campaign_type_to_display'
            )
        ) {
            this.isDisplayDemoRequestVisible = true;
            return;
        }
        this.onSelect.emit(campaignType);
    }
}

declare var angular: angular.IAngularStatic;
angular.module('one.downgraded').directive(
    'zemCampaignTypeSelector',
    downgradeComponent({
        component: CampaignTypeSelectorComponent,
        outputs: ['onSelect'],
    })
);
