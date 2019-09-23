import './attribution-column-picker.component.less';

import {
    Component,
    ChangeDetectionStrategy,
    EventEmitter,
    Input,
    Output,
    OnInit,
    OnChanges,
} from '@angular/core';
import {
    CLICK_CONVERSION_WINDOWS,
    VIEW_CONVERSION_WINDOWS,
} from './attribution-column-picker.config';
import {ConversionWindow} from '../../../../app.constants';
import {ConversionWindowConfig} from '../../../../core/conversion-pixels/types/conversion-windows-config';
import {PixelColumn} from '../../types/pixel-column';
import {PixelOptionsColumn} from '../../types/pixel-options-column';
import * as pixelHelpers from './helpers/attribution-column-picker.helpers';
import * as arrayHelpers from '../../../../shared/helpers/array.helpers';
import {downgradeComponent} from '@angular/upgrade/static';

@Component({
    selector: 'zem-attribution-column-picker',
    templateUrl: './attribution-column-picker.component.html',
    changeDetection: ChangeDetectionStrategy.OnPush,
})
export class AttributionColumnPickerComponent implements OnInit, OnChanges {
    @Input()
    pixelColumns: PixelColumn[];
    @Output()
    toggleColumn = new EventEmitter<{field: string}>();
    @Output()
    toggleColumns = new EventEmitter<{fields: string[]}>();

    selectedPixel: PixelColumn;
    selectedColumns: PixelOptionsColumn[];
    availableColumns: PixelOptionsColumn[];
    selectedClickConversionWindow: ConversionWindowConfig;
    selectedViewConversionWindow: ConversionWindowConfig;

    isInitialized = false;

    CLICK_CONVERSION_WINDOWS = CLICK_CONVERSION_WINDOWS;
    VIEW_CONVERSION_WINDOWS = VIEW_CONVERSION_WINDOWS;

    ngOnInit() {
        this.selectedPixel = this.getSelectedPixel(this.pixelColumns);
        this.selectedColumns = this.getSelectedColumns(this.selectedPixel);
        this.selectedClickConversionWindow =
            this.getClickConversionWindow(this.selectedColumns) ||
            CLICK_CONVERSION_WINDOWS[0];
        this.selectedViewConversionWindow =
            this.getViewConversionWindow(this.selectedColumns) ||
            VIEW_CONVERSION_WINDOWS[0];
        this.availableColumns = this.getAvailableColumns(
            this.selectedPixel,
            this.selectedClickConversionWindow.value,
            this.selectedViewConversionWindow.value
        );
        this.isInitialized = true;
    }

    ngOnChanges() {
        if (this.isInitialized) {
            const newSelectedPixel = this.getSelectedPixel(this.pixelColumns);
            if (arrayHelpers.isEmpty(newSelectedPixel.columns)) {
                this.selectedPixel.columns = this.selectedPixel.columns.map(
                    column => {
                        return {
                            ...column,
                            visible: false,
                        };
                    }
                );
                this.selectedColumns = this.getSelectedColumns(
                    this.selectedPixel
                );
            } else {
                this.selectedPixel = newSelectedPixel;
                this.selectedColumns = this.getSelectedColumns(
                    this.selectedPixel
                );
                this.selectedClickConversionWindow =
                    this.getClickConversionWindow(this.selectedColumns) ||
                    this.selectedClickConversionWindow;
                this.selectedViewConversionWindow =
                    this.getViewConversionWindow(this.selectedColumns) ||
                    this.selectedViewConversionWindow;
            }
            this.availableColumns = this.getAvailableColumns(
                this.selectedPixel,
                this.selectedClickConversionWindow.value,
                this.selectedViewConversionWindow.value
            );
        }
    }

    onClickConversionWindowChange($event: ConversionWindowConfig) {
        let manualyUpdateComponentState = true;
        const selectedColumns = this.selectedColumns.filter(column => {
            return column.data.attribution === '';
        });
        if (
            $event !== this.selectedClickConversionWindow ||
            !arrayHelpers.isEmpty(selectedColumns)
        ) {
            const fieldsToToggle = pixelHelpers.getFieldsToToggle(
                selectedColumns,
                RegExp(
                    `_${pixelHelpers.mapConversionWindowValue(
                        this.selectedClickConversionWindow.value
                    )}$`
                ),
                `_${pixelHelpers.mapConversionWindowValue($event.value)}`
            );
            if (!arrayHelpers.isEmpty(fieldsToToggle)) {
                manualyUpdateComponentState = false;
                this.toggleColumns.emit({fields: fieldsToToggle});
            }
        }
        if (manualyUpdateComponentState) {
            this.selectedClickConversionWindow = $event;
            this.availableColumns = this.getAvailableColumns(
                this.selectedPixel,
                this.selectedClickConversionWindow.value,
                this.selectedViewConversionWindow.value
            );
        }
    }

    onViewConversionWindowChange($event: ConversionWindowConfig) {
        let manualyUpdateComponentState = true;
        const selectedColumns = this.selectedColumns.filter(column => {
            return column.data.attribution === '_view';
        });
        if (
            $event !== this.selectedViewConversionWindow ||
            !arrayHelpers.isEmpty(selectedColumns)
        ) {
            const fieldsToToggle = pixelHelpers.getFieldsToToggle(
                selectedColumns,
                RegExp(
                    `_${pixelHelpers.mapConversionWindowValue(
                        this.selectedViewConversionWindow.value
                    )}$`
                ),
                `_${pixelHelpers.mapConversionWindowValue($event.value)}`
            );
            if (!arrayHelpers.isEmpty(fieldsToToggle)) {
                manualyUpdateComponentState = false;
                this.toggleColumns.emit({fields: fieldsToToggle});
            }
        }
        if (manualyUpdateComponentState) {
            this.selectedViewConversionWindow = $event;
            this.availableColumns = this.getAvailableColumns(
                this.selectedPixel,
                this.selectedClickConversionWindow.value,
                this.selectedViewConversionWindow.value
            );
        }
    }

    onSelectedPixelChange($event: PixelColumn['name']) {
        let manualyUpdateComponentState = true;
        const newPixel = this.pixelColumns.find((pixel: PixelColumn) => {
            return pixel.name === $event;
        });
        if (!arrayHelpers.isEmpty(this.selectedColumns)) {
            const fieldsToToggle = pixelHelpers.getFieldsToToggle(
                this.selectedColumns,
                RegExp(this.selectedPixel.columns[0].data.pixel),
                newPixel.columns[0].data.pixel
            );
            if (!arrayHelpers.isEmpty(fieldsToToggle)) {
                manualyUpdateComponentState = false;
                this.toggleColumns.emit({fields: fieldsToToggle});
            }
        }
        if (manualyUpdateComponentState) {
            this.selectedPixel = newPixel;
            this.availableColumns = this.getAvailableColumns(
                newPixel,
                this.selectedClickConversionWindow.value,
                this.selectedViewConversionWindow.value
            );
        }
    }

    onColumnToggled($event: boolean, column: PixelOptionsColumn) {
        this.toggleColumn.emit({field: column.field});
    }

    private getSelectedPixel(pixelColumns: PixelColumn[]): PixelColumn {
        if (!arrayHelpers.isEmpty(pixelColumns)) {
            for (const pixel of pixelColumns) {
                const selectedColumns: PixelOptionsColumn[] = pixel.columns.filter(
                    (column: PixelOptionsColumn) => {
                        return column.visible === true;
                    }
                );
                if (!arrayHelpers.isEmpty(selectedColumns)) {
                    return pixel;
                }
            }
        }
        return {
            name: '',
            columns: [],
        };
    }

    private getSelectedColumns(
        selectedPixel: PixelColumn
    ): PixelOptionsColumn[] {
        if (!arrayHelpers.isEmpty(selectedPixel.columns)) {
            return selectedPixel.columns.filter(
                (column: PixelOptionsColumn) => {
                    return column.visible === true;
                }
            );
        }
        return [];
    }

    private getClickConversionWindow(
        selectedColumns: PixelOptionsColumn[]
    ): ConversionWindowConfig {
        if (!arrayHelpers.isEmpty(selectedColumns)) {
            for (const column of selectedColumns) {
                if (column.data.attribution === '') {
                    return CLICK_CONVERSION_WINDOWS.find(
                        (window: ConversionWindowConfig) => {
                            return (
                                column.data.window ===
                                pixelHelpers.mapConversionWindowValue(
                                    window.value
                                )
                            );
                        }
                    );
                }
            }
        }
    }

    private getViewConversionWindow(
        selectedColumns: PixelOptionsColumn[]
    ): ConversionWindowConfig {
        if (!arrayHelpers.isEmpty(selectedColumns)) {
            for (const column of selectedColumns) {
                if (column.data.attribution === '_view') {
                    return VIEW_CONVERSION_WINDOWS.find(
                        (window: ConversionWindowConfig) => {
                            return (
                                column.data.window ===
                                pixelHelpers.mapConversionWindowValue(
                                    window.value
                                )
                            );
                        }
                    );
                }
            }
        }
    }

    private getAvailableColumns(
        selectedPixel: PixelColumn,
        clickConversionWindow: ConversionWindow,
        viewConversionWindow: ConversionWindow
    ): PixelOptionsColumn[] {
        if (!arrayHelpers.isEmpty(selectedPixel.columns)) {
            return selectedPixel.columns.filter(
                (column: PixelOptionsColumn) => {
                    return (
                        (column.data.attribution === '_view' &&
                            column.data.window ===
                                pixelHelpers.mapConversionWindowValue(
                                    viewConversionWindow
                                )) ||
                        (column.data.attribution === '' &&
                            column.data.window ===
                                pixelHelpers.mapConversionWindowValue(
                                    clickConversionWindow
                                ))
                    );
                }
            );
        }
        return [];
    }
}

declare var angular: angular.IAngularStatic;
angular.module('one.downgraded').directive(
    'zemAttributionColumnPicker',
    downgradeComponent({
        component: AttributionColumnPickerComponent,
        inputs: ['pixelColumns'],
        outputs: ['toggleColumn', 'toggleColumns'],
    })
);
