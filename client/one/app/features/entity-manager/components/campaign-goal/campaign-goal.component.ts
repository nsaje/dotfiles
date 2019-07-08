import './campaign-goal.component.less';

import {
    Component,
    ChangeDetectionStrategy,
    Input,
    Output,
    EventEmitter,
    ViewChild,
    OnInit,
} from '@angular/core';
import {CampaignGoal} from '../../../../core/entities/types/campaign/campaign-goal';
import {CampaignGoalKPI, Currency} from '../../../../app.constants';
import {ModalComponent} from '../../../../shared/components/modal/modal.component';
import * as campaignGoalsHelpers from '../../helpers/campaign-goals.helpers';

@Component({
    selector: 'zem-campaign-goal',
    templateUrl: './campaign-goal.component.html',
    changeDetection: ChangeDetectionStrategy.OnPush,
})
export class CampaignGoalComponent implements OnInit {
    @Input()
    index: number;
    @Input()
    campaignGoal: CampaignGoal;
    @Input()
    currency: Currency;
    @Output()
    campaignGoalPrimaryChange = new EventEmitter<void>();
    @Output()
    campaignGoalDelete = new EventEmitter<void>();

    @ViewChild(ModalComponent)
    pixelTagModal: ModalComponent;

    pixelTag: string;
    CampaignGoalKPI = CampaignGoalKPI;
    isExpanded: boolean = false;

    private currencyGoalKPIs: CampaignGoalKPI[] = [
        CampaignGoalKPI.CPA,
        CampaignGoalKPI.CPC,
        CampaignGoalKPI.CPM,
        CampaignGoalKPI.CPV,
        CampaignGoalKPI.CP_NON_BOUNCED_VISIT,
        CampaignGoalKPI.CP_NEW_VISITOR,
        CampaignGoalKPI.CP_PAGE_VIEW,
        CampaignGoalKPI.CPCV,
    ];

    private nonCurrencyGoalKPIs: CampaignGoalKPI[] = [
        CampaignGoalKPI.TIME_ON_SITE,
        CampaignGoalKPI.MAX_BOUNCE_RATE,
        CampaignGoalKPI.PAGES_PER_SESSION,
        CampaignGoalKPI.NEW_UNIQUE_VISITORS,
    ];

    ngOnInit(): void {
        this.isExpanded = !this.campaignGoal.id;
    }

    setPrimary() {
        this.campaignGoalPrimaryChange.emit();
    }

    toggleEditCampaignGoal($event: any) {
        $event.stopPropagation();
        this.isExpanded = !this.isExpanded;
    }

    deleteCampaignGoal($event: any) {
        $event.stopPropagation();
        this.campaignGoalDelete.emit();
    }

    openPixelTagModal($event: any) {
        $event.stopPropagation();
        this.pixelTag = this.getPixelTag(
            this.campaignGoal.conversionGoal.name,
            this.campaignGoal.conversionGoal.pixelUrl
        );
        this.pixelTagModal.open();
    }

    closePixelTagModal() {
        this.pixelTagModal.close();
    }

    getCampaignGoalDescription(campaignGoal: CampaignGoal): string {
        return campaignGoalsHelpers.getCampaignGoalDescription(
            campaignGoal,
            this.currency,
            this.currencyGoalKPIs,
            this.nonCurrencyGoalKPIs
        );
    }

    private getPixelTag(name: string, pixelUrl: string) {
        return `<!-- ${name} -->\n<img src="'${pixelUrl}'" height="1" width="1" border="0" alt="" />`;
    }
}
