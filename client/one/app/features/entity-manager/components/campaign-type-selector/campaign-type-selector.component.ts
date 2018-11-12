import './campaign-type-selector.component.less';

import {
    Component,
    ChangeDetectionStrategy,
    Output,
    EventEmitter,
    Input,
} from '@angular/core';
import {downgradeComponent} from '@angular/upgrade/static';
import {CAMPAIGN_TYPE} from '../../../../app.constants';
import {GoogleAnalyticsService} from '../../../../core/google-analytics/google-analytics.service';

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

    constructor(private googleAnalyticsService: GoogleAnalyticsService) {}

    selectCampaignType(campaignType: number) {
        if (this.shouldLogCampaignTypeSelection) {
            this.googleAnalyticsService.logCampaignTypeSelection(campaignType);
        }
        this.onSelect.emit(campaignType);
    }

    showDisplayDemoRequest() {
        if (this.shouldLogCampaignTypeSelection) {
            this.googleAnalyticsService.logCampaignTypeSelection(
                CAMPAIGN_TYPE.DISPLAY
            );
        }
        this.isDisplayDemoRequestVisible = true;
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
