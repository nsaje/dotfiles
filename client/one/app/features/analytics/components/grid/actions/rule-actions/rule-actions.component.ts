import './rule-actions.component.less';

import {
    Component,
    ChangeDetectionStrategy,
    ViewChild,
    Input,
} from '@angular/core';
import {downgradeComponent} from '@angular/upgrade/static';
import {DropdownDirective} from '../../../../../../shared/components/dropdown/dropdown.directive';
import {ModalComponent} from '../../../../../../shared/components/modal/modal.component';
import {EntityType, RoutePathName} from '../../../../../../app.constants';
import {RuleEditFormApi} from '../../../../../rules/components/rule-edit-form/types/rule-edit-form-api';
import {Router} from '@angular/router';

@Component({
    selector: 'zem-rule-actions',
    templateUrl: './rule-actions.component.html',
    changeDetection: ChangeDetectionStrategy.OnPush,
})
export class RuleActionsComponent {
    @Input()
    agencyId: string;
    @Input()
    accountId: string;
    @Input()
    entityId: string;
    @Input()
    entityName: string;
    @Input()
    entityType: EntityType;
    @Input()
    isCreateRuleDisabled: boolean = false;

    @ViewChild(DropdownDirective, {static: false})
    ruleActionsDropdown: DropdownDirective;
    @ViewChild(ModalComponent, {static: false})
    ruleModal: ModalComponent;

    isSaveInProgress: boolean = false;

    private ruleEditFormApi: RuleEditFormApi;

    constructor(private router: Router) {}

    openModal(): void {
        if (this.isCreateRuleDisabled) {
            return;
        }
        this.ruleActionsDropdown.close();
        this.ruleModal.open();
    }

    save(): void {
        this.isSaveInProgress = true;
        this.ruleEditFormApi
            .executeSave()
            .then(() => {
                this.isSaveInProgress = false;
                this.ruleModal.close();
            })
            .catch(() => {
                this.isSaveInProgress = false;
            });
    }

    navigateToRulesView(): void {
        this.router.navigate([RoutePathName.APP_BASE, RoutePathName.RULES], {
            queryParams: {
                agencyId: this.agencyId,
                accountId: this.accountId,
            },
        });
    }

    onRuleEditFormReady($event: RuleEditFormApi) {
        this.ruleEditFormApi = $event;
    }
}

declare var angular: angular.IAngularStatic;
angular.module('one.downgraded').directive(
    'zemRuleActions',
    downgradeComponent({
        component: RuleActionsComponent,
        propagateDigest: false,
    })
);
