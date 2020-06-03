import {TestBed, ComponentFixture} from '@angular/core/testing';
import {CreditsGridComponent} from './credits-grid.component';
import {SharedModule} from '../../../../shared/shared.module';
import {CreditGridType} from '../../credits.constants';
import {PaginationState} from '../../../../shared/components/smart-grid/types/pagination-state';

describe('CreditsGridComponent', () => {
    let component: CreditsGridComponent;
    let fixture: ComponentFixture<CreditsGridComponent>;
    const mockedPaginationStateEvent: PaginationState = {
        page: 1,
        pageSize: 20,
    };

    beforeEach(() => {
        TestBed.configureTestingModule({
            declarations: [CreditsGridComponent],
            imports: [SharedModule],
        });
    });

    beforeEach(() => {
        fixture = TestBed.createComponent(CreditsGridComponent);
        component = fixture.componentInstance;
        component.creditGridType = CreditGridType.ACTIVE;

        spyOn(component.paginationChange, 'emit').and.stub();
    });

    it('should be correctly initialized', () => {
        expect(component).toBeDefined();
    });

    it('should emit correct active pagination events', () => {
        component.onPaginationChange(mockedPaginationStateEvent);
        expect(component.paginationChange.emit).toHaveBeenCalledWith({
            activePage: 1,
            activePageSize: 20,
        } as any);
        expect(component.paginationChange.emit).toHaveBeenCalledTimes(1);
    });

    it('should emit correct past pagination events', () => {
        component.creditGridType = CreditGridType.PAST;
        component.onPaginationChange(mockedPaginationStateEvent);
        expect(component.paginationChange.emit).toHaveBeenCalledWith({
            pastPage: 1,
            pastPageSize: 20,
        } as any);

        expect(component.paginationChange.emit).toHaveBeenCalledTimes(1);
    });
});
