import { Component, Input, OnChanges, AfterViewInit } from '@angular/core';
import { ActivatedRoute } from '@angular/router';
import { DatePipe } from '@angular/common';
import { ModalService } from '@gu/components'
import { TaskContextData } from '../../models/task-context';
import { KetenProcessenService } from './keten-processen.service';
import { KetenProcessen, Task } from '../../models/keten-processen';
import { User } from '@gu/models';

@Component({
  selector: 'gu-keten-processen',
  templateUrl: './keten-processen.component.html',
  styleUrls: ['./keten-processen.component.scss']
})

export class KetenProcessenComponent implements OnChanges, AfterViewInit {
  /**
   * A "Ketenproces" is a process that is modelled in the Camunda BPM (Business Process Model).
   * This component allows you to start a new process or execute a process task. Process tasks
   * can also be assigned to a specific user.
   */
  @Input() mainZaakUrl: string;
  @Input() bronorganisatie: string;
  @Input() identificatie: string;
  @Input() currentUser: User;

  data: KetenProcessen[];
  processInstanceId: string;

  isLoading = true;
  hasError: boolean;
  errorMessage: string;

  pipe = new DatePipe("nl-NL");

  // Send Message
  sendMessageErrorMessage: string;
  sendMessageHasError: boolean;

  // Task context data
  taskContextData: TaskContextData;
  isLoadingContext: boolean;
  contextHasError: boolean;
  contextErrorMessage: string;

  // Assign task
  assignTaskTask: Task;

  doRedirectTarget: '_blank' | '_self';

  constructor(
    private route: ActivatedRoute,
    private modalService: ModalService,
    private ketenProcessenService: KetenProcessenService,
  ) { }

  /**
   * Detect a change in the url to get the current url params.
   * Updated data will be fetched if the params change.
   */
  ngOnChanges(): void {
    this.route.params.subscribe( params => {
      this.bronorganisatie = params['bronorganisatie'];
      this.identificatie = params['identificatie'];

      this.fetchCurrentUser();
      this.fetchProcesses();
    });
  }

  /**
   * Check if a the url has the param "user-task". If so,
   * the user task should be opened in a pop-up.
   */
  ngAfterViewInit() {
    this.route.queryParams.subscribe(params => {
      const userTaskId = params['user-task'];
      if (userTaskId) {
        this.executeTask(userTaskId);
      }
    });
  }

  /**
   * Fetches the current user.
   */
  fetchCurrentUser(): void {
    this.ketenProcessenService.getCurrentUser().subscribe( res => {
      this.currentUser = res;
    })
  }

  /**
   * Fetch all the related processes from the zaak.
   */
  fetchProcesses(): void {
    this.isLoading = true;
    this.hasError = false;
    this.errorMessage = '';
    this.hasError = true;
    this.ketenProcessenService.getProcesses(this.mainZaakUrl).subscribe( data => {
      this.data = data;
      this.processInstanceId = data.length > 0 ? data[0].id : null;
      this.isLoading = false;
    }, errorRes => {
      this.errorMessage = errorRes.error.detail;
      this.hasError = true;
      this.isLoading = false;
    })
  }

  /**
   * Send a message to Camunda.
   * The message lets Camunda know which process to start.
   * @param {string} message
   */
  sendMessage(message: string): void {
    this.isLoading = true
    const formData = {
      processInstanceId: this.processInstanceId,
      message: message
    }
    this.ketenProcessenService.sendMessage(formData).subscribe( () => {
      this.fetchProcesses();
    }, errorRes => {
      this.sendMessageErrorMessage = errorRes.error.detail;
      this.sendMessageHasError = true;
      this.isLoading = false;
    })
  }

  /**
   * Open a selected task.
   * @param {string} taskId
   */
  executeTask(taskId: string): void {
    this.fetchFormLayout(taskId);
  }

  /**
   * Assign a selected task to user.
   * Opens up a modal to assign a user to the task.
   * @param {Task} task
   */
  assignTask(task: Task) {
    this.assignTaskTask = task;
    this.modalService.open('assignTaskModal');
  }

  /**
   * Redirects to the given task redirect link.
   * Also checks if the link should be opened in the current window or new window.
   * @param {TaskContextData} taskContext
   */
  doRedirect(taskContext: TaskContextData) {
    if (taskContext.form === 'zac:doRedirect') {
      this.doRedirectTarget = taskContext.context.openInNewWindow ? "_blank" : "_self";
      window.open(taskContext.context.redirectTo, this.doRedirectTarget);
    }
  }

  /**
   * Fetches the data for the task.
   * @param taskId
   */
  fetchFormLayout(taskId: string): void {
    this.contextHasError = false;
    this.isLoadingContext = true;
    this.modalService.open('ketenprocessenModal');
    this.ketenProcessenService.getFormLayout(taskId).subscribe(res => {
      this.doRedirect(res)
      this.taskContextData = res;
      this.isLoadingContext = false;
    }, errorRes => {
      this.contextErrorMessage = "Er is een fout opgetreden bij het laden van de taak."
      this.contextHasError = true;
      this.isLoadingContext = false;
    })
  }
}
