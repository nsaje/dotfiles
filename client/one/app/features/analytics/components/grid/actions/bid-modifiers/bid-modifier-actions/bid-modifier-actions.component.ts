import './bid-modifier-actions.component.less';

import {
    Component,
    ChangeDetectionStrategy,
    Input,
    ViewChild,
    Output,
    EventEmitter,
} from '@angular/core';
import {downgradeComponent} from '@angular/upgrade/static';
import {Breakdown} from '../../../../../../../app.constants';
import {DropdownDirective} from '../../../../../../../shared/components/dropdown/dropdown.directive';
import {APP_CONFIG} from '../../../../../../../app.config';
import {ModalComponent} from '../../../../../../../shared/components/modal/modal.component';
import {BidModifierImportFormApi} from '../bid-modifier-import-form/types/bid-modifier-import-form-api';
import * as commonHelpers from '../../../../../../../shared/helpers/common.helpers';

@Component({
    selector: 'zem-bid-modifier-actions',
    templateUrl: './bid-modifier-actions.component.html',
    changeDetection: ChangeDetectionStrategy.OnPush,
})
export class BidModifierActionsComponent {
    @Input()
    adGroupId: number;
    @Input()
    breakdown: Breakdown;
    @Output()
    importSuccess = new EventEmitter<void>();

    importRequestInProgress: boolean;
    importFileIsValid: boolean;

    private bidModifierImportFormApi: BidModifierImportFormApi;

    @ViewChild(DropdownDirective, {static: false})
    bidModifierActionsDropdown: DropdownDirective;
    @ViewChild(ModalComponent, {static: false})
    bidModifierImportFormModal: ModalComponent;

    export(): void {
        this.bidModifierActionsDropdown.close();
        const url = `${APP_CONFIG.apiRestInternalUrl}/adgroups/${this.adGroupId}/bidmodifiers/download/${this.breakdown}/`;
        window.open(url, '_blank');
    }

    import(): void {
        this.importRequestInProgress = true;
        this.bidModifierImportFormApi
            .executeImport()
            .then((importSuccess: boolean) => {
                this.importRequestInProgress = false;
                if (importSuccess) {
                    this.bidModifierImportFormModal.close();
                    this.importSuccess.emit();
                }
            });
    }

    onComponentReady($event: BidModifierImportFormApi) {
        this.bidModifierImportFormApi = $event;
    }

    onFileChange($event: File) {
        this.importFileIsValid = commonHelpers.isDefined($event);
    }
}

declare var angular: angular.IAngularStatic;
angular.module('one.downgraded').directive(
    'zemBidModifierActions',
    downgradeComponent({
        component: BidModifierActionsComponent,
        propagateDigest: false,
    })
);
