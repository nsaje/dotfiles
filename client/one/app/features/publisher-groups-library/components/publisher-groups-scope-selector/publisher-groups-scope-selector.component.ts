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

@Component({
    selector: 'zem-publisher-groups-scope-selector',
    templateUrl: './publisher-groups-scope-selector.component.html',
    changeDetection: ChangeDetectionStrategy.OnPush,
})
export class PublisherGroupsScopeSelectorComponent {
    @Input()
    scopeState: ScopeSelectorState;
    @Input()
    isAgencyScopeDisabled: boolean;
    @Input()
    isAccountScopeDisabled: boolean;
    @Input()
    accounts: Account[];
    @Input()
    accountId: string;
    @Input()
    hasAgencyScope: boolean;
    @Output()
    scopeStateChange = new EventEmitter<ScopeSelectorState>();
    @Output()
    accountChange = new EventEmitter<string | string[]>();
}

declare var angular: angular.IAngularStatic;
angular.module('one.downgraded').directive(
    'zemPublisherGroupsScopeSelector',
    downgradeComponent({
        component: PublisherGroupsScopeSelectorComponent,
        propagateDigest: false,
    })
);
