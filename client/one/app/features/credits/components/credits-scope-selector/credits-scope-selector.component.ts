import './credits-scope-selector.component.less';

import {
    Component,
    ChangeDetectionStrategy,
    Input,
    Output,
    EventEmitter,
} from '@angular/core';
import {downgradeComponent} from '@angular/upgrade/static';
import {ScopeSelectorState} from '../../../../shared/components/scope-selector/scope-selector.constants';
import {Account} from '../../../../core/entities/types/account/account';
import {FieldErrors} from '../../../../shared/types/field-errors';

@Component({
    selector: 'zem-credits-scope-selector',
    templateUrl: './credits-scope-selector.component.html',
    changeDetection: ChangeDetectionStrategy.OnPush,
})
export class CreditsScopeSelectorComponent {
    @Input()
    scopeState: ScopeSelectorState;
    @Input()
    agencyErrors: FieldErrors = [];
    @Input()
    accountErrors: FieldErrors = [];
    @Input()
    isAgencyScopeDisabled: boolean;
    @Input()
    isAccountScopeDisabled: boolean;
    @Input()
    accounts: Account[];
    @Input()
    accountId: string;
    @Output()
    scopeStateChange = new EventEmitter<ScopeSelectorState>();
    @Output()
    accountChange = new EventEmitter<string | string[]>();
}

declare var angular: angular.IAngularStatic;
angular.module('one.downgraded').directive(
    'zemCreditsScopeSelector',
    downgradeComponent({
        component: CreditsScopeSelectorComponent,
    })
);
