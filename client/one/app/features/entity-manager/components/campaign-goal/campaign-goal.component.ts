import './campaign-goal.component.less';

import {
    Component,
    ChangeDetectionStrategy,
    Input,
    Output,
    EventEmitter,
    ViewChild,
    OnInit,
    OnChanges,
    SimpleChanges,
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
export class CampaignGoalComponent implements OnInit, OnChanges {
    @Input()
    index: number;
    @Input()
    campaignGoal: CampaignGoal;
    @Input()
    currency: Currency;
    @Input()
    isDisabled: boolean;
    @Output()
    campaignGoalPrimaryChange = new EventEmitter<void>();
    @Output()
    campaignGoalDelete = new EventEmitter<void>();
    @Output()
    campaignGoalEditFormClose = new EventEmitter<void>();

    @ViewChild(ModalComponent, {static: false})
    pixelTagModal: ModalComponent;

    campaignGoalDescription: string;
    pixelTag: string;
    CampaignGoalKPI = CampaignGoalKPI;
    isEditFormVisible: boolean = false;

    ngOnInit(): void {
        this.isEditFormVisible = !this.campaignGoal.id;
    }

    ngOnChanges(changes: SimpleChanges): void {
        if (changes.campaignGoal) {
            this.campaignGoalDescription = campaignGoalsHelpers.getCampaignGoalDescription(
                this.campaignGoal,
                this.currency
            );
        }
    }

    setPrimary() {
        if (this.isDisabled) {
            return;
        }
        this.campaignGoalPrimaryChange.emit();
    }

    toggleCampaignGoalEditForm($event: any) {
        $event.stopPropagation();
        this.isEditFormVisible = !this.isEditFormVisible;
        if (!this.isEditFormVisible) {
            this.campaignGoalEditFormClose.emit();
        }
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

    private getPixelTag(name: string, pixelUrl: string) {
        return `<!-- ${name} -->\n<img src="'${pixelUrl}'" height="1" width="1" border="0" alt="" />`;
    }
}
