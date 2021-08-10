import { Component, EventEmitter, Input, OnChanges, OnInit, Output, SimpleChanges } from '@angular/core';
import { FormBuilder, FormControl, FormGroup, Validators } from '@angular/forms';
import { Result } from '../../models/zaaktype';
import { ZaaktypeEigenschap } from '../../models/zaaktype-eigenschappen';
import { FeaturesSearchService } from '../features-search.service';
import { Search } from '../../models/search';
import { Zaak, TableSort } from '@gu/models';
import { Router } from '@angular/router';
import { DatePipe } from '@angular/common';

/**
 * This component allows the user to search Zaken dynamically.
 * Selecting a zaaktype will show its corresponding properties,
 * which can be choosed to further refine the search query.
 *
 * The user can also save the given search input as a report by
 * selecting the checkbox and give te report a name.
 */
@Component({
  selector: 'gu-search-form',
  templateUrl: './search-form.component.html',
  styleUrls: ['./search-form.component.scss']
})
export class SearchFormComponent implements OnInit, OnChanges {
  @Input() sortData: TableSort;
  @Output() loadResult: EventEmitter<Zaak[]> = new EventEmitter<Zaak[]>();

  searchForm: FormGroup
  formData: Search;

  zaaktypenData: Result[];
  zaaktypeEigenschappenData: ZaaktypeEigenschap[] = [];

  selectedPropertyValue: ZaaktypeEigenschap;

  isLoading: boolean;
  isSubmitting: boolean;
  hasError: boolean;
  errorMessage: string;

  showReportNameField: boolean;
  reportName: string;
  saveReportIsSuccess: boolean;

  constructor(
    private fb: FormBuilder,
    private searchService: FeaturesSearchService,
    private router: Router,
    private datePipe: DatePipe
  ) { }

  ngOnInit(): void {
    this.searchForm = this.fb.group({
      zaaktype: [''],
      omschrijving: [''],
      eigenschapnaam: [''],
      eigenschapwaarde: [''],
      saveReport: [''],
      queryName: ['']
    })
    this.fetchZaaktypen();
  }

  ngOnChanges(changes: SimpleChanges) {
    if (changes.sortData.previousValue !== this.sortData ) {
      this.postSearchZaken(this.formData, this.sortData);
    }
  }

  /**
   * Fetch all the different zaak types.
   */
  fetchZaaktypen() {
    this.isLoading = true;
    this.hasError = false;
    this.searchService.getZaaktypen().subscribe(res => {
      this.isLoading = false;
      this.zaaktypenData = res.results;
    }, error => {
      this.isLoading = false;
      this.hasError = true;
      this.errorMessage = error.error.detail ? error.error.detail : "Er is een fout opgetreden bij het ophalen van zaaktypen."
    })
  }

  /**
   * Fetch the properties of a case type based on the selection.
   * @param {Result} zaaktype
   */
  onZaaktypeSelect(zaaktype: Result) {
    if (zaaktype) {
      this.isLoading = true;
      this.hasError = false;

      const catalogus = zaaktype.catalogus;
      const omschrijving = zaaktype.omschrijving;

      this.searchService.getZaaktypeEigenschappen(catalogus, omschrijving).subscribe(res => {
        this.zaaktypeEigenschappenData = res;
        this.eigenschapnaam.patchValue(undefined);
        this.isLoading = false;
      }, error => {
        this.isLoading = false;
        this.hasError = true;
        this.errorMessage = error.error.detail ? error.error.detail : "Er is een fout opgetreden bij het ophalen van zaakeigenschappen."
      })
    } else {
      this.zaaktypeEigenschappenData = [];
    }
  }

  /**
   * Set the selected property value
   * @param {ZaaktypeEigenschap} property
   */
  onPropertySelect(property: ZaaktypeEigenschap) {
    this.selectedPropertyValue = property;
  }


  /**
   * Show input for report name and set it as required for the form.
   */
  onCheckboxChange() {
    this.saveReportControl.updateValueAndValidity({ onlySelf: false, emitEvent: true });
    if (this.saveReportControl.value) {
      this.showReportNameField = true;
      this.queryNameControl.setValidators([Validators.required])
    } else {
      this.showReportNameField = false;
      this.queryNameControl.clearValidators();
    }
    this.queryNameControl.updateValueAndValidity();
  }

  /**
   * Create form data.
   */
  submitForm() {
    this.hasError = false;
    this.saveReportIsSuccess = false;

    // Check if zaaktype has been filled in
    let zaaktype;
    if (this.zaaktype.value) {
      this.zaaktypenData.forEach( zaaktypeElement => {
        if (zaaktypeElement.identificatie === this.zaaktype.value)
          zaaktype = {
            omschrijving: zaaktypeElement.omschrijving,
            catalogus: zaaktypeElement.catalogus
          }
      });
    }

    // Create object for eigenschappen
    const eigenschapValue =
      this.selectedPropertyValue?.spec.format === 'date' ?
        this.datePipe.transform(this.eigenschapwaarde.value, "yyyy-MM-dd") :
        this.eigenschapwaarde.value;

    const eigenschappen = {
      [this.eigenschapnaam.value]: {
        value: eigenschapValue
      }
    }

    // Only add key with values if the values are present
    this.formData = {
      ...zaaktype && {zaaktype: zaaktype},
      ...this.omschrijving.value && {omschrijving: this.omschrijving.value},
      ...(this.eigenschapnaam.value && this.eigenschapwaarde.value) && {eigenschappen: eigenschappen}
    }

    this.postSearchZaken(this.formData)

    // Check if the user wants to save the search query as a report
    if (this.saveReportControl.value) {
      this.reportName = this.queryNameControl.value;
      this.postCreateReport(this.reportName, this.formData)
    }
  }

  /**
   * POST search query.
   * @param {Search} formData
   * @param {TableSort} sortData
   */
  postSearchZaken(formData: Search, sortData?: TableSort) {
    this.isSubmitting = true;
    this.searchService.postSearchZaken(formData, sortData).subscribe(res =>{
      this.loadResult.emit(res.results);
      this.isSubmitting = false;
    }, error => {
      this.hasError = true;
      this.errorMessage = error.error.detail ? error.error.detail : "Er is een fout opgetreden bij het zoeken."
      this.isSubmitting = false;
    })
  }

  /**
   * Save the current search query as a Report.
   * @param {string} name
   * @param {Search} query
   */
  postCreateReport(name: string, query: Search) {
    const formData = {
      name: name,
      query: query
    }
    this.searchService.postCreateReport(formData).subscribe(
      () => {
        this.saveReportIsSuccess = true;
        this.saveReportControl.patchValue(false);
        this.queryNameControl.patchValue('');
      },
      error => {
        console.error(error);
      }
    )
  }

  get zaaktype(): FormControl {
    return this.searchForm.get('zaaktype') as FormControl;
  };

  get omschrijving(): FormControl {
    return this.searchForm.get('omschrijving') as FormControl;
  };

  get eigenschapnaam(): FormControl {
    return this.searchForm.get('eigenschapnaam') as FormControl;
  };

  get eigenschapwaarde(): FormControl {
    return this.searchForm.get('eigenschapwaarde') as FormControl;
  };

  get saveReportControl(): FormControl {
    return this.searchForm.get('saveReport') as FormControl;
  };

  get queryNameControl(): FormControl {
    return this.searchForm.get('queryName') as FormControl;
  };
}
