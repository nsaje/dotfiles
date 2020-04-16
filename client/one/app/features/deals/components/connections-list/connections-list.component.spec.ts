import {TestBed, ComponentFixture} from '@angular/core/testing';
import {FormsModule} from '@angular/forms';
import {SharedModule} from '../../../../shared/shared.module';
import {ConnectionsListComponent} from './connections-list.component';

describe('ConnectionsListComponent', () => {
    let component: ConnectionsListComponent;
    let fixture: ComponentFixture<ConnectionsListComponent>;

    beforeEach(() => {
        TestBed.configureTestingModule({
            declarations: [ConnectionsListComponent],
            imports: [FormsModule, SharedModule],
        });
    });

    beforeEach(() => {
        fixture = TestBed.createComponent(ConnectionsListComponent);
        component = fixture.componentInstance;
    });

    it('should be correctly initialized', () => {
        expect(component).toBeDefined();
    });
});
