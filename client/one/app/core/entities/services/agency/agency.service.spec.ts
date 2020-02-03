import {asapScheduler, of} from 'rxjs';
import {RequestStateUpdater} from '../../../../shared/types/request-state-updater';
import {AgencyEndpoint} from './agency.endpoint';
import {AgencyService} from './agency.service';
import {Agency} from '../../types/agency/agency';

describe('AgencyService', () => {
    let service: AgencyService;
    let agencyEndpointStub: jasmine.SpyObj<AgencyEndpoint>;
    let mockedAgency: Agency;
    let requestStateUpdater: RequestStateUpdater;

    beforeEach(() => {
        agencyEndpointStub = jasmine.createSpyObj(AgencyEndpoint.name, [
            'list',
        ]);

        mockedAgency = {
            id: '1',
            name: 'mocked agency',
        };
        service = new AgencyService(agencyEndpointStub);

        requestStateUpdater = (requestName, requestState) => {};
    });

    it('should list all agencies for user via endpoint', () => {
        agencyEndpointStub.list.and
            .returnValue(of([mockedAgency], asapScheduler))
            .calls.reset();

        service.list(requestStateUpdater).subscribe(agencies => {
            expect(agencies[0]).toEqual(mockedAgency);
        });
        expect(agencyEndpointStub.list).toHaveBeenCalledTimes(1);
        expect(agencyEndpointStub.list).toHaveBeenCalledWith(
            requestStateUpdater
        );
    });
});
