import {Injectable} from '@angular/core';
import {Breakdown, Level} from '../../../../app.constants';
import {Alert} from '../../../../core/alerts/types/alert';
import {RequestStateUpdater} from '../../../../shared/types/request-state-updater';
import {Store} from 'rxjs-observable-store';
import {AlertsStoreState} from './alerts.store.state';
import * as storeHelpers from '../../../../shared/helpers/store.helpers';
import {downgradeInjectable} from '@angular/upgrade/static';
import {AlertsService} from '../../../../core/alerts/services/alerts.service';

@Injectable()
export class AlertsStore extends Store<AlertsStoreState> {
    private requestStateUpdater: RequestStateUpdater;

    constructor(private alertsService: AlertsService) {
        super(new AlertsStoreState());
        this.requestStateUpdater = storeHelpers.getStoreRequestStateUpdater(
            this
        );
    }

    setStore(
        level: Level,
        entityId: string | null,
        breakdown: Breakdown | null,
        startDate: Date | null,
        endDate: Date | null
    ) {
        const subscription = this.alertsService
            .list(
                level,
                entityId,
                breakdown,
                startDate,
                endDate,
                this.requestStateUpdater
            )
            .subscribe((data: Alert[]) => {
                this.setState({
                    ...this.state,
                    alerts: data,
                });
                subscription.unsubscribe();
            });
    }

    registerAlert(alert: Alert) {
        this.patchState([...this.state.alerts, alert], 'alerts');
    }

    removeAlert(alert: Alert) {
        const alerts = this.state.alerts.filter(item => {
            return item !== alert;
        });
        this.patchState(alerts, 'alerts');
    }
}

declare var angular: angular.IAngularStatic;
angular
    .module('one.downgraded')
    .factory('zemAlertsStore', downgradeInjectable(AlertsStore));
