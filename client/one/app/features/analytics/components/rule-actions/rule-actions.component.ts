import './rule-actions.component.less';

import {
    Component,
    ChangeDetectionStrategy,
    ViewChild,
    Input,
    ChangeDetectorRef,
} from '@angular/core';
import {downgradeComponent} from '@angular/upgrade/static';
import {DropdownDirective} from '../../../../shared/components/dropdown/dropdown.directive';
import {ModalComponent} from '../../../../shared/components/modal/modal.component';
import {EntityType} from '../../../../app.constants';

@Component({
    selector: 'zem-rule-actions',
    templateUrl: './rule-actions.component.html',
    changeDetection: ChangeDetectionStrategy.OnPush,
})
export class RuleActionsComponent {
    @Input()
    entityId: string;
    @Input()
    entityType: EntityType;

    @ViewChild(DropdownDirective, {static: false})
    ruleActionsDropdown: DropdownDirective;
    @ViewChild(ModalComponent, {static: false})
    ruleModal: ModalComponent;

    isSaveInProgress: boolean = false;

    constructor(private changeDetectorRef: ChangeDetectorRef) {}

    openModal(): void {
        this.ruleActionsDropdown.close();
        this.ruleModal.open();
    }

    save(): void {
        // Fake save request
        this.isSaveInProgress = true;
        setTimeout(() => {
            this.isSaveInProgress = false;
            this.ruleModal.close();
            this.changeDetectorRef.detectChanges();
        }, 1000);
    }

    cancel(): void {
        this.ruleModal.close();
    }
}

declare var angular: angular.IAngularStatic;
angular.module('one.downgraded').directive(
    'zemRuleActions',
    downgradeComponent({
        component: RuleActionsComponent,
    })
);
