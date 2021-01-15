import {TestBed, ComponentFixture} from '@angular/core/testing';
import {FormsModule} from '@angular/forms';
import {CreativesActionsComponent} from './creatives-actions.component';
import {SharedModule} from '../../../../../shared/shared.module';

describe('CreativesActionsComponent', () => {
    let component: CreativesActionsComponent;
    let fixture: ComponentFixture<CreativesActionsComponent>;

    beforeEach(() => {
        TestBed.configureTestingModule({
            declarations: [CreativesActionsComponent],
            imports: [FormsModule, SharedModule],
        });
    });

    beforeEach(() => {
        fixture = TestBed.createComponent(CreativesActionsComponent);
        component = fixture.componentInstance;
    });

    it('should be correctly initialized', () => {
        expect(component).toBeDefined();
    });
});
