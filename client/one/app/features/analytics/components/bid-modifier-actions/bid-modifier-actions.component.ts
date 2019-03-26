import './bid-modifier-actions.component.less';

import {
    Component,
    ChangeDetectionStrategy,
    Input,
    OnInit,
    ViewChild,
    Output,
    EventEmitter,
} from '@angular/core';
import {downgradeComponent} from '@angular/upgrade/static';
import {Breakdown} from '../../../../app.constants';
import {DropdownDirective} from '../../../../shared/components/dropdown/dropdown.directive';
import {APP_CONFIG} from '../../../../app.config';
import {ModalComponent} from '../../../../shared/components/modal/modal.component';

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

    @ViewChild(DropdownDirective)
    bidModifierActionsDropdown: DropdownDirective;
    @ViewChild(ModalComponent)
    bidModifierUploadModal: ModalComponent;

    export(): void {
        this.bidModifierActionsDropdown.close();
        const url = `${APP_CONFIG.apiRestInternalUrl}/adgroups/${
            this.adGroupId
        }/bidmodifiers/download/${this.breakdown}/`;
        window.open(url, '_blank');
    }

    import(): void {
        this.bidModifierActionsDropdown.close();
        this.bidModifierUploadModal.open();
    }

    onImportSuccess(): void {
        this.bidModifierUploadModal.close();
        this.importSuccess.emit();
    }

    onCancel(): void {
        this.bidModifierUploadModal.close();
    }
}

declare var angular: angular.IAngularStatic;
angular.module('one.downgraded').directive(
    'zemBidModifierActions',
    downgradeComponent({
        component: BidModifierActionsComponent,
    })
);
