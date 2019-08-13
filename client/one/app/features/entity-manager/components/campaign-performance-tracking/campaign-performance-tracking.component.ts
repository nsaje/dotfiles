import './campaign-performance-tracking.component.less';

import {
    Component,
    ChangeDetectionStrategy,
    Input,
    Output,
    EventEmitter,
} from '@angular/core';
import {ChangeEvent} from '../../../../shared/types/change-event';
import {CampaignTracking} from '../../../../core/entities/types/campaign/campaign-tracking';
import {FieldErrors} from '../../../../shared/types/field-errors';
import {CampaignTrackingErrors} from '../../types/campaign-tracking-errors';
import {GaTrackingType} from '../../../../app.constants';
import {CAMPAIGN_TRACKING_VALUE_TEXT} from '../../entity-manager.config';

@Component({
    selector: 'zem-campaign-performance-tracking',
    templateUrl: './campaign-performance-tracking.component.html',
    changeDetection: ChangeDetectionStrategy.OnPush,
})
export class CampaignPerformanceTrackingComponent {
    @Input()
    campaignTracking: CampaignTracking;
    @Input()
    campaignTrackingErrors: CampaignTrackingErrors;
    @Output()
    campaignTrackingChange = new EventEmitter<ChangeEvent<CampaignTracking>>();

    GaTrackingType = GaTrackingType;
    availableGaTypes = Object.keys(GaTrackingType).map(key => ({
        label: CAMPAIGN_TRACKING_VALUE_TEXT[key],
        value: GaTrackingType[key],
    }));

    onGaToggle($event: boolean) {
        this.campaignTrackingChange.emit({
            target: this.campaignTracking,
            changes: {
                ga: {
                    ...this.campaignTracking.ga,
                    enabled: $event,
                },
            },
        });
    }

    onGaTypeChange($event: GaTrackingType) {
        this.campaignTrackingChange.emit({
            target: this.campaignTracking,
            changes: {
                ga: {
                    ...this.campaignTracking.ga,
                    type: $event,
                    webPropertyId: '',
                },
            },
        });
    }

    onGaPropertyIdChange($event: string) {
        this.campaignTrackingChange.emit({
            target: this.campaignTracking,
            changes: {
                ga: {
                    ...this.campaignTracking.ga,
                    webPropertyId: $event,
                },
            },
        });
    }

    onAdobeToggle($event: boolean) {
        this.campaignTrackingChange.emit({
            target: this.campaignTracking,
            changes: {
                adobe: {
                    ...this.campaignTracking.adobe,
                    enabled: $event,
                },
            },
        });
    }

    onAdobeTrackingParameterChange($event: string) {
        this.campaignTrackingChange.emit({
            target: this.campaignTracking,
            changes: {
                adobe: {
                    ...this.campaignTracking.adobe,
                    trackingParameter: $event,
                },
            },
        });
    }
}
