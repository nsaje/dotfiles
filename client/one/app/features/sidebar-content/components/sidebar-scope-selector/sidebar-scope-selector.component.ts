import './sidebar-scope-selector.component.less';

import {
    Component,
    ChangeDetectionStrategy,
    Input,
    Output,
    EventEmitter,
    OnChanges,
    SimpleChanges,
} from '@angular/core';
import {Agency} from '../../../../core/entities/types/agency/agency';
import * as arrayHelpers from '../../../../shared/helpers/array.helpers';

@Component({
    selector: 'zem-sidebar-scope-selector',
    templateUrl: './sidebar-scope-selector.component.html',
    changeDetection: ChangeDetectionStrategy.OnPush,
})
export class SidebarScopeSelectorComponent implements OnChanges {
    @Input()
    agencies: Agency[] | null;
    @Input()
    selectedAgencyId: string | null;
    @Input()
    hasAgencyScope: boolean;
    @Input()
    accounts: Account[] | null;
    @Input()
    selectedAccountId: string | null;
    @Input()
    isOpen: boolean;

    @Output()
    agencyChange = new EventEmitter<string>();
    @Output()
    accountChange = new EventEmitter<string | null>();

    canChangeAgency: boolean;

    ngOnChanges(changes: SimpleChanges): void {
        if (changes.agencies) {
            this.canChangeAgency = !arrayHelpers.isEmpty(this.agencies);
        }
    }

    onAgencyChange(agencyId: string) {
        this.agencyChange.emit(agencyId);
    }

    onAccountChange(accountId: string | null) {
        this.accountChange.emit(accountId);
    }
}
