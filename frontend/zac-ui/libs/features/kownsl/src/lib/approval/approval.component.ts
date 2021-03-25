import { Component, OnInit } from '@angular/core';
import { DatePipe } from '@angular/common';
import { ReviewRequest } from '../../models/review-request';
import { Zaak } from '../../models/zaak';
import { ApprovalService } from './approval.service';
import { RowData, Table } from '@gu/models';
import { FormBuilder, FormGroup, Validators } from '@angular/forms';
import { ApprovalForm } from '../../models/approval-form';
import { ActivatedRoute, Router } from '@angular/router';

@Component({
  selector: 'gu-features-kownsl-approval',
  templateUrl: './approval.component.html',
  styleUrls: ['../features-kownsl.component.scss']
})
export class ApprovalComponent implements OnInit {
  uuid: string;
  zaakUrl: string;

  approvalData: ReviewRequest;
  isLoading: boolean;

  isSubmitting: boolean;
  submitSuccess: boolean;
  submitFailed: boolean;

  hasError: boolean;
  errorMessage: string;

  isNotLoggedIn: boolean;
  readonly NOT_LOGGED_IN_MESSAGE = "Authenticatiegegevens zijn niet opgegeven.";

  loginUrl: string;

  tableData: Table = new Table ([], []);

  approvalForm: FormGroup;

  pipe = new DatePipe("nl-NL");

  constructor(
    private fb: FormBuilder,
    private approvalService: ApprovalService,
    private route: ActivatedRoute,
    private router: Router
  ) { }

  ngOnInit(): void {
    this.uuid = this.route.snapshot.queryParams["uuid"];
    if (this.uuid) {
      this.fetchApproval()
      this.approvalForm = this.fb.group({
        approved: this.fb.control("", Validators.required),
        toelichting: this.fb.control("")
      })
    } else {
      this.errorMessage = "Er is geen geldig zaaknummer gevonden..."
    }
  }

  fetchApproval(): void {
    this.isLoading = true;
    this.approvalService.getApproval(this.uuid).subscribe(res => {
      this.setZaakUrl(res.body.zaak);
      const isSubmittedBefore = res.headers.get('X-Kownsl-Submitted');
      if (isSubmittedBefore === "false") {
        this.approvalData = res.body;
        this.tableData = this.createTableData(res.body);
      } else {
        this.hasError = true;
        this.errorMessage = "U heeft deze aanvraag al beantwoord.";
      }
      this.isLoading = false;
    }, res => {
      this.errorMessage = res.error.detail;
      if (this.errorMessage === this.NOT_LOGGED_IN_MESSAGE) {
        this.setLoginUrl()
        this.isNotLoggedIn = true;
      }
      this.hasError = true;
      this.isLoading = false;
    })
  }

  setZaakUrl(zaakData: Zaak): void {
    this.zaakUrl = `/zaken/${zaakData.bronorganisatie}/${zaakData.identificatie}`;
  }

  setLoginUrl(): void {
    const currentPath = this.router.url;
    this.loginUrl = `/accounts/login/?next=/ui${currentPath}`;
  }

  createTableData(approvalData: ReviewRequest): Table {
    const tableData: Table = new Table(['Accordeur', 'Gedaan op', 'Akkoord'], []);

    // Add table body data
    tableData.bodyData = approvalData.reviews.map( review => {
      const author = `${review.author.firstName} ${review.author.lastName}`;
      const date = this.pipe.transform(review.created, 'short');
      const approved = review.approved ? 'Akkoord' : 'Niet Akkoord';
      const rowData: RowData = {
        cellData: {
          author: author ? author : '',
          created: date ? date : '',
          approved: approved
        },
        expandData: review.toelichting
      }
      return rowData
    });

    return tableData;
  }

  submitForm(): void {
    const formData: ApprovalForm = {
      approved: this.approvalForm.controls['approved'].value,
      toelichting: this.approvalForm.controls['toelichting'].value
    }
    this.postApproval(formData);
  }

  postApproval(formData: ApprovalForm): void {
    this.isSubmitting = true;
    this.approvalService.postApproval(formData, this.uuid).subscribe(data => {
      this.isSubmitting = false;
      this.submitSuccess = true;
    }, error => {
      this.errorMessage = "Er is een fout opgetreden bij het verzenden van uw gegevens..."
      this.submitFailed = true;
      this.isSubmitting = false;
    })
  }
}
