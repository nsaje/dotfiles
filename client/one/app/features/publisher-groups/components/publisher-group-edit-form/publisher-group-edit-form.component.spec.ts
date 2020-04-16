import {TestBed, ComponentFixture} from '@angular/core/testing';
import {FormsModule} from '@angular/forms';
import {PublisherGroupEditFormComponent} from './publisher-group-edit-form.component';
import {NgSelectModule} from '@ng-select/ng-select';
import {NgbDatepickerModule} from '@ng-bootstrap/ng-bootstrap';
import {SharedModule} from '../../../../shared/shared.module';

describe('PublisherGroupEditFormComponent', () => {
    let component: PublisherGroupEditFormComponent;
    let fixture: ComponentFixture<PublisherGroupEditFormComponent>;

    beforeEach(() => {
        TestBed.configureTestingModule({
            declarations: [PublisherGroupEditFormComponent],
            imports: [
                FormsModule,
                NgSelectModule,
                NgbDatepickerModule,
                SharedModule,
            ],
        });
    });

    beforeEach(() => {
        fixture = TestBed.createComponent(PublisherGroupEditFormComponent);
        component = fixture.componentInstance;
    });

    it('should be correctly initialized', () => {
        expect(component).toBeDefined();
    });
});
