import {TestBed, ComponentFixture} from '@angular/core/testing';
import {FormsModule} from '@angular/forms';
import {SharedModule} from '../../../../shared/shared.module';
import {DealsLibraryView} from './deals-library.view';

describe('DealsLibraryView', () => {
    let component: DealsLibraryView;
    let fixture: ComponentFixture<DealsLibraryView>;

    beforeEach(() => {
        TestBed.configureTestingModule({
            declarations: [DealsLibraryView],
            imports: [FormsModule, SharedModule],
        });
    });

    beforeEach(() => {
        fixture = TestBed.createComponent(DealsLibraryView);
        component = fixture.componentInstance;
    });

    it('should be correctly initialized', () => {
        expect(component).toBeDefined();
    });
});
