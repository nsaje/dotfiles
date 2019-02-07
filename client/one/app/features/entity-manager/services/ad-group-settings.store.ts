import {Injectable, OnDestroy, Inject} from '@angular/core';
import {Store} from 'rxjs-observable-store';
import {Subject} from 'rxjs';
import {AdGroupSettingsStoreState} from './ad-group-settings.store.state';
import {AdGroupService} from '../../../core/entities/services/ad-group.service';
import {HttpErrorResponse} from '@angular/common/http';
import {AdGroup} from '../../../core/entities/types/ad-group/ad-group';
import {RequestStateUpdater} from '../../../shared/types/request-state-updater';
import * as endpointHelpers from '../../../shared/helpers/endpoint.helpers';
import * as commonHelpers from '../../../shared/helpers/common.helpers';
import {AdGroupWithExtras} from '../../../core/entities/types/ad-group/ad-group-with-extras';

@Injectable()
export class AdGroupSettingsStore extends Store<AdGroupSettingsStoreState>
    implements OnDestroy {
    private ngUnsubscribe$: Subject<undefined> = new Subject();
    private requestStateUpdater: RequestStateUpdater;

    constructor(
        private adGroupService: AdGroupService,
        @Inject('zemNavigationNewService') private zemNavigationNewService: any
    ) {
        super(new AdGroupSettingsStoreState());
        this.requestStateUpdater = endpointHelpers.getRequestStateUpdater(this);
    }

    loadEntityDefaults(campaignId: number): void {
        this.adGroupService
            .defaults(campaignId, this.requestStateUpdater)
            .subscribe(
                (adGroupWithExtras: AdGroupWithExtras) => {
                    this.setState({
                        ...this.state,
                        entity: adGroupWithExtras.adGroup,
                        extras: adGroupWithExtras.extras,
                    });
                },
                error => {}
            );
    }

    loadEntity(id: number): void {
        this.adGroupService.get(id, this.requestStateUpdater).subscribe(
            (adGroupWithExtras: AdGroupWithExtras) => {
                this.setState({
                    ...this.state,
                    entity: adGroupWithExtras.adGroup,
                    extras: adGroupWithExtras.extras,
                });
            },
            error => {}
        );
    }

    validateEntity(): void {
        this.adGroupService
            .validate(this.state.entity, this.requestStateUpdater)
            .subscribe(
                () => {
                    this.setState({
                        ...this.state,
                        fieldsErrors: {},
                    });
                },
                (error: HttpErrorResponse) => {
                    this.setState({
                        ...this.state,
                        fieldsErrors: commonHelpers.isDefined(error.error)
                            ? commonHelpers.getValueOrDefault(
                                  error.error.details,
                                  {}
                              )
                            : {},
                    });
                }
            );
    }

    saveEntity(): Promise<boolean> {
        return new Promise<boolean>(resolve => {
            this.adGroupService
                .save(this.state.entity, this.requestStateUpdater)
                .subscribe(
                    (adGroup: AdGroup) => {
                        this.setState({
                            ...this.state,
                            entity: adGroup,
                            fieldsErrors: {},
                        });
                        resolve(true);
                    },
                    (error: HttpErrorResponse) => {
                        this.setState({
                            ...this.state,
                            fieldsErrors: commonHelpers.isDefined(error.error)
                                ? commonHelpers.getValueOrDefault(
                                      error.error.details,
                                      {}
                                  )
                                : {},
                        });
                        resolve(false);
                    }
                );
        });
    }

    archiveEntity(): void {
        this.adGroupService
            .archive(this.state.entity.id, this.requestStateUpdater)
            .subscribe(
                () => {
                    this.zemNavigationNewService.refreshState();
                },
                (error: HttpErrorResponse) => {
                    this.setState({
                        ...this.state,
                        fieldsErrors: commonHelpers.isDefined(error.error)
                            ? commonHelpers.getValueOrDefault(
                                  error.error.details,
                                  {}
                              )
                            : {},
                    });
                }
            );
    }

    ngOnDestroy(): void {
        this.ngUnsubscribe$.next();
        this.ngUnsubscribe$.complete();
    }
}
