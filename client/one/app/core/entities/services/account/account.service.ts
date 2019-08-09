import {Injectable} from '@angular/core';
import {AccountEndpoint} from './account.endpoint';
import {EntitiesUpdatesService} from '../entities-updates.service';
import {RequestStateUpdater} from '../../../../shared/types/request-state-updater';
import {AccountWithExtras} from '../../types/account/account-with-extras';
import {Observable} from 'rxjs';
import {Account} from '../../types/account/account';
import {tap} from 'rxjs/operators';
import {EntityType, EntityUpdateAction} from '../../../../app.constants';
import * as commonHelpers from '../../../../shared/helpers/common.helpers';

@Injectable()
export class AccountService {
    constructor(
        private endpoint: AccountEndpoint,
        private entitiesUpdatesService: EntitiesUpdatesService
    ) {}

    defaults(
        requestStateUpdater: RequestStateUpdater
    ): Observable<AccountWithExtras> {
        return this.endpoint.defaults(requestStateUpdater);
    }

    get(
        id: string,
        requestStateUpdater: RequestStateUpdater
    ): Observable<AccountWithExtras> {
        return this.endpoint.get(id, requestStateUpdater);
    }

    validate(
        account: Partial<Account>,
        requestStateUpdater: RequestStateUpdater
    ): Observable<void> {
        return this.endpoint.validate(account, requestStateUpdater);
    }

    save(
        account: Account,
        requestStateUpdater: RequestStateUpdater
    ): Observable<Account> {
        if (!commonHelpers.isDefined(account.id)) {
            return this.create(account, requestStateUpdater);
        }
        return this.edit(account, requestStateUpdater);
    }

    archive(
        id: string,
        requestStateUpdater: RequestStateUpdater
    ): Observable<Account> {
        return this.endpoint
            .edit({id: id, archived: true}, requestStateUpdater)
            .pipe(
                tap(account => {
                    this.entitiesUpdatesService.registerEntityUpdate({
                        id: account.id,
                        type: EntityType.ACCOUNT,
                        action: EntityUpdateAction.ARCHIVE,
                    });
                })
            );
    }

    private create(
        account: Account,
        requestStateUpdater: RequestStateUpdater
    ): Observable<Account> {
        return this.endpoint.create(account, requestStateUpdater).pipe(
            tap(account => {
                this.entitiesUpdatesService.registerEntityUpdate({
                    id: account.id,
                    type: EntityType.ACCOUNT,
                    action: EntityUpdateAction.CREATE,
                });
            })
        );
    }

    private edit(
        account: Account,
        requestStateUpdater: RequestStateUpdater
    ): Observable<Account> {
        return this.endpoint.edit(account, requestStateUpdater).pipe(
            tap(account => {
                this.entitiesUpdatesService.registerEntityUpdate({
                    id: account.id,
                    type: EntityType.ACCOUNT,
                    action: EntityUpdateAction.EDIT,
                });
            })
        );
    }
}
