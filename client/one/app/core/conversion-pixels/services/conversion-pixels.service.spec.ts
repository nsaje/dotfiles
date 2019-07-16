import {ConversionPixelsEndpoint} from './conversion-pixels.endpoint';
import {ConversionPixelsService} from './conversion-pixels.service';
import {RequestStateUpdater} from '../../../shared/types/request-state-updater';
import {asapScheduler, of} from 'rxjs';
import {ConversionPixel} from '../types/conversion-pixel';

describe('ConversionPixelsService', () => {
    let service: ConversionPixelsService;
    let conversionPixelsEndpointStub: jasmine.SpyObj<ConversionPixelsEndpoint>;
    let requestStateUpdater: RequestStateUpdater;

    beforeEach(() => {
        conversionPixelsEndpointStub = jasmine.createSpyObj(
            ConversionPixelsEndpoint.name,
            ['list', 'create', 'edit']
        );

        service = new ConversionPixelsService(conversionPixelsEndpointStub);

        requestStateUpdater = (requestName, requestState) => {};
    });

    it('should list conversion pixels via endpoint', () => {
        const accountId = '12345';
        const mockedConversionPixels: ConversionPixel[] = [
            {
                id: '123',
                accountId: '12345',
                name: 'Zemanta Pixel 1',
                url: 'http://one.zemanta.com/pixel_1',
                lastTriggered: new Date(),
                impressions: 123,
                conversionWindows: [],
            },
            {
                id: '123',
                accountId: '12345',
                name: 'Zemanta Pixel 2',
                url: 'http://one.zemanta.com/pixel_2',
                lastTriggered: new Date(),
                impressions: 124,
                conversionWindows: [],
            },
        ];

        conversionPixelsEndpointStub.list.and
            .returnValue(of(mockedConversionPixels, asapScheduler))
            .calls.reset();

        service
            .list(accountId, requestStateUpdater)
            .subscribe(conversionPixels => {
                expect(conversionPixels).toEqual(mockedConversionPixels);
            });
        expect(conversionPixelsEndpointStub.list).toHaveBeenCalledTimes(1);
        expect(conversionPixelsEndpointStub.list).toHaveBeenCalledWith(
            accountId,
            requestStateUpdater
        );
    });

    it('should create conversion pixel via endpoint', () => {
        const accountId = '12345';
        const conversionPixelName = 'Zemanta New Conversion Pixel';
        const mockedConversionPixel: ConversionPixel = {
            id: '125',
            accountId: accountId,
            name: conversionPixelName,
            url: 'http://one.zemanta.com/pixel_3',
            lastTriggered: new Date(),
            impressions: 124,
            conversionWindows: [],
        };

        conversionPixelsEndpointStub.create.and
            .returnValue(of(mockedConversionPixel, asapScheduler))
            .calls.reset();

        service
            .create(accountId, conversionPixelName, requestStateUpdater)
            .subscribe(conversionPixel => {
                expect(conversionPixel).toEqual(mockedConversionPixel);
            });

        expect(conversionPixelsEndpointStub.create).toHaveBeenCalledTimes(1);
        expect(conversionPixelsEndpointStub.create).toHaveBeenCalledWith(
            accountId,
            conversionPixelName,
            requestStateUpdater
        );
    });

    it('should edit conversion pixel via endpoint', () => {
        const accountId = '12345';
        const mockedConversionPixel: ConversionPixel = {
            id: '126',
            accountId: accountId,
            name: 'Zemanta Conversion Pixel 4',
            url: 'http://one.zemanta.com/pixel_4',
            lastTriggered: new Date(),
            impressions: 124,
            conversionWindows: [],
        };

        conversionPixelsEndpointStub.edit.and
            .returnValue(of(mockedConversionPixel, asapScheduler))
            .calls.reset();

        service
            .edit(mockedConversionPixel, requestStateUpdater)
            .subscribe(conversionPixel => {
                expect(conversionPixel).toEqual(mockedConversionPixel);
            });

        expect(conversionPixelsEndpointStub.edit).toHaveBeenCalledTimes(1);
        expect(conversionPixelsEndpointStub.edit).toHaveBeenCalledWith(
            mockedConversionPixel,
            requestStateUpdater
        );
    });
});
