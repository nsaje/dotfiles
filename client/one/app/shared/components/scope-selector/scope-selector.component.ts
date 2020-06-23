import './scope-selector.component.less';

import {
    Component,
    ChangeDetectionStrategy,
    Input,
    Output,
    EventEmitter,
    ContentChild,
    TemplateRef,
    OnChanges,
    SimpleChanges,
} from '@angular/core';
import {ScopeSelectorState} from './scope-selector.constants';
import {FieldErrors} from '../../types/field-errors';

@Component({
    selector: 'zem-scope-selector',
    templateUrl: './scope-selector.component.html',
    changeDetection: ChangeDetectionStrategy.OnPush,
})
export class ScopeSelectorComponent implements OnChanges {
    @Input()
    scopeState: ScopeSelectorState;
    @Input()
    isAllAccountsScopeVisible: boolean = false;
    @Input()
    isAllAccountsScopeDisabled: boolean;
    @Input()
    isAgencyScopeDisabled: boolean;
    @Input()
    isAccountScopeDisabled: boolean;
    @Input()
    allAccountsErrors: FieldErrors = [];
    @Input()
    agencyErrors: FieldErrors = [];
    @Input()
    accountErrors: FieldErrors = [];
    @Output()
    scopeStateChange = new EventEmitter<ScopeSelectorState>();

    ScopeSelectorState = ScopeSelectorState;
    errors: FieldErrors = [];

    @ContentChild('allAccountsScopeHeaderTemplate', {
        read: TemplateRef,
        static: false,
    })
    allAccountsScopeHeaderTemplate: TemplateRef<any>;

    @ContentChild('allAccountsScopeContentTemplate', {
        read: TemplateRef,
        static: false,
    })
    allAccountsScopeContentTemplate: TemplateRef<any>;

    @ContentChild('agencyScopeHeaderTemplate', {
        read: TemplateRef,
        static: false,
    })
    agencyScopeHeaderTemplate: TemplateRef<any>;

    @ContentChild('agencyScopeContentTemplate', {
        read: TemplateRef,
        static: false,
    })
    agencyScopeContentTemplate: TemplateRef<any>;

    @ContentChild('accountScopeHeaderTemplate', {
        read: TemplateRef,
        static: false,
    })
    accountScopeHeaderTemplate: TemplateRef<any>;

    @ContentChild('accountScopeContentTemplate', {
        read: TemplateRef,
        static: false,
    })
    accountScopeContentTemplate: TemplateRef<any>;

    ngOnChanges(changes: SimpleChanges): void {
        if (
            changes.allAccountsErrors ||
            changes.agencyErrors ||
            changes.accountErrors
        ) {
            this.errors = [
                ...(this.allAccountsErrors || []),
                ...(this.agencyErrors || []),
                ...(this.accountErrors || []),
            ];
        }
    }
}
