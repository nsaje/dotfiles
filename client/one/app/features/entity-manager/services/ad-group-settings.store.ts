import {Injectable, OnDestroy, Inject} from '@angular/core';
import {Store} from 'rxjs-observable-store';
import {Subject} from 'rxjs';
import {AdGroupSettingsStoreState} from './ad-group-settings.store.state';
import {AdGroupService} from '../../../core/entities/services/ad-group.service';

@Injectable()
export class AdGroupSettingsStore extends Store<AdGroupSettingsStoreState>
    implements OnDestroy {
    private ngUnsubscribe$: Subject<undefined> = new Subject();

    constructor(
        private adGroupService: AdGroupService,
        @Inject('zemNavigationNewService') private zemNavigationNewService: any
    ) {
        super(new AdGroupSettingsStoreState());
    }

    loadSettings(id: number): void {
        if (!id) {
            return;
        }
        this.adGroupService.get(id).subscribe(adGroup => {
            this.setState({...this.state, adGroup: adGroup});
        });
    }

    saveSettings(): Promise<boolean> {
        return new Promise<boolean>((resolve, reject) => {
            // TODO (jurebajt): Add request state updater callback
            this.adGroupService.save(this.state.adGroup).subscribe(
                () => {
                    const isNewEntity = this.state.adGroup.id === null;
                    if (isNewEntity) {
                        // TODO (jurebajt): Redirect to entity's analytics page
                        resolve(false);
                    }
                    resolve(true);
                },
                errors => {
                    // TODO (jurebajt): Set state errors
                    reject(false);
                }
            );
        });
    }

    archiveEntity() {
        // TODO (jurebajt): Add request state updater callback
        this.adGroupService.archive(this.state.adGroup.id).subscribe(
            () => {
                this.zemNavigationNewService.refreshState();
            },
            errors => {
                // TODO (jurebajt): Set state errors
            }
        );
    }

    ngOnDestroy(): void {
        this.ngUnsubscribe$.next();
        this.ngUnsubscribe$.complete();
    }
}
