import {Component, Input} from '@angular/core';
import {Observable} from 'rxjs';
import {Author, ReviewRequestDetails, ReviewRequestSummary} from '@gu/kownsl';
import {ExtensiveCell, ReadWriteDocument, RowData, Table} from '@gu/models';
import {ApplicationHttpClient} from '@gu/services';
import {Review, ReviewDocument} from './detail-modal.interface';


/**
 * <gu-detail-modal [reviewRequestDetails]="reviewRequestDetails"></gu-gu-detail-modal>
 *
 * Show review details.
 *
 * Requires reviewRequestDetails: ReviewRequestDetails input to show in a modal.
 */
@Component({
  selector: 'gu-detail-modal',
  templateUrl: './detail-modal.component.html',
  styleUrls: ['./detail-modal.component.scss']
})
export class DetailModalComponent  {
  @Input() reviewRequestDetails: ReviewRequestDetails;
  @Input() reviewRequestSummary: ReviewRequestSummary;


  constructor(private http: ApplicationHttpClient) {
  }

  //
  // Getters / setters.
  //

  /**
   * Returns the title to render.
   * @return {string}
   */
  get title(): string {
    switch (this.reviewRequestDetails?.reviewType) {
      case 'approval':
        return 'Accorderingen';
      case 'advice':
        return 'Adviezen';
      default:
        return '';
    }
  }

  /**
   * Return the table to render.
   * @return {Table}
   */
  get table(): Table {
    if(this.reviewRequestDetails?.approvals) {
      return this.formatTableDataApproval(this.reviewRequestDetails)
    }

    if(this.reviewRequestDetails?.advices){
      return this.formatTableDataAdvice(this.reviewRequestDetails)
    }

    return null;
  }

  //
  // Context.
  //


  /**
   * Returns table for advices of reviewRequestDetails.
   * @param {ReviewRequestDetails} reviewRequestDetails
   * @return {Table}
   */
  formatTableDataAdvice(reviewRequestDetails: ReviewRequestDetails): Table {
    const headData = ['Advies', 'Van', 'Gegeven op', 'Documentadviezen'];

    const bodyData = reviewRequestDetails.advices.map((review: Review) => {
      const author = this.getAuthorName(review.author);
      const docAdviezen = review.documents ? review.documents.length.toString() : '-';
      const reviewDocumentTableData = review.documents?.length > 0 ? this.formatTableReviewDoc(review.documents) : null;

      const cellData: RowData = {
        cellData: {
          advies: review.advice,
          van: author,

          datum: {
            type: review.created ? 'date' : 'text',
            date: review.created
          } as ExtensiveCell,

          docAdviezen: docAdviezen
        },
        nestedTableData: reviewDocumentTableData,
      }
      return cellData;
    })

    return new Table(headData, bodyData);
  }

  /**
   * Returns table for approvals of reviewRequestDetails.
   * @param {ReviewRequestDetails} reviewRequestDetails
   * @return {Table}
   */
  formatTableDataApproval(reviewRequestDetails: ReviewRequestDetails): Table {
    const headData = ['Resultaat', 'Van', 'Gegeven op', 'Toelichting'];

    const bodyData = reviewRequestDetails.approvals.map((review: Review) => {
      const author = this.getAuthorName(review.author);

      const icon = review.status === 'Akkoord' ? 'done' : 'close'
      const iconColor = review.status === 'Akkoord' ? 'green' : 'red'

      const cellData: RowData = {
        cellData: {
          akkoord: {
            type: 'icon',
            label: icon,
            iconColor: iconColor
          } as ExtensiveCell,

          van: author,
          datum: {
            type: review.created ? 'date' : 'text',
            date: review.created
          } as ExtensiveCell,

          toelichting: review.toelichting
        }
      }

      return cellData;
    })

    return new Table(headData, bodyData);
  }

  /**
   * Returns table for review documents.
   * @param {ReviewDocument[]} reviewDocumentss
   * @return {Table}
   */
  formatTableReviewDoc(reviewDocuments: ReviewDocument[]): Table {
    const headData = ['Document', 'Originele versie', 'Aangepaste versie'];

    const bodyData = reviewDocuments.map((doc: ReviewDocument) => {
      return {
        cellData: {
          title: doc.title,

          source: {
            type: 'button',
            label: doc.sourceVersion.toString(10),
            value: doc.sourceUrl
          } as ExtensiveCell,

          advice: {
            type: 'button',
            label: doc.adviceVersion.toString(10),
            value: doc.adviceUrl
          } as ExtensiveCell,
        }
      }
    })

    return new Table(headData, bodyData);
  }

  /**
   * Returns the string representation for the author.
   * @param {Author} author
   * @return {string}
   */
  getAuthorName(author: Author): string {
    return author['firstName'] ? `${author['firstName']} ${author['lastName']}` : author['username'];
  }

  //
  // Events.
  //
  /**
   * Gets called when a table row is clicked.
   * @param {Object} action
   */
  tableClick(action: object): void {
    const actionType = Object.keys(action)[0];
    const endpoint = action[actionType];
    this.readDocument(endpoint).subscribe((res: ReadWriteDocument) => {
      window.open(res.magicUrl, "_blank");
    });
  }

  readDocument(endpoint): Observable<ReadWriteDocument> {
    return this.http.Post<ReadWriteDocument>(endpoint);
  }
}
