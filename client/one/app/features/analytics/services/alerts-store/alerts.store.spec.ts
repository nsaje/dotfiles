import {AlertsService} from '../../../../core/alerts/services/alerts.service';
import {AlertsStore} from './alerts.store';
import {Alert} from '../../../../core/alerts/types/alert';
import {AlertType, Level, Breakdown} from '../../../../app.constants';
import {fakeAsync, tick} from '@angular/core/testing';
import {of, asapScheduler} from 'rxjs';

describe('AlertsStore', () => {
    let alertsServiceStub: jasmine.SpyObj<AlertsService>;
    let store: AlertsStore;

    let mockedAlerts: Alert[];

    beforeEach(() => {
        alertsServiceStub = jasmine.createSpyObj(AlertsService.name, ['list']);
        store = new AlertsStore(alertsServiceStub);

        mockedAlerts = [
            {
                type: AlertType.INFO,
                message: 'Info alert',
                isClosable: false,
            },
            {
                type: AlertType.SUCCESS,
                message: 'Success alert',
                isClosable: false,
            },
            {
                type: AlertType.WARNING,
                message: 'Warning alert',
                isClosable: false,
            },
            {
                type: AlertType.DANGER,
                message: 'Danger alert',
                isClosable: false,
            },
        ];
    });

    it('should correctly initialize store', fakeAsync(() => {
        const level = Level.ACCOUNTS;
        const entityId = '12345';
        const breakdown = Breakdown.PLACEMENT;
        const startDate = new Date(2020, 3, 1);
        const endDate = new Date(2020, 3, 20);

        alertsServiceStub.list.and
            .returnValue(of(mockedAlerts, asapScheduler))
            .calls.reset();

        store.setStore(level, entityId, breakdown, startDate, endDate);
        tick();

        expect(store.state.alerts).toEqual(mockedAlerts);

        expect(alertsServiceStub.list).toHaveBeenCalledTimes(1);
        expect(alertsServiceStub.list).toHaveBeenCalledWith(
            level,
            entityId,
            breakdown,
            startDate,
            endDate,
            jasmine.anything()
        );
    }));

    it('should correctly register alert', fakeAsync(() => {
        const mockedAlert: Alert = {
            type: AlertType.DANGER,
            message: 'Client side Danger alert',
            isClosable: true,
        };

        store.setState({
            ...store.state,
            alerts: mockedAlerts,
        });

        store.registerAlert(mockedAlert);
        tick();

        expect(store.state.alerts.length).toEqual(mockedAlerts.length + 1);
        expect(store.state.alerts.includes(mockedAlert)).toBeTrue();
    }));

    it('should correctly remove alert', fakeAsync(() => {
        const mockedAlert: Alert = {
            type: AlertType.DANGER,
            message: 'Client side Danger alert',
            isClosable: true,
        };

        store.setState({
            ...store.state,
            alerts: [...mockedAlerts, mockedAlert],
        });

        store.removeAlert(mockedAlert);
        tick();

        expect(store.state.alerts.length).toEqual(mockedAlerts.length);
        expect(store.state.alerts.includes(mockedAlert)).toBeFalse();
    }));
});
