import {TestBed, ComponentFixture} from '@angular/core/testing';
import {FormsModule} from '@angular/forms';
import {MultiStepMenuComponent} from './multi-step-menu.component';
import {OnChanges, SimpleChange, SimpleChanges} from '@angular/core';
import {MultiStepMenuOption} from './types/multi-step-menu-option';
import {MultiStepComponent} from '../multi-step/multi-step.component';
import {MultiStepStepDirective} from '../multi-step/multi-step-step.directive';

describe('MultiStepMenuComponent', () => {
    let component: MultiStepMenuComponent;
    let fixture: ComponentFixture<MultiStepMenuComponent>;

    function changeComponent<T extends OnChanges>(
        component: T,
        changes: Partial<T>
    ) {
        const simpleChanges: SimpleChanges = {};

        Object.keys(changes).forEach(changeKey => {
            component[changeKey] = changes[changeKey];
            simpleChanges[changeKey] = new SimpleChange(
                null,
                changes[changeKey],
                false
            );
        });
        component.ngOnChanges(simpleChanges);
    }

    beforeEach(() => {
        TestBed.configureTestingModule({
            declarations: [
                MultiStepMenuComponent,
                MultiStepComponent,
                MultiStepStepDirective,
            ],
            imports: [FormsModule],
        });
    });

    beforeEach(() => {
        fixture = TestBed.createComponent(MultiStepMenuComponent);
        component = fixture.componentInstance;
    });

    it('should be correctly initialized', () => {
        expect(component).toBeDefined();
    });

    it('should correctly initialize menu structure', () => {
        const mockedHandler: () => void = () => {};
        let mockedOptions: MultiStepMenuOption[] = [];
        changeComponent(component, {options: mockedOptions});

        expect(component.steps).toEqual([
            {
                stepId: 1,
                name: null,
                parentStepId: null,
                items: [],
            },
        ]);

        ///////////////////////////////////////////////////////////////

        mockedOptions = [
            {
                name: 'test',
                handler: mockedHandler,
            },
        ];
        changeComponent(component, {options: mockedOptions});

        expect(component.steps).toEqual([
            {
                stepId: 1,
                name: null,
                parentStepId: null,
                items: [
                    {
                        name: 'test',
                        description: undefined,
                        handler: mockedHandler,
                        hasNextStep: false,
                    },
                ],
            },
        ]);

        ///////////////////////////////////////////////////////////////

        mockedOptions = [
            {
                name: 'test',
                description: 'This is a test',
                handler: mockedHandler,
            },
        ];
        changeComponent(component, {options: mockedOptions});

        expect(component.steps).toEqual([
            {
                stepId: 1,
                name: null,
                parentStepId: null,
                items: [
                    {
                        name: 'test',
                        description: 'This is a test',
                        handler: mockedHandler,
                        hasNextStep: false,
                    },
                ],
            },
        ]);

        ///////////////////////////////////////////////////////////////
        mockedOptions = [
            {
                name: 'Fruits',
                description: 'Click to see a list of fruits',
                nextOptions: [
                    {
                        name: 'Apples',
                        description: 'Very delicious',
                        handler: mockedHandler,
                    },
                    {
                        name: 'Citruses',
                        description: 'Very healthy',
                        nextOptions: [
                            {
                                name: 'Oranges',
                                handler: mockedHandler,
                            },
                            {
                                name: 'Lemons',
                                handler: mockedHandler,
                            },
                        ],
                    },
                ],
            },
            {
                name: 'Vegetables',
                description: 'Click to see a list of vegetables',
                nextOptions: [
                    {
                        name: 'Potatoes',
                        handler: mockedHandler,
                    },
                    {
                        name: 'Cucumbers',
                        handler: mockedHandler,
                    },
                ],
            },
        ];
        changeComponent(component, {options: mockedOptions});

        expect(component.steps).toEqual([
            {
                stepId: 1,
                name: null,
                parentStepId: null,
                items: [
                    {
                        name: 'Fruits',
                        description: 'Click to see a list of fruits',
                        handler: jasmine.any(Function),
                        hasNextStep: true,
                    },
                    {
                        name: 'Vegetables',
                        description: 'Click to see a list of vegetables',
                        handler: jasmine.any(Function),
                        hasNextStep: true,
                    },
                ],
            },
            {
                stepId: 2,
                name: 'Fruits',
                parentStepId: 1,
                items: [
                    {
                        name: 'Apples',
                        description: 'Very delicious',
                        handler: mockedHandler,
                        hasNextStep: false,
                    },
                    {
                        name: 'Citruses',
                        description: 'Very healthy',
                        handler: jasmine.any(Function),
                        hasNextStep: true,
                    },
                ],
            },
            {
                stepId: 3,
                name: 'Citruses',
                parentStepId: 2,
                items: [
                    {
                        name: 'Oranges',
                        description: undefined,
                        handler: mockedHandler,
                        hasNextStep: false,
                    },
                    {
                        name: 'Lemons',
                        description: undefined,
                        handler: mockedHandler,
                        hasNextStep: false,
                    },
                ],
            },
            {
                stepId: 4,
                name: 'Vegetables',
                parentStepId: 1,
                items: [
                    {
                        name: 'Potatoes',
                        description: undefined,
                        handler: mockedHandler,
                        hasNextStep: false,
                    },
                    {
                        name: 'Cucumbers',
                        description: undefined,
                        handler: mockedHandler,
                        hasNextStep: false,
                    },
                ],
            },
        ]);
    });
});
