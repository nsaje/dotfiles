import {CommonModule} from '@angular/common';
import {HttpClientModule} from '@angular/common/http';
import {NgModule} from '@angular/core';
import {FormsModule} from '@angular/forms';
import {PortalModule} from '@angular/cdk/portal';
import {HighchartsChartModule} from 'highcharts-angular';
import {
    NgbDatepickerModule,
    NgbPopoverModule,
    NgbPaginationModule,
    NgbDropdownModule,
} from '@ng-bootstrap/ng-bootstrap';
import {NgSelectModule} from '@ng-select/ng-select';
import {NgOptionHighlightModule} from '@ng-select/ng-option-highlight';
import {NgxFileDropModule} from 'ngx-file-drop';
import {AgGridModule} from 'ag-grid-angular';

import {BigNumberPipe} from './pipes/big-number.pipe';
import {FilterKeydownEventDirective} from './directives/filter-keydown-event/filter-keydown-event.directive';
import {FocusDirective} from './directives/focus/focus.directive';
import {CategorizedSelectComponent} from './components/categorized-select/categorized-select.component';
import {CategorizedTagsListComponent} from './components/categorized-tags-list/categorized-tags-list.component';
import {DropdownDirective} from './components/dropdown/dropdown.directive';
import {DropdownToggleDirective} from './components/dropdown/dropdown-toggle.directive';
import {DropdownContentDirective} from './components/dropdown/dropdown-content.directive';
import {HelpPopoverComponent} from './components/help-popover/help-popover.component';
import {DaypartingInputComponent} from './components/dayparting-input/dayparting-input.component';
import {DrawerComponent} from './components/drawer/drawer.component';
import {IntegerInputComponent} from './components/integer-input/integer-input.component';
import {IntegerFormGroupComponent} from './components/integer-form-group/integer-form-group.component';
import {DecimalInputComponent} from './components/decimal-input/decimal-input.component';
import {DecimalFormGroupComponent} from './components/decimal-form-group/decimal-form-group.component';
import {CurrencyInputComponent} from './components/currency-input/currency-input.component';
import {CurrencyFormGroupComponent} from './components/currency-form-group/currency-form-group.component';
import {DateInputComponent} from './components/date-input/date-input.component';
import {DateFormGroupComponent} from './components/date-form-group/date-form-group.component';
import {SelectInputComponent} from './components/select-input/select-input.component';
import {SelectFormGroupComponent} from './components/select-form-group/select-form-group.component';
import {PrefixedInputComponent} from './components/prefixed-input/prefixed-input.component';
import {TextInputComponent} from './components/text-input/text-input.component';
import {TextFormGroupComponent} from './components/text-form-group/text-form-group.component';
import {TextAreaComponent} from './components/textarea/textarea.component';
import {TextAreaFormGroupComponent} from './components/textarea-form-group/textarea-form-group.component';
import {BidModifierInputComponent} from './components/bid-modifier-input/bid-modifier-input.component';
import {PopoverDirective} from './components/popover/popover.directive';
import {ModalComponent} from './components/modal/modal.component';
import {CheckboxInputComponent} from './components/checkbox-input/checkbox-input.component';
import {CheckboxFormGroupComponent} from './components/checkbox-form-group/checkbox-form-group.component';
import {RadioInputComponent} from './components/radio-input/radio-input.component';
import {InternalFeatureDirective} from './directives/internal-feature/internal-feature.directive';
import {FileSelectorComponent} from './components/file-selector/file-selector.component';
import {CommentPopoverComponent} from './components/comment-popover/comment-popover.component';
import {PaginationComponent} from './components/pagination/pagination.component';
import {SmartGridComponent} from './components/smart-grid/smart-grid.component';
import {GridLoadingOverlayComponent} from './components/smart-grid/components/overlays/grid-loading-overlay/grid-loading-overlay.component';
import {NoRowsOverlayComponent} from './components/smart-grid/components/overlays/no-rows-overlay/no-rows-overlay.component';
import {DealEditFormComponent} from './components/deal-edit-form/deal-edit-form.component';
import {SelectListComponent} from './components/select-list/select-list.component';
import {TextHighlightDirective} from './directives/text-highlight/text-highlight.directive';
import {ContentFormGroupComponent} from './components/content-form-group/content-form-group.component';
import {ScopeSelectorCardComponent} from './components/scope-selector/components/scope-selector-card.component';
import {ScopeSelectorComponent} from './components/scope-selector/scope-selector.component';
import {BidModifierTypesGridComponent} from './components/bid-modifier-types-grid/bid-modifier-types-grid.component';
import {ListGroupComponent} from './components/list-group/list-group.component';
import {ImageCheckboxInputComponent} from './components/image-checkbox-input/image-checkbox-input.component';
import {ImageCheckboxInputGroupComponent} from './components/image-checkbox-input-group/image-checkbox-input-group.component';
import {ExpandableSectionComponent} from './components/expandable-section/expandable-section.component';
import {NewFeatureDirective} from './directives/new-feature/new-feature.directive';
import {LoadingOverlayDirective} from './directives/loading-overlay/loading-overlay.directive';
import {ItemScopeCellComponent} from './components/smart-grid/components/cells/item-scope-cell/item-scope-cell.component';
import {PublisherGroupEditFormComponent} from './components/publisher-group-edit-form/publisher-group-edit-form.component';
import {ConnectionActionsCellComponent} from './components/connection-actions-cell/connection-actions-cell.component';
import {IconTooltipCellComponent} from './components/smart-grid/components/cells/icon-tooltip-cell/icon-tooltip-cell.component';
import {NoteCellComponent} from './components/smart-grid/components/cells/note-cell/note-cell.component';
import {LinkCellComponent} from './components/smart-grid/components/cells/link-cell/link-cell.component';
import {PortalComponent} from './components/portal/portal.component';
import {AlertComponent} from './components/alert/alert.component';
import {ListGroupItemComponent} from './components/list-group/components/list-group-item/list-group-item.component';
import {CheckboxSliderComponent} from './components/checkbox-slider/checkbox-slider.component';
import {ItemListComponent} from './components/item-list/item-list.component';
import {SwitchButtonCellComponent} from './components/smart-grid/components/cells/switch-button-cell/switch-button-cell.component';
import {EntitySelectorComponent} from './components/entity-selector/entity-selector.component';
import {ArchivedTagDirective} from './directives/archived-tag/archived-tag.directive';
import {PinnedRowCellComponent} from './components/smart-grid/components/cells/pinned-row-cell/pinned-row-cell.component';
import {HeaderCellComponent} from './components/smart-grid/components/cells/header-cell/header-cell.component';
import {CheckboxCellComponent} from './components/smart-grid/components/cells/checkbox-cell/checkbox-cell.component';
import {MultiStepComponent} from './components/multi-step/multi-step.component';
import {MultiStepStepDirective} from './components/multi-step/multi-step-step.directive';
import {TagPickerComponent} from './components/tag-picker/tag-picker.component';
import {LoaderComponent} from './components/loader/loader.component';
import {ButtonComponent} from './components/button/button.component';
import {TagFormGroupComponent} from './components/tag-form-group/tag-form-group.component';
import {TabsComponent} from './components/tabs/tabs.component';
import {TabDirective} from './components/tabs/tab.directive';
import {MultiStepMenuComponent} from './components/multi-step-menu/multi-step-menu.component';
import {ThumbnailCellComponent} from './components/thumbnail-cell/thumbnail-cell.component';
import {DisplayAdPreviewComponent} from './components/display-ad-preview/display-ad-preview.component';
import {NativeAdPreviewComponent} from './components/native-ad-preview/native-ad-preview.component';

const EXPORTED_DECLARATIONS = [
    // Pipes
    BigNumberPipe,

    // Directives
    FilterKeydownEventDirective,
    FocusDirective,
    PopoverDirective,
    InternalFeatureDirective,
    NewFeatureDirective,
    ArchivedTagDirective,
    TextHighlightDirective,
    LoadingOverlayDirective,

    // Components
    CategorizedSelectComponent,
    CategorizedTagsListComponent,
    DropdownDirective,
    DropdownToggleDirective,
    DropdownContentDirective,
    DrawerComponent,
    DaypartingInputComponent,
    CheckboxInputComponent,
    CheckboxFormGroupComponent,
    RadioInputComponent,
    IntegerInputComponent,
    IntegerFormGroupComponent,
    DecimalInputComponent,
    DecimalFormGroupComponent,
    CurrencyInputComponent,
    CurrencyFormGroupComponent,
    DateInputComponent,
    DateFormGroupComponent,
    SelectInputComponent,
    SelectFormGroupComponent,
    PrefixedInputComponent,
    TextInputComponent,
    TextFormGroupComponent,
    TextAreaComponent,
    TextAreaFormGroupComponent,
    BidModifierInputComponent,
    ModalComponent,
    HelpPopoverComponent,
    CommentPopoverComponent,
    FileSelectorComponent,
    ContentFormGroupComponent,
    PaginationComponent,
    SmartGridComponent,
    GridLoadingOverlayComponent,
    NoRowsOverlayComponent,
    DealEditFormComponent,
    SelectListComponent,
    ScopeSelectorCardComponent,
    ScopeSelectorComponent,
    BidModifierTypesGridComponent,
    ListGroupComponent,
    ListGroupItemComponent,
    ImageCheckboxInputComponent,
    ImageCheckboxInputGroupComponent,
    ExpandableSectionComponent,
    ItemScopeCellComponent,
    IconTooltipCellComponent,
    NoteCellComponent,
    LinkCellComponent,
    PublisherGroupEditFormComponent,
    ConnectionActionsCellComponent,
    PortalComponent,
    AlertComponent,
    CheckboxSliderComponent,
    ItemListComponent,
    SwitchButtonCellComponent,
    EntitySelectorComponent,
    PinnedRowCellComponent,
    HeaderCellComponent,
    CheckboxCellComponent,
    MultiStepComponent,
    MultiStepStepDirective,
    TagPickerComponent,
    TagFormGroupComponent,
    LoaderComponent,
    ButtonComponent,
    TabsComponent,
    TabDirective,
    MultiStepMenuComponent,
    ThumbnailCellComponent,
    NativeAdPreviewComponent,
    DisplayAdPreviewComponent,
];

@NgModule({
    imports: [
        CommonModule,
        HttpClientModule,
        FormsModule,
        PortalModule,
        HighchartsChartModule,
        NgbDatepickerModule,
        NgSelectModule,
        NgOptionHighlightModule,
        NgbPopoverModule,
        NgbDropdownModule,
        NgxFileDropModule,
        AgGridModule.withComponents([
            GridLoadingOverlayComponent,
            NoRowsOverlayComponent,
            ItemScopeCellComponent,
            IconTooltipCellComponent,
            NoteCellComponent,
            LinkCellComponent,
            SwitchButtonCellComponent,
            PinnedRowCellComponent,
            HeaderCellComponent,
            CheckboxCellComponent,
        ]),
        NgbPaginationModule,
    ],
    declarations: EXPORTED_DECLARATIONS,
    exports: [
        CommonModule,
        FormsModule,
        PortalModule,
        HighchartsChartModule,
        ...EXPORTED_DECLARATIONS,
    ],
    entryComponents: [
        ConnectionActionsCellComponent,
        ThumbnailCellComponent,
        NativeAdPreviewComponent,
        DisplayAdPreviewComponent,
    ],
})
export class SharedModule {}
