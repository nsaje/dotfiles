import './account-list-item.component.less';
import {
    Input,
    Component,
    ChangeDetectionStrategy,
    OnChanges,
} from '@angular/core';

@Component({
    selector: 'zem-account-list-item',
    templateUrl: './account-list-item.component.html',
    changeDetection: ChangeDetectionStrategy.OnPush,
})
export class AccountListItemComponent implements OnChanges {
    @Input()
    account: Account;
    @Input()
    selected: boolean;

    accountUrl: string;

    ngOnChanges() {
        this.accountUrl = this.account
            ? `/v2/analytics/account/${this.account.id}`
            : undefined;
    }
}