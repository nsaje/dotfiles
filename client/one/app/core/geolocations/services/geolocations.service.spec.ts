import {GeolocationsEndpoint} from './geolocations.endpoint';
import {GeolocationsService} from './geolocations.service';
import {RequestStateUpdater} from '../../../shared/types/request-state-updater';
import {Geolocation} from '../types/geolocation';
import {GeolocationType} from '../../../app.constants';
import {asapScheduler, of} from 'rxjs';

describe('GeolocationsService', () => {
    let service: GeolocationsService;
    let geolocationsEndpointStub: jasmine.SpyObj<GeolocationsEndpoint>;
    let requestStateUpdater: RequestStateUpdater;

    beforeEach(() => {
        geolocationsEndpointStub = jasmine.createSpyObj(
            GeolocationsEndpoint.name,
            ['list']
        );

        service = new GeolocationsService(geolocationsEndpointStub);

        requestStateUpdater = (requestName, requestState) => {};
    });

    it('should list geolocations via endpoint', () => {
        const nameContains = 'aust';
        const types = [GeolocationType.COUNTRY];
        const keys: string[] | null = null;
        const limit = 20;
        const offset = 0;

        const mockedGeolocations: Geolocation[] = [
            {
                key: 'AU',
                type: GeolocationType.COUNTRY,
                name: 'Australia',
                outbrainId: 'dafd9b2285eb829458b9982a9ff8792b',
                woeid: '23424748',
                facebookKey: 'AU',
            },
            {
                key: 'AT',
                type: GeolocationType.COUNTRY,
                name: 'Austria',
                outbrainId: 'dec651d8904b326ccbd3ad568e18abb9',
                woeid: '23424750',
                facebookKey: 'AT',
            },
        ];

        geolocationsEndpointStub.list.and
            .returnValue(of(mockedGeolocations, asapScheduler))
            .calls.reset();

        service
            .list(nameContains, types, keys, limit, offset, requestStateUpdater)
            .subscribe(geolocations => {
                expect(geolocations).toEqual(mockedGeolocations);
            });

        expect(geolocationsEndpointStub.list).toHaveBeenCalledTimes(1);
        expect(geolocationsEndpointStub.list).toHaveBeenCalledWith(
            nameContains,
            types,
            keys,
            limit,
            offset,
            requestStateUpdater
        );
    });
});
