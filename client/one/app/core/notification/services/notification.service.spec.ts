import {NotificationService} from './notification.service';
import {BidModifiersService} from '../../bid-modifiers/services/bid-modifiers.service';
import {ToastrService} from 'ngx-toastr';

describe('NotificationService', () => {
    let service: NotificationService;
    let serviceStub: jasmine.SpyObj<ToastrService>;

    beforeEach(() => {
        serviceStub = jasmine.createSpyObj(ToastrService.name, [
            'info',
            'success',
            'warning',
            'error',
        ]);
        service = new NotificationService(serviceStub);
    });

    it('should call toastr info', () => {
        service.info('Hello');

        expect(serviceStub.info).toHaveBeenCalledWith('Hello', undefined, {
            timeOut: 0,
        });
    });

    it('should call toastr success', () => {
        service.success('Hello');

        expect(serviceStub.success).toHaveBeenCalledWith('Hello', undefined, {
            timeOut: 0,
        });
    });

    it('should call toastr warning', () => {
        service.warning('Hello');

        expect(serviceStub.warning).toHaveBeenCalledWith('Hello', undefined, {
            timeOut: 0,
        });
    });

    it('should call toastr error', () => {
        service.error('Hello');

        expect(serviceStub.error).toHaveBeenCalledWith('Hello', undefined, {
            timeOut: 0,
        });
    });

    it('should use a timeout of 0 if no timeout is supplied in the options', () => {
        service.info('Hello', 'World', {});

        expect(serviceStub.info).toHaveBeenCalledWith('Hello', 'World', {
            timeOut: 0,
        });
    });

    it('should use the supplied timeout if it is supplied in the options', () => {
        service.info('Hello', 'World', {timeout: 5000});

        expect(serviceStub.info).toHaveBeenCalledWith('Hello', 'World', {
            timeOut: 5000,
        });
    });
});
