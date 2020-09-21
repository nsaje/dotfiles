import {TestBed, ComponentFixture} from '@angular/core/testing';
import {FormsModule} from '@angular/forms';
import {SharedModule} from '../../../../shared/shared.module';
import {ConnectionTypeTargetingComponent} from './connection-type-targeting.component';

describe('ConnectionTypeTargetingComponent', () => {
    let component: ConnectionTypeTargetingComponent;
    let fixture: ComponentFixture<ConnectionTypeTargetingComponent>;

    beforeEach(() => {
        TestBed.configureTestingModule({
            declarations: [ConnectionTypeTargetingComponent],
            imports: [FormsModule, SharedModule],
        });
    });

    beforeEach(() => {
        fixture = TestBed.createComponent(ConnectionTypeTargetingComponent);
        component = fixture.componentInstance;
    });

    it('should be correctly initialized', () => {
        expect(component).toBeDefined();
    });
});
