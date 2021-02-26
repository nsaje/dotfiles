import {asapScheduler, of} from 'rxjs';
import {RequestStateUpdater} from '../../../shared/types/request-state-updater';
import {EntityHistoryEndpoint} from './entity-history.endpoint';
import {EntityHistoryService} from './entity-history.service';
import {EntityHistory} from '../types/entity-history';
import {
    EntityHistoryLevel,
    EntityHistoryOrder,
} from '../entity-history.constants';

describe('EntityHistoryService', () => {
    let service: EntityHistoryService;
    let endpointStub: jasmine.SpyObj<EntityHistoryEndpoint>;
    let requestStateUpdater: RequestStateUpdater;
    const entityId = '1234';
    const level = EntityHistoryLevel.AD_GROUP;
    const order = EntityHistoryOrder.CREATED_DT_DESC;
    const fromDate = new Date();

    const mockedEntityHistory: EntityHistory[] = [
        {
            datetime: fromDate,
            changedBy: 'John Doe',
            changedText:
                'Added campaign goal "30.00000 Time on Site - Seconds"',
        },
    ];

    beforeEach(() => {
        endpointStub = jasmine.createSpyObj(EntityHistoryEndpoint.name, [
            'getHistory',
        ]);

        service = new EntityHistoryService(endpointStub);
        requestStateUpdater = (requestName, requestState) => {};
    });

    it('should correctly get bid insights', () => {
        endpointStub.getHistory.and
            .returnValue(of(mockedEntityHistory, asapScheduler))
            .calls.reset();

        service
            .getHistory(entityId, level, order, fromDate, requestStateUpdater)
            .subscribe(history => {
                expect(history).toEqual(mockedEntityHistory);
            });

        expect(endpointStub.getHistory).toHaveBeenCalledTimes(1);
        expect(endpointStub.getHistory).toHaveBeenCalledWith(
            entityId,
            level,
            order,
            fromDate,
            requestStateUpdater
        );
    });
});
