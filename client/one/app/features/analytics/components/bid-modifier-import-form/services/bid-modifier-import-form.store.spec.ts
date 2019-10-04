import {BidModifiersService} from '../../../../../core/bid-modifiers/services/bid-modifiers.service';
import {BidModifierImportFormStore} from './bid-modifier-import-form.store';
import {Breakdown} from '../../../../../app.constants';
import {fakeAsync, tick} from '@angular/core/testing';
import {of, throwError} from 'rxjs';

describe('BidModifierImportFormStore', () => {
    let serviceStub: jasmine.SpyObj<BidModifiersService>;
    let store: BidModifierImportFormStore;
    let mockedAdGroupId: number;
    let mockedBreakdown: Breakdown;
    let mockedFile: any;

    beforeEach(() => {
        serviceStub = jasmine.createSpyObj(BidModifiersService.name, [
            'importFromFile',
        ]);
        store = new BidModifierImportFormStore(serviceStub);
        mockedAdGroupId = 12345;
        mockedBreakdown = Breakdown.DEVICE;
        mockedFile = {
            name: 'file.csv',
        };
    });

    it('should correctly import bid modifiers from file', fakeAsync(() => {
        store.init(mockedAdGroupId, mockedBreakdown);
        store.updateFile(mockedFile);

        serviceStub.importFromFile.and.returnValue(of()).calls.reset();

        store.import();
        tick();

        expect(serviceStub.importFromFile).toHaveBeenCalledTimes(1);
        expect(serviceStub.importFromFile).toHaveBeenCalledWith(
            mockedAdGroupId,
            mockedBreakdown,
            mockedFile,
            jasmine.any(Function)
        );
    }));

    it('should correctly handle errors when importing bid modifiers from file', fakeAsync(() => {
        store.init(mockedAdGroupId, mockedBreakdown);
        store.updateFile(mockedFile);

        serviceStub.importFromFile.and
            .returnValue(
                throwError({
                    message: 'Error message',
                    error: {
                        details: {
                            file: 'Errors in CSV file!',
                        },
                    },
                })
            )
            .calls.reset();

        store.import();
        tick();

        expect(serviceStub.importFromFile).toHaveBeenCalledTimes(1);
        expect(serviceStub.importFromFile).toHaveBeenCalledWith(
            mockedAdGroupId,
            mockedBreakdown,
            mockedFile,
            jasmine.any(Function)
        );
        expect(store.state.fieldsErrors).toEqual({
            errorFileUrl: null,
            file: 'Errors in CSV file!',
        });
    }));
});
