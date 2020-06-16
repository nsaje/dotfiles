import {AlertsService} from './alerts.service';
import {AlertsEndpoint} from './alerts.endpoint';
import {RequestStateUpdater} from '../../../shared/types/request-state-updater';
import {of, asapScheduler} from 'rxjs';
import {Alert} from '../types/alert';
import {AlertType, Level, Breakdown} from '../../../app.constants';

describe('AlertsService', () => {
    let service: AlertsService;
    let alertsEndpointStub: jasmine.SpyObj<AlertsEndpoint>;
    let requestStateUpdater: RequestStateUpdater;

    let mockedAlerts: Alert[];

    beforeEach(() => {
        alertsEndpointStub = jasmine.createSpyObj(AlertsEndpoint.name, [
            'list',
        ]);
        service = new AlertsService(alertsEndpointStub);
        requestStateUpdater = (requestName, requestState) => {};

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

    it('should get alerts via endpoint', () => {
        const level = Level.ACCOUNTS;
        const entityId = '12345';
        const breakdown = Breakdown.PLACEMENT;
        const startDate = new Date(2020, 3, 1);
        const endDate = new Date(2020, 3, 20);

        alertsEndpointStub.list.and
            .returnValue(of(mockedAlerts, asapScheduler))
            .calls.reset();

        service
            .list(
                level,
                entityId,
                breakdown,
                startDate,
                endDate,
                requestStateUpdater
            )
            .subscribe(alerts => {
                expect(alerts).toEqual(mockedAlerts);
            });
        expect(alertsEndpointStub.list).toHaveBeenCalledTimes(1);
        expect(alertsEndpointStub.list).toHaveBeenCalledWith(
            level,
            entityId,
            breakdown,
            startDate,
            endDate,
            requestStateUpdater
        );
    });
});
