import {TestBed, ComponentFixture} from '@angular/core/testing';
import {FormsModule} from '@angular/forms';
import {SharedModule} from '../../../../shared/shared.module';
import {DealsLibraryActionsComponent} from './deals-library-actions.component';

describe('DealsLibraryActionsComponent', () => {
    let component: DealsLibraryActionsComponent;
    let fixture: ComponentFixture<DealsLibraryActionsComponent>;

    beforeEach(() => {
        TestBed.configureTestingModule({
            declarations: [DealsLibraryActionsComponent],
            imports: [FormsModule, SharedModule],
        });
    });

    beforeEach(() => {
        fixture = TestBed.createComponent(DealsLibraryActionsComponent);
        component = fixture.componentInstance;
    });

    it('should be correctly initialized', () => {
        expect(component).toBeDefined();
    });
});
