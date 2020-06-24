import {TestBed, ComponentFixture} from '@angular/core/testing';
import {FormsModule} from '@angular/forms';
import {SharedModule} from '../../../../shared/shared.module';
import {EntityPermissionSelectorComponent} from './entity-permission-selector.component';
import Spy = jasmine.Spy;

describe('EntityPermissionSelectorComponent', () => {
    let component: EntityPermissionSelectorComponent;
    let fixture: ComponentFixture<EntityPermissionSelectorComponent>;
    let selectionChangeSpy: Spy;

    beforeEach(() => {
        TestBed.configureTestingModule({
            declarations: [EntityPermissionSelectorComponent],
            imports: [FormsModule, SharedModule],
        });
    });

    beforeEach(() => {
        fixture = TestBed.createComponent(EntityPermissionSelectorComponent);
        component = fixture.componentInstance;
    });

    it('should be correctly initialized', () => {
        expect(component).toBeDefined();
    });

    it('should emit changed values after an option is toggled to true', () => {
        component.selection = {
            read: true,
            write: false,
            user: undefined,
            budget: true,
            budget_margin: false,
            agency_spend_margin: undefined,
            media_cost_data_cost_licence_fee: false,
        };

        selectionChangeSpy = spyOn(
            component.selectionChange,
            'emit'
        ).and.stub();

        component.toggleOption({
            value: 'write',
            selected: true,
            displayValue: '',
            description: '',
        });

        expect(component.selectionChange.emit).toHaveBeenCalledWith({
            read: true,
            write: true,
            user: undefined,
            budget: true,
            budget_margin: false,
            agency_spend_margin: undefined,
            media_cost_data_cost_licence_fee: false,
        });
    });

    it('should emit changed values after an option is toggled to false', () => {
        component.selection = {
            read: true,
            write: false,
            user: undefined,
            budget: true,
            budget_margin: false,
            agency_spend_margin: undefined,
            media_cost_data_cost_licence_fee: false,
        };

        selectionChangeSpy = spyOn(
            component.selectionChange,
            'emit'
        ).and.stub();

        component.toggleOption({
            value: 'budget',
            selected: false,
            displayValue: '',
            description: '',
        });

        expect(component.selectionChange.emit).toHaveBeenCalledWith({
            read: true,
            write: false,
            user: undefined,
            budget: false,
            budget_margin: false,
            agency_spend_margin: undefined,
            media_cost_data_cost_licence_fee: false,
        });
    });

    it('should emit changed values after an undefined option is toggled to true', () => {
        component.selection = {
            read: true,
            write: false,
            user: undefined,
            budget: true,
            budget_margin: false,
            agency_spend_margin: undefined,
            media_cost_data_cost_licence_fee: false,
        };

        selectionChangeSpy = spyOn(
            component.selectionChange,
            'emit'
        ).and.stub();

        component.toggleOption({
            value: 'user',
            selected: true,
            displayValue: '',
            description: '',
        });

        expect(component.selectionChange.emit).toHaveBeenCalledWith({
            read: true,
            write: false,
            user: true,
            budget: true,
            budget_margin: false,
            agency_spend_margin: undefined,
            media_cost_data_cost_licence_fee: false,
        });
    });

    it('should emit changed values after a reporting option is toggled to true', () => {
        component.selection = {
            read: true,
            write: false,
            user: undefined,
            budget: true,
            budget_margin: false,
            agency_spend_margin: undefined,
            media_cost_data_cost_licence_fee: false,
        };

        selectionChangeSpy = spyOn(
            component.selectionChange,
            'emit'
        ).and.stub();

        component.toggleReportingOptions([
            {
                value: 'total_spend',
                selected: true,
                displayValue: '',
            },
            {
                value: 'agency_spend_margin',
                selected: true,
                displayValue: '',
            },
            {
                value: 'media_cost_data_cost_licence_fee',
                selected: false,
                displayValue: '',
            },
        ]);

        expect(component.selectionChange.emit).toHaveBeenCalledWith({
            read: true,
            write: false,
            user: undefined,
            budget: true,
            budget_margin: false,
            agency_spend_margin: true,
            media_cost_data_cost_licence_fee: false,
        });
    });

    it('should emit changed values after a reporting option is toggled to false', () => {
        component.selection = {
            read: true,
            write: false,
            user: undefined,
            budget: true,
            budget_margin: false,
            agency_spend_margin: true,
            media_cost_data_cost_licence_fee: true,
        };

        selectionChangeSpy = spyOn(
            component.selectionChange,
            'emit'
        ).and.stub();

        component.toggleReportingOptions([
            {
                value: 'total_spend',
                selected: true,
                displayValue: '',
            },
            {
                value: 'agency_spend_margin',
                selected: true,
                displayValue: '',
            },
            {
                value: 'media_cost_data_cost_licence_fee',
                selected: false,
                displayValue: '',
            },
        ]);

        expect(component.selectionChange.emit).toHaveBeenCalledWith({
            read: true,
            write: false,
            user: undefined,
            budget: true,
            budget_margin: false,
            agency_spend_margin: true,
            media_cost_data_cost_licence_fee: false,
        });
    });
});
