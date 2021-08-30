import { Component, EventEmitter, Input, OnChanges, Output, SimpleChanges } from '@angular/core';
import { DatePipe } from '@angular/common';
import { TaskContextData } from '../../../../models/task-context';
import { ApplicationHttpClient } from '@gu/services';
import { Result } from '../../../../models/user-search';
import { FormArray, FormBuilder, FormControl, FormGroup, Validators } from '@angular/forms';
import { KetenProcessenService } from '../../keten-processen.service';
import { atleastOneValidator } from '@gu/utils';
import {ReadWriteDocument} from "@gu/models";
import {ModalService} from "@gu/components";

@Component({
  selector: 'gu-config-adviseren-accorderen',
  templateUrl: './adviseren-accorderen.component.html',
  styleUrls: ['../configuration-components.scss']
})
export class AdviserenAccorderenComponent implements OnChanges {
  @Input() taskContextData: TaskContextData;

  @Output() successReload: EventEmitter<boolean> = new EventEmitter<boolean>();

  readonly assignedUsersTitle = {
    advice: 'Adviseurs',
    approval: 'Accordeurs'
  }
  reviewType: 'advice' | 'approval';

  steps = 1;
  minDate = new Date();
  items: Result[] = [];

  assignUsersForm: FormGroup;

  isSubmitting: boolean;
  submitSuccess: boolean;
  submitHasError: boolean;
  submitErrorMessage: string;
  assignedUsersErrorMessage: string;

  constructor(
    private datePipe: DatePipe,
    private fb: FormBuilder,
    private http: ApplicationHttpClient,
    private modalService: ModalService,
    private ketenProcessenService: KetenProcessenService,
  ) {}

  ngOnChanges(changes: SimpleChanges) {
    if (changes.taskContextData.previousValue !== this.taskContextData ) {
      this.reviewType = this.taskContextData.context.reviewType;
      this.assignUsersForm = this.fb.group({
        documents: this.addDocumentCheckboxes(),
        assignedUsers: this.fb.array([this.addAssignUsersStep()]),
        toelichting: this.fb.control("", Validators.maxLength(4000))
      })
    }
  }

  addStep(i) {
    if (this.extraStepControl(i).value) {
      this.steps++
      this.assignedUsers.push(this.addAssignUsersStep());
    } else {
      this.deleteStep();
    }
  }

  deleteStep() {
    this.steps--
    this.assignedUsers.removeAt(this.assignedUsers.length - 1);
  }

  handleDocumentClick(url) {
    this.ketenProcessenService.readDocument(url).subscribe((res: ReadWriteDocument) => {
      window.open(res.magicUrl, "_blank");
    });
  }

  onSearch(searchInput) {
    this.ketenProcessenService.getAccounts(searchInput).subscribe(res => {
      this.items = res.results;
    })
  }

  submitForm() {
    this.isSubmitting = true;

    const selectedDocuments = this.documents.value
      .map((checked, i) => checked ? this.taskContextData.context.documents[i].url : null)
      .filter(v => v !== null);
    const assignedUsers = this.assignedUsers.controls
      .map( (step, i) => {
        const deadline = this.datePipe.transform(this.assignedDeadlineControl(i).value, "yyyy-MM-dd");
        const users = this.assignedUsersControl(i).value;
        return {
          deadline: deadline,
          users: users
        }
      })
    const toelichting = this.toelichting.value;
    const formData = {
      form: this.taskContextData.form,
      assignedUsers: assignedUsers,
      selectedDocuments: selectedDocuments,
      toelichting: toelichting
    };
    this.putForm(formData);
  }

  putForm(formData) {
    this.ketenProcessenService.putTaskData(this.taskContextData.task.id, formData).subscribe(() => {
      this.isSubmitting = false;
      this.submitSuccess = true;
      this.successReload.emit(true);

      this.modalService.close('ketenprocessenModal');
    }, error => {
      this.isSubmitting = false;
      this.assignedUsersErrorMessage = error.assignedUsers[0];
      this.submitErrorMessage = error.detail ? error.detail : "Er is een fout opgetreden";
      this.submitHasError = true;
    })
  }

  addDocumentCheckboxes() {
    const arr = this.taskContextData.context.documents.map(() => {
      return this.fb.control(false);
    });
    return this.fb.array(arr, atleastOneValidator());
  }

  addAssignUsersStep() {
    return this.fb.group({
      deadline: [undefined, Validators.required],
      users: [[], Validators.minLength(1)],
      extraStep: ['']
    })
  }

  get documents(): FormArray {
    return this.assignUsersForm.get('documents') as FormArray;
  };

  get assignedUsers(): FormArray {
    return this.assignUsersForm.get('assignedUsers') as FormArray;
  };

  get toelichting(): FormControl {
    return this.assignUsersForm.get('toelichting') as FormControl;
  };

  assignedUsersControl(index: number): FormControl {
    return this.assignedUsers.at(index).get('users') as FormControl;
  }

  assignedDeadlineControl(index: number): FormControl {
    return this.assignedUsers.at(index).get('deadline') as FormControl;
  }

  extraStepControl(index: number): FormControl {
    return this.assignedUsers.at(index).get('extraStep') as FormControl;
  }

  assignedMinDateControl(index: number): Date {
    const today = new Date();
    if (this.assignedUsers.at(index - 1)) {
      const previousDeadline = this.assignedUsers.at(index - 1).get('deadline').value ? this.assignedUsers.at(index - 1).get('deadline').value : today;
      const dayAfterDeadline = new Date(previousDeadline);
      dayAfterDeadline.setDate(previousDeadline.getDate() + 1);
      return dayAfterDeadline;
    } else {
      return today
    }
  }
}
